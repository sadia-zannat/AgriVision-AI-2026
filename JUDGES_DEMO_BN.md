# AgriVision AI — ৩ মিনিটের demo

আগে app খুলে একটি নিজের পরিষ্কার tomato leaf photo ও ছোট video clip প্রস্তুত রাখুন। Internet না থাকলে chat provider Offline নিন। Raspberry Pi ভাঙা; demo Windows laptop-এ চলছে বলুন।

1. **০:০০–০:৩০** — “এটি Tomato leaf screening ও evidence-based care assistant। Green boxes detector-এর actual output; class score severity নয়।” Webcam permission → verified external camera নাম → Start দেখান।
2. **০:৩০–১:০০** — পাতাটি কাছে দেখান। Screening/box/label দেখান। অন্ধকার করলে পুরোনো রোগ মুছে LOW_QUALITY হয়। No detection হলে আরও কাছে নিন; জোর করে রোগ দেখানোর দাবি করবেন না। Photo backup খোলা যেতে পারে; uploaded source স্পষ্ট রাখুন।
3. **১:০০–১:৪৫** — Ask Doctor about this → “এর কারণ ও করণীয় কী?” → Bangla উত্তর। EN toggle → follow-up। Source disclosure খুলে extension guide দেখান। API ছাড়া স্থানীয় YOLO + curated guide চালানো সম্ভব বলুন।
4. **১:৪৫–২:১৫** — Capture → History → raw ও annotated image। কয়েক সেকেন্ড Record → Stop → History → Play। Recorded drone video থাকলে RECORDED label দেখিয়ে clip চালান; live aerial operation দাবি নয়।
5. **২:১৫–২:৪৫** — Field: UNAVAILABLE / SIMULATED / recorded track-এর পার্থক্য। Coordinates device-এর, exact leaf location নয়। CSV report দেখান।
6. **২:৪৫–৩:০০** — Settings-এ preserved model ও secondary detector নির্বাচন দেখান। “Default ৫-class classification with real leaf regions; secondary model-এর ৯ label ও ২৬টি knowledge guide আছে। সব রোগ trained নয়, এবং disagreement হলে review দেখায়।”

কোনো known test ছবি ব্যবহার করলে সেটি reference/QA image বলুন। Test score বা upstream mAP-কে নতুন camera/field accuracy বলবেন না। Guide care information chemical prescription বা laboratory diagnosis নয়।
