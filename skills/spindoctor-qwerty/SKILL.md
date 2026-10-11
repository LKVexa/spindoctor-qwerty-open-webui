---
name: spindoctor-qwerty
description: Use SpinDoctor's six Open WebUI tools for classical circuits, presets, private files and user-confirmed theory tests.
---

Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
SPDX-License-Identifier: GPL-3.0-or-later

On first use, and whenever the user asks for help or functions, call `spindoctor_functions` and display its returned Markdown table verbatim. Do not replace it with a small selection of commands. The complete reference is also in FUNCTIONS.md.

Use the six tools advertised by Open WebUI: `spindoctor_functions`, `spindoctor_run_script`, `spindoctor_run_preset`, `spindoctor_list_presets`, `spindoctor_report`, `spindoctor_test_theory`. Read returned `ok`, errors, completed work and report links. Do not claim a result before running it. Presets are qc-001 through qc-241; override values are strings.

SpinDoctor is a classical FP64 simulator. It has at most 298 logical qubits and at most 59 qubits in one entangled factor, subject to memory. Above 29 qubits only basis z is supported. A multi-controlled X gate has at most seven controls. The tools do not provide physical quantum hardware, quantum advantage, unbounded entanglement or independent verification of every result.

Before testing a theory from a file, pasted text or chat, extract or read it and restate the hypothesis, assumptions, variables and measurable prediction. Show the proposed q.* script and checks and obtain the user's confirmation. For chat, use the confirmed summary and optional quoted excerpts. The tool cannot fetch chat history by itself. Then run `spindoctor_test_theory` with explicit hypothesis, prediction, script and checks; explain supported, contradicted and inconclusive verdicts within the modeled assumptions.

Each verified native user has a private workspace. File paths resolve inside it; external paths and traversal are refused. An ordinary chat attachment is not automatically staged. With the actual host upload UUID available, use `spindoctor_test_theory(source="file", action="extract", file_id="...")`; native ownership or read access is checked. Reuse its returned relative `input_name` for `q.input add path="..."` or private folder work. Use only real UUIDs supplied by the host, never a guessed server path or an attachment URL. The toolkit requires ownership or an explicit native read grant for this input path, including administrators.

An administrator may provision a private input folder inside a user's workspace; then `q.folder run path="relative-folder"` is supported in run scripts and explicitly supplied theory scripts. Supply a folder command in the explicit theory script rather than relying on automatic source extraction. Fixed-workspace exports, saves and checkpoints remain available. Report paths in tool results are replaced by [private]. Offer the returned authenticated download links and native file cards. Authorized report downloads preserve the original engine bytes and may include that user's run/source metadata. Do not show server storage paths or substitute local file links.

`spindoctor_run_script` accepts at most 200 commands and 1 MiB of text; theory execution also stops after at most 200 commands. Input files are at most 5 MiB, with narrower engine PDF/folder limits where applicable. A call uploads at most the configured number of reports (default 32, maximum 64); remaining reports stay private and can be retrieved with `spindoctor_report`. The server timeout defaults to ten minutes. Treat timeout or cancellation as incomplete work and inspect results before retrying.
