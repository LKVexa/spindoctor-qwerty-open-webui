#!/usr/bin/env python3
# Test transport through actual native Open WebUI Tools and authenticated downloads.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from native_env import prepare
from native_host import NativeHost


async def main():
    protocol = sys.stdout.buffer  # explicit UTF-8 bytes, independent of the inherited Windows console encoding
    incoming = sys.stdin.buffer
    sys.stdout = sys.stderr
    base = prepare(Path(tempfile.mkdtemp(prefix="spindoctor-webui-native-e2e-")))
    host = await NativeHost().start(base)
    from open_webui.models.tools import Tools
    from open_webui.utils.tools import get_tools
    verified_downloads = 0

    async def configured(arguments):
        incoming = arguments.pop("workspace", None) or os.environ.get("SPINDOCTOR_WORKSPACE")
        if incoming:
            host.workspace_root = Path(incoming).resolve() / "native-workspaces"
            host.valves["workspace_root"] = str(host.workspace_root)
            await Tools.update_tool_valves_by_id(host.tool_id, host.valves)
            host.tools = await get_tools(host.request, [host.tool_id], host.user, {"__user__": host.user.model_dump(), "__request__": host.request, "__event_emitter__": host.emitter})
        if arguments.get("path"):
            path = Path(arguments.pop("path"))
            file = await host.upload(path.name, path.read_bytes())
            arguments["file_id"] = file["id"]
        script = arguments.get("script", "")
        match = re.search(r'q\.folder run path="([^"]+)"', script)
        if match:
            folder = Path(match.group(1)).resolve()
            destination = host.workspace() / "test-folder"
            destination.mkdir(parents=True, exist_ok=True)
            # Trusted test fixtures are placed inside the private directory before native dispatch.
            for file in folder.iterdir():
                if file.is_file() and not file.is_symlink():
                    (destination / file.name).write_bytes(file.read_bytes())
            arguments["script"] = script.replace(match.group(0), 'q.folder run path="test-folder"')
        return arguments

    async def reconstructed(value):
        nonlocal verified_downloads
        paths = []
        def find(item):
            if isinstance(item, dict):
                for child in item.values():
                    find(child)
            elif isinstance(item, list):
                for child in item:
                    find(child)
            elif isinstance(item, str) and item.startswith("[private]") and item.lower().endswith(".pdf"):
                relative = item[len("[private]"):].replace("\\", "/").lstrip("/")
                if relative.startswith("reports/"):
                    paths.append(relative)
        find(value)
        downloaded = {}
        existing = {item["report_name"]: item for item in value.get("downloads", [])}
        for relative in dict.fromkeys(paths):
            pdf = Path(relative)
            txt_name = pdf.with_suffix(".txt").relative_to("reports").as_posix()
            if pdf.relative_to("reports").as_posix() not in existing or txt_name not in existing:
                reports, _ = await host.call("spindoctor_report", {"name": txt_name})
                existing.update({item["report_name"]: item for item in reports.get("downloads", [])})
            for item_path in [pdf, pdf.with_suffix(".txt")]:
                card = existing.get(item_path.relative_to("reports").as_posix())
                if not card:
                    raise ValueError("Expected authenticated report download missing: " + item_path.name)
                response = await host.download(card["id"])
                response.raise_for_status()
                source = host.workspace() / item_path
                observed_hash = hashlib.sha256(response.content).hexdigest()
                private_bytes = source.read_bytes()
                private_hash = hashlib.sha256(private_bytes).hexdigest()
                if observed_hash != private_hash:
                    mismatch = {"relative_report": item_path.as_posix(), "native_file_id": card["id"], "http_status": response.status_code, "download_bytes": len(response.content), "private_bytes": len(private_bytes), "download_sha256": observed_hash, "private_sha256": private_hash, "private_source": str(source)}
                    (base / "report-mismatch.json").write_text(json.dumps(mismatch, indent=2), encoding="utf-8")
                    raise ValueError("Native download differs from private engine report: " + json.dumps(mismatch))
                case = hashlib.sha256(str(host.workspace()).encode("utf-8")).hexdigest()
                output = base / "downloaded" / case / item_path
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(response.content)
                downloaded["[private]/" + item_path.as_posix()] = str(output)
                verified_downloads += 1
        def replace(item):
            if isinstance(item, dict):
                return {key: replace(child) for key, child in item.items()}
            if isinstance(item, list):
                return [replace(child) for child in item]
            if isinstance(item, str):
                return downloaded.get(item.replace("\\", "/"), item)
            return item
        return replace(value)

    try:
        while True:
            line = await asyncio.to_thread(incoming.readline)
            if not line:
                break
            request = None
            try:
                request = json.loads(line)
                if "id" not in request:
                    continue
                if request["method"] == "initialize":
                    result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "spindoctor-open-webui-native-test-bridge", "version": "1.1.0"}}
                elif request["method"] == "tools/list":
                    result = {"tools": [{"name": name, "description": tool["spec"]["description"], "inputSchema": tool["spec"]["parameters"]} for name, tool in host.tools.items()]}
                elif request["method"] == "tools/call":
                    params = request["params"]
                    arguments = await configured(dict(params.get("arguments") or {}))
                    value, text = await host.call(params["name"], arguments)
                    (base / "last-tool-result.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
                    framed = await reconstructed(value)
                    result = {"content": [{"type": "text", "text": text}], "structuredContent": framed, "isError": not value.get("ok", True)}
                else:
                    raise ValueError("Unsupported test method")
                response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
            except Exception as error:
                response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None, "error": {"code": -32000, "message": str(error)}}
            protocol.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
            protocol.flush()
    finally:
        await host.close()
        (base / "bridge-receipt.json").write_text(json.dumps({"verified_native_downloads": verified_downloads, "boundary": "Native DB Valves configured per case before get_tools, true toolkit calls and byte-verified authenticated native downloads. Parsed structuredContent and reconstructed local report paths are test framing."}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
