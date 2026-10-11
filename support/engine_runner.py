#!/usr/bin/env python3
# SpinDoctor isolated Open WebUI engine runner 1.1.0
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run the unchanged engine with an explicit private I/O boundary."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--workspace", required=True)
    options = parser.parse_args()
    engine = Path(options.engine).resolve()
    workspace = Path(options.workspace).resolve()
    os.chdir(workspace)
    os.environ["SPINDOCTOR_WORKSPACE"] = str(workspace)
    sys.path.insert(0, str(engine))  # confined to this short-lived child, never the host
    from spindoctor import api, functions, theory, folder, inputs, csvreport  # preload trusted lazy modules before the I/O boundary
    import ctypes  # engine memory observations may import this lazily
    import ctypes.wintypes
    import codecs
    for encoding in ["utf-8-sig", "utf-16", "utf-16-be", "utf-16-le", "latin-1"]:
        codecs.lookup(encoding)  # report/PDF writers may initialize these codecs lazily
    try:
        import resource  # Unix read-only process accounting
    except ImportError:
        pass
    try:
        import pypdf  # use the installed optional parser without imports after the I/O boundary
    except ImportError:
        pass  # the approved engine retains its built-in PDF text extractor

    readonly = {(engine / "spindoctor/data/SPINDOCTOR_PRESETS.json").resolve(),
                (engine / "spindoctor/data/SPINDOCTOR_COMMAND_CATALOGUE.txt").resolve()}
    # Read-only OS memory observations are used by the unchanged engine on Linux.
    readonly.update({Path("/proc/meminfo").resolve(), Path("/proc/self/status").resolve()})

    def permitted(value, write=False):
        if isinstance(value, int):
            return
        if not isinstance(value, (str, bytes, os.PathLike)):
            raise PermissionError("Tool file access requires a private workspace path")
        path = Path(os.fsdecode(value)).resolve()
        if path == workspace or workspace in path.parents:
            return
        if not write and path in readonly:
            return
        raise PermissionError("Tool file access must remain in this user's private workspace")

    def audit(event, arguments):
        if event == "open":
            path, mode, flags = arguments
            write = (isinstance(mode, str) and any(ch in mode for ch in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            permitted(path, write)
        elif event in {"os.listdir", "os.scandir", "os.chdir"}:
            permitted(arguments[0])
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate", "os.utime"}:
            permitted(arguments[0], True)
        elif event in {"os.rename", "os.link", "os.symlink"}:
            permitted(arguments[0], True)
            permitted(arguments[1], True)
            if event in {"os.link", "os.symlink"}:
                raise PermissionError("Tool-created links are unavailable")
        elif event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.spawn"}:
            raise PermissionError("Engine network and process creation are unavailable")

    sys.addaudithook(audit)

    def private_folder_script(script):
        lines = []
        for line in script.splitlines():
            tokens = line.strip().split(None, 2)
            if len(tokens) >= 2 and [token.lower() for token in tokens[:2]] == ["q.folder", "run"]:
                fields = folder.parse_fields(line.strip())
                if fields.get("path"):
                    # Check the resolved destination, but keep lexical link components
                    # for the approved engine's independent reparse-point check.
                    path = os.path.abspath(os.path.join(str(workspace), fields["path"]))
                    permitted(path)
                    if any('"' in value for value in fields.values()) or '"' in path:
                        raise ValueError("Folder option values cannot contain a double quote")
                    fields["path"] = path
                    line = "q.folder run " + " ".join(key + '="' + value + '"' for key, value in fields.items())
            lines.append(line)
        return "\n".join(lines)

    try:
        raw = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Tool arguments exceed the 2 MiB limit")
        request = json.loads(raw.decode("utf-8"))
        args = request["arguments"]
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be an object")
        args["workspace"] = str(workspace)
        if request["name"] in {"spindoctor_run_script", "spindoctor_test_theory"} and isinstance(args.get("script"), str):
            args["script"] = private_folder_script(args["script"])
        result = api.call(request["name"], args)
        payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        if len(payload) > 32 * 1024 * 1024:
            payload = b'{"ok":false,"error":"Engine output exceeds the 32 MiB limit"}'
        sys.stdout.buffer.write(payload + b"\n")
        return 0
    except Exception as error:
        sys.stdout.buffer.write((json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) + "\n").encode("utf-8"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
