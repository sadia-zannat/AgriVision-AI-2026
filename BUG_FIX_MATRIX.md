# Rebuild acceptance matrix — 2.0

| Reported problem | Integrated behavior | Verification / limit |
| --- | --- | --- |
| Built-in camera silently replaces USB | Enumerated names, exact device request, returned track ID check, actual label retained | JS + browser mock passed; physical Windows USB test remains |
| No boxes or label on leaf | Actual pretrained detector regions, green SVG rectangles and attached label; selectable two-stage/direct profiles | Real model + browser checks passed; classifier profile intentionally has no boxes |
| Photo blocked by hidden confirmation | Removed required leaf checkbox; automatic photo/chat inference plus Detect now | Real API/browser passed |
| Detector falsely appears certain | Detector/classifier labels and disagreement saved; low confidence/no detection explicit | Known secondary error deliberately exposed; field accuracy unresolved |
| Old disease after dark frame | Fresh quality rejection clears previous class and geometry | Real API + mock live stream passed |
| Whole plant returns no disease | NO_DETECTION reports scope/close-up guidance; never declares Healthy | Two screenshot-derived cases still have no box; this is an unresolved model/domain limit |
| Uploaded image invisible | Composer preview, file metadata/remove, sent user image and annotated assistant image | Browser passed, including failed-send retention |
| New monitor photo discusses old saved event | Source/photo/settings/model changes clear pending old event; Doctor captures current image | Browser regression passed |
| Fast Capture → Doctor loses image | Capture and Doctor controls disabled until fresh evidence is ready | Reproduced and fixed in browser |
| New photo waits behind old inference and disappears | In-flight generation tokens and pending-photo inference retry | Implemented; photo flow passed |
| Switching tabs wipes static photo result | Static result retained; live/video invalidated as appropriate | Implemented; current photo workflows passed |
| Offline chat unrelated/repetitive | Local YOLO + 26 structured bilingual guides; question-intent sections and bounded follow-up context | Python + browser passed |
| Offline “hi” repeats last disease | Greeting is a local conversational reply without inherited prediction | Python + browser passed |
| API key filled but chat stays offline | Correct documented payload, no model-list hard gate, reloadable keys, explicit Test connection, readable failure states | Mock contract/fallback passed; user's actual account not tested |
| Chat photo collides with live camera inference | Short evidence lock wait, temporary live-inference suspension and automatic resume | API + browser concurrency regression passed |
| Weak API fallback | Meta/Gemini/Groq/Ollama/offline adapter chain, budget/cooldown and per-message offline choice | Mock tests passed; free access not guaranteed |
| Chat clipping / composer outside laptop screen | Flexible message scroll, bounded composer, responsive panel height | 1366 / 1920 / 390px browser checks passed |
| Bright sources clutter answers | Sources/evidence collapsed by default; safe text/Markdown subset | Browser passed |
| Recording stop blocks camera switch | Local Blob finalized first; upload background; failed save keeps download/retry | Browser MediaRecorder/storage/restart passed with mock track |
| GPS warning contradicts simulation | Location error resets mode; stale live / mismatched recorded positions unavailable | API + browser passed |
| History loses model context | Immutable event result, geometry, separate images, source/device/time/hashes in event/CSV | API + browser passed |
| Broad “all diseases / other crops” claim | Explicit class taxonomy, optional direct detector, finite knowledge catalog; no fabricated magnesium/crop training | API/knowledge checks passed; full disease coverage not delivered |
| Many incremental patches | One extracted, editable integrated project with weights, tests and runbook | Release package audit |
