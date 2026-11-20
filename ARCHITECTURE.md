# AgriVision 2.0 architecture

A single FastAPI/Uvicorn process on loopback port 8000 serves the editable static dashboard and local APIs. Runtime app use requires Python, not Node or a frontend build service. CPU installation is the Windows default. CUDA may be used if the installed PyTorch runtime supports it; no CUDA performance is claimed.

## Media and vision

Browser `getUserMedia` permission probe reveals names and immediately releases its tracks. The user selects a device ID; the app requests that exact ID and verifies the resulting track settings. It never silently substitutes the built-in camera. Pause, disconnect, source changes and Stop invalidate previous live results. No Python camera worker competes for the USB device.

The browser displays the native preview while sampled JPEG frames are sent to `/api/predict`; there is one browser inference request in flight and bounded backend admission. Processing runs in worker threads with an inference lock and capped PyTorch CPU threads. Static photos have explicit automatic/manual analysis; a pending newer photo is not lost behind an older request. Results carry a generation token so outdated requests cannot update the current view.

The two-stage profile runs real YOLOv8n detection followed by the preserved five-class classifier. Optional profiles expose direct nine-label detection or original classification. Actual normalized boxes are mapped from optional ROI to full image coordinates at the server boundary. The SVG display uses object-fit geometry, so boxes stay aligned across aspect ratios and resize. Chat evidence can wait up to five seconds for the inference lock; the browser suspends sampled live inference while answering and clears the old live result, then resumes. There is no fabricated rectangle around a classifier prediction. The raw media preview remains unchanged; image annotations are a display layer or a separate saved JPEG.

## Evidence and Plant Doctor

`/api/capture` analyzes a fresh frame and saves normalized raw JPEG, separate annotated JPEG, model hashes, source, device label/ID, quality, normalized geometry and telemetry. SQLite event JSON keeps full provenance. CSV exports box details and both model hashes. Historical events retain their original model result; changing the current model does not rewrite history.

Attachments are server-decoded/type checked. JPG/PNG/WEBP are EXIF-normalized, reduced to 1920px maximum and stored as JPEG. Maximum input: 10MB / 16MP / minimum 64px. PDF/TXT/CSV documents: 8MB, UTF-8 for text, up to 20 PDF pages extracted and 20,000 characters. Documents are untrusted evidence, never instructions or verified agronomy sources. Composer and sent-message previews are real images. Failed send leaves attachments and text available.

A chat photo is analyzed locally regardless of cloud availability. `/api/chat` answers through an explicitly selected provider or bounded Meta → Gemini → Groq → Ollama → offline fallback. API keys remain server-side in local `.env`; status never exposes them. Configuration is re-read for provider requests; Meta generation is not blocked behind a model-list permission check. `/api/providers/test/{name}` performs an explicit small connection request and returns sanitized status.

Offline operation is deterministic retrieval from 26 curated bilingual guides. It explains local model evidence with causes, symptoms, care and prevention; it does not pretend to be a free-form multimodal foundation model. Cause-only questions do not repeat every section. A follow-up can reuse only the immediately preceding submitted evidence in that conversation, with visible context. New images replace old context; greetings and newly named unrelated diseases do not inherit an old visual result. Saved-event attachments are explicit, and changing the monitor image clears its old pending event.

Cloud output uses controlled source disclosure, strips unsupported URLs/numbered references and rejects numeric chemical prescriptions. These checks are not formal guarantees of factual correctness. Sources are collapsed by default. Only known supported vision families receive an image; text-only Ollama gets model evidence with an explicit image-not-transmitted instruction. No actual customer key was used during QA.

## Recording, telemetry and operating systems

MediaRecorder creates real WebM/MP4 bytes. On stop the browser finalizes the local Blob before a background upload; stop/switch is not blocked on an upload. Failure retains a local download/retry recovery UI. Backend verifies container signature and a readable video frame. History provides playback/download. Raw recording does not have boxes burned into video. Default 120s auto-stop and 120MB upload limit bound storage.

GPS states: UNAVAILABLE, SIMULATED, RECORDED TELEMETRY and LIVE TELEMETRY. Recorded CSV points only apply to recorded video near the sample time; browser location expires after 30 seconds. Permission failure explicitly resets to UNAVAILABLE, rather than leaving a simulated coordinate under a contradictory warning. No image-based leaf geolocation is claimed.

SQLite connections are context-managed, use WAL and parameterized queries. Additive legacy-event migration preserves existing rows. Temporary QA storage is separate from user artifacts. Status reports process RSS, process threads, host CPU and actual inference device; it reports no invented GPU utilization or FPS. App storage defaults to 1GB, with bounded uploads. Server shutdown closes its owned process; browser tracks stop on Stop/pagehide. Raspberry Pi execution, live drone networking and georeferenced treatment control are not implemented.

## Local security and editing

Trusted hosts, same-origin checks and a custom mutation header restrict browser drive-by requests. CSP excludes arbitrary scripts, unsafe eval, remote media, frames and objects. Static serving is limited to frontend assets and supplied references; `.env` and weights are not public routes. Upload paths are UUID-backed and filename-safe. No wildcard CORS or automatic LAN exposure is enabled. Keys, virtualenv, datasets and runtime artifacts are excluded from the release.

This is a local demonstration application, not a hosted multi-user authenticated service. Use HDMI Duplicate/Extend for another monitor. A second computer's LAN access needs deliberate separate configuration; localhost on the second computer is not the first laptop. Plain HTTP LAN camera restrictions still apply.
