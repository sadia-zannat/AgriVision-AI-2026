"""Curated, bilingual tomato knowledge. Knowledge coverage is distinct from trained visual classes."""
import re
KSTATE={'title':'K-State — Tomato Leaf and Fruit Diseases and Disorders, L721 (2009)','url':'https://bookstore.ksre.k-state.edu/pubs/L721.pdf','local':'/references/KSTATE_TOMATO_DISEASE_GUIDE.pdf'}
IOWA={'title':'Iowa State — Tomato diseases and disorders, PM1266 (2006)','url':'https://shop.iastate.edu/extension/home-garden/yard-and-garden/gardening/pd54.html','local':'/references/IOWA_TOMATO_GUIDE.pdf','edition_note':'Pages refer to the supplied 2006 PM1266 PDF; catalog links to the revised PD54 edition.'}
def web(title,url):return {'title':title,'url':url}
UCURL=web('UC IPM — Tomato yellow leaf curl','https://ipm.ucanr.edu/agriculture/tomato/tomato-yellow-leaf-curl/')
MOSAIC=web('UC IPM — Tobacco mosaic','https://ipm.ucanr.edu/agriculture/tomato/tobacco-mosaic/')
MITE=web('UConn IPM — Tomato spider mites','https://ipm.cahnr.uconn.edu/tomato-spider-mites/')
MAG=web('SDSU Extension — Monitoring and correcting magnesium deficiency in high tunnels','https://extension.sdstate.edu/monitoring-and-correcting-magnesium-deficiency-high-tunnels')
TARGET=web('UF IFAS — Target spot of tomato in Florida','https://ask.ifas.ufl.edu/publication/PP351')
MINER=web('UC IPM — Tomato leafminers','https://ipm.ucanr.edu/agriculture/tomato/leafminers/')

def entry(key,label,aliases,en,bn,source,pages=None):
    fields=['cause','symptoms','action','prevention']
    return {'id':key,'label':label,'tags':[label.lower(),*aliases],
            'en_fields':dict(zip(fields,en)), 'bn_fields':dict(zip(fields,bn)),
            'en':' '.join(en),'bn':' '.join(bn),'source':dict(source,pages=pages),'kind':'curated paraphrase'}

CORPUS=[
entry('early','Early Blight',['early blight','আর্লি','অল্টারনারিয়া'],
 ['Alternaria fungi survive in infected crop debris; wet foliage favors spread.',
  'Older lower leaves may develop brown spots with concentric rings and surrounding yellowing.',
  'Reduce leaf wetness, remove badly affected foliage carefully and have similar spots checked before treatment.',
  'Use clean seedlings, mulch, crop rotation and adequate spacing; water at the soil surface.'],
 ['Alternaria ছত্রাক আক্রান্ত ফসলের আবর্জনায় টিকে থাকতে পারে; ভেজা পাতায় ছড়ানোর সুযোগ বাড়ে।',
  'পুরোনো নিচের পাতায় বাদামি দাগ, বৃত্তাকার বলয় ও চারপাশে হলুদভাব দেখা যেতে পারে।',
  'পাতা ভেজা কমান, বেশি আক্রান্ত পাতা সাবধানে সরান এবং একই রকম দাগের অন্য কারণ আছে কি না যাচাই করুন।',
  'পরিষ্কার চারা, mulch, ফসল পর্যায়ক্রম ও পর্যাপ্ত দূরত্ব রাখুন; গোড়ায় পানি দিন।'],KSTATE,[1,2]),
entry('late','Late Blight',['late blight','লেট ব্লাইট','নাবি ধসা'],
 ['Phytophthora infestans is a water mold; cool humid conditions and wet foliage favor outbreaks.',
  'Irregular water-soaked dark patches may enlarge quickly; humid conditions can produce white growth underneath.',
  'Rapid spread needs prompt agricultural expert confirmation. Separate suspect plants and avoid moving wet material.',
  'Use clean plants, reduce prolonged foliage wetness and manage infected tomato and potato crop residues.'],
 ['Phytophthora infestans নামের water mold এ রোগ ঘটায়; ঠান্ডা আর্দ্র আবহাওয়া ও ভেজা পাতায় ঝুঁকি বাড়ে।',
  'পানিভেজা অনিয়মিত কালচে দাগ দ্রুত বড় হতে পারে; আর্দ্রতায় পাতার নিচে সাদা আবরণ দেখা যেতে পারে।',
  'দ্রুত ছড়ালে দ্রুত কৃষি বিশেষজ্ঞের মূল্যায়ন নিন। সন্দেহজনক গাছ আলাদা রাখুন এবং ভেজা আক্রান্ত অংশ ছড়াবেন না।',
  'পরিষ্কার চারা নিন, পাতায় দীর্ঘ সময় পানি জমতে দেবেন না এবং টমেটো ও আলুর আক্রান্ত অবশিষ্টাংশ সামলান।'],IOWA,[4]),
entry('bacterial','Bacterial Spot',['bacterial spot','ব্যাকটেরিয়াল স্পট','ব্যাকটেরিয়া','ব্যাকটেরিয়া'],
 ['Xanthomonas bacteria spread through contaminated seed/transplants, splashing water and wet handling.',
  'Small dark leaf spots can merge; fruit may develop raised scabby spots. Bacterial speck can look similar.',
  'Keep foliage dry, avoid working wet plants and seek confirmation before choosing a control product.',
  'Start with clean seed and transplants, clean tools, rotate crops and avoid overhead irrigation.'],
 ['Xanthomonas ব্যাকটেরিয়া দূষিত বীজ বা চারা, পানির ছিটা ও ভেজা গাছে কাজের মাধ্যমে ছড়াতে পারে।',
  'পাতায় ছোট কালো দাগ একত্র হতে পারে; ফলে খসখসে উঁচু দাগ হতে পারে। Bacterial Speck দেখতে কাছাকাছি।',
  'পাতা শুকনো রাখুন, ভেজা গাছে কাজ এড়িয়ে চলুন এবং নিয়ন্ত্রণের উপায় বাছার আগে কারণ নিশ্চিত করুন।',
  'পরিষ্কার বীজ ও চারা, পরিষ্কার যন্ত্র, ফসল পর্যায়ক্রম এবং গোড়ায় পানি দেওয়া অনুসরণ করুন।'],KSTATE,[3]),
entry('septoria','Septoria Leaf Spot',['septoria','সেপ্টোরিয়া','সেপ্টোরিয়া'],
 ['Septoria lycopersici survives in crop debris; water splashes carry spores.',
  'Many small round spots with pale centers and dark borders usually begin on older leaves; tiny black dots may be visible.',
  'Remove affected lower leaves carefully, reduce splash and ask for confirmation if spots overlap with other diseases.',
  'Mulch, stake plants, allow airflow and remove infected crop debris after the season.'],
 ['Septoria lycopersici ছত্রাক ফসলের অবশিষ্টাংশে টিকে থাকে; পানির ছিটায় spores ছড়ায়।',
  'পুরোনো পাতায় হালকা কেন্দ্র ও গাঢ় প্রান্তের অনেক ছোট গোল দাগ হয়; ক্ষুদ্র কালো বিন্দু থাকতে পারে।',
  'আক্রান্ত নিচের পাতা সাবধানে সরান, পানির ছিটা কমান এবং অন্য রোগের সঙ্গে মিললে বিশেষজ্ঞ দিয়ে নিশ্চিত করুন।',
  'Mulch ও খুঁটি ব্যবহার, বাতাস চলাচল এবং মৌসুম শেষে আক্রান্ত আবর্জনা সরানো সাহায্য করে।'],IOWA,[1,2]),
entry('leafmold','Leaf Mold',['leaf mold','লিফ মোল্ড','পাতার ছাঁচ'],
 ['Leaf mold is favored by high humidity and poor greenhouse ventilation.',
  'Yellow patches on the upper surface can accompany olive or brown fuzzy growth underneath; nutrient problems may look similar.',
  'Inspect both leaf surfaces, improve ventilation and reduce humidity; confirm the cause.',
  'Use appropriate spacing and resistant varieties where available; limit condensation on leaves.'],
 ['বেশি আর্দ্রতা ও greenhouse-এ কম বাতাস চলাচল Leaf Mold-এর ঝুঁকি বাড়ায়।',
  'পাতার উপরে হলুদ দাগ এবং নিচে জলপাই বা বাদামি তুলার মতো আবরণ হতে পারে; পুষ্টির ঘাটতির সঙ্গে মিল থাকে।',
  'পাতার দুই পাশ দেখুন, বাতাস চলাচল বাড়ান, আর্দ্রতা কমান এবং কারণ যাচাই করুন।',
  'পর্যাপ্ত দূরত্ব, পাওয়া গেলে প্রতিরোধী জাত এবং পাতায় condensation কমানোর ব্যবস্থা রাখুন।'],IOWA,[8]),
entry('curl','Yellow Leaf Curl Virus',['yellow leaf curl','tylcv','হলুদ পাতা কোঁকড়ানো','ইয়েলো লিফ কার্ল'],
 ['Bemisia whiteflies transmit tomato yellow leaf curl virus.',
  'Young leaves may yellow and curl upwards; plants may be stunted with reduced fruit set.',
  'There is no curative treatment for an infected plant. Confirm the virus and discuss removal and whitefly management locally.',
  'Use clean transplants, resistant varieties and protection against whiteflies; manage nearby hosts.'],
 ['Bemisia সাদা মাছি Tomato Yellow Leaf Curl Virus ছড়ায়।',
  'কচি পাতা হলুদ হয়ে উপরের দিকে কুঁচকাতে পারে; গাছ খাটো ও ফল ধরা কমতে পারে।',
  'আক্রান্ত গাছের ভাইরাস সারানোর চিকিৎসা নেই। ভাইরাস নিশ্চিত করে গাছ সরানো ও সাদা মাছি নিয়ন্ত্রণ নিয়ে কৃষিবিদের পরামর্শ নিন।',
  'পরিষ্কার চারা, প্রতিরোধী জাত, সাদা মাছি থেকে সুরক্ষা এবং আশপাশের host গাছ ব্যবস্থাপনা করুন।'],UCURL),
entry('yellowgeneric','Tomato Yellow Virus',['tomato yellow virus'],
 ['The secondary detector uses a broad yellow-virus label; it cannot establish a particular virus species.',
  'Yellowing, curling and stunting can also result from nutrients, roots, weather or other diseases.',
  'Inspect young and old leaves, stems and insect vectors; confirm a suspected virus with an expert or laboratory.',
  'Use clean planting material and control relevant vectors after confirming the cause.'],
 ['Secondary detector-এর “Tomato Yellow Virus” একটি সাধারণ dataset label; এটি নির্দিষ্ট ভাইরাস প্রমাণ করে না।',
  'হলুদভাব, পাতা কুঁচকানো ও খাটো গাছ পুষ্টি, শিকড়, আবহাওয়া বা অন্য রোগেও হতে পারে।',
  'কচি ও পুরোনো পাতা, কান্ড ও বাহক পোকা দেখুন; বিশেষজ্ঞ বা পরীক্ষাগারে সন্দেহের ভাইরাস নিশ্চিত করুন।',
  'পরিষ্কার চারা ব্যবহার করুন; কারণ নিশ্চিত করে প্রাসঙ্গিক বাহক পোকা ব্যবস্থাপনা করুন।'],IOWA,[7]),
entry('mosaic','Tomato Mosaic Virus',['mosaic','মোজাইক'],
 ['Tobamoviruses can spread mechanically through contaminated seed, hands, tools and plant contact.',
  'Mottled light and dark green leaves, distortion and stunting may occur; appearance alone does not identify the virus.',
  'Virus infection has no curative treatment. Confirm the cause and prevent contaminated handling between plants.',
  'Use tested seed, clean tools and hands and suitable resistant varieties.'],
 ['Tobamovirus দূষিত বীজ, হাত, যন্ত্র এবং গাছের সংস্পর্শে যান্ত্রিকভাবে ছড়াতে পারে।',
  'পাতায় হালকা ও গাঢ় সবুজ ছোপ, বিকৃতি এবং বৃদ্ধি কম হতে পারে; দেখে ভাইরাসের প্রজাতি নিশ্চিত হয় না।',
  'ভাইরাস আক্রান্ত গাছ সারানোর চিকিৎসা নেই। কারণ নিশ্চিত করুন এবং এক গাছ থেকে অন্য গাছে দূষণ ছড়ানো বন্ধ করুন।',
  'পরীক্ষিত বীজ, পরিষ্কার হাত ও যন্ত্র এবং উপযুক্ত প্রতিরোধী জাত ব্যবহার করুন।'],MOSAIC),
entry('mites','Spider Mites',['spider mites','spider mite','মাকড়','মাকড়','মাইট'],
 ['Two-spotted spider mites feed on plant cells; hot dry conditions favor populations.',
  'Fine pale stippling, bronzing and sometimes webbing occur. Inspect leaf undersides with magnification.',
  'Confirm living mites and monitor spread before selecting an integrated pest-management action.',
  'Monitor plants regularly and avoid practices that unnecessarily disrupt beneficial organisms.'],
 ['Two-spotted spider mite পাতার কোষ থেকে খাদ্য নেয়; গরম শুকনো পরিবেশে সংখ্যা বাড়তে পারে।',
  'পাতায় সূক্ষ্ম ফ্যাকাশে বিন্দু, ব্রোঞ্জ রং এবং কখনো জাল হয়। আতশকাচ দিয়ে পাতার নিচে দেখুন।',
  'জীবন্ত mite আছে কি না নিশ্চিত করে ছড়ানো পর্যবেক্ষণ করুন; তারপর সমন্বিত বালাই ব্যবস্থাপনা বাছুন।',
  'নিয়মিত পর্যবেক্ষণ করুন এবং উপকারী জীবের অপ্রয়োজনীয় ক্ষতি এড়ান।'],MITE),
entry('healthy','Healthy',['healthy','সুস্থ','স্বাভাবিক','thik ache'],
 ['A Healthy model match is a visual class match, not proof that every part of the plant is disease-free.',
  'Check both leaf surfaces, growing tips, stems and fruit for spots, distortion, pests or progressive wilting.',
  'If symptoms are progressing despite a Healthy match, take close photographs and seek an agricultural assessment.',
  'Maintain even watering, plant spacing, clean tools and regular monitoring.'],
 ['Healthy ফলটি ছবির class match; পুরো গাছ রোগমুক্ত থাকার প্রমাণ নয়।',
  'পাতার দুই পাশ, কচি ডগা, কান্ড ও ফলে দাগ, বিকৃতি, পোকা বা বাড়তে থাকা নেতিয়ে পড়া আছে কি না দেখুন।',
  'Healthy দেখালেও লক্ষণ বাড়লে কাছ থেকে ছবি তুলুন এবং কৃষি বিশেষজ্ঞের মূল্যায়ন নিন।',
  'নিয়মিত সমান সেচ, গাছের দূরত্ব, পরিষ্কার যন্ত্র ও পর্যবেক্ষণ চালিয়ে যান।'],KSTATE,[1,5]),
entry('target','Target Spot',['target spot','টার্গেট স্পট'],
 ['Corynespora cassiicola causes target spot; humid, wet canopies favor disease.',
  'Leaf spots with rings can resemble early blight; fruit can also be affected.',
  'Confirm the cause before selecting controls. Reduce canopy wetness and infected crop debris.',
  'Use clean plants and improve airflow and field sanitation.'],
 ['Corynespora cassiicola Target Spot ঘটায়; আর্দ্র ও ভেজা canopy রোগ বাড়ায়।',
  'বলয়যুক্ত পাতার দাগ Early Blight-এর মতো হতে পারে; ফলেও আক্রমণ হয়।',
  'নিয়ন্ত্রণ বাছার আগে কারণ নিশ্চিত করুন। ভেজা canopy ও আক্রান্ত ফসলের আবর্জনা কমান।',
  'পরিষ্কার চারা, বাতাস চলাচল ও ক্ষেতের পরিচ্ছন্নতা রাখুন।'],TARGET),
entry('speck','Bacterial Speck',['bacterial speck','ব্যাকটেরিয়াল স্পেক'],
 ['Pseudomonas bacteria can arrive on seed or transplants and spread in wet conditions.',
  'Small dark leaf spots and tiny black fruit specks overlap with bacterial spot symptoms.',
  'Keep plants dry during handling and obtain confirmation rather than identifying the bacteria from one photo.',
  'Use clean planting stock and tools and avoid splashing irrigation.'],
 ['Pseudomonas ব্যাকটেরিয়া বীজ বা চারায় আসতে পারে এবং ভেজা পরিবেশে ছড়ায়।',
  'পাতায় ছোট কালচে দাগ ও ফলে ক্ষুদ্র কালো speck হয়; Bacterial Spot-এর সঙ্গে মিল থাকে।',
  'ভেজা গাছে কাজ এড়ান এবং এক ছবি দিয়ে ব্যাকটেরিয়া নিশ্চিত না করে বিশেষজ্ঞের মূল্যায়ন নিন।',
  'পরিষ্কার চারা ও যন্ত্র ব্যবহার করুন এবং সেচের ছিটা কমান।'],KSTATE,[3]),
entry('canker','Bacterial Canker',['bacterial canker','ক্যাঙ্কার'],
 ['Clavibacter bacteria can spread in contaminated planting material and through handling.',
  'One-sided wilting, stem streaks or cankers and bird-eye fruit spots may occur.',
  'Stem and fruit examination is needed; separate suspect plants and obtain expert confirmation.',
  'Use clean seed and transplants, sanitize tools and avoid carrying infected debris between beds.'],
 ['Clavibacter ব্যাকটেরিয়া দূষিত চারা বা বীজ এবং কাজের সময় ছড়াতে পারে।',
  'একপাশ নেতিয়ে পড়া, কান্ডে রেখা বা ক্ষত এবং ফলে bird-eye দাগ হতে পারে।',
  'কান্ড ও ফলও পরীক্ষা দরকার; সন্দেহজনক গাছ আলাদা করে বিশেষজ্ঞ দিয়ে নিশ্চিত করুন।',
  'পরিষ্কার বীজ ও চারা, পরিষ্কার যন্ত্র এবং আক্রান্ত আবর্জনা অন্য বেডে না নেওয়া অনুসরণ করুন।'],KSTATE,[3,4]),
entry('anthracnose','Anthracnose',['anthracnose','অ্যানথ্রাকনোজ'],
 ['Colletotrichum fungi infect fruit and survive on infected residues.',
  'Ripe fruit may develop sunken circular lesions; a leaf photograph alone is poor evidence.',
  'Inspect fruit, harvest ripe fruit promptly and remove infected fruit from the growing area.',
  'Reduce soil splash and wet foliage using mulch, staking and soil-level watering.'],
 ['Colletotrichum ছত্রাক ফলে আক্রমণ করে এবং আক্রান্ত অবশিষ্টাংশে টিকে থাকতে পারে।',
  'পাকা ফলে গোল বসে যাওয়া দাগ হয়; শুধু পাতার ছবি যথেষ্ট evidence নয়।',
  'ফল দেখুন, সময়মতো পাকা ফল তুলুন এবং আক্রান্ত ফল ক্ষেত থেকে সরান।',
  'Mulch, খুঁটি ও গোড়ায় সেচ দিয়ে মাটির ছিটা এবং ভেজাভাব কমান।'],IOWA,[3]),
entry('fusarium','Fusarium Wilt',['fusarium','ফিউজারিয়াম','ফিউজারিয়াম'],
 ['Soil-borne Fusarium infects roots and the plant water-conducting system.',
  'Yellowing and wilting may begin on one side; internal vascular browning needs examination.',
  'Inspect roots and cut-stem symptoms with expert help; leaf appearance cannot distinguish wilt causes.',
  'Use resistant varieties, clean transplants and avoid moving infested soil.'],
 ['মাটিবাহিত Fusarium শিকড় ও গাছের পানি পরিবহন ব্যবস্থায় আক্রমণ করে।',
  'একপাশ থেকে হলুদভাব ও নেতিয়ে পড়া শুরু হতে পারে; কান্ডের ভেতরের বাদামি ভাব পরীক্ষা দরকার।',
  'বিশেষজ্ঞের সহায়তায় শিকড় ও কাটা কান্ড দেখুন; শুধু পাতা দেখে wilt-এর কারণ আলাদা করা যায় না।',
  'প্রতিরোধী জাত, পরিষ্কার চারা এবং আক্রান্ত মাটি অন্য স্থানে না নেওয়া সাহায্য করে।'],IOWA,[3,4]),
entry('verticillium','Verticillium Wilt',['verticillium','ভার্টিসিলিয়াম'],
 ['Verticillium is a soil-borne fungus that affects vascular tissue.',
  'Older leaves may yellow, develop wedge-like dead areas and wilt; other root and vascular disorders can resemble this.',
  'Check soil moisture, roots and stems and seek confirmation before choosing a response.',
  'Use resistant varieties and clean plants and reduce movement of infested soil.'],
 ['মাটিবাহিত Verticillium ছত্রাক গাছের পরিবহন tissue-তে আক্রমণ করে।',
  'পুরোনো পাতা হলুদ, কীলকের মতো মরা অংশ ও নেতিয়ে পড়া দেখা যেতে পারে; অন্য শিকড়ের সমস্যাও একই রকম।',
  'মাটির আর্দ্রতা, শিকড় ও কান্ড পরীক্ষা করে কারণ নিশ্চিত করুন।',
  'প্রতিরোধী জাত ও পরিষ্কার চারা ব্যবহার করুন; আক্রান্ত মাটি ছড়াবেন না।'],IOWA,[4]),
entry('graymold','Gray Mold',['gray mold','grey mold','ধূসর ছাঁচ'],
 ['Botrytis is favored by damp conditions and often colonizes damaged or dying tissue.',
  'Gray fuzzy growth may occur on affected leaves, stems, flowers or fruit.',
  'Remove dead material carefully and improve airflow; have suspicious stem lesions assessed.',
  'Limit condensation and prolonged wetness and avoid injuring plants.'],
 ['Botrytis ভেজা পরিবেশে এবং ক্ষতিগ্রস্ত বা মরা tissue-তে বাড়ে।',
  'আক্রান্ত পাতা, কান্ড, ফুল বা ফলে ধূসর তুলার মতো আবরণ হতে পারে।',
  'মরা অংশ সাবধানে সরান ও বাতাস চলাচল বাড়ান; কান্ডের সন্দেহজনক ক্ষত যাচাই করান।',
  'দীর্ঘ সময় ভেজা থাকা ও condensation কমান এবং গাছে আঘাত এড়ান।'],IOWA,[8]),
entry('powdery','Powdery Mildew',['powdery mildew','পাউডারি'],
 ['Powdery mildew fungi grow on susceptible foliage.',
  'White powdery patches and yellowing may be visible; leaf mold and residues can be confused with it.',
  'Inspect both surfaces and confirm the growth is fungal; improve airflow.',
  'Use suitable resistant plants where available and monitor protected crops regularly.'],
 ['Powdery mildew ছত্রাক সংবেদনশীল পাতায় বৃদ্ধি পায়।',
  'সাদা গুঁড়ার মতো আবরণ ও হলুদভাব হতে পারে; Leaf Mold বা জমে থাকা পদার্থের সঙ্গে ভুল হতে পারে।',
  'পাতার দুই পাশ দেখুন, আবরণটি ছত্রাক কি না নিশ্চিত করুন এবং বাতাস চলাচল বাড়ান।',
  'পাওয়া গেলে উপযুক্ত প্রতিরোধী চারা এবং নিয়মিত greenhouse পর্যবেক্ষণ রাখুন।'],IOWA,[8]),
entry('spottedwilt','Tomato Spotted Wilt',['spotted wilt','tswv','স্পটেড উইল্ট'],
 ['Tomato spotted wilt virus is transmitted by thrips.',
  'Bronzing, dark spots, wilting and rings on fruit may occur; laboratory confirmation may be needed.',
  'Virus-infected plants cannot be cured. Have the cause confirmed and manage infected plants and vectors with local advice.',
  'Use clean planting material and monitor thrips and weed hosts.'],
 ['Thrips পোকা Tomato Spotted Wilt Virus ছড়ায়।',
  'ব্রোঞ্জ রং, কালো দাগ, নেতিয়ে পড়া এবং ফলে বলয় হতে পারে; পরীক্ষাগারে নিশ্চিত করা লাগতে পারে।',
  'ভাইরাস আক্রান্ত গাছ সারানো যায় না। কারণ নিশ্চিত করে কৃষিবিদের পরামর্শে আক্রান্ত গাছ ও বাহক সামলান।',
  'পরিষ্কার চারা নিন এবং thrips ও host আগাছা পর্যবেক্ষণ করুন।'],IOWA,[7]),
entry('nutrition','Magnesium Deficiency',['magnesium','ম্যাগনেস','পুষ্টির ঘাটতি'],
 ['Magnesium deficiency or nutrient imbalance can limit chlorophyll formation; a photograph cannot establish soil availability.',
  'Older leaves may yellow between veins while veins remain greener; several diseases and root problems can look similar.',
  'Obtain soil or tissue testing and check pH and other nutrients before selecting fertilizer. No magnesium visual class is installed.',
  'Use a test-based nutrition plan and avoid unmeasured fertilizer additions.'],
 ['Magnesium-এর ঘাটতি বা পুষ্টির ভারসাম্যহীনতায় chlorophyll কমতে পারে; ছবি মাটিতে পুষ্টির পরিমাণ জানায় না।',
  'পুরোনো পাতার শিরা তুলনামূলক সবুজ রেখে মাঝখান হলুদ হতে পারে; রোগ ও শিকড়ের সমস্যাও দেখতে একই রকম।',
  'সার দেওয়ার আগে মাটি বা tissue পরীক্ষা এবং pH ও অন্য পুষ্টি যাচাই করুন। ইনস্টল করা model-এ Magnesium visual class নেই।',
  'পরীক্ষাভিত্তিক পুষ্টি ব্যবস্থাপনা করুন; আন্দাজে অতিরিক্ত সার দেবেন না।'],MAG),
entry('miner','Leafminer Damage',['leafminer','leaf miner','লিফ মাইনার','সুড়ঙ্গ','সুড়ঙ্গ'],
 ['Leafminer larvae feed inside leaf tissue.',
  'Pale winding mines or blotches can appear inside the leaf; inspect for larvae and fresh damage.',
  'Confirm the pest and monitor infestation before taking action; preserve parasitoids and other natural enemies.',
  'Avoid unnecessary broad-spectrum insecticides that disrupt biological control.'],
 ['Leafminer-এর লার্ভা পাতার ভেতরের tissue খায়।',
  'পাতার ভেতর ফ্যাকাশে আঁকাবাঁকা সুড়ঙ্গ বা blotch হয়; লার্ভা ও নতুন ক্ষতি দেখুন।',
  'পোকা নিশ্চিত করে আক্রমণ পর্যবেক্ষণ করুন; parasitoid ও অন্য প্রাকৃতিক শত্রু রক্ষা করুন।',
  'প্রাকৃতিক নিয়ন্ত্রণ নষ্ট করে এমন অপ্রয়োজনীয় broad-spectrum কীটনাশক এড়িয়ে চলুন।'],MINER),
entry('leafroll','Physiological Leaf Roll',['leaf roll','physiological','পাতা মোড়ানো','পাতা মোড়ানো','পাতা কুঁচকে','curling'],
 ['Heat, changing soil moisture, pruning or root disturbance can cause noninfectious leaf roll.',
  'Leaves roll while remaining relatively green; curling alone does not establish a virus.',
  'Check moisture, roots and recent weather; maintain even watering and avoid further root injury.',
  'Limit severe pruning and large irrigation swings and protect roots during cultivation.'],
 ['গরম, মাটির আর্দ্রতা বদল, pruning বা শিকড়ের আঘাতে সংক্রমণ ছাড়াই পাতা মোড়াতে পারে।',
  'পাতা তুলনামূলক সবুজ থেকেও মোড়ায়; শুধু কুঁচকানো মানেই ভাইরাস নয়।',
  'আর্দ্রতা, শিকড় ও সাম্প্রতিক আবহাওয়া দেখুন; সমান সেচ রাখুন এবং শিকড়ের ক্ষতি এড়ান।',
  'অতিরিক্ত pruning ও সেচের বড় ওঠানামা কমান; নিড়ানির সময় শিকড় বাঁচান।'],IOWA,[11]),
entry('blossom','Blossom End Rot',['blossom end rot','ব্লসম এন্ড','ফলের নিচে কালো'],
 ['Disrupted calcium supply to developing fruit, often linked to uneven moisture or root stress, causes this physiological disorder.',
  'A dark, sunken patch develops at the blossom end of fruit. This is not diagnosed from a leaf.',
  'Maintain even soil moisture and protect roots. Check soil conditions before adding calcium or other fertilizer.',
  'Mulch, avoid excessive fertilizer and prevent severe drying followed by heavy watering.'],
 ['অনিয়মিত আর্দ্রতা বা শিকড়ের চাপে বাড়তে থাকা ফলে calcium পৌঁছানো বাধাগ্রস্ত হলে এই শারীরবৃত্তীয় সমস্যা হয়।',
  'ফলের ফুলের দিকের নিচে কালচে বসে যাওয়া দাগ হয়; পাতার ছবি দিয়ে শনাক্ত করা যায় না।',
  'মাটির আর্দ্রতা সমান রাখুন ও শিকড় রক্ষা করুন। Calcium বা সার বাড়ানোর আগে মাটি যাচাই করুন।',
  'Mulch দিন, অতিরিক্ত সার এড়ান এবং খুব শুকিয়ে যাওয়ার পর অতিরিক্ত সেচ দেবেন না।'],IOWA,[9]),
entry('sunscald','Sunscald',['sunscald','রোদে পোড়া','রোদে পোড়া'],
 ['Exposed fruit can be damaged by strong sunlight and heat.',
  'Pale or papery patches develop on exposed fruit surfaces; later decay may follow.',
  'Inspect the fruit and protect remaining canopy; do not confuse a fruit disorder with a leaf-model result.',
  'Avoid excessive leaf removal and maintain healthy foliage.'],
 ['তীব্র রোদ ও গরমে উন্মুক্ত ফলের ক্ষতি হয়।',
  'রোদ লাগা ফলে ফ্যাকাশে বা কাগজের মতো দাগ হয়; পরে পচন ধরতে পারে।',
  'ফল পরীক্ষা করুন এবং অবশিষ্ট canopy রক্ষা করুন; পাতার model-এর ফল দিয়ে এটি নিশ্চিত করবেন না।',
  'অতিরিক্ত পাতা সরাবেন না এবং সুস্থ পাতার আবরণ রাখুন।'],IOWA,[10]),
entry('herbicide','Herbicide Injury',['herbicide','আগাছানাশক','ওষুধে পাতা'],
 ['Herbicide drift, contaminated material or accidental exposure can injure tomato plants.',
  'Twisted or narrow young leaves and distorted growth may resemble viral disease.',
  'Review nearby spraying and input history and seek assessment; a disease label alone cannot establish chemical injury.',
  'Prevent drift and avoid contaminated compost, soil or equipment.'],
 ['আগাছানাশকের drift, দূষিত উপকরণ বা ভুল প্রয়োগে টমেটোর ক্ষতি হয়।',
  'কচি পাতা সরু বা পেঁচানো এবং বৃদ্ধি বিকৃত হতে পারে; ভাইরাসের সঙ্গে মিল থাকে।',
  'পাশের spray ও ব্যবহৃত উপকরণের ইতিহাস দেখুন এবং মূল্যায়ন নিন; রোগের label দিয়ে রাসায়নিক ক্ষতি নিশ্চিত হয় না।',
  'Drift বন্ধ করুন এবং দূষিত compost, মাটি বা যন্ত্র এড়ান।'],IOWA,[11]),
entry('watering','Tomato Watering',['watering','irrigation','water','পানি','সেচ','সার','fertilizer'],
 ['Moisture stress and persistently wet foliage create different plant-health problems.',
  'Inspect the soil and plant rather than watering from a fixed photo-based schedule.',
  'Water the soil near the roots, adjusting to soil moisture, plant size and weather; avoid persistently saturated roots.',
  'Keep moisture reasonably even, use mulch and allow airflow; soil testing should guide fertilizer decisions.'],
 ['পানির অভাব এবং দীর্ঘ সময় ভেজা পাতা আলাদা সমস্যার ঝুঁকি তৈরি করে।',
  'শুধু ছবি দেখে নির্দিষ্ট সময়সূচি না দিয়ে মাটি ও গাছের অবস্থা দেখুন।',
  'মাটির আর্দ্রতা, গাছের আকার ও আবহাওয়া অনুযায়ী গোড়ায় পানি দিন; শিকড় সবসময় পানিতে ডুবে রাখবেন না।',
  'আর্দ্রতা সমান রাখুন, mulch ও বাতাস চলাচল রাখুন; মাটির পরীক্ষার ভিত্তিতে সার ঠিক করুন।'],IOWA,[1,2,9])
]

def matched(question):
    q=question.lower()
    return [d for d in CORPUS if any(t in q for t in d['tags'])]

def retrieve(question,prediction=None):
    q=question.lower();label=(prediction or {}).get('label') or '';labels=[label]
    labels += [d.get('label') for d in (prediction or {}).get('detections',[])[:3]]
    ranked=[]
    for doc in CORPUS:
        named=sum(len(t) for t in doc['tags'] if t in q)
        evidence=60 if doc['label'] in labels else 0
        if doc['id']=='healthy' and any(labels) and 'Healthy' not in labels:named=0
        if named or evidence:ranked.append((named+evidence,doc))
    return [doc for _,doc in sorted(ranked,key=lambda x:-x[0])[:3]]

def source_list(docs):return [dict(d['source'],id=d['id'],paraphrase=d['en']) for d in docs]

def direct(question,lang,has_image=False,has_document=False):
    if has_image or has_document:return None
    q=re.sub(r'[\s!,.?।]+',' ',question.lower()).strip();bn=lang=='bn'
    if q in {'hi','hello','hey','হাই','হ্যালো','সালাম','আসসালামু আলাইকুম','assalamualaikum','assalamu alaikum'}:
        return 'হ্যালো! টমেটো পাতার ছবি দিন। স্থানীয় YOLO দিয়ে সম্ভাব্য ফল এবং guide থেকে কারণ, লক্ষণ ও করণীয় জানাব। API ছাড়াও এই অংশ কাজ করে।' if bn else 'Hello! Send a tomato leaf photo. Local YOLO supplies possible conditions and the offline guide explains causes, symptoms and care.'
    if q in {'thanks','thank you','ধন্যবাদ'}:return 'পরের প্রশ্ন বা ছবি পাঠাতে পারেন।' if bn else 'Send another question or photo whenever you need.'
    if q in {'help','what can you do','কি করতে পারো','কী করতে পারো','তুমি কী করতে পারো'}:
        return 'আমি স্থানীয় Tomato YOLO ফল ও সবুজ detection box দেখাই, guide থেকে কারণ-লক্ষণ-করণীয়-প্রতিরোধ জানাই এবং একই ছবির follow-up প্রশ্ন মনে রাখি। Knowledge catalog-এর সব সমস্যার trained visual class নেই; অন্য ফসল ও Magnesium শনাক্ত করার model নেই।' if bn else 'I explain local Tomato YOLO results with real detection boxes and sourced causes, symptoms, care and prevention. Follow-up questions can use the same submitted evidence. Knowledge coverage exceeds visual classes; other crops and magnesium have no installed visual model.'
    return None

def follow_up(question):
    q=question.lower()
    # Only explicit follow-up intent; never attach an old image to a greeting or an unseen new image.
    return bool(re.search(r'cause|symptom|treat|prevent|remed|why|more|next|\bit\b|\bthis\b|karon|lokk|lokkh|proti|korbo|kivabe|kmne|ki kor|eta|eita|rog',q) or any(t in q for t in ['কারণ','লক্ষণ','করণীয়','করণীয়','প্রতিকার','প্রতিরোধ','এটা','এটি','এই রোগ','কী করব','আরও']))

def sections(question):
    q=question.lower();found=[]
    for key,words in [('cause',['cause','why','karon','কারণ','কেন']),('symptoms',['symptom','lokk','lokkh','লক্ষণ','চিনব']),('action',['treat','remed','proti','korbo','ki kor','করণ','প্রতিকার','চিকিৎসা','কী করব','কি করব']),('prevention',['prevent','প্রতিরোধ','বাঁচাব'])]:
        if any(w in q for w in words):found.append(key)
    return found or ['cause','symptoms','action','prevention']

def offline(question,lang,crop,prediction,docs,has_image,document_text):
    bn=lang=='bn';parts=[]
    if crop!='tomato':return f'{crop}: '+('এই ফসলের trained model নেই। Tomato weights দিয়ে এটির রোগ শনাক্ত করা হয়নি। ফসলের নাম ও নির্দিষ্ট লক্ষণ দিন এবং crop-specific বিশেষজ্ঞের মূল্যায়ন নিন।' if bn else 'No trained model for this crop is installed. Tomato weights do not identify its diseases. Use a crop-specific assessment.')
    if prediction:
        label=prediction.get('label');s=prediction['status']
        if label and s in ('OK','REVIEW'):
            parts.append(('**স্থানীয় YOLO ফল: সম্ভাব্য ' if bn else '**Local YOLO: possible ')+label+'**'+(f" · {prediction['score']*100:.1f}% class score." if prediction.get('score') is not None else '.'))
            if label=='Healthy':parts.append('এটি পুরো গাছ সুস্থ থাকার নিশ্চয়তা নয়।' if bn else 'This does not certify the entire plant as healthy.')
            if s=='REVIEW':parts.append('দুই model-এর রোগের label মেলেনি। এটিকে নিশ্চিত রোগ ধরবেন না; নিচের লক্ষণ মিলিয়ে বিশেষজ্ঞের মূল্যায়ন নিন।' if bn else 'The models disagree on the condition. Compare the symptoms below and obtain confirmation.')
            parts.append('Score রোগের severity বা রোগ নিশ্চিত হওয়ার probability নয়।' if bn else 'The score is neither severity nor a calibrated probability of diagnosis.')
        else:
            reasons={'NO_DETECTION':('Threshold-এর উপরে কোনো supported leaf region পাওয়া যায়নি। একটি পাতার দুই পাশ কাছ থেকে, স্থির আলোয় তুলুন। Box না পাওয়া মানে সুস্থ নয়.','No supported leaf region above threshold. Take a close, well-lit photo of both sides of one leaf. No box does not mean healthy.'),
                     'LOW_CONFIDENCE':('Model অনিশ্চিত; একটি রোগ নিশ্চিত করা যাচ্ছে না। আরেকটি পরিষ্কার ছবি ও লক্ষণ দিন।','The model is uncertain. Provide another clear photo and describe symptoms.'),
                     'LOW_QUALITY':('ছবিটি খুব অন্ধকার, ঝাপসা বা ফাঁকা। স্থির আলোয় পরিষ্কার ছবি দিন।','The image is too dark, blurred or uniform. Please provide a clear photo.')}
            parts.append((reasons.get(s) or ('স্থানীয় model ফল দেয়নি: '+s,'Local model did not return a condition: '+s))[0 if bn else 1])
    elif has_image:parts.append('ছবি পাওয়া গেছে, কিন্তু local model-এর ফল পাওয়া যায়নি।' if bn else 'Photo received, but no local model result is available.')
    elif docs:parts.append('এটি guide-এর সাধারণ তথ্য; নতুন ছবি থেকে disease detection নয়।' if bn else 'This is guide information, not a new image-based disease detection.')
    heads={'cause':('কারণ','Cause'),'symptoms':('লক্ষণ','Symptoms'),'action':('করণীয়','Care'),'prevention':('প্রতিরোধ','Prevention')}
    for i,d in enumerate(docs[:2]):
        fields=d['bn_fields' if bn else 'en_fields'];lines=[f"**{d['label']}** [{i+1}]"]
        for key in sections(question):lines.append(f"**{heads[key][0 if bn else 1]}:** {fields[key]}")
        parts.append('\n'.join(lines))
    if any(w in question.lower() for w in ['dose','dosage','মাত্রা','কতটুকু সার','কত সার','spray']):parts.append('ছবি দিয়ে সার বা কীটনাশকের মাত্রা ঠিক করা যায় না। স্থানীয় অনুমোদিত পণ্য ও কৃষিবিদের নির্দেশ অনুসরণ করুন।' if bn else 'A photo cannot establish a fertilizer or pesticide dose. Follow locally approved products and agronomic guidance.')
    if not docs and not prediction:
        if document_text:parts.append('নথির preview পড়তে পারেন। Offline mode নথির নতুন দাবির সত্যতা যাচাই করে না; নির্দিষ্ট টমেটো সমস্যা বা রোগের নাম নিয়ে প্রশ্ন করুন।' if bn else 'The document preview is available. Offline mode does not verify new document claims; ask about a specific tomato condition.')
        else:parts.append('টমেটো পাতার ছবি দিন অথবা রোগ/লক্ষণের নাম লিখুন। “কারণ”, “লক্ষণ”, “করণীয়” বা “প্রতিরোধ” নিয়ে follow-up করতে পারেন।' if bn else 'Attach a tomato leaf photo or name a condition. Ask follow-ups about causes, symptoms, care or prevention.')
    return '\n\n'.join(parts)
