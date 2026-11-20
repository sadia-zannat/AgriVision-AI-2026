# Final QA report — AgriVision AI 2.0

Release scope: complete integrated editable source, preserved user weights, additional pretrained detector, offline bilingual condition guides, cloud fallback adapters, browser camera/recording, evidence history and GPS provenance. This is a demonstration release with explicit model limitations, not a claim of universal disease detection or field validation.

## Executed results

| Verification | Result | Evidence |
| --- | --- | --- |
| Python API/model/knowledge/security/training-helper suite | **66 passed**, 0 failures; 2 dependency deprecation warnings | `docs/qa-python-results.xml`, `docs/qa-python-output.txt` |
| Dependency-free JavaScript camera/stabilizer tests | **5 passed**, 0 failures | `docs/qa-node-output.txt` |
| Real local-server Chromium workflows | **14 passed**, no uncaught application JavaScript errors | `docs/qa-browser-results.json` |
| Original model preservation | SHA-256 matches supplied weights, 3,194,562 bytes | MODEL_CARD.md and release manifest |
| Secondary detector | Real weights loaded, actual task/taxonomy checked, normalized predictions exercised | `models/detector_provenance.json`, model smoke JSON |
| Actual model smoke inputs | One labeled guide image + three screenshot-derived inputs | `docs/qa-model-smoke.json`; not an accuracy benchmark |
| Python compile / JavaScript syntax | Passed for project code | release verification notes |
| Windows launchers | Paths/quotes/setup flow inspected; actual Windows execution not performed | README_BN.md; user-only checks below |

Execution environment: Linux, Python 3.12, CPU PyTorch and Chromium. Exact package versions are in `docs/TESTED_ENVIRONMENT.json`. Browser execution used generated video tracks with two named mock device IDs. MediaRecorder itself, real encoded video bytes, upload validation and playback/download routes were used. No physical USB camera was attached to this environment. API contract/error/fallback tests used HTTP mock responses, not customer credentials.

## Regressions verified

- A photo without a confirmation checkbox runs real inference. Blank/dark/white/uniform images have no retained disease or boxes.
- Actual detector coordinates produce green rectangles with attached class labels; ROI-relative coordinates map back to the full photograph. Classifier-only profile emits no fabricated boxes.
- Low classifier confidence keeps uncertainty; detector/classifier disagreement is retained and marked REVIEW rather than hidden.
- Raw normalized evidence and annotated JPEG differ and remain separately downloadable. Input hash corresponds to the saved raw normalized bytes; CSV includes geometry and both model hashes.
- Chat image inference waits briefly for a busy live model; the browser pauses sampled inference during a chat answer and resumes afterward. A concurrent live-camera/chat-photo browser workflow passed.
- Direct chat image attachment runs local YOLO with no API, retains real previews, and receives sourced Bengali/English guide output.
- Cause-only follow-up uses the same submitted evidence and names that context. A new photo, new conversation, greeting or newly named unrelated disease does not silently inherit a stale disease.
- Capture controls wait for the capture to finish before enabling the Doctor attachment action, closing a reproduced capture/chat timing race.
- New monitor images clear old pending saved-event attachments. New photo inference is not lost behind an older in-flight request. Static photo results survive visibility changes.
- Failed chat send retains attachment and text for retry. PDF/TXT/CSV previews are bounded and type checked; invalid/binary/oversize uploads are rejected.
- Named camera permission probe releases its tracks. Exact requested device ID is checked; mismatch fails. Mock USB/built-in switching, pause/resume/Stop/restart, dark-frame clearing and cleanup passed.
- Real MediaRecorder output on a mock video track was saved and read back. Recorded-video playback/capture preserves RECORDED VIDEO origin. Raw recording does not burn in inference overlays.
- Responsive checks at 1366×768, 1920×1080 and 390×844 found no document horizontal overflow. Desktop Send remains in the viewport and the message region scrolls.
- Simulated location stays labeled. Geolocation failure resets to UNAVAILABLE, eliminating the contradictory simulated-coordinate/unavailable-warning state.
- Meta does not require a successful models-list call. Meta/Gemini/Groq image payload contracts, text-only Ollama behavior, quota/access errors, bounded fallback, explicit offline mode, local credential reload and sanitized connection tests passed with mock HTTP.
- Same-origin/custom-header/host restrictions, secret-path non-serving, SQL migration preservation and optional model absence were checked.

## Model findings that remain unresolved

On K-State figure 2, ground truth is Early Blight. The preserved classifier gives Early Blight approximately 0.954; the secondary detector labels the region Tomato Yellow Virus approximately 0.911. The default profile shows the original class with an actual detected region and exposes the disagreement. This does **not** prove the two-stage approach has validated field accuracy.

On the three screenshot-derived user photos, two returned NO_DETECTION, and one produced several proposed regions with tentative classifier labels. Their true diagnoses are unknown; labels must not be judged correct from this test. Compression, small leaves and domain shift remain material reliability risks. Use a close, sharply focused leaf and seek expert confirmation. No box means no supported detection above threshold, not Healthy. Do not lower thresholds to force a disease result for judging.

The optional direct nine-label profile increases available dataset labels, but it is not demonstrated to be more accurate than the original classifier. Neither model covers all tomato diseases or magnesium deficiency; no non-tomato disease model was added. The 26 knowledge guides are informational coverage, not 26 trained visual labels.

## Not tested here — only the user's laptop/accounts can close these

1. Windows 11 fresh installation, launcher behavior and actual RTX 4060/CUDA compatibility or speed. The provided setup installs CPU PyTorch, so CUDA is not a prerequisite.
2. Actual external USB camera/driver identity, disconnection behavior and interference from Windows Camera/Zoom/Teams. Use the external-lens-cover test and inspect the track label.
3. Original-resolution photos and real tomato plants under local lighting; phone-screen glare and wide drone imagery. Independent labeled local validation is required for accuracy claims.
4. Customer Meta key, credits, model permission, actual Gemini/Groq quota and live multimodal response quality. Use Settings → Test connection; an account-dependent failure is not resolved merely by filling a key field.
5. Real laptop camera codec/recording behavior, audio-free video and local playback. Automated browser recording used a generated track.
6. Real device geolocation or external drone telemetry. Permission may be denied or a laptop may lack a position fix; UNAVAILABLE is then correct.

## Known product boundaries

No retraining was run; the optional ten-class pipeline is retained but no new ten-class checkpoint is claimed. No live drone flight, Raspberry Pi deployment, exact leaf georeferencing, lesion segmentation, validated severity, chemical dosage engine or universal offline vision-language model is delivered. Offline answers are finite sourced guides conditioned on real local YOLO evidence. Unsupported questions can request more evidence. Cloud response guardrails reduce certain bad outputs but cannot prove every generated agricultural statement correct.

The two Python warnings concern Starlette/httpx/anyio deprecations in the tested runtime, not failed assertions. Dependency versions and future cloud model availability can change. Setup requires internet once; configured offline application use then works without it. ZIP integrity and secret/runtime exclusion are checked during packaging. Screenshots are real application captures using clearly labeled QA input, not field-performance evidence.
