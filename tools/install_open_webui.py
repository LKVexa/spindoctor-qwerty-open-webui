#!/usr/bin/env python3
# Fresh server-side payload copy and reviewed Open WebUI Valves configuration.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

RELEASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Copy a complete release into a NEW server directory; print the native tool source and Valves files to import.")
    parser.add_argument("--target", required=True, help="New absolute server installation directory")
    parser.add_argument("--workspace", default="", help="Absolute private-workspace parent outside the installation; omission uses the tool default")
    parser.add_argument("--python", default=sys.executable, help="Existing absolute server Python executable (engine requires 3.8+)")
    options = parser.parse_args()
    target = Path(options.target)
    executable = Path(options.python)
    if not target.is_absolute() or not executable.is_absolute() or not executable.is_file():
        parser.error("Use an absolute target and an existing absolute Python executable")
    if target.exists() or target.is_symlink():
        parser.error("The target already exists; choose a new directory to preserve existing files")
    target = target.resolve()
    executable = executable.resolve()
    if target.exists():
        parser.error("The target already exists; choose a new directory to preserve existing files")
    if target == RELEASE or RELEASE in target.parents or target in RELEASE.parents:
        parser.error("The installation must be separate from the source checkout")
    workspace = ""
    if options.workspace:
        path = Path(options.workspace)
        if not path.is_absolute():
            parser.error("The workspace parent must be absolute")
        path = path.resolve()
        if any(path == root or root in path.parents or path in root.parents for root in [target, RELEASE]):
            parser.error("Private workspaces must be separate from source and installed files")
        workspace = str(path)
    required = ["engine/spindoctor/api.py", "support/engine_runner.py", "spindoctor_qwerty_tool.py", "LICENSE", "NOTICE", "COPYRIGHT"]
    if not all((RELEASE / name).is_file() for name in required):
        parser.error("The complete source release is required")
    shutil.copytree(RELEASE, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.pyo", "node_modules", "valves.json", "INSTALLATION.json"))
    valves = {"engine_dir": str(target / "engine"), "workspace_root": workspace, "python_executable": str(executable), "timeout_seconds": 600, "max_downloads": 32}
    (target / "valves.json").write_text(json.dumps(valves, indent=2) + "\n", encoding="utf-8")
    record = {"version": "1.1.0", "license": "GPL-3.0-or-later", "author": "RUSSELL PHILIP SMITHSON", "copyright": "Copyright (C) 2026 RUSSELL PHILIP SMITHSON", "source_sha256": hashlib.sha256((target / "spindoctor_qwerty_tool.py").read_bytes()).hexdigest(), "native_database_updated": False}
    (target / "INSTALLATION.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tool_source": str(target / "spindoctor_qwerty_tool.py"), "valves": str(target / "valves.json"), "next": "Create the native Workspace Tool from this source, then apply these Valves on the same Open WebUI server."}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
