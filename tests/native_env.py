# Disposable native Open WebUI test environment; no user-profile changes.
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from pathlib import Path
import secrets


def prepare(base):
    base = Path(base).resolve()
    marker = base / "test-owner.json"
    owner = {"owner": "spindoctor-open-webui-native-tests", "version": "1.1.0"}
    if base.exists() and any(base.iterdir()) and (not marker.is_file() or json.loads(marker.read_text()) != owner):
        raise ValueError("Choose a fresh or marked SpinDoctor test directory")
    base.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(owner), encoding="utf-8")
    dirs = {}
    for name in ["data", "static", "cache", "temp", "huggingface", "torch", "appdata", "localappdata", "workspaces"]:
        path = (base / name).resolve()
        if path.parent != base:
            raise ValueError("Test directory links are unavailable")
        path.mkdir(exist_ok=True)
        dirs[name] = path
    secret = base / "test.secret"
    if not secret.exists():
        secret.write_text(secrets.token_urlsafe(48), encoding="ascii")
    values = {"FROM_INIT_PY": "true", "GLOBAL_LOG_LEVEL": "ERROR", "DATA_DIR": str(dirs["data"]), "DATABASE_URL": "sqlite:///" + (dirs["data"] / "webui.db").as_posix(),
              "STATIC_DIR": str(dirs["static"]), "WEBUI_SECRET_KEY": secret.read_text(encoding="ascii"), "WEBUI_AUTH": "true", "STORAGE_PROVIDER": "local",
              "OFFLINE_MODE": "true", "HF_HUB_OFFLINE": "1", "ENABLE_VERSION_UPDATE_CHECK": "false", "ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS": "false",
              "ENABLE_PERSISTENT_CONFIG": "false", "ENABLE_PLUGINS": "true", "ENABLE_TOOLS": "true", "ENABLE_OLLAMA_API": "false", "ENABLE_OPENAI_API": "false",
              "RAG_EMBEDDING_MODEL": "", "RAG_RERANKING_MODEL": "", "RAG_EMBEDDING_MODEL_AUTO_UPDATE": "false", "RAG_RERANKING_MODEL_AUTO_UPDATE": "false",
              "BYPASS_EMBEDDING_AND_RETRIEVAL": "true", "HF_HOME": str(dirs["huggingface"]), "SENTENCE_TRANSFORMERS_HOME": str(dirs["huggingface"]),
              "TORCH_HOME": str(dirs["torch"]), "XDG_CACHE_HOME": str(dirs["cache"]), "APPDATA": str(dirs["appdata"]), "LOCALAPPDATA": str(dirs["localappdata"]),
              "TEMP": str(dirs["temp"]), "TMP": str(dirs["temp"]), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ANONYMIZED_TELEMETRY": "False"}
    os.environ.update(values)
    return base
