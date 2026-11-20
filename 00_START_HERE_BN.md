# প্রথমে এই ফাইলটি পড়ুন

1. পুরোনো server terminal-এ Ctrl+C দিন। নতুন ZIP → Extract All → নতুন folder।
2. Python 3.12 64-bit থাকলে SETUP_WINDOWS.bat double click। প্রথমবার internet লাগবে।
3. RUN_AGRIVISION_WINDOWS.bat double click → Chrome/Edge → http://localhost:8000। Terminal খোলা রাখুন।
4. Photo → Open leaf photo → সবুজ actual detection box ও সম্ভাব্য class দেখুন। কোনো confirmation checkbox নেই।
5. Chat-এ Offline · YOLO + guides বেছে image icon দিয়ে ছবি পাঠান। API ছাড়াই local model ও guide উত্তর দেবে।
6. Meta চাইলে এই folder-এর .env-এ MODEL_API_KEY= এর পরে নিজের key দিন → Save → Settings → Meta Test connection। .env না থাকলে .env.example copy করে .env নাম দিন; .env.txt নয়।
7. USB camera: Enable cameras → Allow → external device-এর নাম → Start। Lens ঢেকে actual source মিলান।
8. Ask Doctor about this → প্রশ্ন। Record → Stop → History থেকে playback/download।

বিস্তারিত click-by-click: README_BN.md। নিজের laptop-এর ছোট checklist: USER_ONLY_ACTIONS_BN.md। পরীক্ষার ফল ও সীমা: QA_REPORT.md।

Original 5-class weights অক্ষত। Default-এ actual detector box + সেই classifier; optional detector-এ 9 dataset label। 26টি guide মানে 26টি trained visual class নয়। সব রোগ/Magnesium/অন্য crop শনাক্তের দাবি নেই। CHECK MODELS হলে model-এর মতভেদ আছে।
