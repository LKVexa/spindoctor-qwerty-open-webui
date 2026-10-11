# SpinDoctor Qwerty for Open WebUI

Release **1.1.0**, SpinDoctor **3.1.2**, build `3.1.2-298-20261010`.
Copyright (C) 2026 **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>.
Licensed under **GPL-3.0-or-later**; LICENSE contains the complete GPL version 3 text. NOTICE and COPYRIGHT record attribution and warranty terms.

Six native Open WebUI tools provide classical circuits, all **241 presets**, the complete function table, private state and authenticated report downloads. This release targets **Open WebUI 0.12.0**. It bundles the approved 35-file engine unchanged and runs it in a separate short-lived Python process. The host's temporary tool module never determines the engine location and the host's Python import path is not changed.

SpinDoctor is a **classical FP64 simulator**: at most **298 logical qubits**, at most **59 qubits in one entangled factor**, subject to available memory, and at most seven controls for multi-controlled X. Above 29 qubits only basis z is supported. These are simulator limits, not physical quantum hardware or quantum advantage. See [FUNCTIONS.md](FUNCTIONS.md) for the full table and engine limitations.

## Install on the Open WebUI server

The engine and support folder must exist on the machine or container running the backend. A browser upload of the Python toolkit alone cannot install those server files. Use a fresh installation directory and a separate private-workspace parent. The helper preserves existing directories and emits configuration for review; it does not alter native accounts, chats or the Open WebUI database.

```sh
python tools/install_open_webui.py --target "$INSTALL_DIR" --workspace "$PRIVATE_WORKSPACES" --python "$SERVER_PYTHON"
```

All three variables represent absolute paths on the backend. The selected Python must exist there; using the Open WebUI Python environment is convenient. The unchanged engine itself needs Python 3.8+. The native toolkit uses the host's Pydantic and Open WebUI packages. It requires no NumPy and explicitly uses the engine's standard-library backend. On Windows, choose the actual server Python executable rather than a shell command such as `py -3`. With containers, mount the complete installed payload and use paths as seen **inside the backend container**, with a writable separate private-workspace volume.

In **Workspace → Tools**, create a new tool and paste the installed `spindoctor_qwerty_tool.py`. Set its native Valves using the values in the generated `valves.json`, then enable it for the intended model/chat. Open WebUI owns tool permissions and tool selection. This follows its [native Tools development contract](https://docs.openwebui.com/features/extensibility/plugin/tools/development/).

| Valve | Purpose |
| --- | --- |
| `engine_dir` | Required stable absolute path to the installed `engine` directory; its adjacent `support` folder must remain present |
| `workspace_root` | Absolute parent outside installed/source files; blank defaults to `~/spindoctor-workspace/open-webui` on the backend |
| `python_executable` | Existing absolute Python executable; blank uses the host interpreter |
| `timeout_seconds` | Default 600 seconds; range 1–1800 |
| `max_downloads` | Report files attached per call; default 32, range 1–64 |

The helper's generated JSON is a **Valves dictionary**, not a package-discovery manifest or an automatic database install. For deployments using the native HTTP API, toolkit creation uses `/api/v1/tools/create`; applying Valves uses `/api/v1/tools/id/<tool-id>/valves/update` with that dictionary directly. Local Python tool IDs must be Python identifiers, such as `spindoctor_qwerty`. The pinned implementation is [tools.py](https://github.com/open-webui/open-webui/blob/15818d88fd7bde1b73de33590f50d15d21e8d7c1/backend/open_webui/routers/tools.py).

Add the instructions in [SKILL.md](skills/spindoctor-qwerty/SKILL.md) to the model's active instructions. This directory is a supplied instruction artifact; automatic filesystem skill discovery and native Skills UI installation are not claimed or tested. On first use or help/functions requests, call `spindoctor_functions` and show its returned Markdown table verbatim.

## Use the six tools

| Tool | Use |
| --- | --- |
| `spindoctor_functions` | Full raw Markdown table; sections commands, gates, tools, presets or all |
| `spindoctor_run_script` | Newline-separated q.* commands, private state and report downloads |
| `spindoctor_run_preset` | qc-001 through qc-241; override values must be strings |
| `spindoctor_list_presets` | List all presets or filter their descriptions |
| `spindoctor_report` | Read a relative TXT report or list recent reports and retrieve their native downloads |
| `spindoctor_test_theory` | Extract or test file/text/confirmed-chat theory with hypothesis, prediction, script and checks |

For example, run this script through `spindoctor_run_script`:

```text
q.circuit new bell 2
q.circuit add h 0
q.circuit add cx 0 1
q.circuit run shots 256 basis z
q.circuit result
```

Each verified native user has a separate directory derived from their actual user ID under the configured parent. State and reports persist across tool calls. Calls for one user serialize within a toolkit instance. Multiple backend workers or separately loaded instances do not share that in-memory lock; use a single worker for concurrent mutation of one user's state. Native tool access grants remain controlled by Open WebUI.

## Uploaded files and private folders

Ordinary chat attachments are **not automatically staged**. When the host provides an actual upload UUID, call `spindoctor_test_theory` with `source="file"`, `action="extract"` and that `file_id`. The wrapper resolves the native file record, verifies ownership or an explicit read grant, reads at most 5 MiB and copies it into this user's private directory. It ignores arbitrary attachment URLs and paths. The returned relative `input_name` can be reused with `q.input add path="..."`. This input gate also requires ownership/read grants for administrators; native HTTP administrator download policy is broader.

For theory testing, restate the claims, assumptions, variables and measurable prediction, show the proposed q.* script/checks and obtain the user's confirmation before `action="run"`. Chat input is the supplied confirmed summary plus optional excerpts; the toolkit does not fetch conversation history. Sample theory sources are in `engine/examples/theory`. PDFs need readable text; no OCR is provided. If pypdf is installed in the selected child interpreter it is preloaded before the file policy; otherwise the unchanged engine uses its built-in PDF text extractor.

Administrators can provision supported input files in a user's private directory; use relative names, or a relative folder with `q.folder run path="folder-name"`. For run scripts and explicitly supplied theory scripts, the child uses the approved folder parser and translates a contained relative folder path to the absolute path required by the engine, preserving option values and order. A theory's automatically extracted source commands receive no such translation; supply the folder command in its explicit script. External file paths, traversal and links created by the engine are refused. This policy applies to script inputs, folder ingestion and theory reads. Fixed-workspace save/export/checkpoint commands remain usable. The child audit policy constrains the approved q.* engine's I/O; it is not a general operating-system sandbox for arbitrary Python programs.

`spindoctor_run_script` accepts at most 200 commands and 1 MiB of text; tool argument JSON is at most 2 MiB. The engine also caps theory execution at 200 commands. Child stdout is capped at 32 MiB and stderr at 64 KiB. Timeout and cancellation terminate and reap the child. Engine-specific PDF, folder, factor and memory limits still apply.

## Reports and privacy

Reports are copied **byte-for-byte** into native file storage using `process=False`, so they are not embedded for retrieval. The tool emits native file cards and returns authenticated `/api/v1/files/<uuid>/content?attachment=true` links. The native file record owns the actual UUID and user identity; the wrapper supplies no server storage paths to the model. The implementation uses the pinned [native file router](https://github.com/open-webui/open-webui/blob/15818d88fd7bde1b73de33590f50d15d21e8d7c1/backend/open_webui/routers/files.py) and [saved-chat event emitter](https://github.com/open-webui/open-webui/blob/15818d88fd7bde1b73de33590f50d15d21e8d7c1/backend/open_webui/socket/main.py).

Each download includes a safe `report_name` relative to this user's reports directory, distinguishing nested files with the same basename. A response contains only files uploaded by that call; saved-chat history keeps older cards separately. The wrapper copies the native event list before emitting because the saved-chat emitter appends historical cards in place.

Model-visible results, report text, errors and event cards replace private engine and workspace paths, including JSON-escaped Windows variants. Authorized downloads preserve original report bytes and may contain that user's own run/source metadata. Open WebUI's normal authenticated ownership/read/admin policy controls downloads. By default only 32 report files are attached per call; use `spindoctor_report` for remaining reports. Each uploaded report must be at most 32 MiB.

## Verification and limits

[E2E_RESULTS.md](E2E_RESULTS.md) records native component, authenticated file-route, persistence, lifecycle, installer and engine results, including earlier failed attempts. The native gate uses the **genuine installed 0.12.0 loader, DB/get_tools, middleware argument filtering, file upload, saved-chat emitter and authenticated routes in a minimal ASGI application**. It covers these real components; it does not prove a complete browser/model session.

Final prepublication checks passed **49/49 native**, **6/6 separate-process persistence**, **12/12 engine in 130.4 seconds with 255 byte-verified PDF/TXT pairs**, and **18/18 installer** with one Windows symlink-privilege skip. The first-25 preset comparison matched 20 references with five documented differences.

The official full application did not reach verified HTTP readiness in this Windows environment. One isolated startup attempt exited with a fatal access violation during a pandas/importlib path-stat import, before SpinDoctor was installed. Earlier attempts reached native lifespan but health requests timed out. Full CLI startup, interactive UI, real-model tool selection, saved streaming chat execution and browser file-card rendering remain uncompleted. No general Windows incompatibility or plugin root cause is inferred.

## Reproduce

Use the external `open-webui==0.12.0` environment and a fresh scratch directory. Set TEMP/TMP there, and `PYTHONDONTWRITEBYTECODE=1`, before starting. The test harnesses configure isolated native persistence/cache/static/upload directories without changing an existing user profile. Replace angle-bracket arguments with your selected paths.

```sh
python -B tests/install_check.py <installer-results.json>
python -B tests/native_check.py --base <fresh-absolute-native-test-directory> --out <native-results.json>
python -B tests/restart_check.py --receipt <native-results.json> --out <restart-results.json>
python -B tests/e2e_mcp.py --server <absolute-open-webui-python> -B <absolute-tests-native_bridge.py> --examples <absolute-engine-examples-theory-directory> --out <engine-results.json>
```

The last transport is explicitly a test adapter around native tool callbacks, not a production MCP server. It configures real DB Valves per case, stages trusted test fixtures inside the private directory or through owned native uploads, and authenticates/byte-checks report downloads before reconstructing local paths for the shared engine checks. Its structured-content field is test framing. Runtime packages, user data, generated PDFs and caches are excluded from this source release.
