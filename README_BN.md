# AgriVision AI — Detection Final 2.0

টমেটো পাতার স্থানীয় YOLO detection, তোমার অক্ষত trained classifier, real green box + label, API ছাড়াই Plant Doctor, optional Meta/Gemini/Groq, recording ও evidence history এক project-এ। Frontend সম্পূর্ণ editable; Node.js প্রয়োজন নেই।

## ১. Windows-এ প্রথমবার চালানো

1. পুরোনো AgriVision server-এর কালো terminal-এ **Ctrl+C** দিন। পুরোনো folder রাখুন।
2. নতুন ZIP → right click → **Extract All** → নতুন folder, যেমন `C:\AgriVision_Final`। ZIP-এর ভেতর থেকে `.bat` চালাবেন না।
3. Python **3.12, 64-bit** ও Python launcher ইনস্টল থাকতে হবে। না থাকলে [python.org](https://www.python.org/downloads/windows/) থেকে নিন; installer-এ Python launcher/`py` ও PATH চালু রাখুন।
4. Extract করা project folder খুলে **SETUP_WINDOWS.bat** double click করুন। Internet লাগবে; `.venv`, CPU PyTorch ও dependencies তৈরি হবে। Terminal বন্ধ করবেন না। “Setup complete” দেখালে যেকোনো key চাপুন।
5. **RUN_AGRIVISION_WINDOWS.bat** double click করুন। Chrome/Edge-এ `http://localhost:8000` খুলবে। নিজে না খুললে ঠিকানাটি লিখুন। Server terminal খোলা রাখুন।
6. পরেরবার শুধু **RUN_AGRIVISION_WINDOWS.bat**। বন্ধ করতে আগে recording থামান, তারপর terminal-এ **Ctrl+C**।

এই setup CPU-তে চলে; RTX 4060/CUDA setup ছাড়াই demonstration করা যায়। GPU utilization বা laptop FPS এখানে মাপা হয়নি। প্রথম inference কিছুটা ধীর হতে পারে।

## ২. আগে API ছাড়াই ছবি পরীক্ষা করুন

1. **Photo / ছবি** tab → **Open leaf photo** → একটি টমেটো পাতার JPG/PNG/WEBP দিন।
2. স্বয়ংক্রিয়ভাবে inference হবে। প্রয়োজন হলে **Detect now** চাপুন। কোনো “Tomato leaf positioned” checkbox লাগবে না।
3. Detector region পেলে সবুজ rectangle ও তার সঙ্গেই সম্ভাব্য রোগের label থাকবে। **Center ROI** একটি ঐচ্ছিক crop guide; সেটি detection box নয়।
4. **CHECK MODELS** দেখালে detector ও classifier-এর label আলাদা। Screening card-এ দুই ফল দেখুন। একটি class score-কে নিশ্চিত রোগ বা severity ধরবেন না।
5. **Ask Doctor about this →** চাপলে এই ছবির fresh capture chat-এ যুক্ত হবে। প্রশ্ন লিখে সবুজ send বোতাম চাপুন। Capture শেষ না হওয়া পর্যন্ত এই বোতাম নিষ্ক্রিয় থাকবে।
6. সরাসরি chat-এর image icon দিয়েও ছবি দিন। বাস্তব preview, filename ও remove button দেখাবে। প্রশ্ন লিখুন, যেমন “এই পাতার সম্ভাব্য সমস্যা, কারণ, লক্ষণ ও করণীয় বলুন।”
7. Chat-এর provider dropdown-এ **Offline · YOLO + guides** নিলে কোনো cloud API call হয় না। একবার dependencies install হওয়ার পর এই পথে internet লাগে না।
8. পরের প্রশ্ন “এর কারণ কী?”, “করণীয় কী?”, “কীভাবে প্রতিরোধ করব?” হলে একই conversation-এর সদ্য দেওয়া evidence ব্যবহার করবে এবং follow-up label দেখাবে। অন্য ছবির জন্য নতুন ছবি দিন; greeting-এ পুরোনো রোগ যোগ হয় না।
9. **বাংলা / EN** দিয়ে পরবর্তী উত্তরের ভাষা বাছুন। আগের message-এর ভাষা স্বয়ংক্রিয়ভাবে বদলাবে না।

Doctor-এর **২৬টি curated guide**-এ কারণ, লক্ষণ, করণীয় ও প্রতিরোধ আছে। সব guide-এর রোগ visually trained নয়। রোগের নাম লিখেও সাধারণ তথ্য জানতে পারেন। Settings → Offline disease knowledge থেকে নাম বেছে প্রশ্ন তৈরি করা যায়।

## ৩. কোন model কী করে

| Settings → Tomato vision profiles | কাজ | সীমা |
| --- | --- | --- |
| Leaf boxes + your 5-class model — default | Secondary YOLO থেকে actual region; ওই region-এ তোমার preserved classifier-এর label | ৫টি condition class; model disagreement দৃশ্যমান; experimental integration |
| Secondary detector · 9 labels · review | নতুন pretrained secondary detector-এর নিজস্ব box ও ৯ dataset label | অতিরিক্ত coverage, নিশ্চিত diagnosis নয়; independent field validation হয়নি |
| Your original classifier · 5 classes | তোমার আগের সম্পূর্ণ ছবির classifier | bounding box তৈরি করে না |
| Optional expanded classifier | আলাদা trained ১০-class weights থাকলে পাওয়া যায় | এ release-এ retraining করা হয়নি; তৈরি না হলে unavailable |

Original পাঁচ class: Bacterial Spot, Early Blight, Healthy, Late Blight, Yellow Leaf Curl Virus।

Secondary detector-এর নয় label: Early Blight, Septoria Leaf Spot, Healthy, Bacterial Spot, Late Blight, Tomato Mosaic Virus, Tomato Yellow Virus, Leaf Mold, Spider Mites। Generic “Tomato Yellow Virus” মানেই নির্দিষ্ট TYLCV প্রমাণ নয়। Magnesium deficiency, Leafminer, Target Spot এবং অন্য crop-এর visual support দাবি করা হয়নি। এদের কিছু বিষয়ে guide তথ্য আছে।

**গুরুত্বপূর্ণ:** সব টমেটো রোগ এক ছবি থেকে নিশ্চিতভাবে চেনার model দেওয়া হয়নি। Known K-State Early Blight ছবিতে original model ঠিক class দিলেও secondary detector ভুল yellow-virus label দিয়েছে। Default two-stage profile এই disagreement লুকায় না। তোমার screenshot থেকে নেওয়া ৩টি ছোট ছবির মধ্যে ২টিতে detector কোনো box পায়নি; সেগুলোর নিশ্চিত রোগ জানা নেই। কাছ থেকে একটি পাতা তুলুন; না পাওয়া মানে healthy নয়।

## ৪. Meta API key কোথায় দেবেন

1. **SETUP_WINDOWS.bat** একবার চালালে project folder-এ `.env` তৈরি হয়। নিজে করতে হলে `.env.example` copy → duplicate-এর নাম **`.env`** করুন।
2. Windows File Explorer → **View → Show → File name extensions** চালু করুন। ফাইলটি `.env.txt` যেন না হয়।
3. VS Code খুলুন → **File → Open Folder** → এই extracted project folder। বামে `.env` খুলুন।
4. কেবল নিজের laptop-এ নিচের জায়গাগুলো পূরণ করুন। `YOUR_KEY_HERE` উদাহরণ; আসল key দিয়ে বদলাবেন।

```dotenv
MODEL_API_KEY=YOUR_META_KEY_HERE
META_MODEL=muse-spark-1.3
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
GROQ_API_KEY=
GROQ_MODEL=qwen/qwen3.8-27b
CHAT_PROVIDER_ORDER=meta,gemini,groq,ollama,offline
```

5. **Ctrl+S**। Provider keys প্রতি request-এ reload হয়; restart জরুরি নয়। `DEFAULT_MODEL` বা inference device বদলালে server restart দিন। পুরোনো `.env`-এ `META_API_KEY` থাকলেও alias হিসেবে পড়বে; `MODEL_API_KEY` পূরণ থাকলে সেটি অগ্রাধিকার পায়।
6. Website → **Settings → Plant Doctor providers → META → Test connection**। “connection test succeeded” হলে ওই account-এ text request কাজ করেছে। এটি image diagnosis accuracy প্রমাণ করে না।
7. Chat provider **Auto** বা **Meta** নিন। ছবি দিয়ে প্রশ্ন পাঠান। Message-এর নিচে যে provider আসল উত্তর দিয়েছে সেটি দেখাবে; fallback-এর কারণ **View sources & evidence**-এ।

| ফল | অর্থ / করণীয় |
| --- | --- |
| not configured | ভুল folder-এর `.env`, `.env.txt`, বা key ফাঁকা কি না দেখুন |
| HTTP 401/403 | Key, project/account access বা model permission যাচাই করুন |
| HTTP 404 | Account-এ model ID/endpoint পাওয়া যায়নি; official console-এর ID মিলান |
| HTTP 400 | Model/request format প্রত্যাখ্যান করেছে; configured model যাচাই করুন |
| HTTP 429 | Rate limit বা quota; কিছুক্ষণ পরে Test connection অথবা offline mode |
| timed out / connection failed | Internet/proxy/firewall/provider availability দেখুন; local mode কাজ করবে |

আলাদা `/models` listing সফল না হলেও generation request পরীক্ষা করা হয়। “hi” একটি local greeting; Meta পরীক্ষা করার জন্য **Test connection** ব্যবহার করুন। Test একটি ছোট real API request পাঠায়। Key কখনো frontend-এ, screenshot-এ, chat-এ বা GitHub-এ দেবেন না। এখানে তোমার live credentials পাওয়া যায়নি; account-specific Meta failure-এর নিশ্চিত কারণ বলা হয়নি।

## ৫. বিকল্প API

- **Gemini**: [AI Studio API keys](https://aistudio.google.com/api-keys) → নিজের key → `.env`-এ `GEMINI_API_KEY`। Default `gemini-2.5-flash-lite`; image input নেয়। [Official pricing](https://ai.google.dev/gemini-api/docs/pricing)-এ eligible free tier আছে; account/model quota সীমিত। Free-tier data-use terms দেখে ব্যবহার করুন।
- **Groq**: [Groq keys](https://console.groq.com/keys) → `.env`-এ `GROQ_API_KEY`। Default `qwen/qwen3.8-27b` একটি [documented vision model](https://console.groq.com/docs/vision)। [Free-plan limits](https://console.groq.com/docs/rate-limits) আছে; model access ও quota account-নির্ভর।
- **Ollama, optional**: আগে নিজে local model install করতে হবে; `.env`-এ `OLLAMA_ENABLED=true`। Text-only model-এ ছবি পাঠানো হয় না; capability যাচাই করে evidence text দেওয়া হয়। Installed vision model হলে ছবিও দেওয়া যায়। Demo-এর আগে বড় model download বাধ্যতামূলক নয়।

সব key ফাঁকা রাখলেও স্থানীয় YOLO + offline guide কাজ করে। Auto order-এর কোনো provider ব্যর্থ হলে পরবর্তী configured provider, শেষে offline guide। বড় uploaded document-এর নতুন দাবির সত্যতা offline mode যাচাই করে না।

## ৬. External USB camera

1. USB camera লাগান। Windows Camera/Zoom/Teams/অন্য camera tab বন্ধ রাখুন।
2. Chrome/Edge-এ **localhost:8000** ব্যবহার করুন। Webcam → **Enable cameras** → browser permission **Allow**।
3. নাম দেখে external USB camera বাছুন। শুধু “Integrated Camera” দেখলে সেটি সাধারণত built-in; USB device খুঁজে refresh দিন।
4. **Start**। Preview-এর নিচে আসল track label, resolution এবং requested device ID মিলেছে কি না দেখুন।
5. পরীক্ষার জন্য external lens ঢাকুন: একই preview অন্ধকার হচ্ছে কি না দেখুন। Built-in lens ঢাকলে preview বদলানো উচিত নয়।
6. Settings → Camera source declaration-এ নিজের verified source বাছুন। Source declaration ও actual track label আলাদাভাবে event-এ থাকে।
7. পাতাকে কাছে, স্থিরভাবে, ভালো আলোয় রাখুন। Live inference চালু থাকবে। **Pause → Resume → Stop → অন্য camera → Start** একবার দেখুন।
8. Permission denied হলে browser address bar-এর site controls → Camera → Allow; Windows Settings → Privacy & security → Camera-তে desktop app access চালু আছে কি না দেখুন। Occupied হলে অন্য camera app বন্ধ করুন।

Cloud পরীক্ষায় generated video tracks দিয়ে exact device selection পরীক্ষা হয়েছে; তোমার physical USB hardware এখানে পরীক্ষা হয়নি। Phone screen-এ ছবি দেখালে glare/moiré থাকে; একে field accuracy validation বলা যাবে না।

## ৭. Capture, recording, history, video

- **Capture**: fresh frame, actual prediction, raw normalized image, আলাদা annotated image, source/device/time/model hashes/GPS provenance সংরক্ষণ করে। EXIF সরানো ও সর্বোচ্চ 1920px-এ normalized JPEG সংরক্ষিত হয়; original uploaded file-এর byte-for-byte archival copy নয়।
- **History**: thumbnail → details → **Download original** (normalized raw image) / **Download with boxes**। Report → CSV-তে normalized box coordinates-ও থাকে।
- **Record**: browser MediaRecorder দিয়ে আসল camera video; “Stop recording” চাপুন। History-তে playback/download। Preview pause/stop করলে recording আগে finalize হয়।
- Upload/save ব্যর্থ হলে recording recovery box-এ **Download** ও **Retry save** থাকবে; নিজের copy নামিয়ে রাখুন। Recording raw video, inference box overlay video-তে burn করা হয় না; annotated still capture আলাদাভাবে পাওয়া যায়।
- Default 120s auto-stop, 120MB upload limit; `.env`-এ সীমা সামান্য বদলানো যায়। দীর্ঘ recording-এর বদলে ছোট demo clip রাখুন।
- **Recorded video** → MP4/H.264 বা WebM → browser controls দিয়ে Play। Inference sampled frames-এ হয়। Screenshot-derived QA, recorded video এবং live camera আলাদা source হিসেবে থাকে। Wide drone scene-এ ছোট পাতা এই model-এর নির্ভরযোগ্য scope নয়।

## ৮. GPS

Default **UNAVAILABLE**। Field → **Simulate track** সবসময় **SIMULATED**। **Use device location** সফল হলে device position; ৩০ সেকেন্ড পরে stale হয়। Permission ব্যর্থ হলে mode UNAVAILABLE করা হয়।

Recorded CSV: `time_s,latitude,longitude`; clip time-এর ৫ সেকেন্ডের মধ্যে point মিললে **RECORDED TELEMETRY**। Unmatched বা camera source-এ recorded coordinate দেখানো হয় না। কোনো পাতার ছবির অবস্থান অনুমান করা হয় না। Drone/device GPS = পাতার বা জমির সুনির্দিষ্ট স্থান নয়। Laptop-এর browser location GPS receiver-এর বিকল্প বা নিশ্চিত GPS fix নয়।

## ৯. VS Code ও পুরোনো data

- VS Code → Open Folder → এই project। Python interpreter: `.venv\Scripts\python.exe`। `.vscode` tasks ব্যবহার করা যায়; frontend `frontend/static/`, backend `backend/`। Live Server দিয়ে HTML খুলে app চালাবেন না; FastAPI launcher লাগবে।
- পুরোনো `.env`, `artifacts` ও model folder আগে backup করুন। নতুন folder-এ পুরোনো project overwrite করবেন না।
- পুরোনো capture/history রাখতে চাইলে server বন্ধ করে **পুরো** পুরোনো `artifacts` directory নতুনটির জায়গায় copy করুন, অথবা `.env`-এর `APP_DATA_DIR=C:/.../artifacts` দিন। Active SQLite file copy করবেন না। Additive DB migration পুরোনো rows রাখে।
- পুরোনো `.env` থেকে key নতুন `.env`-এ কপি করুন; private file কাউকে পাঠাবেন না। Trained original weights এই ZIP-এই আছে, আবার upload দরকার নেই।

## ১০. Optional training ও tests

Competition demo-এর আগে নতুন training বাধ্যতামূলক নয়। এই release-এ কোনো retraining হয়নি। `TRAIN_10CLASS_OPTIONAL.bat` ও `scripts/prepare_tomato_10class.py`, `train_tomato_10class.py` রেখে দেওয়া হয়েছে। প্রথমে script-এর `--help` পড়ুন; dataset download/license, space ও compute নিজের ব্যবস্থা। Duplicate-aware split, class audit, fixed seed ও guarded final test আছে। Output `tomato_10class_best.pt`; original overwrite হয় না। Classifier train করলে detection boxes পাওয়া যায় না।

Developer verification (PowerShell, project folder):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/test_frontend.cjs
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tests/browser_qa.py
```

Node দরকার শুধু JavaScript unit test চালাতে; app চালাতে নয়। Browser QA temporary storage ও mocked cameras ব্যবহার করে; নিজের webcam permission নেয় না। বিস্তারিত ফল `QA_REPORT.md`, `docs/qa-*` ও `docs/screenshots/`-এ।
