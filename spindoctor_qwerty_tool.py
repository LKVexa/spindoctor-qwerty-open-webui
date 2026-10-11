"""
title: SpinDoctor Qwerty
author: RUSSELL PHILIP SMITHSON
author_email: russellsmithson77@outlook.com
version: 1.1.0
license: GPL-3.0-or-later
description: SpinDoctor 3.1.2 classical FP64 simulator: six tools, 241 presets, 298 logical qubits and private authenticated theory/report downloads.
required_open_webui_version: 0.12.0
"""
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
import re
import sys
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        engine_dir: str = Field(default="", description="Stable absolute server path to this release's engine folder; configure outside the temporary tool module.")
        workspace_root: str = Field(default="", description="Absolute external private-workspace parent; default ~/spindoctor-workspace/open-webui. Each verified user has a separate hashed directory.")
        python_executable: str = Field(default="", description="Absolute Python executable; defaults to the Open WebUI interpreter. Engine needs Python3.8+.")
        timeout_seconds: int = Field(default=600, ge=1, le=1800, description="Engine child timeout; cancellation terminates and reaps the child.")
        max_downloads: int = Field(default=32, ge=1, le=64, description="Maximum report files copied into native authenticated storage per call; originals remain private.")

    def __init__(self):
        self.valves = self.Valves()
        self._locks = {}

    async def _identity(self, injected, request):
        if request is None or not isinstance(injected, dict) or not injected.get("id"):
            raise ValueError("A verified Open WebUI user and host-injected request are required")
        from open_webui.utils.auth import get_verified_user_by_id
        user = await get_verified_user_by_id(injected["id"])
        if user is None or user.role not in {"user", "admin"}:
            raise ValueError("A verified active user is required")
        return user

    def _paths(self, user):
        engine = Path(self.valves.engine_dir)
        if not self.valves.engine_dir or not engine.is_absolute():
            raise ValueError("Configure an absolute engine_dir Valve on the Open WebUI server")
        engine = engine.resolve()
        runner = (engine.parent / "support/engine_runner.py").resolve()
        if not (engine / "spindoctor/api.py").is_file() or not runner.is_file():
            raise ValueError("engine_dir must point to the complete release engine and adjacent support folder")
        parent = Path(self.valves.workspace_root) if self.valves.workspace_root else Path.home() / "spindoctor-workspace/open-webui"
        if not parent.is_absolute():
            raise ValueError("workspace_root must be an absolute path")
        parent = parent.resolve()
        install = engine.parent
        if parent == install or install in parent.parents or parent in install.parents:
            raise ValueError("Private workspaces must remain separate from the installation")
        digest = hashlib.sha256(user.id.encode("utf-8")).hexdigest()
        workspace = parent / digest
        if workspace.resolve() != workspace:
            raise ValueError("Private workspace links are unavailable")
        workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
        executable = Path(self.valves.python_executable or sys.executable)
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError("Configure an existing absolute Python executable")
        return engine, runner, workspace, executable

    @staticmethod
    def _contained(value, workspace):
        path = Path(value)
        if not path.is_absolute():
            path = workspace / path
        path = path.resolve()
        if path != workspace and workspace not in path.parents:
            raise ValueError("File paths must remain in this user's private workspace")
        return path

    async def _input_file(self, file_id, user, workspace):
        from open_webui.models.files import Files
        from open_webui.routers.files import has_access_to_file
        from open_webui.storage.provider import Storage
        file = await Files.get_file_by_id(file_id)
        if not file or (file.user_id != user.id and not await has_access_to_file(file_id, "read", user)):
            raise ValueError("Input file is unavailable to this user")
        size = (file.meta or {}).get("size", 0)
        if not isinstance(size, int) or size > 5 * 1024 * 1024:
            raise ValueError("Input file exceeds the 5 MiB limit")
        source = Path(await asyncio.to_thread(Storage.get_file, file.path))
        if not source.is_file() or source.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Input file is unavailable or exceeds the limit")
        directory = self._contained("host-inputs", workspace)
        directory.mkdir(exist_ok=True)
        name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename).name)[:160] or "input.txt"
        destination = self._contained(directory / (str(uuid.UUID(file.id)) + "-" + name), workspace)
        def bounded_input():
            with source.open("rb") as stream:
                return stream.read(5 * 1024 * 1024 + 1)
        data = await asyncio.to_thread(bounded_input)
        if len(data) > 5 * 1024 * 1024:
            raise ValueError("Input file changed or exceeds the limit")
        await asyncio.to_thread(destination.write_bytes, data)
        return destination

    async def _spawn(self, *arguments, **options):
        return await asyncio.create_subprocess_exec(*arguments, **options)

    async def _engine(self, name, arguments, paths):
        engine, runner, workspace, executable = paths
        encoded = json.dumps({"name": name, "arguments": arguments}, ensure_ascii=False).encode("utf-8")
        if len(encoded) > 2 * 1024 * 1024:
            raise ValueError("Tool arguments exceed the 2 MiB limit")
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", SPINDOCTOR_NO_NUMPY="1", SPINDOCTOR_WORKSPACE=str(workspace))
        process = await self._spawn(str(executable), "-I", "-B", "-X", "utf8", str(runner), "--engine", str(engine), "--workspace", str(workspace),
                    cwd=workspace, env=environment, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        tasks = []
        async def bounded(stream, maximum):
            chunks = []
            length = 0
            while True:
                chunk = await stream.read(65536)
                if not chunk:
                    return b"".join(chunks)
                length += len(chunk)
                if length > maximum:
                    raise ValueError("Engine output exceeds the configured boundary")
                chunks.append(chunk)
        try:
            async def feed():
                process.stdin.write(encoded)
                await process.stdin.drain()
                process.stdin.close()
            tasks = [asyncio.create_task(bounded(process.stdout, 32 * 1024 * 1024)), asyncio.create_task(bounded(process.stderr, 65536)), asyncio.create_task(process.wait()), asyncio.create_task(feed())]
            stdout, stderr, code, _ = await asyncio.wait_for(asyncio.gather(*tasks), self.valves.timeout_seconds)
            try:
                result = json.loads(stdout.decode("utf-8"))
            except (ValueError, UnicodeError):
                raise ValueError("Engine returned an invalid result") from None
            if not isinstance(result, dict):
                raise ValueError("Engine returned an invalid result")
            return result
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.wait()
            for task in tasks:
                if not task.done():
                    task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _downloads(self, result, user, request, workspace, emitter):
        candidates = []
        def collect(value, key=""):
            if isinstance(value, dict):
                for childkey, child in value.items():
                    collect(child, childkey)
            elif isinstance(value, list):
                for child in value:
                    collect(child, key)
            elif isinstance(value, str) and (key in {"reports", "pdf", "path"}):
                try:
                    candidate = self._contained(Path("reports") / value if key == "reports" and not Path(value).is_absolute() else value, workspace)
                    reports = (workspace / "reports").resolve()
                    if reports in candidate.parents and candidate.is_file() and candidate.suffix.lower() in {".txt", ".json", ".csv", ".pdf", ".html"}:
                        candidates.append(candidate)
                except ValueError:
                    pass
        collect(result)
        candidates = list(dict.fromkeys(candidates))
        cards = []
        from open_webui.routers.files import upload_file_handler
        from starlette.datastructures import UploadFile, Headers
        for path in candidates[:self.valves.max_downloads]:
            if path.stat().st_size > 32 * 1024 * 1024:
                continue
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            with path.open("rb") as stream:
                upload = UploadFile(file=stream, filename=path.name, headers=Headers({"content-type": mime}))
                stored = await upload_file_handler(request=request, file=upload, metadata={}, process=False, process_in_background=False, user=user)
            meta = {"name": stored.filename, "content_type": mime, "size": stored.meta.get("size", path.stat().st_size)}
            cards.append({"type": "file", "id": stored.id, "url": stored.id, "name": stored.filename, "content_type": mime, "size": meta["size"], "meta": meta, "report_name": path.relative_to((workspace / "reports").resolve()).as_posix()})
        if cards and emitter:
            # The native saved-chat emitter extends its supplied list with historical cards.
            # Keep this call's response independent and emit only the native card whitelist.
            emitted = [{key: (dict(value) if key == "meta" else value) for key, value in card.items() if key != "report_name"} for card in cards]
            await emitter({"type": "files", "data": {"files": emitted}})
        return cards, max(0, len(candidates) - self.valves.max_downloads)

    @staticmethod
    def _public(value, workspace, engine):
        if isinstance(value, dict):
            return {key: Tools._public(child, workspace, engine) for key, child in value.items() if key not in {"workspace", "reportsDir", "folderPath"}}
        if isinstance(value, list):
            return [Tools._public(child, workspace, engine) for child in value]
        if isinstance(value, str):
            paths = [str(workspace), workspace.as_posix(), str(engine), engine.as_posix(), str(engine.parent), engine.parent.as_posix()]
            variants = []
            for private in paths:
                variants.extend([private, json.dumps(private)[1:-1], json.dumps(json.dumps(private)[1:-1])[1:-1]])
            for private in sorted(set(variants), key=len, reverse=True):
                value = value.replace(private, "[private]")
            return value
        return value

    async def _call(self, name, arguments, injected, request, emitter):
        try:
            user = await self._identity(injected, request)
            paths = self._paths(user)
            workspace = paths[2]
            lock = self._locks.setdefault(user.id, asyncio.Lock())
            async with lock:
                arguments = dict(arguments)
                file_id = arguments.pop("file_id", "")
                if file_id:
                    arguments["path"] = str(await self._input_file(file_id, user, workspace))
                elif arguments.get("path"):
                    arguments["path"] = str(self._contained(arguments["path"], workspace))
                if arguments.get("name"):
                    self._contained(arguments["name"], workspace / "reports")
                result = await self._engine(name, arguments, paths)
                if name == "spindoctor_functions" and result.get("ok"):
                    return result["markdown"]
                cards, remaining = await self._downloads(result, user, request, workspace, emitter)
                public = self._public(result, workspace, paths[0])
                if file_id:
                    public["input_name"] = str(Path(arguments["path"]).relative_to(workspace)).replace("\\", "/")
                public["downloads"] = [{"id": card["id"], "name": card["name"], "report_name": card["report_name"], "url": "/api/v1/files/" + card["id"] + "/content?attachment=true"} for card in cards]
                public["download_links"] = "\n".join("[" + card["report_name"].replace("[", "_").replace("]", "_") + "](/api/v1/files/" + card["id"] + "/content?attachment=true)" for card in cards)
                if remaining:
                    public["downloads_remaining"] = remaining
                return json.dumps(public, ensure_ascii=False)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logging.getLogger(__name__).exception("SpinDoctor tool operation failed")
            message = str(error) if isinstance(error, ValueError) else "Open WebUI tool operation failed; consult server logs"
            if "paths" in locals():
                message = self._public(message, paths[2], paths[0])
            return json.dumps({"ok": False, "error": message})

    async def spindoctor_functions(self, section: Literal["commands", "gates", "tools", "presets", "all"] = "commands", filter: str = "", __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """Return the complete function Markdown table; show it verbatim on first use or help/functions requests.
        :param section: commands, gates, tools, presets or all.
        :param filter: Optional case-insensitive text filter.
        """
        if section not in {"commands", "gates", "tools", "presets", "all"}:
            return json.dumps({"ok": False, "error": "Invalid function section"})
        return await self._call("spindoctor_functions", {"section": section, "filter": filter}, __user__, __request__, __event_emitter__)

    async def spindoctor_run_script(self, script: str, __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """Run q.* commands in this user's private classical workspace; return results and authenticated report downloads.
        :param script: Newline-separated q.* script, at most 200 commands; file I/O stays inside the private workspace.
        """
        if not isinstance(script, str) or len(script.encode("utf-8")) > 1024 * 1024 or sum(1 for line in script.splitlines() if line.strip() and not line.strip().startswith(("#", "//"))) > 200:
            return json.dumps({"ok": False, "error": "Script must be text within 1 MiB and 200 commands"})
        return await self._call("spindoctor_run_script", {"script": script}, __user__, __request__, __event_emitter__)

    async def spindoctor_run_preset(self, preset_id: str, overrides: Optional[dict[str, str]] = None, __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """Run qc-001 through qc-241 with string-valued overrides in this user's private workspace.
        :param preset_id: Preset ID such as qc-061.
        :param overrides: Optional dictionary with string values.
        """
        if not re.fullmatch(r"qc-\d{3}", preset_id or "") or not 1 <= int(preset_id[3:]) <= 241 or (overrides is not None and (not isinstance(overrides, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in overrides.items()))):
            return json.dumps({"ok": False, "error": "Use qc-001 through qc-241 and string-valued overrides"})
        return await self._call("spindoctor_run_preset", {"preset_id": preset_id, "overrides": overrides or {}}, __user__, __request__, __event_emitter__)

    async def spindoctor_list_presets(self, filter: str = "", __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """List or filter all 241 SpinDoctor presets.
        :param filter: Optional text such as grover or qec.
        """
        return await self._call("spindoctor_list_presets", {"filter": filter}, __user__, __request__, __event_emitter__)

    async def spindoctor_report(self, name: str = "", limit: int = 20, __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """List or read this user's private TXT reports and provide authenticated downloads.
        :param name: Relative report name, for example qc-061.txt; traversal and external paths are refused.
        :param limit: Recent report count, from 1 to 100.
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            return json.dumps({"ok": False, "error": "Report limit must be an integer from 1 to 100"})
        return await self._call("spindoctor_report", {"name": name, "limit": limit}, __user__, __request__, __event_emitter__)

    async def spindoctor_test_theory(self, source: Literal["file", "text", "chat"] = "text", action: Literal["extract", "run"] = "run", path: str = "", file_id: str = "", text: str = "", hypothesis: str = "", prediction: str = "", script: str = "", checks: Optional[list[dict]] = None, excerpts: Optional[list[str]] = None, assumptions: Optional[list[str]] = None, variables: Optional[list[str]] = None, title: str = "", isolate: bool = True, __user__: Optional[dict] = None, __request__=None, __event_emitter__=None) -> str:
        """Extract or test local text/file or a user-confirmed chat theory; first summarize claims, assumptions, variables and prediction and obtain confirmation. Classical simulation only.
        :param source: file, text or chat; chat text must be the user's confirmed summary.
        :param action: extract source only, or run the simulator and prediction checks.
        :param path: Private relative path; for a host upload prefer its actual file_id.
        :param file_id: Actual Open WebUI upload UUID; native ownership/read access is verified before copying.
        :param text: Pasted theory or confirmed chat summary.
        :param hypothesis: Hypothesis to test.
        :param prediction: Measurable prediction.
        :param script: Newline-separated q.* commands; defaults to source commands.
        :param checks: Probability, value or ok machine-check dictionaries.
        :param excerpts: Optional quoted chat excerpts.
        :param assumptions: Assumptions of the simulated model.
        :param variables: Variables of the theory.
        :param title: Optional report title.
        :param isolate: Use a fresh sub-workspace for this theory, default true.
        """
        if source not in {"file", "text", "chat"} or action not in {"extract", "run"}:
            return json.dumps({"ok": False, "error": "Invalid theory source or action"})
        return await self._call("spindoctor_test_theory", {"source": source, "action": action, "path": path, "file_id": file_id, "text": text, "hypothesis": hypothesis, "prediction": prediction, "script": script, "checks": checks or [], "excerpts": excerpts or [], "assumptions": assumptions or [], "variables": variables or [], "title": title, "isolate": isolate}, __user__, __request__, __event_emitter__)
