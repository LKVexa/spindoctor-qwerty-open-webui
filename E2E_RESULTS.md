# Open WebUI validation — 2026-10-11

Release **1.1.0**, SpinDoctor **3.1.2** build `3.1.2-298-20261010`, unchanged engine **1.1.0**.
Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>.
GPL-3.0-or-later; LICENSE contains the complete GPL version 3 text.

## Test boundary

Windows, genuine **Open WebUI 0.12.0**, Python **3.12.14**, complete external host environment.
Official source pin `15818d88fd7bde1b73de33590f50d15d21e8d7c1`; native loader/files/auth/tools/middleware and nine additional HTTP-related installed source syntax trees were compared with the pin. Dependency installation/check and the initial real loader preflight **9/9** passed. Runtime dependencies were preinstalled outside this source release; clean network bootstrap is not covered.

The native harness uses the actual asynchronous loader, native SQL database/models, persisted Valves, get_tools injection/ACLs, native middleware argument filtering, unchanged child engine, native upload with processing disabled, saved-chat emitter and native authenticated file routes in a **minimal ASGI application**. Fresh local test accounts use genuine Auth/User pairs, hashed random passwords and the account-stamped native session claim format. Authentication and file/tool permissions are enabled. No external account or model is used. No SDK/vendor/guard/engine code or existing profile was modified.

Native saved-chat records and files are real database/storage records. The test gate is narrower than the official full application, browser UI or streaming model/chat loop. Those uncompleted boundaries are stated below.

## Final checks

| Suite | Result | Scope |
| --- | --- | --- |
| Fresh-copy helper | **18/18**, one Windows symlink skip | Stable actual absolute Valves/interpreter, spaces, external/default workspace, exact engine/license, full author/version/copyright, source hash, no native DB mutation, skill/runner copy, existing/unrelated/empty files preserved and invalid destinations, interpreters and workspaces rejected |
| Genuine native component suite | **49/49** | Six tool schemas, raw Markdown, 241 presets, state/report/theory, actual file routes/ownership/cards, private-user separation, input staging including the kit Hadamard PDF, middleware injection filtering, child lifecycle, five saved-chat/repeated-name/download mapping regressions and two relative-folder/containment checks |
| Separate-process native persistence | **6/6** | Actual database/Valves/state/chat/file records and authenticated byte-exact download reloaded in a new process |
| Engine suite through native callbacks/downloads | **12/12 in 130.4 seconds** | Six tools, 16 command families, 298-qubit/mcx7 circuit, four mixed-folder formats plus skipped Markdown, three theory sources, first-25 references and **255 structurally valid PDF/TXT pairs**, with actual authenticated byte-exact downloads |

Final configured host persistence, caches, static files, uploads, temporary files and engine workspaces are isolated in the selected scratch directory. The source release remains cache-free. The test adapter configures actual DB Valves before dispatch, stages owned theory files through native uploads and places trusted folder fixtures in the private workspace. It parses the production tool's observed JSON/Markdown. Authenticated downloads are compared byte-for-byte with the original private report before paths are reconstructed for structural report checks. The adapter's `structuredContent` and local report paths are explicit test framing; production exposes native UUID download links and cards.

The native PDF upload fixture extracted the kit's Hadamard theory PDF with **pypdf 6.7.5**, preserving its actual q.* lines and text. Lifecycle checks use actual child processes with trusted timeout/backpressure, cancellation and output-overflow fixtures; every child was reaped. The installer rejects an originally supplied dangling target symlink before resolving it. Its conditional symlink regression was skipped because Windows denied symlink creation privilege (**WinError 1314**); that OS skip is separate from the 18 passing checks.

The twelve shared engine checks cover initialization, six tools, full function Markdown, 241-preset listing, one script per command family, a 298-qubit circuit including `mcx7`, mixed text/CSV/JSON/QASM folder ingestion, theory from a file, confirmed chat summary/excerpts and exported transcript, first-25 preset references and TXT/PDF structure. This fixture coverage is separate from full-host model/browser behavior.

## Retained failures and corrections

The first native attempt reached the real loader, registry and catalogue checks but failed its initial script/report assertion and then stopped while selecting an absent PDF. Its old top-level exception receipt reports 0/1; it must not be interpreted as a complete suite result. A private runner diagnostic traced the production file policy's denial of a lazily loaded UTF-16-BE codec. Trusted engine lazy modules, report codecs and platform memory-observation dependencies are now preloaded before the child audit policy. The unchanged engine's direct Bell probe then passed.

The second native attempt retained **27/33**. Engine, actual DB state, upload records and saved-chat cards worked, while HTTP downloads and the subsequent upload returned 401. The test fixture had inserted User rows without the persistent Auth row/session stamp required by 0.12.0; the native authorization guard correctly rejected its tokens. Test accounts and restart token issuance were corrected using genuine paired Auth/User rows and actual stamped native session claims. No authorization bypass was introduced. Both failed receipts/logs remain retained separately.

The first shared engine transport attempt produced no protocol progress and was interrupted, with its uncompleted-attempt record retained. The native adapter redirected genuine migration/import logs to stderr while the inherited test client captured that stream in an unread pipe. Windows pipe backpressure was an inferred explanation, not a proven runtime root cause. The test client now writes real stderr diagnostics to retained scratch files and includes their locations in its receipt, allowing host initialization to continue without that unread pipe. This change affects the test transport only; vendor and engine files are unchanged.

The second shared engine attempt initialized and discovered all six tools, then failed while the test adapter wrote the full function table through an inherited Windows cp1252 text stream: U+23CE could not be encoded. Setting PYTHONUTF8 inside a running interpreter does not change already-open streams. The adapter now reads protocol bytes and explicitly writes UTF-8 bytes. The production worker already uses explicit UTF-8 and its native function-table check passed; the failed transport log is retained separately.

The third shared engine attempt passed its four initial checks and verified 48 authenticated downloads, then aborted during the family scripts on an exact PDF-byte mismatch. Read-only native database/storage probes showed all 140 uploaded files matched private engine reports. The concrete cause was the real saved-chat emitter's in-place `files.extend(existing_files)`: the wrapper had passed and returned the same list, so historical cards entered the current response. A repeated basename then selected a previous call's UUID. The wrapper now emits a separate copied native-card list and keeps its current response independent. Safe relative `report_name` fields also distinguish nested same-basename reports. Added genuine saved-chat/HTTP regressions verify only fresh UUIDs in the current response, changed same-name PDF bytes, both generations in history, distinct nested names and exact downloads. The earlier native 42/42 did not cover that interaction; the then-expanded native suite passed **47/47**, before the folder checks brought the final suite to 49/49. The original failed run remains retained; the byte comparison was preserved. Test download reconstruction also preserves a distinct directory for each actual workspace, so earlier cases with matching filenames remain available for structural checks.

The next shared engine attempt completed **11/12 in 119.8 seconds**, with **251 structurally valid PDF/TXT pairs**. All command-family, 298-qubit, theory and preset-reference checks passed; only mixed folder ingestion failed. The test adapter had staged inputs privately and supplied `q.folder run path="test-folder"`, while the unchanged engine requires an absolute folder path. This also exposed the missing translation behind the documented relative-folder workflow. The child wrapper now parses folder options with the approved engine parser, checks the resolved destination against the private boundary, and supplies an absolute lexical path while preserving flags/order and the engine's independent link checks. Direct isolated runner checks passed a folder with spaces and explicit flags, and refused traversal. The fresh native suite passed **49/49**, including the new relative-folder/flag and traversal regressions; the subsequent persistence suite passed **6/6** and the full engine rerun passed **12/12 in 130.4 seconds**, with **255 PDF/TXT pairs** and **20 identical plus five documented reference differences**. The 11/12 receipt remains retained separately.

## Official full application startup — uncompleted

Before installing SpinDoctor, isolated unchanged `open-webui serve` attempts completed migrations and eventually reached native lifespan/scheduler, but health requests were refused or timed out. A 30-second standard faulthandler snapshot observed a Transformers metadata import traversing distribution files with pathlib stat. A traced retry reached native lifespan and an idle Windows Proactor loop but did not verify health.

A final same-invocation official CLI child and health client exited after **70.3 seconds**, before readiness, with a recorded **Windows fatal access violation during a pandas/importlib path-stat import**. Health **0/1** failed and the child was reaped. This happened before SpinDoctor installation. The precise root cause is unverified; no general Windows incompatibility or plugin fault is inferred. Full-app startup evidence and detailed logs are retained locally, separately from plugin checks.

## Uncompleted tests and limits

Official full CLI/server startup was attempted and did not reach verified readiness. Full saved streaming chat/model tool loop, real model reasoning/selection, browser file-card rendering/download interaction, native UI/HTTP toolkit and Skills installation, retrieval/embedding, automatic attachment/history access, Linux/macOS, another Open WebUI version, remote/object storage and multiworker concurrent state mutation were not tested. PDF checks verify headers, page markers, cross-reference/startxref markers and EOF structure; visual layout and broader renderer compatibility were not checked. The separate persistence check exercises native components in a new process, not a full server restart. Native component success does not fill these gaps.

The wrapper uses the standard-library numerical backend. Optional pypdf is preloaded if present, with the engine's built-in extractor available otherwise; broader PDF layout/font/encryption/OCR input coverage is not claimed. Report bytes are preserved exactly; authorized downloads can include the user's own run/source paths. Model-visible result/error/text/card privacy is separately checked. Per-user locks serialize one toolkit instance; independently loaded instances/workers have separate locks.

The handoff kit reports the C# SpinDoctor 3.1.2 suite **18/18 with three 29-qubit checks adapted to the 298 limit**, with Russell's approval to publish on that basis. That historical suite was not rerun here and is separate from these Python/native results.

## Reproduce

Use the external `open-webui==0.12.0` Python environment. Set TEMP/TMP to an isolated existing scratch directory and `PYTHONDONTWRITEBYTECODE=1` before testing. Run from the repository; substitute actual paths for angle-bracket arguments. The native test environment marks its owned disposable base and refuses an unrelated nonempty base.

```sh
python -B tests/install_check.py <installer-results.json>
python -B tests/native_check.py --base <fresh-absolute-native-test-directory> --out <native-results.json>
python -B tests/restart_check.py --receipt <native-results.json> --out <restart-results.json>
python -B tests/e2e_mcp.py --server <absolute-open-webui-python> -B <absolute-tests-native_bridge.py> --examples <absolute-engine-examples-theory-directory> --out <engine-results.json>
```

The release has **55 files**, including **35 engine files byte-identical** to the approved kit and the complete byte-identical GPL LICENSE. All **33 Python** and **five JSON** syntax checks pass. The original **19 files remain byte-unchanged**, with a separate preserved backup. No runtime packages, generated reports, database, logs or caches are bundled. Strict scanning and the final hash inventory are recorded at freeze. Publication readback and fresh-clone results are recorded separately after publication; this file reports prepublication verification.
