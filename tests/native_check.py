#!/usr/bin/env python3
# Genuine Open WebUI native registry, storage, ownership and event checks.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import traceback
import uuid
from native_env import prepare
from native_host import NativeHost, RELEASE


async def run(base):
    checks = []
    def check(name, passed, detail=None):
        checks.append({"name": name, "pass": bool(passed), "detail": detail})
        print(("PASS " if passed else "FAIL ") + name, flush=True)
    host = await NativeHost().start(base)
    try:
        check("genuine installed host version is 0.12.0", importlib.metadata.version("open-webui") == "0.12.0")
        check("native metadata has full author version and GPL", host.frontmatter.get("author") == "RUSSELL PHILIP SMITHSON" and host.frontmatter.get("version") == "1.1.0" and host.frontmatter.get("license") == "GPL-3.0-or-later")
        check("native loader temporary source is deleted", not Path(host.module.__file__).exists())
        check("actual DB registry exposes exactly six tools", len(host.tools) == 6 and set(host.tools) == {"spindoctor_functions", "spindoctor_run_script", "spindoctor_run_preset", "spindoctor_list_presets", "spindoctor_report", "spindoctor_test_theory"})
        check("host schemas hide injected arguments and server workspace", all(not any(key.startswith("__") or key == "workspace" for key in tool["spec"]["parameters"]["properties"]) for tool in host.tools.values()))
        value, text = await host.call("spindoctor_functions", {})
        check("native persisted Valves work after temporary module deletion", value.get("ok") and "| Function |" in text and "298" in text)
        check("function result is raw Markdown", not text.startswith("{") and "| What it does |" in text)
        value, _ = await host.call("spindoctor_list_presets", {})
        check("native dispatcher lists 241 presets", value.get("count") == 241)
        value, text = await host.call("spindoctor_run_script", {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 64 basis z\nq.circuit result"})
        check("native script creates state and authentic report downloads", value.get("ok") and len(value.get("downloads", [])) >= 4 and (host.workspace() / "spindoctor-cartridge-session.json").exists(), value)
        check("model result hides server workspace and engine paths", str(host.workspace()) not in text and str(RELEASE) not in text and "file://" not in text)
        downloads = value.get("downloads", [])
        pdf = next(item for item in downloads if item["name"].endswith(".pdf"))
        from open_webui.models.files import Files
        record = await Files.get_file_by_id(pdf["id"])
        owner = await host.download(pdf["id"])
        check("native stored file belongs to verified injected user", record.user_id == host.user.id)
        check("authenticated HTTP PDF download is byte exact", owner.status_code == 200 and owner.content == Path(record.path).read_bytes() and owner.content.startswith(b"%PDF-1."))
        check("download MIME and attachment filename are native", owner.headers.get("content-type", "").startswith("application/pdf") and owner.headers.get("content-disposition", "").startswith("attachment;") and pdf["name"] in owner.headers["content-disposition"])
        check("unauthenticated download is denied", (await host.download(pdf["id"], authenticated=False)).status_code == 401)
        check("unrelated ungranted user download is denied", (await host.download(pdf["id"], user=host.other)).status_code == 404)
        check("native admin policy allows cross-user download", (await host.download(pdf["id"], user=host.admin)).status_code == 200)
        check("nonexistent UUID returns 404", (await host.download(str(uuid.uuid4()))).status_code == 404)
        from open_webui.models.chats import Chats
        cards = await Chats.get_message_metadata(host.chat_id, host.message_id, "files")
        check("real saved-chat emitter persists actual file cards", isinstance(cards, list) and any(item["id"] == pdf["id"] for item in cards))
        check("native event cards have no storage path or user email", all("path" not in item and "@" not in json.dumps(item) and item["url"] == item["id"] for item in cards))
        originals = [host.workspace() / "reports" / item["report_name"] for item in downloads if item["name"].endswith(".pdf")][:2]
        collision = host.workspace() / "reports" / "collision"
        collision.mkdir()
        def copy_pair(source, target):
            target.with_suffix(".pdf").write_bytes(source.read_bytes())
            target.with_suffix(".txt").write_bytes(source.with_suffix(".txt").read_bytes())
        copy_pair(originals[0], collision / "same")
        old, _ = await host.call("spindoctor_report", {"name": "collision/same.txt"})
        old_ids = {item["id"] for item in old.get("downloads", [])}
        old_pdf = next(item for item in old["downloads"] if item["report_name"].endswith(".pdf"))
        old_bytes = (await host.download(old_pdf["id"])).content
        copy_pair(originals[1], collision / "same")
        current, _ = await host.call("spindoctor_report", {"name": "collision/same.txt"})
        current_ids = {item["id"] for item in current.get("downloads", [])}
        current_pdf = next(item for item in current["downloads"] if item["report_name"].endswith(".pdf"))
        current_bytes = await host.download(current_pdf["id"])
        history = await Chats.get_message_metadata(host.chat_id, host.message_id, "files")
        check("native saved-chat mutation cannot add stale downloads to current response", len(old_ids) == len(current_ids) == 2 and old_ids.isdisjoint(current_ids) and {item["report_name"] for item in current["downloads"]} == {"collision/same.txt", "collision/same.pdf"})
        check("changed same-name report downloads its current exact engine PDF", current_bytes.status_code == 200 and current_bytes.content == originals[1].read_bytes() and current_bytes.content != old_bytes)
        check("saved chat preserves both generations without leaking internal mapping fields", old_ids | current_ids <= {item["id"] for item in history} and all("report_name" not in item for item in history))
        nested = collision / "nested"
        nested.mkdir()
        copy_pair(originals[0], nested / "same")
        listed, _ = await host.call("spindoctor_report", {"limit": 2})
        check("duplicate basenames have distinct contained logical report names", {item["report_name"] for item in listed.get("downloads", [])} == {"collision/same.txt", "collision/nested/same.txt"})
        pairs = []
        for name in ["collision/same.txt", "collision/nested/same.txt"]:
            result, _ = await host.call("spindoctor_report", {"name": name})
            card = next(item for item in result["downloads"] if item["report_name"].endswith(".pdf"))
            fetched = await host.download(card["id"])
            pairs.append(fetched.status_code == 200 and fetched.content == (host.workspace() / "reports" / card["report_name"]).read_bytes())
        check("both duplicate-basename UUID downloads match their exact private files", all(pairs))
        from open_webui.utils.tools import get_tools
        other_tools = await get_tools(host.request, [host.tool_id], host.other, {"__user__": host.other.model_dump(), "__request__": host.request})
        check("native unshared toolkit ACL rejects another user", not other_tools)
        from open_webui.models.access_grants import AccessGrants
        await AccessGrants.set_access_grants("tool", host.tool_id, [{"principal_type": "user", "principal_id": host.other.id, "permission": "read"}])
        other_tools = await get_tools(host.request, [host.tool_id], host.other, {"__user__": host.other.model_dump(), "__request__": host.request})
        other_result = json.loads(await other_tools["spindoctor_run_script"]["callable"](script="q.circuit new other_private 1"))
        check("shared toolkit uses separate private per-user state", other_result.get("ok") and host.workspace(host.other) != host.workspace() and (host.workspace(host.other) / "spindoctor-cartridge-session.json").exists() and "other_private" not in (host.workspace() / "spindoctor-cartridge-session.json").read_text())
        from open_webui.utils.plugin import load_tool_module_by_id
        failures = []
        for source in ["class Other: pass", "class Tools:\n def broken(: pass"]:
            try:
                await load_tool_module_by_id("broken_" + uuid.uuid4().hex, content=source)
                failures.append(False)
            except Exception:
                failures.append(True)
        check("native loader rejects missing Tools and syntax errors", all(failures))
        value, _ = await host.call("spindoctor_run_script", {"script": "q.circuit result"})
        check("state persists across native tool calls", value.get("ok"))
        value, _ = await host.call("spindoctor_run_preset", {"preset_id": "qc-001"})
        check("native preset execution succeeds", value.get("ok"), value.get("error"))
        value, _ = await host.call("spindoctor_report", {"name": "qc-001.txt"})
        check("native report reads persisted text and attaches PDF twin", value.get("ok") and bool(value.get("text")) and any(item["name"].endswith(".pdf") for item in value.get("downloads", [])), value.get("error"))
        check("model TXT output hides JSON-escaped Windows private paths", all(variant not in value.get("text", "") for path in [str(host.workspace()), str(RELEASE)] for variant in [path, json.dumps(path)[1:-1]]))
        value, _ = await host.call("spindoctor_run_script", {"script": "q.circuit new invalid 299"})
        check("engine failure remains an explicit result", value.get("ok") is False)
        for name, arguments in [("spindoctor_report", {"name": "../../outside.txt"}), ("spindoctor_test_theory", {"source": "wrong", "action": "extract", "text": "data"}), ("spindoctor_run_preset", {"preset_id": "qc-001", "overrides": {"shots": []}})]:
            value, _ = await host.call(name, arguments)
            check("wrapper rejects invalid " + name + " input", value.get("ok") is False)
        external = base / "external-private.txt"
        external.write_text("PRIVATE-EXTERNAL-SENTINEL", encoding="utf-8")
        value, text = await host.call("spindoctor_run_script", {"script": 'q.input add path="' + external.as_posix() + '"'})
        check("child audit rejects external script file read", value.get("ok") is False and "PRIVATE-EXTERNAL-SENTINEL" not in text)
        value, _ = await host.call("spindoctor_test_theory", {"source": "file", "action": "extract", "path": str(external)})
        check("wrapper rejects external theory file path", value.get("ok") is False)
        private_folder = host.workspace() / "folder with spaces"
        private_folder.mkdir()
        (private_folder / "commands.txt").write_text("q.circuit new private_folder 1\nq.circuit add h 0\nq.circuit run shots 32 basis z\n", encoding="utf-8")
        value, _ = await host.call("spindoctor_run_script", {"script": 'q.folder run verify=false path="folder with spaces" downloads=false purge=false samples=17'})
        job = ((value.get("results") or [{}])[0].get("result") or {}).get("job") or {}
        check("relative private folder preserves parsed flags and completes", value.get("ok") and job.get("phase") == "completed" and job.get("completedFiles") == 1 and job.get("verificationRequired") is False and job.get("verificationSamples") == 17 and job.get("downloads") is False and job.get("purge") is False, job)
        value, text = await host.call("spindoctor_run_script", {"script": 'q.folder run path="../outside" verify=false'})
        check("relative folder traversal is rejected before ingestion", value.get("ok") is False and "private workspace" in text)
        theory = b"Theory: H prepares balanced outcomes.\nq.circuit new input_theory 1\nq.circuit add h 0\nq.circuit run shots 2048 basis z\n"
        native_input = await host.upload("theory.txt", theory)
        value, _ = await host.call("spindoctor_test_theory", {"source": "file", "file_id": native_input["id"], "hypothesis": "Balanced outcomes", "prediction": "P(1)=0.5", "checks": [{"kind": "probability", "outcome": "1", "expected": 0.5, "tolerance": 0.08}]})
        check("owned native upload is staged and theory tested", value.get("verdict") == "supported" and any(item["name"].endswith(".pdf") for item in value.get("downloads", [])), value.get("error"))
        import base64
        import runpy
        pdf_fixture = runpy.run_path(str(RELEASE / "engine/examples/theory/make_sample_pdfs.py"))["PDFS"]["hadamard_theory.pdf"]
        native_pdf = await host.upload("hadamard_theory.pdf", base64.b64decode(pdf_fixture))
        value, _ = await host.call("spindoctor_test_theory", {"source": "file", "action": "extract", "file_id": native_pdf["id"]})
        extracted = value.get("extracted", {})
        check("owned native PDF upload extracts the kit theory text", value.get("ok") and extracted.get("fileType") == ".pdf" and "q.circuit" in extracted.get("text", "") and "Hadamard" in extracted.get("text", ""), extracted)
        foreign = await host.upload("foreign.txt", b"UNGRANTED-FOREIGN-SENTINEL", user=host.other)
        value, text = await host.call("spindoctor_test_theory", {"source": "file", "action": "extract", "file_id": foreign["id"]})
        check("foreign native upload cannot bypass ownership", value.get("ok") is False and "UNGRANTED-FOREIGN-SENTINEL" not in text)
        value, _ = await host.call("spindoctor_test_theory", {"source": "chat", "text": "Confirmed: H prepares balanced outcomes.", "hypothesis": "Balanced outcomes", "prediction": "P(1)=0.5", "script": theory.decode().split("\n", 1)[1], "checks": [{"kind": "probability", "outcome": "1", "expected": 0.5, "tolerance": 0.08}], "excerpts": ["User: Confirmed."]})
        check("confirmed chat theory creates native PDF download", value.get("verdict") == "supported" and any(item["name"].endswith(".pdf") for item in value.get("downloads", [])))
        from open_webui.utils.middleware import execute_tool_call
        spoofed = {"script": "q.circuit new spoof_owner 1", "__user__": host.other.model_dump(), "__request__": None, "workspace": str(host.workspace(host.other))}
        params, observed, _, _, _ = await execute_tool_call({"messages": []}, {"tools": host.tools, "params": {}}, None, {"id": "spoof-check", "function": {"name": "spindoctor_run_script", "arguments": json.dumps(spoofed)}})
        check("actual middleware strips forged reserved and workspace arguments", set(params) == {"script"} and json.loads(observed).get("ok") and "spoof_owner" in (host.workspace() / "spindoctor-cartridge-session.json").read_text() and "spoof_owner" not in (host.workspace(host.other) / "spindoctor-cartridge-session.json").read_text())
        instance = host.instance
        instance.valves = instance.Valves(**host.valves)
        tracked = []
        async def track_spawn(*arguments, **options):
            process = await asyncio.create_subprocess_exec(*arguments, **options)
            tracked.append(process)
            return process
        instance._spawn = track_spawn
        fixture = base / "child_fixture.py"
        fixture.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
        paths = (RELEASE / "engine", fixture, host.workspace(), Path(sys.executable))
        instance.valves.timeout_seconds = 1
        try:
            await instance._engine("spindoctor_functions", {"text": "x" * (1024 * 1024)}, paths)
            timeout = False
        except asyncio.TimeoutError:
            timeout = True
        check("timeout includes blocked stdin and reaps child", timeout and tracked[-1].returncode is not None)
        instance.valves.timeout_seconds = 30
        task = asyncio.create_task(instance._engine("spindoctor_functions", {}, paths))
        for _ in range(100):
            if len(tracked) == 2:
                break
            await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
            canceled = False
        except asyncio.CancelledError:
            canceled = True
        check("cancellation propagates and reaps child", canceled and len(tracked) == 2 and tracked[-1].returncode is not None)
        fixture.write_text("import sys\nsys.stdout.buffer.write(b'x' * (32 * 1024 * 1024 + 65536))\nsys.stdout.flush()\n", encoding="utf-8")
        try:
            await instance._engine("spindoctor_functions", {}, paths)
            overflow = False
        except ValueError as error:
            overflow = "boundary" in str(error)
        check("output overflow terminates and reaps child", overflow and tracked[-1].returncode is not None)
        check("tool imports never add engine to host sys.path", str(RELEASE / "engine") not in sys.path)
        check("source and engine contain no Python caches", not list(RELEASE.rglob("*.pyc")) and not list(RELEASE.rglob("__pycache__")))
        return {"host": "Open WebUI 0.12.0", "passed": sum(item["pass"] for item in checks), "total": len(checks), "checks": checks,
                "base": str(base), "chat_id": host.chat_id, "message_id": host.message_id, "user_id": host.user.id,
                "tool_id": host.tool_id, "persisted_file_ids": [item["id"] for item in cards], "verified_pdf": {"id": pdf["id"], "sha256": hashlib.sha256(owner.content).hexdigest()},
                "boundary": "Genuine installed loader, native DB/get_tools injection, local child engine, native upload and saved-chat emitter, and actual authenticated ASGI file routes. No full CLI app, model or browser."}
    except Exception:
        checks.append({"name": "remaining native suite completed", "pass": False, "detail": traceback.format_exc()})
        return {"host": "Open WebUI 0.12.0", "passed": sum(item["pass"] for item in checks), "total": len(checks), "checks": checks, "base": str(base)}
    finally:
        await host.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    options = parser.parse_args()
    base = prepare(options.base)
    try:
        result = asyncio.run(run(base))
    except Exception:
        result = {"passed": 0, "total": 1, "error": traceback.format_exc()}
    Path(options.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
