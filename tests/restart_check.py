#!/usr/bin/env python3
# Native DB/tool/card/download persistence across a separate Python process.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import traceback
from native_env import prepare
from native_host import session_token


async def run(receipt):
    from fastapi import FastAPI
    from starlette.requests import Request
    from open_webui.models.users import Users
    from open_webui.models.tools import Tools
    from open_webui.models.chats import Chats
    from open_webui.models.files import Files
    from open_webui.routers.files import router
    from open_webui.utils.tools import get_tools
    import httpx
    app = FastAPI()
    app.state.redis = None
    app.include_router(router, prefix="/api/v1/files")
    request = Request({"type": "http", "method": "POST", "path": "/api/chat/completions", "headers": [], "app": app, "query_string": b""})
    user = await Users.get_user_by_id(receipt["user_id"])
    tool = await Tools.get_tool_by_id(receipt["tool_id"])
    valves = await Tools.get_tool_valves_by_id(receipt["tool_id"])
    cards = await Chats.get_message_metadata(receipt["chat_id"], receipt["message_id"], "files")
    registry = await get_tools(request, [receipt["tool_id"]], user, {"__user__": user.model_dump(), "__request__": request})
    result = json.loads(await registry["spindoctor_report"]["callable"](name="qc-001.txt"))
    file = await Files.get_file_by_id(receipt["verified_pdf"]["id"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://native-test") as http:
        response = await http.get("/api/v1/files/" + file.id + "/content?attachment=true", headers={"Authorization": "Bearer " + await session_token(user)})
    checks = [{"name": "native DB source and six schemas survive process restart", "pass": bool(tool) and len(tool.specs) == 6},
              {"name": "actual persisted Valves reload six native callables", "pass": bool(valves.get("engine_dir")) and len(registry) == 6},
              {"name": "private engine state/report survives process restart", "pass": result.get("ok") is True and bool(result.get("text"))},
              {"name": "saved-chat native file cards survive process restart", "pass": set(receipt["persisted_file_ids"]) <= {item["id"] for item in cards}},
              {"name": "native file owner survives process restart", "pass": file.user_id == user.id},
              {"name": "authenticated restarted download is byte exact", "pass": response.status_code == 200 and hashlib.sha256(response.content).hexdigest() == receipt["verified_pdf"]["sha256"]}]
    return {"passed": sum(item["pass"] for item in checks), "total": len(checks), "checks": checks, "boundary": "Separate-process native DB/registry/files/router restart, not a full CLI/server restart."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    prepare(receipt["base"])
    try:
        result = asyncio.run(run(receipt))
    except Exception:
        result = {"passed": 0, "total": 1, "error": traceback.format_exc()}
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
