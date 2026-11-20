# নিজের laptop-এ শুধু এই কাজগুলো

1. নতুন ZIP Extract All করুন; পুরোনো server Ctrl+C দিয়ে বন্ধ করুন। Python 3.12 থাকলে `SETUP_WINDOWS.bat`, তারপর `RUN_AGRIVISION_WINDOWS.bat` চালান। Setup-এর জন্য internet লাগে; পরের offline run-এর জন্য লাগে না।
2. USB camera লাগিয়ে browser permission Allow → নাম দেখে external camera → Start। External lens ঢেকে preview মিলান। Stop → অন্য camera → Start একবার দেখুন। এখানে এই physical পরীক্ষা সম্ভব হয়নি।
3. নিজের টমেটো পাতার কাছের ছবি দিয়ে Photo ও chat পরীক্ষা করুন। Model-এর ফলকে confirmed diagnosis ধরবেন না। Phone-screen ও বাস্তব পাতার input আলাদা করে দেখুন।
4. প্রয়োজন হলে নিজের `.env`-এ `MODEL_API_KEY` দিন → Settings → Meta Test connection। Gemini/Groq ঐচ্ছিক। Key না দিলেও Offline → YOLO + guides কাজ করে। এখানে নিজের account quota/access পরীক্ষা হয়নি।
5. নিজের camera দিয়ে কয়েক সেকেন্ড Record → Stop → History → Play/Download দেখুন। Hardware/driver/browser codec-এর চূড়ান্ত পরীক্ষা নিজের laptop-এ লাগবে।
6. GPS দরকার হলে নিজের permission দিয়ে পরীক্ষা করুন। Fix না পেলে UNAVAILABLE-ই সঠিক। Simulation-কে আসল GPS হিসেবে বলবেন না।

Original trained weights ZIP-এ অক্ষত আছে; আবার upload বা mandatory retraining লাগবে না। RTX 4060 optimization ঐচ্ছিক; CPU runtime দিয়ে আগে demo নিশ্চিত করুন। Windows installer, USB hardware, GPU speed, real-leaf field accuracy ও live API accounts এখানে সরাসরি যাচাই হয়নি।
