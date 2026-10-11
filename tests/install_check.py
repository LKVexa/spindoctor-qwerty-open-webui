#!/usr/bin/env python3
# Fresh-copy preservation and stable absolute native Valves checks.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

RELEASE = Path(__file__).resolve().parents[1]
INSTALLER = RELEASE / "tools/install_open_webui.py"
home = Path(tempfile.mkdtemp(prefix="spindoctor-webui-install-check-"))
checks = []
skips = []
def check(name, passed):
    checks.append({"name": name, "pass": bool(passed)})
    print(("PASS " if passed else "FAIL ") + name)
def run(target, *args):
    return subprocess.run([sys.executable, "-B", str(INSTALLER), "--target", str(target)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1"))
def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}

try:
    target = home / "installed with spaces"
    workspace = home / "private user workspaces"
    result = run(target, "--workspace", str(workspace))
    check("fresh installation accepts spaces without creating workspaces", result.returncode == 0 and target.is_dir() and not workspace.exists())
    valves = json.loads((target / "valves.json").read_text())
    check("native engine and interpreter Valves have actual stable absolute paths", valves["engine_dir"] == str(target / "engine") and valves["python_executable"] == str(Path(sys.executable).resolve()))
    check("external workspace Valve is absolute and explicit", valves["workspace_root"] == str(workspace.resolve()))
    check("timeout and attachment defaults match native Tools", valves["timeout_seconds"] == 600 and valves["max_downloads"] == 32)
    engine = inventory(target / "engine")
    check("all 35 installed engine files match source bytes", len(engine) == 35 and engine == inventory(RELEASE / "engine"))
    check("full GPL license is copied byte-for-byte", (target / "LICENSE").read_bytes() == (RELEASE / "LICENSE").read_bytes())
    record = json.loads((target / "INSTALLATION.json").read_text())
    check("installation record has version GPL full author and copyright", record["version"] == "1.1.0" and record["license"] == "GPL-3.0-or-later" and record["author"] == "RUSSELL PHILIP SMITHSON" and record["copyright"] == "Copyright (C) 2026 RUSSELL PHILIP SMITHSON")
    check("source hash is recorded and native database is untouched", record["source_sha256"] == hashlib.sha256((target / "spindoctor_qwerty_tool.py").read_bytes()).hexdigest() and record["native_database_updated"] is False)
    check("runner and user-facing skill are copied", (target / "support/engine_runner.py").is_file() and (target / "skills/spindoctor-qwerty/SKILL.md").is_file())
    before = inventory(target)
    check("existing installed target is preserved without overwrite", run(target).returncode != 0 and inventory(target) == before)
    occupied = home / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("existing chat files")
    check("unrelated existing files are preserved", run(occupied).returncode != 0 and inventory(occupied) == {"keep.txt": hashlib.sha256(b"existing chat files").hexdigest()})
    empty = home / "empty-but-existing"
    empty.mkdir()
    check("even an existing empty target remains untouched", run(empty).returncode != 0 and not list(empty.iterdir()))
    link = home / "existing-dangling-target"
    destination = home / "must-not-be-created"
    try:
        link.symlink_to(destination, target_is_directory=True)
    except OSError as error:
        if getattr(error, "winerror", None) != 1314:
            raise
        skips.append({"name": "existing dangling target symlink is preserved", "reason": "Windows did not grant symlink creation privilege (WinError 1314)"})
    else:
        check("existing dangling target symlink is preserved without external writes", run(link).returncode != 0 and link.is_symlink() and not destination.exists())
    nested = RELEASE / "forbidden-test-install"
    check("installation inside source rejects before writes", run(nested).returncode != 0 and not nested.exists())
    missing = home / "missing-python"
    check("missing interpreter rejects before writes", run(missing, "--python", str(home / "absent.exe")).returncode != 0 and not missing.exists())
    inside = home / "bad-internal-workspace"
    check("workspace inside installed payload rejects before writes", run(inside, "--workspace", str(inside / "workspace")).returncode != 0 and not inside.exists())
    default = home / "default-workspace"
    check("omitted workspace preserves native home default", run(default).returncode == 0 and json.loads((default / "valves.json").read_text())["workspace_root"] == "")
    relative = home / "relative-workspace"
    check("relative workspace rejects before writes", run(relative, "--workspace", "relative").returncode != 0 and not relative.exists())
    check("payload excludes git metadata and Python caches", not any(p.name in (".git", "__pycache__") or p.suffix in (".pyc", ".pyo") for p in target.rglob("*")))
    summary = {"python": sys.version.split()[0], "passed": sum(row["pass"] for row in checks), "total": len(checks), "checks": checks, "skips": skips}
    if len(sys.argv) > 1:
        receipt = Path(sys.argv[1]); receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    status = 0 if summary["passed"] == summary["total"] else 1
finally:
    if home.resolve().parent != Path(tempfile.gettempdir()).resolve() or not home.name.startswith("spindoctor-webui-install-check-"):
        raise RuntimeError("Unsafe test cleanup path")
    shutil.rmtree(home)
sys.exit(status)
