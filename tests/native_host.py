# Actual native DB registry, injected Tools and authenticated file routes.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
import os
from pathlib import Path
import sys
import secrets
import time
import uuid

RELEASE = Path(__file__).resolve().parents[1]


async def session_token(user):
    """Issue the same account-stamped session claims used by native sign-in."""
    from open_webui.models.auths import Auths
    from open_webui.utils.auth import create_token
    auth = await Auths.get_auth_by_id(user.id)
    if not auth or not auth.active or not auth.session_stamp:
        raise ValueError("Native test account has no active stamped Auth record")
    return create_token({"id": user.id, "typ": "session", "auth_method": "password", "auth_time": int(time.time()), "session_stamp": auth.session_stamp, "mfa_verified": False})


class NativeHost:
    async def start(self, base):
        self.base = Path(base).resolve()
        print("Importing genuine Open WebUI loader/registry", file=sys.stderr, flush=True)
        from fastapi import FastAPI
        from starlette.requests import Request
        from open_webui.models.auths import Auths
        from open_webui.models.tools import Tools, ToolForm, ToolMeta
        from open_webui.models.chats import Chats, ChatForm
        from open_webui.routers.files import router
        from open_webui.utils.plugin import load_tool_module_by_id
        from open_webui.utils.tools import get_tool_specs, get_tools
        from open_webui.utils.auth import get_password_hash
        from open_webui.socket.main import get_event_emitter
        import httpx
        self.app = FastAPI()
        self.app.state.redis = None
        self.app.include_router(router, prefix="/api/v1/files")
        self.request = Request({"type": "http", "method": "POST", "path": "/api/chat/completions", "headers": [], "app": self.app, "query_string": b""})
        password = await get_password_hash(secrets.token_urlsafe(32))
        self.user = await Auths.insert_new_auth("user@example.com", password, "Integration user", role="user")
        self.other = await Auths.insert_new_auth("you@example.com", password, "Other integration user", role="user")
        self.admin = await Auths.insert_new_auth("admin-" + uuid.uuid4().hex + "@example.com", password, "Integration admin", role="admin")
        self.tokens = {user.id: await session_token(user) for user in [self.user, self.other, self.admin]}
        self.source = (RELEASE / "spindoctor_qwerty_tool.py").read_text(encoding="utf-8")
        self.tool_id = "spindoctor_qwerty_" + uuid.uuid4().hex
        self.instance, self.frontmatter, self.module = await load_tool_module_by_id(self.tool_id, content=self.source)
        self.tool_specs = get_tool_specs(self.instance)
        self.record = await Tools.insert_new_tool(self.user.id, ToolForm(id=self.tool_id, name="SpinDoctor Qwerty", content=self.source, meta=ToolMeta(description="Native integration test")), self.tool_specs, module=self.instance)
        self.workspace_root = self.base / "workspaces"
        self.valves = {"engine_dir": str(RELEASE / "engine"), "workspace_root": str(self.workspace_root), "python_executable": sys.executable, "max_downloads": 64}
        await Tools.update_tool_valves_by_id(self.tool_id, self.valves)
        self.chat_id = str(uuid.uuid4())
        self.message_id = str(uuid.uuid4())
        message = {"id": self.message_id, "role": "assistant", "content": "", "files": []}
        self.chat = await Chats.insert_new_chat(self.chat_id, self.user.id, ChatForm(chat={"title": "SpinDoctor native integration test", "history": {"currentId": self.message_id, "messages": {self.message_id: message}}}))
        self.emitter = await get_event_emitter({"user_id": self.user.id, "chat_id": self.chat_id, "message_id": self.message_id}, update_db=True)
        self.http = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://native-test")
        self.tools = await get_tools(self.request, [self.tool_id], self.user, {"__user__": self.user.model_dump(), "__request__": self.request, "__event_emitter__": self.emitter})
        print("Genuine native registry loaded", file=sys.stderr, flush=True)
        return self

    def workspace(self, user=None):
        return self.workspace_root / hashlib.sha256((user or self.user).id.encode()).hexdigest()

    async def call(self, name, arguments):
        text = await self.tools[name]["callable"](**arguments)
        value = {"ok": True, "markdown": text} if name == "spindoctor_functions" and not text.startswith("{") else json.loads(text)
        return value, text

    async def upload(self, filename, data, user=None):
        user = user or self.user
        result = await self.http.post("/api/v1/files/?process=false", headers={"Authorization": "Bearer " + self.tokens[user.id]}, files={"file": (filename, data)})
        result.raise_for_status()
        return result.json()

    async def download(self, file_id, user=None, authenticated=True):
        headers = {"Authorization": "Bearer " + self.tokens[(user or self.user).id]} if authenticated else {}
        return await self.http.get("/api/v1/files/" + file_id + "/content?attachment=true", headers=headers)

    async def close(self):
        await self.http.aclose()
