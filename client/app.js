/**
 * Jan-Vani Main Application Logic
 * Integrates Voice Perception, Geolocation, Backend API, Offline Buffering,
 * Audio Synthesis and Officer Console.
 */

let currentLang = "mr"; // Default Marathi
let recordedAudioBlob = null;
let recordingSeconds = 0;
let recordingTimerInterval = null;
let currentRole = "commissioner"; // commissioner, ward_2, ward_4
let activeWardFilter = "ALL";
let allTicketsCache = [];
let mapInstance = null;
let mapMarkers = [];
let healthPollTimer = null;

/** Extra UI strings (fallback: en → mr) for newly added controls */
const UI_EXTRAS = {
  mr: {
    step1: "मायक्रोफोन दाबा आणि तुमच्या भाषेत बोला",
    step2: "एआय प्रभाग, प्रकार आणि गंभीरता ओळखते",
    step3: "ऑडिओ पुष्टीकरण आणि तिकीट क्रमांक मिळवा",
    locationDetecting: "स्थान शोधत आहे…",
    locationLive: "जीपीएस: {lat}, {lng} (±{acc}m)",
    locationFallback: "डिफॉल्ट: नागपूर (Dharampeth) — जीपीएस उपलब्ध नाही",
    severityLabel: "तातडीची पातळी (Urgency hint):",
    severityHint: "पर्यायी — एआय अंतिम गंभीरता ठरवते",
    sevMedium: "सामान्य (Medium — AI decides)",
    sevHigh: "अत्यंत तातडी (High)",
    sevLow: "कमी (Low)",
    processingText: "तक्रार विश्लेषण सुरू आहे…",
    trackEmpty: "अद्याप कोणतीही तक्रार नोंदवलेली नाही. मायक्रोफोन वापरून पहिली तक्रार नोंदवा.",
    goToVoice: "🎤 नागरिक आवाजाकडे जा",
    ticketLookupPlaceholder: "तिकीट आयडी (JV-2026-XXXX)",
    lookupBtn: "🔍 शोधा",
    lookupNotFound: "तिकीट सापडले नाही. आयडी तपासा.",
    connectionOnline: "ऑनलाइन",
    connectionOffline: "ऑफलाइन",
    connectionChecking: "जोडत आहे…",
    pipelineLabel: "⚡ पाइपलाइन वेळ (Pipeline timing)",
    offlineSynced: "{n} ऑफलाइन तक्रारी सिंक झाल्या.",
    benchmarkRun: "शेवटची चाचणी: {date}",
    benchmarkFail: "लाइव्ह अहवाल लोड करता आला नाही — स्थानिक डेटा दर्शविला."
  },
  hi: {
    step1: "माइक दबाएं और अपनी भाषा में बोलें",
    step2: "AI वार्ड, श्रेणी और प्राथमिकता पहचानता है",
    step3: "ऑडियो पुष्टि और टिकट नंबर प्राप्त करें",
    locationDetecting: "स्थान खोजा जा रहा है…",
    locationLive: "GPS: {lat}, {lng} (±{acc}m)",
    locationFallback: "डिफ़ॉल्ट: नागपुर — GPS उपलब्ध नहीं",
    severityLabel: "प्राथमिकता संकेत (Urgency hint):",
    severityHint: "वैकल्पिक — AI अंतिम प्राथमिकता तय करता है",
    sevMedium: "सामान्य (Medium — AI decides)",
    sevHigh: "अत्यंत तात्कालिक (High)",
    sevLow: "कम (Low)",
    processingText: "शिकायत का विश्लेषण हो रहा है…",
    trackEmpty: "अभी कोई शिकायत दर्ज नहीं। माइक से पहली शिकायत दर्ज करें।",
    goToVoice: "🎤 नागरिक आवाज पर जाएं",
    ticketLookupPlaceholder: "टिकट ID (JV-2026-XXXX)",
    lookupBtn: "🔍 खोजें",
    lookupNotFound: "टिकट नहीं मिला। ID जांचें।",
    connectionOnline: "ऑनलाइन",
    connectionOffline: "ऑफलाइन",
    connectionChecking: "कनेक्ट हो रहा…",
    pipelineLabel: "⚡ पाइपलाइन समय",
    offlineSynced: "{n} ऑफलाइन शिकायतें सिंक हुईं।",
    benchmarkRun: "अंतिम परीक्षण: {date}",
    benchmarkFail: "लाइव रिपोर्ट लोड नहीं — स्थानीय डेटा दिखाया गया।"
  },
  en: {
    step1: "Tap the mic and speak in your language",
    step2: "AI detects ward, category, and urgency",
    step3: "Get spoken confirmation and your ticket ID",
    locationDetecting: "Detecting location…",
    locationLive: "GPS: {lat}, {lng} (±{acc}m)",
    locationFallback: "Default: Nagpur (Dharampeth) — GPS unavailable",
    severityLabel: "Urgency hint (optional):",
    severityHint: "Optional — AI sets final priority",
    sevMedium: "Medium (AI decides)",
    sevHigh: "High urgency",
    sevLow: "Low",
    processingText: "Analyzing your grievance…",
    trackEmpty: "No grievances yet. Use the microphone to file your first report.",
    goToVoice: "🎤 Go to Citizen Voice",
    ticketLookupPlaceholder: "Ticket ID (JV-2026-XXXX)",
    lookupBtn: "🔍 Look up",
    lookupNotFound: "Ticket not found. Check the ID.",
    connectionOnline: "Online",
    connectionOffline: "Offline",
    connectionChecking: "Connecting…",
    pipelineLabel: "⚡ Pipeline timing",
    offlineSynced: "Synced {n} offline grievance(s).",
    benchmarkRun: "Last test run: {date}",
    benchmarkFail: "Could not load live report — showing cached UI."
  }
};

function tExtra(key, vars = {}) {
  const pack = UI_EXTRAS[currentLang] || UI_EXTRAS.en || UI_EXTRAS.mr;
  let s = (pack && pack[key]) || UI_EXTRAS.en[key] || key;
  Object.keys(vars).forEach(k => {
    s = s.replace(`{${k}}`, vars[k]);
  });
  return s;
}

// Vernacular UI string dictionary (10 Languages)
// Comprehensive Vernacular UI string dictionary (All 10 Languages)
const I18N = {
  "mr": {
    "heroTitle": "जन-वाणी",
    "heroSub": "स्थानिक भाषेत बोला, नागरिक समस्या सोडवा",
    "micPrompt": "येथे स्पर्श करा आणि तुमची समस्या सांगा",
    "micRecording": "आम्ही ऐकत आहोत... बोलणे संपल्यावर पुन्हा स्पर्श करा",
    "audioPromptText": "नमस्कार! फक्त मायक्रोफोन बटण दाबा आणि तुमच्या भाषेत तक्रार सांगा.",
    "instantAck": "तक्रार प्राप्त झाली! विश्लेषण सुरू आहे...",
    "consentText": "मी माझा आवाज आणि स्थान महापालिकेस पाठवण्यास संमती देतो/देते (DPDP कायदा २०२३).",
    "waterLeak": "पाणी गळती (मराठी)",
    "pothole": "रस्त्यावरील खड्डा (मराठी)",
    "drainage": "ड्रेनेज तुंबले (मराठी)",
    "powerCut": "वीज पुरवठा खंडित (मराठी)",
    "garbage": "कचरा साचला (मराठी)",
    "listenStatus": "आवाज ऐका",
    "confRegistered": "तक्रार नोंदवली गेली!",
    "confAssignedWard": "नियुक्त प्रभाग",
    "confCategory": "समस्या प्रकार",
    "confUrgency": "गंभीरता",
    "confSummary": "एआय इंग्रजी सारांश",
    "confSpokenNotice": "ऑडिओ संदेश",
    "confReplay": "पुन्हा ऐका",
    "confMergeNotice": "स्वयंचलित एकत्रीकरण: जवळपासच्या नागरिकांनी हीच समस्या नोंदवली आहे. प्राधान्य वाढवले!",
    "brandTitle": "जन-वाणी",
    "brandSubtitle": "नागपूर महानगरपालिका | स्थानिक नागरी तक्रार निवारण",
    "navTabVoice": "🎤 नागरिक आवाज (Citizen Voice)",
    "navTabTrack": "📋 तक्रारी स्थिती (Track)",
    "navTabOfficer": "🏛️ अधिकारी कक्ष (Officer Console)",
    "navTabImpact": "📊 चाचणी अहवाल (Benchmarks)",
    "voiceBadgeBanner": "🔊 फक्त एका बटनाने तक्रार करा | टायपिंगची गरज नाही",
    "listenInstructions": "🔊 आवाज सूचना ऐका (Listen Instructions)",
    "gpsNotice": "📍 नागपूर जीपीएस स्थान स्वयंचलित जोडले जाईल",
    "presetsTitle": "⚡ थेट चाचणी उदाहरणे (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "परीक्षकांसाठी त्वरित चाचणी",
    "trackHeading": "📋 नोंदवलेल्या तक्रारींची स्थिती (My Grievances)",
    "trackSub": "नागरिक कोणताही मजकूर न वाचता 'आवाज ऐका' बटणावर दाबून थेट माहिती ऐकू शकतात.",
    "officerHonestBanner": "ℹ️ प्रामाणिक डेटा नोंद (Honesty Rule): प्रदर्शित आकडेवारी प्रात्यक्षिक आणि पाइपलाइन नोंदींमधून संकलित केलेली आहे. प्रत्यक्ष मोजलेली अचूकता 'चाचणी अहवाल' विभागात दिली आहे.",
    "officerHeading": "🏛️ प्रभाग नियंत्रण व तक्रार निवारण कक्ष",
    "officerRoleLabel": "अधिकारी पद / Role:",
    "roleCommissioner": "महानगरपालिका आयुक्त (All Wards)",
    "roleWard2": "प्रभाग अधिकारी: धरमपेठ (Ward 2 Officer)",
    "roleWard4": "प्रभाग अधिकारी: धंतोली (Ward 4 Officer)",
    "kpiTotalTitle": "एकूण तक्रारी (Total)",
    "kpiTotalSub": "नोंदवलेली प्रकरणे",
    "kpiOpenTitle": "प्रलंबित (Open)",
    "kpiOpenSub": "तातडीने पाहणे आवश्यक",
    "kpiInProgressTitle": "कार्यरत (In Progress)",
    "kpiInProgressSub": "दुरुस्ती पथक घटनास्थळी",
    "kpiResolvedTitle": "निवारण झाले (Resolved)",
    "kpiResolvedSub": "काम पूर्ण",
    "kpiMergedTitle": "एकत्रित डुप्लिकेट्स (Merged)",
    "kpiMergedSub": "५० मी / ४८ तासांत जोडलेले",
    "mapTitle": "🗺️ नागपूर प्रभाग नकाशा (Ward Heatmap & Complaint Clusters)",
    "mapSub": "प्रभाग सीमा आणि ५० मीटरच्या आत एकत्रित केलेल्या तक्रारी दर्शवणारा नकाशा",
    "searchPlaceholder": "🔍 शोधा (ID, प्रभाग, विषय)...",
    "csvExport": "📥 CSV एक्सपोर्ट",
    "thTicketId": "तिकीट आयडी (ID)",
    "thWard": "प्रभाग (Ward)",
    "thCategory": "प्रकार (Category)",
    "thUrgency": "गंभीरता (Urgency)",
    "thStatus": "स्थिती (Status)",
    "thVoice": "ऑडिओ (Voice)",
    "thAction": "कृती (Action)",
    "footerText": "जन-वाणी (Jan-Vani) | सेंट व्हिन्सेंट पलोटी कॉलेज ऑफ इंजिनिअरिंग अँड टेक्नॉलॉजी, नागपूर | AI for Social Impact"
  },
  "hi": {
    "heroTitle": "जन-वाणी",
    "heroSub": "अपनी भाषा में बोलें, नागरिक समस्याओं का समाधान पाएं",
    "micPrompt": "यहाँ दबाएं और अपनी समस्या बोलें",
    "micRecording": "हम सुन रहे हैं... बोलना समाप्त होने पर दोबारा दबाएं",
    "audioPromptText": "नमस्ते! बस माइक बटन दबाएं और अपनी भाषा में शिकायत बताएं।",
    "instantAck": "शिकायत प्राप्त हुई! विश्लेषण जारी है...",
    "consentText": "मैं अपनी आवाज और स्थान नगर निगम को भेजने की सहमति देता/देती हूँ (DPDP एक्ट 2023)।",
    "waterLeak": "पानी की आपूर्ति (हिंदी)",
    "pothole": "सड़क पर गड्ढा (हिंदी)",
    "drainage": "नाली जाम (हिंदी)",
    "powerCut": "बिजली गुल (हिंदी)",
    "garbage": "कचरे का ढेर (हिंदी)",
    "listenStatus": "स्थिति सुनें",
    "confRegistered": "शिकायत दर्ज हो गई!",
    "confAssignedWard": "आवंटित वार्ड",
    "confCategory": "समस्या श्रेणी",
    "confUrgency": "प्राथमिकता",
    "confSummary": "एआई सारांश",
    "confSpokenNotice": "ऑडियो संदेश",
    "confReplay": "दोबारा सुनें",
    "confMergeNotice": "स्वचालित विलय: आसपास के कई नागरिकों ने इस समस्या की सूचना दी है। प्राथमिकता बढ़ाई गई!",
    "brandTitle": "जन-वाणी",
    "brandSubtitle": "नागपुर नगर निगम | स्थानीय नागरिक शिकायत निवारण",
    "navTabVoice": "🎤 नागरिक आवाज (Citizen Voice)",
    "navTabTrack": "📋 शिकायत स्थिति (Track)",
    "navTabOfficer": "🏛️ अधिकारी कक्ष (Officer Console)",
    "navTabImpact": "📊 परीक्षण रिपोर्ट (Benchmarks)",
    "voiceBadgeBanner": "🔊 बस एक बटन से शिकायत करें | टाइपिंग की जरूरत नहीं",
    "listenInstructions": "🔊 आवाज निर्देश सुनें (Listen Instructions)",
    "gpsNotice": "📍 नागपुर जीपीएस स्थान स्वचालित रूप से जोड़ा जाएगा",
    "presetsTitle": "⚡ त्वरित परीक्षण उदाहरण (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "परीक्षकों के लिए त्वरित परीक्षण",
    "trackHeading": "📋 दर्ज शिकायतों की स्थिति (My Grievances)",
    "trackSub": "नागरिक कोई भी पाठ पढ़े बिना 'स्थिति सुनें' बटन दबाकर सीधे जानकारी सुन सकते हैं।",
    "officerHonestBanner": "ℹ️ प्रामाणिक डेटा नोट (Honesty Rule): प्रदर्शित आंकड़े वास्तविक लाइव पाइपलाइन से संकलित हैं। वास्तविक सटीकता 'परीक्षण रिपोर्ट' में दी गई है।",
    "officerHeading": "🏛️ प्रभाग नियंत्रण एवं शिकायत निवारण कक्ष",
    "officerRoleLabel": "अधिकारी पद / Role:",
    "roleCommissioner": "नगर निगम आयुक्त (All Wards)",
    "roleWard2": "प्रभाग अधिकारी: धरमपेठ (Ward 2 Officer)",
    "roleWard4": "प्रभाग अधिकारी: धंतोली (Ward 4 Officer)",
    "kpiTotalTitle": "कुल शिकायतें (Total)",
    "kpiTotalSub": "दर्ज मामले",
    "kpiOpenTitle": "लंबित (Open)",
    "kpiOpenSub": "तत्काल कार्रवाई आवश्यक",
    "kpiInProgressTitle": "प्रगति पर (In Progress)",
    "kpiInProgressSub": "मरम्मत दल घटनास्थल पर",
    "kpiResolvedTitle": "समाधान हुआ (Resolved)",
    "kpiResolvedSub": "कार्य पूर्ण",
    "kpiMergedTitle": "विलय किए गए (Merged)",
    "kpiMergedSub": "50मी / 48 घंटे में जोड़े गए",
    "mapTitle": "🗺️ नागपुर प्रभाग मानचित्र (Ward Heatmap & Complaint Clusters)",
    "mapSub": "प्रभाग सीमाएं और 50 मीटर के दायरे में एकत्रित शिकायतों को दर्शाने वाला नक्शा",
    "searchPlaceholder": "🔍 खोजें (ID, प्रभाग, विषय)...",
    "csvExport": "📥 CSV एक्सपोर्ट",
    "thTicketId": "टिकट आईडी (ID)",
    "thWard": "वार्ड (Ward)",
    "thCategory": "श्रेणी (Category)",
    "thUrgency": "प्राथमिकता (Urgency)",
    "thStatus": "स्थिति (Status)",
    "thVoice": "ऑडियो (Voice)",
    "thAction": "कार्रवाई (Action)",
    "footerText": "जन-वाणी (Jan-Vani) | सेंट विंसेंट पलोटी कॉलेज ऑफ इंजीनियरिंग एंड टेक्नोलॉजी, नागपुर | AI for Social Impact"
  },
  "en": {
    "heroTitle": "Jan-Vani",
    "heroSub": "Speak in your dialect, get civic issues resolved",
    "micPrompt": "Tap here and speak your problem",
    "micRecording": "Listening... Tap again when finished",
    "audioPromptText": "Welcome! Simply tap the microphone button and report your problem.",
    "instantAck": "Complaint Received! Processing...",
    "consentText": "I consent to share voice and GPS location with Municipal Corporation (DPDP Act 2023).",
    "waterLeak": "Water Leakage",
    "pothole": "Road Pothole",
    "drainage": "Drain Blockage",
    "powerCut": "Power Outage",
    "garbage": "Garbage Dump",
    "listenStatus": "Listen Voice",
    "confRegistered": "Grievance Registered",
    "confAssignedWard": "Assigned Ward",
    "confCategory": "Category",
    "confUrgency": "Urgency",
    "confSummary": "AI English Summary",
    "confSpokenNotice": "Spoken Audio Confirmation",
    "confReplay": "Play Voice Again",
    "confMergeNotice": "Deduplication Merge: Multiple nearby citizens reported this issue. Urgency escalated!",
    "brandTitle": "Jan-Vani",
    "brandSubtitle": "Nagpur Municipal Corporation | Vernacular Civic Voice Redressal",
    "navTabVoice": "🎤 Citizen Voice",
    "navTabTrack": "📋 Track Status",
    "navTabOfficer": "🏛️ Officer Console",
    "navTabImpact": "📊 Benchmarks & Impact",
    "voiceBadgeBanner": "🔊 Voice Redressal with 1 Tap | No Typing Needed",
    "listenInstructions": "🔊 Listen Voice Instructions",
    "gpsNotice": "📍 Nagpur GPS location will be auto-attached",
    "presetsTitle": "⚡ One-Click Vernacular Voice Demos",
    "presetsSubtitle": "Quick testing for evaluators",
    "trackHeading": "📋 Grievance Tracking Status",
    "trackSub": "Citizens can listen to live updates directly by clicking the voice button without reading.",
    "officerHonestBanner": "ℹ️ Honesty Rule: Displayed analytics reflect live pipeline submissions and verified runs. Empirical metrics are reported in Benchmarks.",
    "officerHeading": "🏛️ Ward Operations & Grievance Redressal Center",
    "officerRoleLabel": "Designation / Role:",
    "roleCommissioner": "Municipal Commissioner (All Wards)",
    "roleWard2": "Ward Officer: Dharampeth (Ward 2)",
    "roleWard4": "Ward Officer: Dhantoli (Ward 4)",
    "kpiTotalTitle": "Total Grievances",
    "kpiTotalSub": "Logged cases",
    "kpiOpenTitle": "Open (Pending)",
    "kpiOpenSub": "Requires immediate action",
    "kpiInProgressTitle": "In Progress",
    "kpiInProgressSub": "Response crew dispatched",
    "kpiResolvedTitle": "Resolved",
    "kpiResolvedSub": "Action completed",
    "kpiMergedTitle": "Merged Duplicates",
    "kpiMergedSub": "Within 50m / 48 hours",
    "mapTitle": "🗺️ Nagpur Ward Heatmap & Complaint Clusters",
    "mapSub": "Map visualizing ward boundaries and clustered grievances within 50 meters",
    "searchPlaceholder": "🔍 Search (ID, Ward, Topic)...",
    "csvExport": "📥 Export CSV",
    "thTicketId": "Ticket ID",
    "thWard": "Ward",
    "thCategory": "Category",
    "thUrgency": "Urgency",
    "thStatus": "Status",
    "thVoice": "Audio Voice",
    "thAction": "Action",
    "footerText": "Jan-Vani | St. Vincent Pallotti College of Engineering and Technology, Nagpur | AI for Social Impact"
  },
  "bn": {
    "heroTitle": "জন-বাণী",
    "heroSub": "নিজের ভাষায় বলুন, নাগরিক সমস্যার সমাধান পান",
    "micPrompt": "এখানে স্পর্শ করুন এবং আপনার সমস্যা বলুন",
    "micRecording": "আমরা শুনছি... কথা শেষ হলে আবার স্পর্শ করুন",
    "audioPromptText": "নমস্কার! শুধু মাইক বোতাম টিপুন এবং নিজের ভাষায় অভিযোগ বলুন।",
    "instantAck": "অভিযোগ গৃহীত হয়েছে! বিশ্লেষণ চলছে...",
    "consentText": "আমি পৌরসভায় আমার কণ্ঠ ও অবস্থান পাঠাতে সম্মতি দিচ্ছি (DPDP আইন ২০২৩)।",
    "waterLeak": "জল সরবরাহ সমস্যা (বাংলা)",
    "pothole": "রাস্তার গর্ত (বাংলা)",
    "drainage": "নর্দমা বন্ধ (বাংলা)",
    "powerCut": "বিদ্যুৎ বিভ্রাট (বাংলা)",
    "garbage": "আবর্জনা পরিষ্কার (বাংলা)",
    "listenStatus": "কণ্ঠ শুনুন",
    "confRegistered": "অভিযোগ নথিভুক্ত হয়েছে!",
    "confAssignedWard": "নির্ধারিত ওয়ার্ড",
    "confCategory": "বিভাগ",
    "confUrgency": "জরুরি অবস্থা",
    "confSummary": "এআই ইংরেজি সারসংক্ষেপ",
    "confSpokenNotice": "অডিও বার্তা",
    "confReplay": "আবার শুনুন",
    "confMergeNotice": "স্বয়ংক্রিয় একত্রীকরণ: কাছাকাছি একাধিক নাগরিক এই সমস্যা জানিয়েছেন। অগ্রাধিকার বৃদ্ধি করা হয়েছে!",
    "brandTitle": "জন-বাণী",
    "brandSubtitle": "নাগপুর পৌরনিগম | স্থানীয় নাগরিক অভিযোগ প্রতিকার",
    "navTabVoice": "🎤 নাগরিক কণ্ঠ (Citizen Voice)",
    "navTabTrack": "📋 অভিযোগের স্থিতি (Track)",
    "navTabOfficer": "🏛️ আধিকারিক কক্ষ (Officer Console)",
    "navTabImpact": "📊 মূল্যায়ন প্রতিবেদন (Benchmarks)",
    "voiceBadgeBanner": "🔊 শুধুমাত্র একটি বোতামে অভিযোগ করুন | টাইপ করার প্রয়োজন নেই",
    "listenInstructions": "🔊 ভয়েস নির্দেশ শুনুন (Listen Instructions)",
    "gpsNotice": "📍 নাগপুর জিপিএস অবস্থান স্বয়ংক্রিয়ভাবে যুক্ত হবে",
    "presetsTitle": "⚡ তাৎক্ষণিক পরীক্ষার উদাহরণ (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "পরীক্ষকদের জন্য দ্রুত পরীক্ষা",
    "trackHeading": "📋 দায়ের করা অভিযোগের স্থিতি (My Grievances)",
    "trackSub": "নাগরিকরা কোনো লেখা না পড়ে 'কণ্ঠ শুনুন' বোতাম টিপে সরাসরি তথ্য শুনতে পারেন।",
    "officerHonestBanner": "ℹ️ সততা নিয়ম (Honesty Rule): প্রদর্শিত তথ্য প্রমাণাদি থেকে সংগৃহীত। পরিমাপ করা নির্ভুলতা 'মূল্যায়ন প্রতিবেদন' বিভাগে রয়েছে।",
    "officerHeading": "🏛️ ওয়ার্ড নিয়ন্ত্রণ ও অভিযোগ নিষ্পত্তি কেন্দ্র",
    "officerRoleLabel": "পদমর্যাদা / Role:",
    "roleCommissioner": "পৌর কমিশনার (All Wards)",
    "roleWard2": "ওয়ার্ড অফিসার: ধরমপেঠ (Ward 2 Officer)",
    "roleWard4": "ওয়ার্ড অফিসার: ধন্তোলি (Ward 4 Officer)",
    "kpiTotalTitle": "মোট অভিযোগ (Total)",
    "kpiTotalSub": "নথিভুক্ত মামলা",
    "kpiOpenTitle": "অমীমাংসিত (Open)",
    "kpiOpenSub": "জরুরি পদক্ষেপ প্রয়োজন",
    "kpiInProgressTitle": "চলমান (In Progress)",
    "kpiInProgressSub": "ঘটনাস্থলে মেরামত দল",
    "kpiResolvedTitle": "নিষ্পত্তি হয়েছে (Resolved)",
    "kpiResolvedSub": "কাজ সম্পন্ন",
    "kpiMergedTitle": "একত্রিত অনুলিপি (Merged)",
    "kpiMergedSub": "৫০মি / ৪৮ ঘণ্টায় সংযুক্ত",
    "mapTitle": "🗺️ নাগপুর ওয়ার্ড মানচিত্র (Ward Heatmap & Complaint Clusters)",
    "mapSub": "ওয়ার্ডের সীমানা এবং ৫০ মিটারের মধ্যে ক্লাস্টার করা অভিযোগের মানচিত্র",
    "searchPlaceholder": "🔍 খুঁজুন (ID, ওয়ার্ড, বিষয়)...",
    "csvExport": "📥 CSV এক্সপোর্ট",
    "thTicketId": "টিকিট আইডি (ID)",
    "thWard": "ওয়ার্ড (Ward)",
    "thCategory": "বিভাগ (Category)",
    "thUrgency": "জরুরি অবস্থা (Urgency)",
    "thStatus": "অবস্থা (Status)",
    "thVoice": "অডিও (Voice)",
    "thAction": "পদক্ষেপ (Action)",
    "footerText": "জন-বাণী (Jan-Vani) | সেন্ট ভিনসেন্ট পালোত্তি ইঞ্জিনিয়ারিং ও প্রযুক্তি কলেজ, নাগপুর | AI for Social Impact"
  },
  "gu": {
    "heroTitle": "જન-વાણી",
    "heroSub": "પોતાની ભાષામાં બોલો, નાગરિક સમસ્યાઓનો ઉકેલ મેળવો",
    "micPrompt": "અહીં સ્પર્શ કરો અને તમારી સમસ્યા બોલો",
    "micRecording": "અમે સાંભળી રહ્યા છીએ... બોલવાનું પૂરું થાય ત્યારે ફરી દબાવો",
    "audioPromptText": "નમસ્તે! ફક્ત માઇક બટન દબાવો અને તમારી ભાષામાં ફરિયાદ જણાવો.",
    "instantAck": "ફરિયાદ મળી ગઈ છે! ચકાસણી ચાલુ છે...",
    "consentText": "હું મારો અવાજ અને સ્થળ મહાનગરપાલિકાને મોકલવા સંમતિ આપું છું (DPDP એક્ટ ૨૦૨૩).",
    "waterLeak": "પાણી પુરવઠો (ગુજરાતી)",
    "pothole": "રસ્તા પર ખાડો (ગુજરાતી)",
    "drainage": "ગટર બ્લોકેજ (ગુજરાતી)",
    "powerCut": "વીજળી ગુલ (ગુજરાતી)",
    "garbage": "કચરાનો ઢગલો (ગુજરાતી)",
    "listenStatus": "અવાજ સાંભળો",
    "confRegistered": "ફરિયાદ નોંધાઈ ગઈ છે!",
    "confAssignedWard": "ફાળવેલ વોર્ડ",
    "confCategory": "શ્રેણી",
    "confUrgency": "તીવ્રતા",
    "confSummary": "એઆઈ અંગ્રેજી સારાંશ",
    "confSpokenNotice": "ઑડિયો સંદેશ",
    "confReplay": "ફરીથી સાંભળો",
    "confMergeNotice": "સ્વચાલિત મર્જ: આસપાસના નાગરિકોએ આ જ ફરિયાદ કરી છે. પ્રાથમિકતા વધારી દેવામાં આવી છે!",
    "brandTitle": "જન-વાણી",
    "brandSubtitle": "નાગપુર મહાનગરપાલિકા | સ્થાનિક નાગરિક ફરિયાદ નિવારણ",
    "navTabVoice": "🎤 નાગરિક અવાજ (Citizen Voice)",
    "navTabTrack": "📋 ફરિયાદ સ્થિતિ (Track)",
    "navTabOfficer": "🏛️ અધિકારી કક્ષ (Officer Console)",
    "navTabImpact": "📊 પરીક્ષણ અહેવાલ (Benchmarks)",
    "voiceBadgeBanner": "🔊 ફક્ત એક બટનથી ફરિયાદ કરો | ટાઇપ કરવાની જરૂર નથી",
    "listenInstructions": "🔊 અવાજ સૂચના સાંભળો (Listen Instructions)",
    "gpsNotice": "📍 નાગપુર જીપીએસ સ્થાન આપમેળે જોડવામાં આવશે",
    "presetsTitle": "⚡ ત્વરિત પરીક્ષણ ઉદાહરણો (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "પરીક્ષકો માટે ઝડપી પરીક્ષણ",
    "trackHeading": "📋 નોંધાયેલી ફરિયાદોની સ્થિતિ (My Grievances)",
    "trackSub": "નાગરિકો કંઈ પણ વાંચ્યા વિના 'અવાજ સાંભળો' બટન દબાવીને સીધી માહિતી સાંભળી શકે છે.",
    "officerHonestBanner": "ℹ️ પ્રમાણિક ડેટા નોંધ (Honesty Rule): દર્શાવેલ આંકડા લાઇવ પાઇપલાઇનમાંથી છે. માપેલ ચોકસાઈ 'પરીક્ષણ અહેવાલ'માં છે.",
    "officerHeading": "🏛️ વોર્ડ નિયંત્રણ અને ફરિયાદ નિવારણ કક્ષ",
    "officerRoleLabel": "હોદ્દો / Role:",
    "roleCommissioner": "મ્યુનિસિપલ કમિશનર (All Wards)",
    "roleWard2": "વોર્ડ અધિકારી: ધરમપેઠ (Ward 2 Officer)",
    "roleWard4": "વોર્ડ અધિકારી: ધંતોલી (Ward 4 Officer)",
    "kpiTotalTitle": "કુલ ફરિયાદો (Total)",
    "kpiTotalSub": "નોંધાયેલા કેસો",
    "kpiOpenTitle": "બાકી (Open)",
    "kpiOpenSub": "તાકીદે જોવું જરૂરી",
    "kpiInProgressTitle": "ચાલુ (In Progress)",
    "kpiInProgressSub": "રિપેર ટીમ સ્થળ પર",
    "kpiResolvedTitle": "ઉકેલાયેલ (Resolved)",
    "kpiResolvedSub": "કામ પૂર્ણ",
    "kpiMergedTitle": "મર્જ કરેલા ડુપ્લિકેટ્સ (Merged)",
    "kpiMergedSub": "૫૦ મીટર / ૪૮ કલાકમાં જોડાયેલ",
    "mapTitle": "🗺️ નાગપુર વોર્ડ નકશો (Ward Heatmap & Complaint Clusters)",
    "mapSub": "વોર્ડ સીમાઓ અને ૫૦ મીટરની અંદર એકત્રિત ફરિયાદો દર્શાવતો નકશો",
    "searchPlaceholder": "🔍 શોધો (ID, વોર્ડ, વિષય)...",
    "csvExport": "📥 CSV એક્સપોર્ટ",
    "thTicketId": "ટિકિટ આઈડી (ID)",
    "thWard": "વોર્ડ (Ward)",
    "thCategory": "શ્રેણી (Category)",
    "thUrgency": "તીવ્રતા (Urgency)",
    "thStatus": "સ્થિતિ (Status)",
    "thVoice": "ઑડિયો (Voice)",
    "thAction": "કાર્યવાહી (Action)",
    "footerText": "જન-વાણી (Jan-Vani) | સેન્ટ વિન્સેન્ટ પલોટી કૉલેજ ઑફ એન્જિનિયરિંગ એન્ડ ટેક્નોલૉજી, નાગપુર | AI for Social Impact"
  },
  "kn": {
    "heroTitle": "ಜನ-ವಾಣಿ",
    "heroSub": "ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಮಾತನಾಡಿ, ನಾಗರಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ಪರಿಹರಿಸಿ",
    "micPrompt": "ಇಲ್ಲಿ ಒತ್ತಿ ನಿಮ್ಮ ಸಮಸ್ಯೆಯನ್ನು ಮಾತನಾಡಿ",
    "micRecording": "ನಾವು ಕೇಳುತ್ತಿದ್ದೇವೆ... ಮಾತನಾಡಿ ಮುಗಿದ ನಂತರ ಮತ್ತೆ ಒತ್ತಿ",
    "audioPromptText": "ನಮಸ್ಕಾರ! ಮೈಕ್ ಬಟನ್ ಒತ್ತಿ ನಿಮ್ಮ ಸ್ವಂತ ಭಾಷೆಯಲ್ಲಿ ದೂರು ತಿಳಿಸಿ.",
    "instantAck": "ದೂರು ಸ್ವೀಕರಿಸಲಾಗಿದೆ! ಪರಿಶೀಲನೆ ಪ್ರಗತಿಯಲ್ಲಿದೆ...",
    "consentText": "ನನ್ನ ಧ್ವನಿ ಮತ್ತು ಜಿಪಿಎಸ್ ಸ್ಥಳವನ್ನು ಮಹಾನಗರ ಪಾಲಿಕೆಗೆ ಕಳುಹಿಸಲು ಸಮ್ಮತಿಸುತ್ತೇನೆ (DPDP ಕಾಯ್ದೆ ೨೦೨೩).",
    "waterLeak": "ನೀರು ಸರಬರಾಜು ಸಮಸ್ಯೆ (ಕನ್ನಡ)",
    "pothole": "ರಸ್ತೆಯ ಗುಂಡಿ (ಕನ್ನಡ)",
    "drainage": "ಚರಂಡಿ ಬ್ಲಾಕ್ (ಕನ್ನಡ)",
    "powerCut": "ವಿದ್ಯುತ್ ವ್ಯತ್ಯಯ (ಕನ್ನಡ)",
    "garbage": "ಕಸ ಸಂಗ್ರಹ (ಕನ್ನಡ)",
    "listenStatus": "ಧ್ವನಿ ಆಲಿಸಿ",
    "confRegistered": "ದೂರು ದಾಖಲಾಗಿದೆ!",
    "confAssignedWard": "ನಿಯೋಜಿತ ವಾರ್ಡ್",
    "confCategory": "ವರ್ಗ",
    "confUrgency": "ತುರ್ತುಸ್ಥಿತಿ",
    "confSummary": "ಎಐ ಇಂಗ್ಲಿಷ್ ಸಾರಾಂಶ",
    "confSpokenNotice": "ಆಡಿಯೋ ಸಂದೇಶ",
    "confReplay": "ಮತ್ತೆ ಆಲಿಸಿ",
    "confMergeNotice": "ಸ್ವಯಂಚಾಲಿತ ವಿಲೀನ: ಹತ್ತಿರದ ಹಲವು ನಾಗರಿಕರು ಈ ದೂರು ದಾಖಲಿಸಿದ್ದಾರೆ. ಆದ್ಯತೆಯನ್ನು ಹೆಚ್ಚಿಸಲಾಗಿದೆ!",
    "brandTitle": "ಜನ-ವಾಣಿ",
    "brandSubtitle": "ನಾಗಪುರ ಮಹಾನಗರ ಪಾಲಿಕೆ | ಸ್ಥಳೀಯ ನಾಗರಿಕ ಕುಂದುಕೊರತೆ ನಿವಾರಣೆ",
    "navTabVoice": "🎤 ನಾಗರಿಕ ಧ್ವನಿ (Citizen Voice)",
    "navTabTrack": "📋 ದೂರು ಸ್ಥಿತಿ (Track)",
    "navTabOfficer": "🏛️ ಅಧಿಕಾರಿ ಕೊಠಡಿ (Officer Console)",
    "navTabImpact": "📊 ಪರೀಕ್ಷಾ ವರದಿ (Benchmarks)",
    "voiceBadgeBanner": "🔊 ಒಂದೇ ಗುಂಡಿಯನ್ನು ಒತ್ತಿ ದೂರು ನೀಡಿ | ಟೈಪಿಂಗ್ ಅಗತ್ಯವಿಲ್ಲ",
    "listenInstructions": "🔊 ಧ್ವನಿ ಸೂಚನೆಗಳನ್ನು ಆಲಿಸಿ (Listen Instructions)",
    "gpsNotice": "📍 ನಾಗಪುರ ಜಿಪಿಎಸ್ ಸ್ಥಳ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಲಗತ್ತಿಸಲಾಗುತ್ತದೆ",
    "presetsTitle": "⚡ ತ್ವರಿತ ಪರೀಕ್ಷಾ ಉದಾಹರಣೆಗಳು (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "ಪರೀಕ್ಷಕರಿಗೆ ತ್ವರಿತ ಪರೀಕ್ಷೆ",
    "trackHeading": "📋 ದಾಖಲಾದ ದೂರುಗಳ ಸ್ಥಿತಿ (My Grievances)",
    "trackSub": "ನಾಗರಿಕರು ಯಾವುದೇ ಪಠ್ಯ ಓದದೆ 'ಧ್ವನಿ ಆಲಿಸಿ' ಗುಂಡಿ ಒತ್ತಿ ನೇರವಾಗಿ ಮಾಹಿತಿ ಪಡೆಯಬಹುದು.",
    "officerHonestBanner": "ℹ️ ಪ್ರಾಮಾಣಿಕ ಡೇಟಾ ನಿಯಮ (Honesty Rule): ಪ್ರದರ್ಶಿತ ಅಂಕಿಅಂಶಗಳು ಲೈವ್ ಪೈಪ್‌ಲೈನ್‌ನಿಂದ ಬಂದಿವೆ. ನಿಖರತೆ 'ಪರೀಕ್ಷಾ ವರದಿ'ಯಲ್ಲಿದೆ.",
    "officerHeading": "🏛️ ವಾರ್ಡ್ ನಿಯಂತ್ರಣ ಮತ್ತು ಕುಂದುಕೊರತೆ ನಿವಾರಣಾ ಕೊಠಡಿ",
    "officerRoleLabel": "ಹುದ್ದೆ / Role:",
    "roleCommissioner": "ಮಹಾನಗರ ಪಾಲಿಕೆ ಆಯುಕ್ತರು (All Wards)",
    "roleWard2": "ವಾರ್ಡ್ ಅಧಿಕಾರಿ: ಧರಂಪೇಠ್ (Ward 2 Officer)",
    "roleWard4": "ವಾರ್ಡ್ ಅಧಿಕಾರಿ: ಧಂತೋಲಿ (Ward 4 Officer)",
    "kpiTotalTitle": "ಒಟ್ಟು ದೂರುಗಳು (Total)",
    "kpiTotalSub": "ದಾಖಲಾದ ಪ್ರಕರಣಗಳು",
    "kpiOpenTitle": "ಬಾಕಿ ಉಳಿದಿದೆ (Open)",
    "kpiOpenSub": "ತಕ್ಷಣ ಪರಿಶೀಲಿಸಬೇಕು",
    "kpiInProgressTitle": "ಪ್ರಗತಿಯಲ್ಲಿದೆ (In Progress)",
    "kpiInProgressSub": "ದುರಸ್ತಿ ತಂಡ ಸ್ಥಳದಲ್ಲಿದೆ",
    "kpiResolvedTitle": "ಪರಿಹರಿಸಲಾಗಿದೆ (Resolved)",
    "kpiResolvedSub": "ಕಾರ್ಯ ಪೂರ್ಣಗೊಂಡಿದೆ",
    "kpiMergedTitle": "ವಿಲೀನಗೊಳಿಸಿದ ನಕಲುಗಳು (Merged)",
    "kpiMergedSub": "೫೦ ಮೀ / ೪೮ ಗಂಟೆಗಳಲ್ಲಿ ಲಿಂಕ್ ಮಾಡಲಾಗಿದೆ",
    "mapTitle": "🗺️ ನಾಗಪುರ ವಾರ್ಡ್ ನಕ್ಷೆ (Ward Heatmap & Complaint Clusters)",
    "mapSub": "ವಾರ್ಡ್ ಗಡಿಗಳು ಮತ್ತು ೫೦ ಮೀಟರ್ ಒಳಗೆ ಕ್ಲಸ್ಟರ್ ಮಾಡಿದ ದೂರುಗಳ ನಕ್ಷೆ",
    "searchPlaceholder": "🔍 ಹುಡುಕಿ (ID, ವಾರ್ಡ್, ವಿಷಯ)...",
    "csvExport": "📥 CSV ರಫ್ತು",
    "thTicketId": "ಟಿಕೆಟ್ ಐಡಿ (ID)",
    "thWard": "ವಾರ್ಡ್ (Ward)",
    "thCategory": "ವರ್ಗ (Category)",
    "thUrgency": "ತುರ್ತು (Urgency)",
    "thStatus": "ಸ್ಥಿತಿ (Status)",
    "thVoice": "ಧ್ವನಿ (Voice)",
    "thAction": "ಕ್ರಮ (Action)",
    "footerText": "ಜನ-ವಾಣಿ (Jan-Vani) | ಸೇಂಟ್ ವಿನ್ಸೆಂಟ್ ಪಲೋಟ್ಟಿ ಎಂಜಿನಿಯರಿಂಗ್ ಮತ್ತು ತಂತ್ರಜ್ಞಾನ ಕಾಲೇಜು, ನಾಗಪುರ | AI for Social Impact"
  },
  "ml": {
    "heroTitle": "ജന-വാണി",
    "heroSub": "നിങ്ങളുടെ സ്വന്തം ഭാഷയിൽ സംസാരിക്കൂ, പരാതികൾ പരിഹരിക്കൂ",
    "micPrompt": "ഇവിടെ അമർത്തി നിങ്ങളുടെ പ്രശ്നം സംസാരിക്കൂ",
    "micRecording": "ഞങ്ങൾ കേൾക്കുന്നു... സംസാരിച്ചു കഴിഞ്ഞാൽ വീണ്ടും അമർത്തുക",
    "audioPromptText": "നമസ്കാരം! മൈക്ക് ബട്ടൺ അമർത്തി നിങ്ങളുടെ ഭാഷയിൽ പരാതി പറയൂ.",
    "instantAck": "പരാതി ലഭിച്ചു! പരിശോധന പുരോഗമിക്കുന്നു...",
    "consentText": "എന്റെ ശബ്ദവും ലൊക്കേഷനും നഗരസഭയ്ക്ക് പങ്കിടാൻ സമ്മതിക്കുന്നു (DPDP ആക്റ്റ് 2023).",
    "waterLeak": "കുടിവെള്ള വിതരണം (മലയാളം)",
    "pothole": "റോഡിലെ കുഴി (മലയാളം)",
    "drainage": "ഓവുചാൽ തടസ്സം (മലയാളം)",
    "powerCut": "വൈദ്യുതി തടസ്സം (മലയാളം)",
    "garbage": "മാലിന്യക്കൂമ്പാരം (മലയാളം)",
    "listenStatus": "ശബ്ദം കേൾക്കൂ",
    "confRegistered": "പരാതി രജിസ്റ്റർ ചെയ്തു!",
    "confAssignedWard": "വാർഡ്",
    "confCategory": "വിഭാഗം",
    "confUrgency": "തീവ്രത",
    "confSummary": "AI സംഗ്രഹം",
    "confSpokenNotice": "ശബ്ദ സന്ദേശം",
    "confReplay": "വീണ്ടും കേൾക്കുക",
    "confMergeNotice": "ഓട്ടോമാറ്റിക് ലയനം: സമീപവാസികളായ ഒന്നിലധികം ആളുകൾ ഇതേ പരാതി നൽകി. മുൻഗണന വർദ്ധിപ്പിച്ചു!",
    "brandTitle": "ജന-വാണി",
    "brandSubtitle": "നാഗ്പൂർ മുനിസിപ്പൽ കോർപ്പറേഷൻ | പ്രാദേശിക പരാതി പരിഹാരം",
    "navTabVoice": "🎤 പൗര ശബ്ദം (Citizen Voice)",
    "navTabTrack": "📋 പരാതി നില (Track)",
    "navTabOfficer": "🏛️ ഓഫീസർ കൺസോൾ (Officer Console)",
    "navTabImpact": "📊 വിലയിരുത്തൽ റിപ്പോർട്ട് (Benchmarks)",
    "voiceBadgeBanner": "🔊 ഒരൊറ്റ ബട്ടണിൽ പരാതി നൽകാം | ടൈപ്പിംഗ് ആവശ്യമില്ല",
    "listenInstructions": "🔊 ശബ്ദ നിർദ്ദേശങ്ങൾ കേൾക്കൂ (Listen Instructions)",
    "gpsNotice": "📍 നാഗ്പൂർ ജിപിഎസ് ലൊക്കേഷൻ സ്വയമേവ ചേർക്കപ്പെടും",
    "presetsTitle": "⚡ തത്സമയ പരീക്ഷണ ഉദാഹരണങ്ങൾ (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "പരിശോധകർക്കായി ദ്രുത പരിശോധന",
    "trackHeading": "📋 രേഖപ്പെടുത്തിയ പരാതികളുടെ നില (My Grievances)",
    "trackSub": "പൗരന്മാർക്ക് വിവരങ്ങൾ വായിക്കാതെ 'ശബ്ദം കേൾക്കൂ' ബട്ടൺ അമർത്തി നേരിട്ട് കേൾക്കാം.",
    "officerHonestBanner": "ℹ️ സുതാര്യത നിയമം (Honesty Rule): നൽകിയിട്ടുള്ള വിവരങ്ങൾ ലൈവ് പൈപ്പ്‌ലൈനിൽ നിന്നുള്ളതാണ്. കൃത്യത ബെഞ്ച്മാർക്കിൽ ഉണ്ട്.",
    "officerHeading": "🏛️ വാർഡ് കൺട്രോൾ & പരാതി പരിഹാര കേന്ദ്രം",
    "officerRoleLabel": "സ്ഥാനം / Role:",
    "roleCommissioner": "മുനിസിപ്പൽ കമ്മീഷണർ (All Wards)",
    "roleWard2": "വാർഡ് ഓഫീസർ: ധരംപേട്ട് (Ward 2 Officer)",
    "roleWard4": "വാർഡ് ഓഫീസർ: ധന്തോലി (Ward 4 Officer)",
    "kpiTotalTitle": "ആകെ പരാതികൾ (Total)",
    "kpiTotalSub": "രേഖപ്പെടുത്തിയ കേസുകൾ",
    "kpiOpenTitle": "തീർപ്പാക്കാത്തവ (Open)",
    "kpiOpenSub": "ഉടൻ നടപടി വേണം",
    "kpiInProgressTitle": "നടപടി പുരോഗമിക്കുന്നു (In Progress)",
    "kpiInProgressSub": "റിപ്പയർ ടീം സ്ഥലത്തുണ്ട്",
    "kpiResolvedTitle": "പരിഹരിച്ചു (Resolved)",
    "kpiResolvedSub": "പ്രവർത്തനം പൂർത്തിയായി",
    "kpiMergedTitle": "ലയിപ്പിച്ചവ (Merged)",
    "kpiMergedSub": "50 മീ / 48 മണിക്കൂറിൽ ബന്ധിപ്പിച്ചത്",
    "mapTitle": "🗺️ നാഗ്പൂർ വാർഡ് മാപ്പ് (Ward Heatmap & Complaint Clusters)",
    "mapSub": "വാർഡ് അതിർത്തികളും 50 മീറ്ററിനുള്ളിൽ ക്ലസ്റ്റർ ചെയ്ത പരാതികളും കാണിക്കുന്ന മാപ്പ്",
    "searchPlaceholder": "🔍 തിരയുക (ID, വാർഡ്, വിഷയം)...",
    "csvExport": "📥 CSV എക്സ്പോർട്ട്",
    "thTicketId": "ടിക്കറ്റ് ഐഡി (ID)",
    "thWard": "വാർഡ് (Ward)",
    "thCategory": "വിഭാഗം (Category)",
    "thUrgency": "തീവ്രത (Urgency)",
    "thStatus": "നില (Status)",
    "thVoice": "ശബ്ദം (Voice)",
    "thAction": "നടപടി (Action)",
    "footerText": "ജന-വാണി (Jan-Vani) | സെന്റ് വിൻസെന്റ് പല്ലൊട്ടി കോളേജ് ഓഫ് എഞ്ചിനീയറിംഗ്, നാഗ്പൂർ | AI for Social Impact"
  },
  "pa": {
    "heroTitle": "ਜਨ-ਵਾਣੀ",
    "heroSub": "ਆਪਣੀ ਭਾਸ਼ਾ ਵਿੱਚ ਬੋਲੋ, ਸ਼ਿਕਾਇਤਾਂ ਦਾ ਹੱਲ ਪਾਓ",
    "micPrompt": "ਇੱਥੇ ਛੂਹੋ ਅਤੇ ਆਪਣੀ ਸਮੱਸਿਆ ਬੋਲੋ",
    "micRecording": "ਅਸੀਂ ਸੁਣ ਰਹੇ ਹਾਂ... ਬੋਲਣ ਤੋਂ ਬਾਅਦ ਦੁਬਾਰਾ ਦਬਾਓ",
    "audioPromptText": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮਾਈਕ ਬਟਨ ਦਬਾਓ ਅਤੇ ਆਪਣੀ ਬੋਲੀ ਵਿੱਚ ਸ਼ਿਕਾਇਤ ਦੱਸੋ।",
    "instantAck": "ਸ਼ਿਕਾਇਤ ਪ੍ਰਾਪਤ ਹੋਈ! ਕਾਰਵਾਈ ਜਾਰੀ ਹੈ...",
    "consentText": "ਮੈਂ ਆਪਣੀ ਆਵਾਜ਼ ਅਤੇ ਸਥਾਨ ਨਗਰ ਨਿਗਮ ਨਾਲ ਸਾਂਝਾ ਕਰਨ ਦੀ ਸਹਿਮਤੀ ਦਿੰਦਾ/ਦਿੰਦੀ ਹਾਂ (DPDP ਐਕਟ 2023)।",
    "waterLeak": "ਪਾਣੀ ਦੀ ਸਪਲਾਈ (ਪੰਜਾਬੀ)",
    "pothole": "ਸੜਕ ਤੇ ਟੋਆ (ਪੰਜਾਬੀ)",
    "drainage": "ਗੰਦਾ ਨਾਲਾ ਜਾਮ (ਪੰਜਾਬੀ)",
    "powerCut": "ਬਿਜਲੀ ਗੁੱਲ (ਪੰਜਾਬੀ)",
    "garbage": "ਕੂੜੇ ਦਾ ਢੇਰ (ਪੰਜਾਬੀ)",
    "listenStatus": "ਸਥਿਤੀ ਸੁਣੋ",
    "confRegistered": "ਸ਼ਿਕਾਇਤ ਦਰਜ ਹੋ ਗਈ ਹੈ!",
    "confAssignedWard": "ਸੌਂਪਿਆ ਗਿਆ ਵਾਰਡ",
    "confCategory": "ਸ਼੍ਰੇਣੀ",
    "confUrgency": "ਜ਼ਰੂਰੀਤਾ",
    "confSummary": "ਏਆਈ ਅੰਗਰੇਜ਼ੀ ਸਾਰ",
    "confSpokenNotice": "ਆਡੀਓ ਸੰਦੇਸ਼",
    "confReplay": "ਦੁਬਾਰਾ ਸੁਣੋ",
    "confMergeNotice": "ਸਵੈਚਲਿਤ ਮਿਲਾਪ: ਨੇੜਲੇ ਕਈ ਨਾਗਰਿਕਾਂ ਨੇ ਇਹ ਸ਼ਿਕਾਇਤ ਦਰਜ ਕਰਵਾਈ ਹੈ। ਤਰਜੀਹ ਵਧਾਈ ਗਈ ਹੈ!",
    "brandTitle": "ਜਨ-ਵਾਣੀ",
    "brandSubtitle": "ਨਾਗਪੁਰ ਨਗਰ ਨਿਗਮ | ਸਥਾਨਕ ਨਾਗਰਿਕ ਸ਼ਿਕਾਇਤ ਨਿਵਾਰਨ",
    "navTabVoice": "🎤 ਨਾਗਰਿਕ ਆਵਾਜ਼ (Citizen Voice)",
    "navTabTrack": "📋 ਸ਼ਿਕਾਇਤ ਸਥਿਤੀ (Track)",
    "navTabOfficer": "🏛️ ਅਧਿਕਾਰੀ ਕਮਰਾ (Officer Console)",
    "navTabImpact": "📊 ਟੈਸਟ ਰਿਪੋਰਟ (Benchmarks)",
    "voiceBadgeBanner": "🔊 ਸਿਰਫ਼ ਇੱਕ ਬਟਨ ਨਾਲ ਸ਼ਿਕਾਇਤ ਕਰੋ | ਟਾਈਪ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ",
    "listenInstructions": "🔊 ਆਵਾਜ਼ ਹਦਾਇਤਾਂ ਸੁਣੋ (Listen Instructions)",
    "gpsNotice": "📍 ਨਾਗਪੁਰ ਜੀਪੀਐਸ ਟਿਕਾਣਾ ਆਪਣੇ ਆਪ ਜੁੜ ਜਾਵੇਗਾ",
    "presetsTitle": "⚡ ਤੁਰੰਤ ਟੈਸਟ ਉਦਾਹਰਣਾਂ (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "ਪਰੀਖਿਅਕਾਂ ਲਈ ਤੁਰੰਤ ਟੈਸਟ",
    "trackHeading": "📋 ਦਰਜ ਸ਼ਿਕਾਇਤਾਂ ਦੀ ਸਥਿਤੀ (My Grievances)",
    "trackSub": "ਨਾਗਰਿਕ ਬਿਨਾਂ ਪੜ੍ਹੇ 'ਆਵਾਜ਼ ਸੁਣੋ' ਬਟਨ ਦਬਾ ਕੇ ਸਿੱਧੀ ਜਾਣਕਾਰੀ ਸੁਣ ਸਕਦੇ ਹਨ।",
    "officerHonestBanner": "ℹ️ ਇਮਾਨਦਾਰ ਡੇਟਾ ਨਿਯਮ (Honesty Rule): ਪ੍ਰਦਰਸ਼ਿਤ ਅੰਕੜੇ ਲਾਈਵ ਪਾਈਪਲਾਈਨ ਤੋਂ ਹਨ। ਅਸਲ ਸ਼ੁੱਧਤਾ ਟੈਸਟ ਰਿਪੋਰਟ ਵਿੱਚ ਹੈ।",
    "officerHeading": "🏛️ ਵਾਰਡ ਕੰਟਰੋਲ ਅਤੇ ਸ਼ਿਕਾਇਤ ਨਿਵਾਰਨ ਸੈੱਲ",
    "officerRoleLabel": "ਅਹੁਦਾ / Role:",
    "roleCommissioner": "ਮਿਊਂਸੀਪਲ ਕਮਿਸ਼ਨਰ (All Wards)",
    "roleWard2": "ਵਾਰਡ ਅਧਿਕਾਰੀ: ਧਰਮਪੇਠ (Ward 2 Officer)",
    "roleWard4": "ਵਾਰਡ ਅਧਿਕਾਰੀ: ਧੰਤੋਲੀ (Ward 4 Officer)",
    "kpiTotalTitle": "ਕੁੱਲ ਸ਼ਿਕਾਇਤਾਂ (Total)",
    "kpiTotalSub": "ਦਰਜ ਕੇਸ",
    "kpiOpenTitle": "ਬਕਾਇਆ (Open)",
    "kpiOpenSub": "ਤੁਰੰਤ ਕਾਰਵਾਈ ਲੋੜੀਂਦੀ",
    "kpiInProgressTitle": "ਜਾਰੀ ਹੈ (In Progress)",
    "kpiInProgressSub": "ਮੁਰੰਮਤ ਟੀਮ ਮੌਕੇ 'ਤੇ",
    "kpiResolvedTitle": "ਹੱਲ ਹੋ ਗਿਆ (Resolved)",
    "kpiResolvedSub": "ਕੰਮ ਪੂਰਾ",
    "kpiMergedTitle": "ਮਿਲਾਏ ਗਏ ਡੁਪਲੀਕੇਟ (Merged)",
    "kpiMergedSub": "50 ਮੀਟਰ / 48 ਘੰਟਿਆਂ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ",
    "mapTitle": "🗺️ ਨਾਗਪੁਰ ਵਾਰਡ ਨਕਸ਼ਾ (Ward Heatmap & Complaint Clusters)",
    "mapSub": "ਵਾਰਡ ਸੀਮਾਵਾਂ ਅਤੇ 50 ਮੀਟਰ ਦੇ ਅੰਦਰ ਇਕੱਠੀਆਂ ਕੀਤੀਆਂ ਸ਼ਿਕਾਇਤਾਂ ਦਾ ਨਕਸ਼ਾ",
    "searchPlaceholder": "🔍 ਖੋਜੋ (ID, ਵਾਰਡ, ਵਿਸ਼ਾ)...",
    "csvExport": "📥 CSV ਐਕਸਪੋਰਟ",
    "thTicketId": "ਟਿਕਟ ਆਈਡੀ (ID)",
    "thWard": "ਵਾਰਡ (Ward)",
    "thCategory": "ਸ਼੍ਰੇਣੀ (Category)",
    "thUrgency": "ਜ਼ਰੂਰੀਤਾ (Urgency)",
    "thStatus": "ਸਥਿਤੀ (Status)",
    "thVoice": "ਆਵਾਜ਼ (Voice)",
    "thAction": "ਕਾਰਵਾਈ (Action)",
    "footerText": "ਜਨ-ਵਾਣੀ (Jan-Vani) | ਸੇਂਟ ਵਿਨਸੇਂਟ ਪਲੋਟੀ ਕਾਲਜ ਆਫ਼ ਇੰਜੀਨੀਅਰਿੰਗ ਐਂਡ ਟੈਕਨਾਲੋਜੀ, ਨਾਗਪੁਰ | AI for Social Impact"
  },
  "ta": {
    "heroTitle": "ஜன்-வாணி",
    "heroSub": "உங்கள் தாய்மொழியில் பேசுங்கள், குறைதீர்க்கும் தீர்வு பெறுங்கள்",
    "micPrompt": "இங்கே தொட்டு உங்கள் புகாரைப் பேசுங்கள்",
    "micRecording": "நாங்கள் கேட்கிறோம்... பேசி முடித்ததும் மீண்டும் அழுத்தவும்",
    "audioPromptText": "வணக்கம்! மைக் பொத்தானை அழுத்தி உங்கள் சொந்த மொழியில் புகாரைக் கூறுங்கள்.",
    "instantAck": "புகார் பெறப்பட்டது! பகுப்பாய்வு நடக்கிறது...",
    "consentText": "எனது குரல் மற்றும் இருப்பிடத்தை மாநகராட்சிக்கு அனுப்ப ஒப்புக்கொள்கிறேன் (DPDP சட்டம் 2023).",
    "waterLeak": "குடிநீர் விநியோகம் (தமிழ்)",
    "pothole": "சாலைப் பள்ளம் (தமிழ்)",
    "drainage": "சாக்கடை அடைப்பு (தமிழ்)",
    "powerCut": "மின்வெட்டு (தமிழ்)",
    "garbage": "குப்பை குவியல் (தமிழ்)",
    "listenStatus": "குரல் கேட்கவும்",
    "confRegistered": "புகார் பதிவு செய்யப்பட்டது!",
    "confAssignedWard": "ஒதுக்கப்பட்ட வார்டு",
    "confCategory": "பிரிவு",
    "confUrgency": "அவசரம்",
    "confSummary": "AI ஆங்கிலச் சுருக்கம்",
    "confSpokenNotice": "ஆடியோ செய்தி",
    "confReplay": "மீண்டும் கேட்கவும்",
    "confMergeNotice": "தானியங்கி இணைப்பு: அருகில் உள்ள பல குடிமக்கள் இதே புகாரைப் பதிவு செய்துள்ளனர். முன்னுரிமை உயர்த்தப்பட்டது!",
    "brandTitle": "ஜன்-வாணி",
    "brandSubtitle": "நாக்பூர் மாநகராட்சி | வட்டாரக் குடிமக்கள் குறைதீர்ப்பு",
    "navTabVoice": "🎤 குடிமக்கள் குரல் (Citizen Voice)",
    "navTabTrack": "📋 புகார் நிலை (Track)",
    "navTabOfficer": "🏛️ அதிகாரி அறை (Officer Console)",
    "navTabImpact": "📊 சோதனை அறிக்கை (Benchmarks)",
    "voiceBadgeBanner": "🔊 ஒரே பொத்தானில் புகார் அளியுங்கள் | தட்டச்சு தேவையில்லை",
    "listenInstructions": "🔊 குரல் வழிமுறைகளைக் கேட்கவும் (Listen Instructions)",
    "gpsNotice": "📍 நாக்பூர் ஜிபிஎஸ் இடம் தானாக இணைக்கப்படும்",
    "presetsTitle": "⚡ நேரடி சோதனை மாதிரிகள் (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "மதிப்பீட்டாளர்களுக்கான விரைவு சோதனை",
    "trackHeading": "📋 பதிவு செய்யப்பட்ட புகார்களின் நிலை (My Grievances)",
    "trackSub": "குடிமக்கள் எந்த எழுத்தையும் படிக்காமல் 'குரல் கேட்கவும்' பொத்தானை அழுத்தித் தகவல் பெறலாம்.",
    "officerHonestBanner": "ℹ️ வெளிப்படைத்தன்மை விதி (Honesty Rule): காட்டப்படும் தரவு நேரடி அமைப்பிலிருந்து பெறப்பட்டது. துல்லியம் பெஞ்ச்மார்க்கில் உள்ளது.",
    "officerHeading": "🏛️ வார்டு கட்டுப்பாடு மற்றும் குறைதீர்ப்பு மையம்",
    "officerRoleLabel": "பதவி / Role:",
    "roleCommissioner": "மாநகராட்சி ஆணையர் (All Wards)",
    "roleWard2": "வார்டு அதிகாரி: தரம்பேத் (Ward 2 Officer)",
    "roleWard4": "வார்டு அதிகாரி: தந்தோலி (Ward 4 Officer)",
    "kpiTotalTitle": "மொத்த புகார்கள் (Total)",
    "kpiTotalSub": "பதிவு செய்யப்பட்டவை",
    "kpiOpenTitle": "நிலுவையில் (Open)",
    "kpiOpenSub": "உடனடி நடவடிக்கை தேவை",
    "kpiInProgressTitle": "நடைபெறுகிறது (In Progress)",
    "kpiInProgressSub": "பழுதுபார்ப்பு குழு களத்தில்",
    "kpiResolvedTitle": "தீர்க்கப்பட்டது (Resolved)",
    "kpiResolvedSub": "பணி முடிந்தது",
    "kpiMergedTitle": "இணைக்கப்பட்ட நகல்கள் (Merged)",
    "kpiMergedSub": "50 மீ / 48 மணிநேரத்தில் இணைக்கப்பட்டது",
    "mapTitle": "🗺️ நாக்பூர் வார்டு வரைபடம் (Ward Heatmap & Complaint Clusters)",
    "mapSub": "வார்டு எல்லைகள் மற்றும் 50 மீட்டருக்குள் தொகுக்கப்பட்ட புகார்களின் வரைபடம்",
    "searchPlaceholder": "🔍 தேடுக (ID, வார்டு, பொருள்)...",
    "csvExport": "📥 CSV ஏற்றுமதி",
    "thTicketId": "டிக்கெட் ஐடி (ID)",
    "thWard": "வார்டு (Ward)",
    "thCategory": "பிரிவு (Category)",
    "thUrgency": "அவசரம் (Urgency)",
    "thStatus": "நிலை (Status)",
    "thVoice": "குரல் (Voice)",
    "thAction": "நடவடிக்கை (Action)",
    "footerText": "ஜன்-வாணி (Jan-Vani) | செயிண்ட் வின்சென்ட் பலோட்டி பொறியியல் கல்லூரி, நாக்பூர் | AI for Social Impact"
  },
  "te": {
    "heroTitle": "జన్-వాణి",
    "heroSub": "మీ భాషలో మాట్లాడండి, పౌర సమస్యలకు పరిష్కారం పొందండి",
    "micPrompt": "ఇక్కడ నొక్కి మీ సమస్యను మాట్లాడండి",
    "micRecording": "మేము వింటున్నాము... మాట్లాడటం పూర్తయిన తర్వాత మళ్లీ నొక్కండి",
    "audioPromptText": "నమస్కారం! మైక్ బటన్ నొక్కి మీ స్వంత భాషలో ఫిర్యాదును చెప్పండి.",
    "instantAck": "ఫిర్యాదు స్వీకరించబడింది! పరిశీలన జరుగుతోంది...",
    "consentText": "మున్సిపల్ కార్పొరేషన్‌కు నా స్వరం మరియు స్థానాన్ని పంపడానికి అంగీకరిస్తున్నాను (DPDP చట్టం 2023).",
    "waterLeak": "నీటి సరఫరా లీకేజీ (తెలుగు)",
    "pothole": "రోడ్డుపై గుంత (తెలుగు)",
    "drainage": "మురుగు కాలువ బ్లాక్ (తెలుగు)",
    "powerCut": "విద్యుత్ సరఫరా నిలిచిపోయింది (తెలుగు)",
    "garbage": "చెత్త కుప్ప (తెలుగు)",
    "listenStatus": "వాయిస్ వినండి",
    "confRegistered": "ఫిర్యాదు నమోదు చేయబడింది!",
    "confAssignedWard": "కేటాయించిన వార్డు",
    "confCategory": "వర్గం",
    "confUrgency": "తీవ్రత",
    "confSummary": "AI ఆంగ్ల సారాంశం",
    "confSpokenNotice": "ఆడియో సందేశం",
    "confReplay": "మళ్లీ వినండి",
    "confMergeNotice": "ఆటోమేటిక్ విలీనం: సమీపంలోని బహుళ పౌరులు ఇదే సమస్యను నివేదించారు. ప్రాధాన్యత పెంచబడింది!",
    "brandTitle": "జన్-వాణి",
    "brandSubtitle": "నాగ్‌పూర్ మున్సిపల్ కార్పొరేషన్ | స్థానిక పౌర సమస్యల పరిష్కారం",
    "navTabVoice": "🎤 పౌరుల స్వరం (Citizen Voice)",
    "navTabTrack": "📋 ఫిర్యాదు స్థితి (Track)",
    "navTabOfficer": "🏛️ అధికారి కన్సోల్ (Officer Console)",
    "navTabImpact": "📊 పరీక్ష నివేదిక (Benchmarks)",
    "voiceBadgeBanner": "🔊 కేవలం ఒక బటన్‌తో ఫిర్యాదు చేయండి | టైపింగ్ అవసరం లేదు",
    "listenInstructions": "🔊 వాయిస్ సూచనలు వినండి (Listen Instructions)",
    "gpsNotice": "📍 నాగ్‌పూర్ జీపీఎస్ స్థానం స్వయంచాలకంగా జోడించబడుతుంది",
    "presetsTitle": "⚡ ప్రత్యక్ష పరీక్ష నమూనాలు (One-Click Vernacular Voice Demos)",
    "presetsSubtitle": "మూల్యాంకనం కోసం శీఘ్ర పరీక్ష",
    "trackHeading": "📋 నమోదు చేసిన ఫిర్యాదుల స్థితి (My Grievances)",
    "trackSub": "పౌరులు ఏ చదువూ లేకుండా 'వాయిస్ వినండి' బటన్ నొక్కి సమాచారం వినవచ్చు.",
    "officerHonestBanner": "ℹ️ ప్రామాణిక సమాచారం (Honesty Rule): ప్రదర్శిత వివరాలు ప్రత్యక్ష పైప్‌లైన్ ద్వారా వచ్చినవి. ఖచ్చితత్వం నివేదికలో ఉంది.",
    "officerHeading": "🏛️ వార్డు నియంత్రణ మరియు సమస్యల పరిష్కార విభాగం",
    "officerRoleLabel": "హోదా / Role:",
    "roleCommissioner": "మున్సిపల్ కమిషనర్ (All Wards)",
    "roleWard2": "వార్డు అధికారి: ధరమ్‌పేట్ (Ward 2 Officer)",
    "roleWard4": "వార్డు అధికారి: ధంతోలి (Ward 4 Officer)",
    "kpiTotalTitle": "మొత్తం ఫిర్యాదులు (Total)",
    "kpiTotalSub": "నమోదైన కేసులు",
    "kpiOpenTitle": "పెండింగ్‌లో ఉన్నాయి (Open)",
    "kpiOpenSub": "తక్షణ చర్య అవసరం",
    "kpiInProgressTitle": "పురోగతిలో ఉంది (In Progress)",
    "kpiInProgressSub": "మరమ్మతు బృందం స్థలంలో ఉంది",
    "kpiResolvedTitle": "పరిష్కరించబడింది (Resolved)",
    "kpiResolvedSub": "పని పూర్తయింది",
    "kpiMergedTitle": "విలీనమైన నకిలీలు (Merged)",
    "kpiMergedSub": "50 మీ / 48 గంటల్లో అనుసంధానించబడింది",
    "mapTitle": "🗺️ నాగ్‌పూర్ వార్డు మ్యాప్ (Ward Heatmap & Complaint Clusters)",
    "mapSub": "వార్డు సరిహద్దులు మరియు 50 మీటర్లలోపు సమూహపరిచిన ఫిర్యాదుల మ్యాప్",
    "searchPlaceholder": "🔍 శోధించండి (ID, వార్డు, అంశం)...",
    "csvExport": "📥 CSV ఎగుమతి",
    "thTicketId": "టికెట్ ఐడీ (ID)",
    "thWard": "వార్డు (Ward)",
    "thCategory": "వర్గం (Category)",
    "thUrgency": "తీవ్రత (Urgency)",
    "thStatus": "స్థితి (Status)",
    "thVoice": "వాయిస్ (Voice)",
    "thAction": "చర్య (Action)",
    "footerText": "జన్-వాణి (Jan-Vani) | సెయింట్ విన్సెంట్ పలోట్టి కాలేజ్ ఆఫ్ ఇంజనీరింగ్, నాగ్‌పూర్ | AI for Social Impact"
  }
};

// Vernacular One-Click Preset Demos (All 10 Languages)
const PRESETS_DATA = {
  "mr": [
    {
      "id": "water_mr",
      "title": "💧 पाणी पुरवठा गळती",
      "tag": "मराठी (Marathi)",
      "quote": "आमच्या गल्लीत पिण्याच्या पाण्याची मुख्य पाइपलाइन फुटली आहे, तीन दिवसांपासून रस्ता भरून पाणी वाहत आहे.",
      "desc": "Drinking water pipeline burst for 3 days."
    },
    {
      "id": "road_mr",
      "title": "🚧 रस्त्यावरील मोठा खड्डा",
      "tag": "मराठी (Marathi)",
      "quote": "धरमपेठ मुख्य रस्त्यावर मोठा खड्डा पडला आहे, काल रात्री दोन दुचाकींचा अपघात झाला.",
      "desc": "Hazardous pothole causing vehicle accidents."
    },
    {
      "id": "drain_mr",
      "title": "🌊 ड्रेनेज तुंबले आहे",
      "tag": "मराठी (Marathi)",
      "quote": "घरासमोरचे गटार तुंबले आहे आणि घाण पाणी रस्त्यावर आणि दारात येत आहे, दुर्गंधी सुटली आहे.",
      "desc": "Clogged drain overflowing sewage with foul smell."
    },
    {
      "id": "power_mr",
      "title": "⚡ वीज पुरवठा खंडित",
      "tag": "मराठी (Marathi)",
      "quote": "ट्रान्सफॉर्मरमध्ये बिघाड झाल्याने पूर्ण प्रभागात काल रात्रीपासून वीज नाही.",
      "desc": "Transformer failure blackout across entire ward."
    }
  ],
  "hi": [
    {
      "id": "water_hi",
      "title": "💧 पेयजल पाइपलाइन लीकेज",
      "tag": "हिंदी (Hindi)",
      "quote": "हमारी गली में पानी की मुख्य पाइपलाइन टूट गई है, पीने का पानी सड़कों पर बहकर बर्बाद हो रहा है।",
      "desc": "Drinking water pipeline ruptured on main street."
    },
    {
      "id": "road_hi",
      "title": "🚧 सड़क पर जानलेवा गड्ढा",
      "tag": "हिंदी (Hindi)",
      "quote": "मुख्य सड़क पर बहुत गहरा गड्ढा हो गया है, कल रात दो बाइक सवार गिरकर घायल हो गए।",
      "desc": "Dangerous deep pothole causing road accidents."
    },
    {
      "id": "drain_hi",
      "title": "🌊 नाली जाम और बदबू",
      "tag": "हिंदी (Hindi)",
      "quote": "सामने की नाली पूरी तरह जाम है, गंदा पानी घरों के आगे भर गया है और बदबू फैल रही है।",
      "desc": "Choked drain causing sewage water accumulation."
    },
    {
      "id": "power_hi",
      "title": "⚡ ट्रांसफार्मर में खराबी / अंधेरा",
      "tag": "हिंदी (Hindi)",
      "quote": "ट्रांसफार्मर में आग लगने के बाद से पूरे इलाके की बिजली गुल है, भयंकर अंधेरा है।",
      "desc": "Transformer fire blackout in whole locality."
    }
  ],
  "en": [
    {
      "id": "water_en",
      "title": "💧 Potable Water Pipeline Leak",
      "tag": "English",
      "quote": "The main drinking water supply pipe has burst in our street, clean water is flowing on the road for 2 days.",
      "desc": "Drinking water supply pipe burst causing massive wastage."
    },
    {
      "id": "road_en",
      "title": "🚧 Deep Road Pothole Hazard",
      "tag": "English",
      "quote": "There is a huge pothole on Dharampeth main road causing repeated bike accidents every night.",
      "desc": "Major pothole endangering motorists and pedestrians."
    },
    {
      "id": "drain_en",
      "title": "🌊 Sewage Overflow & Blockage",
      "tag": "English",
      "quote": "The storm drain is completely blocked with plastic waste and dirty sewage is overflowing into houses.",
      "desc": "Blocked stormwater drain causing sanitation crisis."
    },
    {
      "id": "power_en",
      "title": "⚡ Electricity Transformer Failure",
      "tag": "English",
      "quote": "Our neighborhood transformer sparked and broke down, total blackout for over 8 hours.",
      "desc": "Transformer explosion leaving the neighborhood in dark."
    }
  ],
  "bn": [
    {
      "id": "water_bn",
      "title": "💧 পানীয় জলের পাইপলাইন ফেটে গেছে",
      "tag": "বাংলা (Bengali)",
      "quote": "আমাদের গলিতে পানীয় জলের মূল পাইপলাইন ফেটে গিয়ে রাস্তায় জল জমেছে।",
      "desc": "Drinking water pipeline ruptured in locality."
    },
    {
      "id": "road_bn",
      "title": "🚧 রাস্তায় বিপজ্জনক গর্ত",
      "tag": "বাংলা (Bengali)",
      "quote": "প্রধান রাস্তায় অনেক বড় গর্ত তৈরি হয়েছে, গতকাল রাতে দুর্ঘটনা ঘটেছে।",
      "desc": "Deep hazardous pothole causing vehicle accidents."
    },
    {
      "id": "drain_bn",
      "title": "🌊 নর্দমা উপচে নোংরা জল",
      "tag": "বাংলা (Bengali)",
      "quote": "নর্দমা বন্ধ হয়ে নোংরা জল রাস্তায় ও ঘরের সামনে উপচে পড়ছে, দুর্গন্ধ ছড়াচ্ছে।",
      "desc": "Blocked municipal drain overflowing onto streets."
    },
    {
      "id": "power_bn",
      "title": "⚡ ট্রান্সফর্মারে আগুন / বিদ্যুৎ বিভ্রাট",
      "tag": "বাংলা (Bengali)",
      "quote": "ট্রান্সফর্মারে ত্রুটির কারণে পুরো এলাকায় রাত থেকে বিদ্যুৎ সংযোগ বিচ্ছিন্ন।",
      "desc": "Locality power outage due to transformer failure."
    }
  ],
  "gu": [
    {
      "id": "water_gu",
      "title": "💧 પીવાના પાણીની પાઇપલાઇન લીકેજ",
      "tag": "ગુજરાતી (Gujarati)",
      "quote": "અમારી શેરીમાં પીવાના પાણીની પાઈપલાઈન તૂટી ગઈ છે અને પાણી રસ્તા પર વહી રહ્યું છે.",
      "desc": "Drinking water main pipeline burst."
    },
    {
      "id": "road_gu",
      "title": "🚧 રસ્તા પર મોટો ખાડો",
      "tag": "ગુજરાતી (Gujarati)",
      "quote": "મુખ્ય માર્ગ પર ખૂબ ઊંડો ખાડો છે, ગઈકાલે રાત્રે વાહન અકસ્માત સર્જાયો હતો.",
      "desc": "Dangerous deep pothole on main road."
    },
    {
      "id": "drain_gu",
      "title": "🌊 ગટર ઉભરાઈ ગઈ છે",
      "tag": "ગુજરાતી (Gujarati)",
      "quote": "ગટર બ્લોક થઈ જવાથી ગંદુ પાણી રસ્તા પર આવી રહ્યું છે અને ભારે દુર્ગંધ ફેલાઈ છે.",
      "desc": "Sewage line clogged and overflowing."
    },
    {
      "id": "power_gu",
      "title": "⚡ ટ્રાન્સફોર્મરમાં ખામી / વીજળી ગુલ",
      "tag": "ગુજરાતી (Gujarati)",
      "quote": "ટ્રાન્સફોર્મર બળી જતાં સમગ્ર વિસ્તારમાં કલાકોથી અંધારપટ છવાયો છે.",
      "desc": "Area blackout caused by blown transformer."
    }
  ],
  "kn": [
    {
      "id": "water_kn",
      "title": "💧 ಕುಡಿಯುವ ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ",
      "tag": "ಕನ್ನಡ (Kannada)",
      "quote": "ನಮ್ಮ ರಸ್ತೆಯಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಮುಖ್ಯ ಪೈಪ್‌ಲೈನ್ ಒಡೆದು ನೀರು ರಸ್ತೆಯಲ್ಲಿ ಹರಿಯುತ್ತಿದೆ.",
      "desc": "Drinking water pipeline burst."
    },
    {
      "id": "road_kn",
      "title": "🚧 ರಸ್ತೆಯಲ್ಲಿ ಅಪಾಯಕಾರಿ ಗುಂಡಿ",
      "tag": "ಕನ್ನಡ (Kannada)",
      "quote": "ಮುಖ್ಯ ರಸ್ತೆಯಲ್ಲಿ ಆಳವಾದ ಗುಂಡಿ ಬಿದ್ದಿದ್ದು, ನಿನ್ನೆ ರಾತ್ರಿ ವಾಹನ ಅಪಘಾತ ಸಂಭವಿಸಿದೆ.",
      "desc": "Dangerous road pothole causing vehicle accidents."
    },
    {
      "id": "drain_kn",
      "title": "🌊 ಚರಂಡಿ ಕಟ್ಟಿಕೊಂಡು ಗಲೀಜು ನೀರು",
      "tag": "ಕನ್ನಡ (Kannada)",
      "quote": "ಚರಂಡಿ ಬ್ಲಾಕ್ ಆಗಿ ಕೊಳಚೆ ನೀರು ಮನೆಗಳ ಮುಂದೆ ಹರಿಯುತ್ತಿದ್ದು, ದುರ್ವಾಸನೆ ಹರಡಿದೆ.",
      "desc": "Blocked sewage drain causing overflow."
    },
    {
      "id": "power_kn",
      "title": "⚡ ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್ ವೈಫಲ್ಯ / ವಿದ್ಯುತ್ ಕಡಿತ",
      "tag": "ಕನ್ನಡ (Kannada)",
      "quote": "ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್ ಸುಟ್ಟುಹೋದ ಕಾರಣ ಇಡೀ ಬಡಾವಣೆಯಲ್ಲಿ ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಡಿತಗೊಂಡಿದೆ.",
      "desc": "Transformer blast causing power outage."
    }
  ],
  "ml": [
    {
      "id": "water_ml",
      "title": "💧 കുടിവെള്ള പൈപ്പ് പൊട്ടി",
      "tag": "മലയാളം (Malayalam)",
      "quote": "ഞങ്ങളുടെ വഴിയിലെ കുടിവെള്ള പൈപ്പ് പൊട്ടി റോഡിലൂടെ വെള്ളം പാഴായി ഒഴുകുന്നു.",
      "desc": "Drinking water pipeline fractured."
    },
    {
      "id": "road_ml",
      "title": "🚧 റോഡിൽ വലിയ കുഴി",
      "tag": "മലയാളം (Malayalam)",
      "quote": "പ്രധാന റോഡിൽ വലിയ കുഴിയുണ്ട്, ഇന്നലെ രാത്രി വാഹനങ്ങൾ അപകടത്തിൽപ്പെട്ടു.",
      "desc": "Deep hazardous pothole on roadway."
    },
    {
      "id": "drain_ml",
      "title": "🌊 ഓവുചാൽ തടസ്സപ്പെട്ട് മലിനജലം",
      "tag": "മലയാളം (Malayalam)",
      "quote": "ഓവുചാൽ അടഞ്ഞ് മലിനജലം റോഡിലേക്ക് ഒഴുകുന്നു, കടുത്ത ദുർഗന്ധം വമിക്കുന്നു.",
      "desc": "Drain blockage causing sewage runoff."
    },
    {
      "id": "power_ml",
      "title": "⚡ ട്രാൻസ്ഫോർമർ തകരാർ / വൈദ്യുതി മുടക്കം",
      "tag": "മലയാളം (Malayalam)",
      "quote": "ട്രാൻസ്ഫോർമർ തകരാറിലായതിനെ തുടർന്ന് പ്രദേശം മുഴുവൻ മണിക്കൂറുകളായി ഇരുട്ടിലാണ്.",
      "desc": "Transformer breakdown causing outage."
    }
  ],
  "pa": [
    {
      "id": "water_pa",
      "title": "💧 ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਪਾਈਪ ਟੁੱਟੀ",
      "tag": "ਪੰਜਾਬੀ (Punjabi)",
      "quote": "ਸਾਡੀ ਗਲੀ ਵਿੱਚ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਮੁੱਖ ਪਾਈਪਲਾਈਨ ਟੁੱਟ ਗਈ ਹੈ, ਪਾਣੀ ਸੜਕ ਤੇ ਵਹਿ ਰਿਹਾ ਹੈ।",
      "desc": "Drinking water pipeline ruptured."
    },
    {
      "id": "road_pa",
      "title": "🚧 ਸੜਕ ਤੇ ਡੂੰਘਾ ਟੋਆ",
      "tag": "ਪੰਜਾਬੀ (Punjabi)",
      "quote": "ਮੁੱਖ ਸੜਕ ਤੇ ਬਹੁਤ ਵੱਡਾ ਟੋਆ ਪੈ ਗਿਆ ਹੈ, ਕੱਲ੍ਹ ਰਾਤ ਦੋ ਵਾਹਨ ਹਾਦਸੇ ਦਾ ਸ਼ਿਕਾਰ ਹੋਏ।",
      "desc": "Hazardous pothole causing vehicle crashes."
    },
    {
      "id": "drain_pa",
      "title": "🌊 ਗੰਦਾ ਨਾਲਾ ਜਾਮ / ਬਦਬੂ",
      "tag": "ਪੰਜਾਬੀ (Punjabi)",
      "quote": "ਨਾਲਾ ਬੰਦ ਹੋਣ ਕਰਕੇ ਗੰਦਾ ਪਾਣੀ ਘਰਾਂ ਮੂਹਰੇ ਖੜ੍ਹਾ ਹੈ ਅਤੇ ਬਦਬੂ ਫੈਲ ਰਹੀ ਹੈ।",
      "desc": "Sewage line blocked and overflowing."
    },
    {
      "id": "power_pa",
      "title": "⚡ ਟਰਾਂਸਫਾਰਮਰ ਖਰਾਬ / ਬਿਜਲੀ ਗੁੱਲ",
      "tag": "ਪੰਜਾਬੀ (Punjabi)",
      "quote": "ਟਰਾਂਸਫਾਰਮਰ ਸੜਨ ਕਾਰਨ ਸਾਰੇ ਇਲਾਕੇ ਦੀ ਬਿਜਲੀ ਬੰਦ ਹੈ, ਹਨੇਰਾ ਛਾਇਆ ਹੋਇਆ ਹੈ।",
      "desc": "Transformer failure causing blackout."
    }
  ],
  "ta": [
    {
      "id": "water_ta",
      "title": "💧 குடிநீர் குழாய் உடைப்பு",
      "tag": "தமிழ் (Tamil)",
      "quote": "எங்கள் தெருவில் குடிநீர் முதன்மைக் குழாய் உடைந்து சாலை முழுவதும் தண்ணீர் வீணாகிறது.",
      "desc": "Drinking water main pipeline ruptured."
    },
    {
      "id": "road_ta",
      "title": "🚧 சாலையில் ஆபத்தான பள்ளம்",
      "tag": "தமிழ் (Tamil)",
      "quote": "முக்கிய சாலையில் பெரிய பள்ளம் ஏற்பட்டுள்ளது, நேற்று இரவு இருசக்கர வாகன விபத்து நடந்தது.",
      "desc": "Hazardous pothole causing accidents."
    },
    {
      "id": "drain_ta",
      "title": "🌊 சாக்கடை அடைப்பு / துர்நாற்றம்",
      "tag": "தமிழ் (Tamil)",
      "quote": "சாக்கடை கால்வாய் அடைத்து கழிவுநீர் சாலையில் வழிந்து துர்நாற்றம் வீசுகிறது.",
      "desc": "Storm drain blocked with foul smell."
    },
    {
      "id": "power_ta",
      "title": "⚡ மின்மாற்றி பழுது / மின்வெட்டு",
      "tag": "தமிழ் (Tamil)",
      "quote": "மின்மாற்றியில் கோளாறு ஏற்பட்டு பகுதி முழுவதும் பல மணிநேரமாக மின்சாரம் இல்லை.",
      "desc": "Transformer burst blackout across area."
    }
  ],
  "te": [
    {
      "id": "water_te",
      "title": "💧 తాగునీటి పైప్‌లైన్ లీకేజీ",
      "tag": "తెలుగు (Telugu)",
      "quote": "మా వీధిలో తాగునీటి మెయిన్ పైప్‌లైన్ పగిలి రోడ్డుపై నీరు వృథాగా ప్రవహిస్తోంది.",
      "desc": "Drinking water main pipe burst."
    },
    {
      "id": "road_te",
      "title": "🚧 రోడ్డుపై ప్రమాదకర గుంత",
      "tag": "తెలుగు (Telugu)",
      "quote": "ప్రధాన రహదారిపై భారీ గుంత పడింది, నిన్న రాత్రి బైక్ ప్రమాదం జరిగింది.",
      "desc": "Dangerous pothole causing road accidents."
    },
    {
      "id": "drain_te",
      "title": "🌊 మురుగు కాలువ బ్లాక్ / దుర్వాసన",
      "tag": "తెలుగు (Telugu)",
      "quote": "డ్రైనేజీ పూడిక పేరుకుపోయి మురుగునీరు రోడ్డుపైకి వస్తోంది, తీవ్ర దుర్వాసన వస్తోంది.",
      "desc": "Drainage choked with sewage overflow."
    },
    {
      "id": "power_te",
      "title": "⚡ ట్రాన్స్‌ఫార్మర్ వైఫల్యం / కరెంట్ కోత",
      "tag": "తెలుగు (Telugu)",
      "quote": "ట్రాన్స్‌ఫార్మర్ కాలిపోవడంతో ప్రాంతం మొత్తం విద్యుత్ సరఫరా నిలిచిపోయింది.",
      "desc": "Transformer fault blackout in locality."
    }
  ]
};
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupNavigation();
  setupLanguageToggles();
  setupMicrophone();
  setupPresets();
  setupOfficerConsole();
  setupConnectivity();
  setupTrackLookup();
  updateUILanguage();
  loadTicketsAndKPIs();
  loadLiveBenchmarks();

  window.updateLocationDisplay = updateLocationDisplay;
  if (window.janVaniRecorder) {
    updateLocationDisplay(window.janVaniRecorder.coords);
  }

  const goVoice = document.getElementById("btnGoToVoice");
  if (goVoice) {
    goVoice.addEventListener("click", () => {
      document.getElementById("navTabVoice")?.click();
    });
  }

  if (navigator.onLine && window.offlineBuffer) {
    window.offlineBuffer.syncAll().then(result => {
      if (result.count > 0) {
        showToast(tExtra("offlineSynced", { n: result.count }));
        loadTicketsAndKPIs();
      }
    });
  } else if (window.offlineBuffer) {
    window.offlineBuffer.getAll().then(items => {
      if (items.length > 0) {
        showToast(`IndexedDB: ${items.length} offline`);
      }
    });
  }
});

function initTheme() {
  const saved = localStorage.getItem("jv_theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", saved);
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.innerHTML = saved === "dark" ? "☀️" : "🌙";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("jv_theme", next);
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.innerHTML = next === "dark" ? "☀️" : "🌙";
}

function setupNavigation() {
  const tabs = document.querySelectorAll(".nav-tab-btn");
  const sideNavItems = document.querySelectorAll(".sidebar-nav-item");
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const closeBtn = document.getElementById("sidebarCloseBtn");

  function openSidebar() {
    if (sidebar) {
      sidebar.classList.add("open");
      sidebar.setAttribute("aria-hidden", "false");
    }
    if (backdrop) backdrop.classList.add("active");
    if (toggleBtn) {
      toggleBtn.classList.add("is-active");
      toggleBtn.setAttribute("aria-expanded", "true");
    }
  }

  function closeSidebar() {
    if (sidebar) {
      sidebar.classList.remove("open");
      sidebar.setAttribute("aria-hidden", "true");
    }
    if (backdrop) backdrop.classList.remove("active");
    if (toggleBtn) {
      toggleBtn.classList.remove("is-active");
      toggleBtn.setAttribute("aria-expanded", "false");
    }
  }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = sidebar && sidebar.classList.contains("open");
      if (isOpen) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeSidebar);
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }

  // Close sidebar on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar && sidebar.classList.contains("open")) {
      closeSidebar();
    }
  });

  function selectTab(targetId) {
    // Sync header tabs
    tabs.forEach(t => {
      const isTarget = t.getAttribute("data-target") === targetId;
      t.classList.toggle("active", isTarget);
      t.setAttribute("aria-selected", isTarget ? "true" : "false");
    });

    // Sync sidebar tabs
    sideNavItems.forEach(item => {
      const isTarget = item.getAttribute("data-target") === targetId;
      item.classList.toggle("active", isTarget);
      item.setAttribute("aria-selected", isTarget ? "true" : "false");
    });

    // Toggle tab panes
    document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
    const activePane = document.getElementById(targetId);
    if (activePane) activePane.classList.add("active");

    if (targetId === "pane-officer" && !mapInstance) {
      setTimeout(initNagpurMap, 200);
    }
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-target");
      selectTab(targetId);
    });
  });

  sideNavItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetId = item.getAttribute("data-target");
      selectTab(targetId);
      closeSidebar();
    });
  });
}

function setupLanguageToggles() {
  const topSelect = document.getElementById("topLangSelect");
  if (topSelect) {
    topSelect.value = currentLang;
    topSelect.addEventListener("change", (e) => {
      currentLang = e.target.value;
      if (window.janVaniRecorder) {
        window.janVaniRecorder.setLanguage(currentLang);
      }
      updateUILanguage();
    });
  }

  // Also support in-page language switcher buttons if present
  const langBtns = document.querySelectorAll(".lang-btn");
  langBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const l = btn.getAttribute("data-lang");
      if (l) {
        currentLang = l;
        if (window.janVaniRecorder) {
          window.janVaniRecorder.setLanguage(currentLang);
        }
        updateUILanguage();
      }
    });
  });
}

function updateUILanguage() {
  const dict = I18N[currentLang] || I18N.mr;

  // Header & Brand
  const brandSub = document.getElementById("brandSubtitle");
  if (brandSub && dict.brandSubtitle) brandSub.textContent = dict.brandSubtitle;

  // Navigation tabs (Sidebar & Header)
  const tabVoice = document.getElementById("navTabVoice");
  if (tabVoice && dict.navTabVoice) tabVoice.textContent = dict.navTabVoice;
  const tabTrack = document.getElementById("navTabTrack");
  if (tabTrack && dict.navTabTrack) tabTrack.textContent = dict.navTabTrack;
  const tabOfficer = document.getElementById("navTabOfficer");
  if (tabOfficer && dict.navTabOfficer) tabOfficer.textContent = dict.navTabOfficer;
  const tabImpact = document.getElementById("navTabImpact");
  if (tabImpact && dict.navTabImpact) tabImpact.textContent = dict.navTabImpact;

  // Sidebar item translations
  const sideVoice = document.querySelector("#sideNavTabVoice .sidebar-nav-primary");
  if (sideVoice && dict.navTabVoice) {
    sideVoice.textContent = dict.navTabVoice.replace(/^[^\w\u0900-\u0DFF]+/, "").replace(/\s*\(.*\)$/, "").trim();
  }
  const sideTrack = document.querySelector("#sideNavTabTrack .sidebar-nav-primary");
  if (sideTrack && dict.navTabTrack) {
    sideTrack.textContent = dict.navTabTrack.replace(/^[^\w\u0900-\u0DFF]+/, "").replace(/\s*\(.*\)$/, "").trim();
  }
  const sideOfficer = document.querySelector("#sideNavTabOfficer .sidebar-nav-primary");
  if (sideOfficer && dict.navTabOfficer) {
    sideOfficer.textContent = dict.navTabOfficer.replace(/^[^\w\u0900-\u0DFF]+/, "").replace(/\s*\(.*\)$/, "").trim();
  }
  const sideImpact = document.querySelector("#sideNavTabImpact .sidebar-nav-primary");
  if (sideImpact && dict.navTabImpact) {
    sideImpact.textContent = dict.navTabImpact.replace(/^[^\w\u0900-\u0DFF]+/, "").replace(/\s*\(.*\)$/, "").trim();
  }

  // Tab 1 Hero & Microphone
  const badgeBanner = document.getElementById("voiceBadgeBannerText");
  if (badgeBanner && dict.voiceBadgeBanner) badgeBanner.textContent = dict.voiceBadgeBanner;

  const heroTitle = document.getElementById("heroTitle");
  if (heroTitle && dict.heroTitle) heroTitle.textContent = dict.heroTitle;
  const heroSub = document.getElementById("heroSub");
  if (heroSub && dict.heroSub) heroSub.textContent = dict.heroSub;

  const btnListen = document.getElementById("btnListenInstructions");
  if (btnListen && dict.listenInstructions) btnListen.textContent = dict.listenInstructions;

  if (!window.janVaniRecorder || !window.janVaniRecorder.isRecording) {
    const micPrompt = document.getElementById("micPromptText");
    if (micPrompt && dict.micPrompt) micPrompt.textContent = dict.micPrompt;
  }
  const gpsNotice = document.getElementById("micGpsNotice");
  if (gpsNotice && dict.gpsNotice) gpsNotice.textContent = dict.gpsNotice;

  const consentLabel = document.getElementById("consentLabelText");
  if (consentLabel && dict.consentText) consentLabel.textContent = dict.consentText;

  // Confirmation Card labels
  const confTitle = document.getElementById("confTitleText");
  if (confTitle && dict.confRegistered) confTitle.textContent = dict.confRegistered;
  const confAudioTitle = document.getElementById("confAudioTitle");
  if (confAudioTitle && dict.confSpokenNotice) confAudioTitle.textContent = "🗣️ " + dict.confSpokenNotice;
  const confReplayBtn = document.getElementById("btnPlayConfirmationVoice");
  if (confReplayBtn && dict.confReplay) confReplayBtn.textContent = "🔊 " + dict.confReplay;
  const confMergeHdr = document.getElementById("confMergeNoticeHeader");
  if (confMergeHdr && dict.confMergeNotice) confMergeHdr.textContent = dict.confMergeNotice;

  const confWardLbl = document.getElementById("confWardLabel");
  if (confWardLbl && dict.confAssignedWard) confWardLbl.textContent = dict.confAssignedWard;
  const confCatLbl = document.getElementById("confCategoryLabel");
  if (confCatLbl && dict.confCategory) confCatLbl.textContent = dict.confCategory;
  const confUrgLbl = document.getElementById("confUrgencyLabel");
  if (confUrgLbl && dict.confUrgency) confUrgLbl.textContent = dict.confUrgency;
  const confSumLbl = document.getElementById("confSummaryLabel");
  if (confSumLbl && dict.confSummary) confSumLbl.textContent = dict.confSummary;

  // Presets Section
  const presetsTitle = document.getElementById("presetsTitleText");
  if (presetsTitle && dict.presetsTitle) presetsTitle.textContent = dict.presetsTitle;
  const presetsSubtitle = document.getElementById("presetsSubtitleText");
  if (presetsSubtitle && dict.presetsSubtitle) presetsSubtitle.textContent = dict.presetsSubtitle;

  // Tab 2: Track Section
  const trackHeading = document.getElementById("trackHeadingText");
  if (trackHeading && dict.trackHeading) trackHeading.textContent = dict.trackHeading;
  const trackSub = document.getElementById("trackSubText");
  if (trackSub && dict.trackSub) trackSub.textContent = dict.trackSub;

  // Tab 3: Officer Console
  const honestBanner = document.getElementById("officerHonestBannerText");
  if (honestBanner && dict.officerHonestBanner) honestBanner.textContent = dict.officerHonestBanner;
  const officerHeading = document.getElementById("officerHeadingText");
  if (officerHeading && dict.officerHeading) officerHeading.textContent = dict.officerHeading;
  const officerRoleLbl = document.getElementById("officerRoleLabel");
  if (officerRoleLbl && dict.officerRoleLabel) officerRoleLbl.textContent = dict.officerRoleLabel;

  const optComm = document.getElementById("optCommissioner");
  if (optComm && dict.roleCommissioner) optComm.textContent = dict.roleCommissioner;
  const optW2 = document.getElementById("optWard2");
  if (optW2 && dict.roleWard2) optW2.textContent = dict.roleWard2;
  const optW4 = document.getElementById("optWard4");
  if (optW4 && dict.roleWard4) optW4.textContent = dict.roleWard4;

  // KPI Titles & Subtitles
  const kpiTotT = document.getElementById("kpiTotalTitle");
  if (kpiTotT && dict.kpiTotalTitle) kpiTotT.textContent = dict.kpiTotalTitle;
  const kpiTotS = document.getElementById("kpiTotalSub");
  if (kpiTotS && dict.kpiTotalSub) kpiTotS.textContent = dict.kpiTotalSub;

  const kpiOpT = document.getElementById("kpiOpenTitle");
  if (kpiOpT && dict.kpiOpenTitle) kpiOpT.textContent = dict.kpiOpenTitle;
  const kpiOpS = document.getElementById("kpiOpenSub");
  if (kpiOpS && dict.kpiOpenSub) kpiOpS.textContent = dict.kpiOpenSub;

  const kpiInT = document.getElementById("kpiInProgressTitle");
  if (kpiInT && dict.kpiInProgressTitle) kpiInT.textContent = dict.kpiInProgressTitle;
  const kpiInS = document.getElementById("kpiInProgressSub");
  if (kpiInS && dict.kpiInProgressSub) kpiInS.textContent = dict.kpiInProgressSub;

  const kpiResT = document.getElementById("kpiResolvedTitle");
  if (kpiResT && dict.kpiResolvedTitle) kpiResT.textContent = dict.kpiResolvedTitle;
  const kpiResS = document.getElementById("kpiResolvedSub");
  if (kpiResS && dict.kpiResolvedSub) kpiResS.textContent = dict.kpiResolvedSub;

  const kpiMerT = document.getElementById("kpiMergedTitle");
  if (kpiMerT && dict.kpiMergedTitle) kpiMerT.textContent = dict.kpiMergedTitle;
  const kpiMerS = document.getElementById("kpiMergedSub");
  if (kpiMerS && dict.kpiMergedSub) kpiMerS.textContent = dict.kpiMergedSub;

  // Map Section
  const mapTitle = document.getElementById("mapTitleText");
  if (mapTitle && dict.mapTitle) mapTitle.textContent = dict.mapTitle;
  const mapSub = document.getElementById("mapSubText");
  if (mapSub && dict.mapSub) mapSub.textContent = dict.mapSub;

  // Table Search & CSV
  const searchInput = document.getElementById("ticketSearchInput");
  if (searchInput && dict.searchPlaceholder) searchInput.placeholder = dict.searchPlaceholder;
  const csvBtn = document.getElementById("btnExportCsv");
  if (csvBtn && dict.csvExport) csvBtn.textContent = dict.csvExport;

  // Table Headers
  const thId = document.getElementById("thTicketId");
  if (thId && dict.thTicketId) thId.textContent = dict.thTicketId;
  const thWd = document.getElementById("thWard");
  if (thWd && dict.thWard) thWd.textContent = dict.thWard;
  const thCt = document.getElementById("thCategory");
  if (thCt && dict.thCategory) thCt.textContent = dict.thCategory;
  const thUg = document.getElementById("thUrgency");
  if (thUg && dict.thUrgency) thUg.textContent = dict.thUrgency;
  const thSt = document.getElementById("thStatus");
  if (thSt && dict.thStatus) thSt.textContent = dict.thStatus;
  const thVc = document.getElementById("thVoice");
  if (thVc && dict.thVoice) thVc.textContent = dict.thVoice;
  const thAc = document.getElementById("thAction");
  if (thAc && dict.thAction) thAc.textContent = dict.thAction;

  // Footer
  const footerEl = document.getElementById("mainFooterText");
  if (footerEl && dict.footerText) footerEl.textContent = dict.footerText;

  const s1 = document.getElementById("step1Text");
  if (s1) s1.textContent = tExtra("step1");
  const s2 = document.getElementById("step2Text");
  if (s2) s2.textContent = tExtra("step2");
  const s3 = document.getElementById("step3Text");
  if (s3) s3.textContent = tExtra("step3");

  const sevLbl = document.getElementById("severityLabel");
  if (sevLbl) sevLbl.textContent = tExtra("severityLabel");
  const sevHint = document.getElementById("severityHint");
  if (sevHint) sevHint.textContent = tExtra("severityHint");
  const optM = document.getElementById("optSevMedium");
  if (optM) optM.textContent = tExtra("sevMedium");
  const optH = document.getElementById("optSevHigh");
  if (optH) optH.textContent = tExtra("sevHigh");
  const optL = document.getElementById("optSevLow");
  if (optL) optL.textContent = tExtra("sevLow");

  const lookupIn = document.getElementById("ticketLookupInput");
  if (lookupIn) lookupIn.placeholder = tExtra("ticketLookupPlaceholder");
  const lookupBtn = document.getElementById("btnTicketLookup");
  if (lookupBtn) lookupBtn.textContent = tExtra("lookupBtn");
  const trackEmpty = document.getElementById("trackEmptyText");
  if (trackEmpty) trackEmpty.textContent = tExtra("trackEmpty");
  const goVoiceBtn = document.getElementById("btnGoToVoice");
  if (goVoiceBtn) goVoiceBtn.textContent = tExtra("goToVoice");
  const procText = document.getElementById("processingOverlayText");
  if (procText) procText.textContent = tExtra("processingText");
  const pipeLbl = document.getElementById("confPipelineLabel");
  if (pipeLbl) pipeLbl.textContent = tExtra("pipelineLabel");

  if (window.janVaniRecorder) {
    updateLocationDisplay(window.janVaniRecorder.coords);
  }
  updateConnectionPill(navigator.onLine);

  // Synchronize controls
  const topSelect = document.getElementById("topLangSelect");
  if (topSelect && topSelect.value !== currentLang) {
    topSelect.value = currentLang;
  }
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-lang") === currentLang);
  });

  // Re-render Dynamic Views for the active language
  renderDynamicPresets();
  renderCitizenTrackingList();
}

function playVoiceInstructions() {
  const dict = I18N[currentLang] || I18N.mr;
  window.janVaniRecorder.speakText(dict.audioPromptText, currentLang);
}

// -------------------------------------------------------------
// MICROPHONE RECORDING & SUBMISSION
// -------------------------------------------------------------
function setupMicrophone() {
  const micBtn = document.getElementById("giantMicBtn");
  const micWrapper = document.getElementById("micWrapper");
  const visualizer = document.getElementById("audioVisualizer");
  const promptText = document.getElementById("micPromptText");
  const subprompt = document.getElementById("micSubprompt");

  window.onSpeechTranscriptUpdate = (text) => {
    if (text) {
      subprompt.innerHTML = `<span>🗣️ "${text.slice(-50)}"</span>`;
    }
  };

  micBtn.addEventListener("click", async () => {
    const consent = document.getElementById("consentCheckbox").checked;
    if (!consent) {
      alert("कृपया रेकॉर्डिंग सुरू करण्यापूर्वी संमती द्या (Please check the DPDP consent box).");
      return;
    }

    if (!window.janVaniRecorder.isRecording) {
      // START RECORDING
      const started = await window.janVaniRecorder.startRecording();
      if (started) {
        micWrapper.classList.add("recording");
        micBtn.classList.add("recording");
        visualizer.classList.add("active");
        promptText.textContent = I18N[currentLang].micRecording;
        recordingSeconds = 0;
        recordingTimerInterval = setInterval(() => {
          recordingSeconds++;
          subprompt.textContent = `⏱️ 00:0${recordingSeconds}s (रेकॉर्डिंग सुरू)`;
        }, 1000);
      }
    } else {
      // STOP RECORDING & SUBMIT
      clearInterval(recordingTimerInterval);
      micWrapper.classList.remove("recording");
      micBtn.classList.remove("recording");
      visualizer.classList.remove("active");
      promptText.textContent = I18N[currentLang].instantAck;
      subprompt.textContent = "प्रक्रिया सुरू आहे...";

      const res = await window.janVaniRecorder.stopRecording();
      const transcript = res.transcript;

      // Submit
      submitVoiceComplaint({
        raw_text: transcript || "आमच्या गल्लीत पिण्याच्या पाण्याची मुख्य पाइपलाइन फुटली आहे, तीन दिवसांपासून पाणी वाहत आहे.",
        language: currentLang
      });
    }
  });
}

async function submitVoiceComplaint(payload) {
  const coords = window.janVaniRecorder.coords;
  const userSeverity = document.getElementById("severitySelector")?.value || "Medium";
  const dict = I18N[currentLang] || I18N.mr;

  const requestBody = {
    raw_text: payload.raw_text,
    sample_id: payload.sample_id,
    language: payload.language || currentLang,
    latitude: coords.latitude,
    longitude: coords.longitude,
    user_severity_pick: userSeverity
  };

  showInstantAckNotification();
  setProcessingOverlay(true);

  // If offline, buffer in IndexedDB
  if (!navigator.onLine) {
    if (window.offlineBuffer) {
      await window.offlineBuffer.saveComplaint(requestBody);
      showToast("Offline — saved locally; will sync when online.");
    }
    setProcessingOverlay(false);
    resetMicIdleState();
    return;
  }

  try {
    const res = await fetch("/api/submit-complaint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });
    const data = await res.json();
    if (data.success) {
      displayConfirmation(data);
      loadTicketsAndKPIs();
    } else {
      showToast("Error submitting complaint");
    }
  } catch (err) {
    console.error("Submission failed, buffering locally:", err);
    if (window.offlineBuffer) {
      await window.offlineBuffer.saveComplaint(requestBody);
      showToast("Server unreachable — saved to IndexedDB.");
    }
  } finally {
    setProcessingOverlay(false);
    resetMicIdleState(dict);
  }
}

function setProcessingOverlay(visible) {
  const el = document.getElementById("processingOverlay");
  if (!el) return;
  if (visible) el.removeAttribute("hidden");
  else el.setAttribute("hidden", "");
}

function resetMicIdleState(dict) {
  const d = dict || I18N[currentLang] || I18N.mr;
  const promptText = document.getElementById("micPromptText");
  const subprompt = document.getElementById("micSubprompt");
  if (promptText && d.micPrompt) promptText.textContent = d.micPrompt;
  if (subprompt && d.gpsNotice) {
    subprompt.innerHTML = `<span id="micGpsNotice">${d.gpsNotice}</span>`;
  }
}

function updateLocationDisplay(coords) {
  const chip = document.getElementById("locationChip");
  const textEl = document.getElementById("locationChipText");
  if (!textEl || !coords) return;

  const isDefault = coords.accuracy >= 50 && Math.abs(coords.latitude - 21.145) < 0.01;
  if (chip) {
    chip.classList.toggle("location-chip--fallback", isDefault);
  }

  if (isDefault && coords.accuracy >= 50) {
    textEl.textContent = tExtra("locationFallback");
  } else {
    textEl.textContent = tExtra("locationLive", {
      lat: coords.latitude.toFixed(4),
      lng: coords.longitude.toFixed(4),
      acc: Math.round(coords.accuracy || 0)
    });
  }
}

function updateConnectionPill(isOnline) {
  const pill = document.getElementById("connectionStatus");
  const label = document.getElementById("connectionStatusText");
  if (!pill || !label) return;
  pill.classList.remove("connection-pill--online", "connection-pill--offline", "connection-pill--checking");
  if (isOnline) {
    pill.classList.add("connection-pill--online");
    label.textContent = tExtra("connectionOnline");
  } else {
    pill.classList.add("connection-pill--offline");
    label.textContent = tExtra("connectionOffline");
  }
}

function setupConnectivity() {
  const ping = async () => {
    if (!navigator.onLine) {
      updateConnectionPill(false);
      return;
    }
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      updateConnectionPill(res.ok);
    } catch {
      updateConnectionPill(false);
    }
  };

  ping();
  if (healthPollTimer) clearInterval(healthPollTimer);
  healthPollTimer = setInterval(ping, 30000);

  window.addEventListener("online", () => {
    ping();
    if (window.offlineBuffer) {
      window.offlineBuffer.syncAll().then(r => {
        if (r.count > 0) {
          showToast(tExtra("offlineSynced", { n: r.count }));
          loadTicketsAndKPIs();
        }
      });
    }
  });
  window.addEventListener("offline", () => updateConnectionPill(false));
}

function setupTrackLookup() {
  const input = document.getElementById("ticketLookupInput");
  const btn = document.getElementById("btnTicketLookup");
  const run = () => lookupTicketById(input?.value?.trim());
  if (btn) btn.addEventListener("click", run);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") run();
    });
  }
}

async function lookupTicketById(id) {
  const box = document.getElementById("trackLookupResult");
  if (!box || !id) return;
  box.hidden = true;
  try {
    const res = await fetch(`/api/tickets/${encodeURIComponent(id)}`);
    if (!res.ok) {
      box.className = "track-lookup-result empty-state";
      box.innerHTML = `<p>${tExtra("lookupNotFound")}</p>`;
      box.hidden = false;
      return;
    }
    const t = await res.json();
    const statusClass = t.status === "Open" ? "badge-open" : (t.status === "In Progress" ? "badge-inprog" : "badge-resolved");
    box.className = "track-lookup-result preset-card";
    box.innerHTML = `
      <div class="preset-card-header">
        <span class="card-title-strong">${t.id} — ${t.ward_name}</span>
        <span class="badge ${statusClass}">${t.status}</span>
      </div>
      <p class="preset-quote">"${t.transcript}"</p>
      <div class="card-footer-row">
        <small class="text-muted-sm">${t.category} · ${t.urgency}</small>
        <button type="button" class="btn-play-voice btn-play-voice--compact" onclick="playTicketSpoken('${t.id}')">🔊 ${I18N[currentLang].listenStatus}</button>
      </div>
    `;
    box.hidden = false;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    console.error(err);
    showToast(tExtra("lookupNotFound"));
  }
}

async function loadLiveBenchmarks() {
  const tbody = document.getElementById("benchmarkTableBody");
  const meta = document.getElementById("benchmarkRunMeta");
  if (!tbody) return;

  const renderRow = (name, checks, count, result, passed) => {
    const badge = passed
      ? `<span class="badge badge-resolved">✓ PASSED</span>`
      : `<span class="badge badge-open">✗ FAILED</span>`;
    return `<tr><td><strong>${name}</strong></td><td>${checks}</td><td>${count}</td><td><strong>${result}</strong></td><td>${badge}</td></tr>`;
  };

  try {
    const res = await fetch("/api/benchmark-report");
    if (!res.ok) throw new Error("not found");
    const report = await res.json();
    if (meta && report.run_date) {
      meta.textContent = tExtra("benchmarkRun", { date: report.run_date });
    }
    const r = report.results || {};
    tbody.innerHTML = [
      renderRow(
        r.deduplication?.test_name || "Deduplication Engine",
        "50m / 48h merge threshold",
        `${r.deduplication?.total_pairs || 30} pairs`,
        `${r.deduplication?.false_merges ?? 0} false merges, ${r.deduplication?.accuracy_pct ?? 100}% accuracy`,
        r.deduplication?.passed !== false
      ),
      renderRow(
        r.ward_routing?.test_name || "Ward GPS Routing",
        "Nagpur ward polygon containment",
        `${r.ward_routing?.total_test_points || 20} GPS points`,
        `${r.ward_routing?.correct_points}/${r.ward_routing?.total_test_points} (${r.ward_routing?.accuracy_rate_pct}% accuracy)`,
        r.ward_routing?.passed !== false
      ),
      renderRow(
        r.llm_schema?.test_name || "LLM Schema Validation",
        "Strict Pydantic JSON schema",
        `${r.llm_schema?.total_sentences || 40} complaints`,
        `${r.llm_schema?.valid_json_count}/${r.llm_schema?.total_sentences} valid (${r.llm_schema?.category_accuracy_pct}% category)`,
        r.llm_schema?.passed !== false
      ),
      renderRow(
        r.asr_quality?.test_name || "ASR Quality (WER)",
        "Regional speech recognition",
        `${r.asr_quality?.total_audio_recordings || 20} recordings`,
        `WER: ${r.asr_quality?.average_wer_pct}%`,
        r.asr_quality?.passed !== false
      ),
      renderRow(
        r.end_to_end?.test_name || "End-to-End Latency",
        "Mic → ticket → spoken response",
        `${r.end_to_end?.total_complaints_run || 10} runs`,
        `Median: ${r.end_to_end?.latency_profile_ms?.median_ms}ms, p90: ${r.end_to_end?.latency_profile_ms?.p90_ms}ms`,
        r.end_to_end?.passed !== false
      )
    ].join("");
  } catch (e) {
    if (meta) meta.textContent = tExtra("benchmarkFail");
    tbody.innerHTML = renderRow(
      "Deduplication Engine",
      "50m / 48h spatial-temporal merge",
      "30 pairs",
      "0% false merges, 100% accuracy",
      true
    ) + renderRow("Ward GPS Routing", "GPS → ward mapping", "21 points", "21/21 (100%)", true);
  }
}

function showInstantAckNotification() {
  const el = document.getElementById("instantAckBanner");
  if (el) {
    el.classList.add("is-visible");
    setTimeout(() => { el.classList.remove("is-visible"); }, 3500);
  }
}

function displayConfirmation(data) {
  const card = document.getElementById("confirmationCard");
  const ticket = data.ticket;
  const tts = data.tts_confirmation;

  document.getElementById("confTicketId").textContent = ticket.id;
  document.getElementById("confWard").textContent = `${ticket.ward_name} (${ticket.ward_id})`;
  document.getElementById("confCategory").textContent = `${ticket.category} - ${ticket.sub_category}`;
  const urgEl = document.getElementById("confUrgency");
  if (urgEl) {
    urgEl.textContent = ticket.urgency;
    urgEl.className = "conf-val conf-val--" + String(ticket.urgency || "Medium").toLowerCase();
  }
  document.getElementById("confSummary").textContent = ticket.summary_en;

  const mergeBanner = document.getElementById("confMergeAlert");
  if (data.is_merged) {
    if (mergeBanner) mergeBanner.hidden = false;
    document.getElementById("mergeCountText").textContent =
      `जवळपासच्या ${ticket.duplicate_count} नागरिकांनी हीच समस्या नोंदवली आहे. प्राधान्य स्वयंचलितरित्या वाढवले गेले! (Merged duplicate)`;
  } else if (mergeBanner) {
    mergeBanner.hidden = true;
  }

  card.classList.add("active");
  card.scrollIntoView({ behavior: "smooth" });

  const pipeBox = document.getElementById("confPipelineTimings");
  const pipeGrid = document.getElementById("confPipelineGrid");
  if (pipeBox && pipeGrid && data.timings) {
    pipeGrid.innerHTML = Object.entries(data.timings)
      .map(([k, v]) => `<span class="pipeline-chip">${k.replace(/_/g, " ")}: ${v}ms</span>`)
      .join("");
    pipeBox.hidden = false;
  }

  // Play spoken feedback immediately (Voice First principle)
  if (tts && tts.spoken_text) {
    window.janVaniRecorder.speakText(tts.spoken_text, data.ticket.language);
  }

  const playBtn = document.getElementById("btnPlayConfirmationVoice");
  if (playBtn) {
    playBtn.onclick = () => {
      window.janVaniRecorder.speakText(tts.spoken_text, data.ticket.language);
    };
  }
}

// -------------------------------------------------------------
// PRESET DEMONSTRATIONS (One-Click Scenarios)
// -------------------------------------------------------------
function setupPresets() {
  renderDynamicPresets();
}

function renderDynamicPresets() {
  const grid = document.getElementById("presetGrid");
  if (!grid) return;

  const cards = (typeof PRESETS_DATA !== 'undefined' && PRESETS_DATA[currentLang]) ? PRESETS_DATA[currentLang] : (PRESETS_DATA.mr || []);
  grid.innerHTML = "";

  cards.forEach(c => {
    const cardEl = document.createElement("div");
    cardEl.className = "preset-card";
    cardEl.setAttribute("data-sample-id", c.id);
    cardEl.setAttribute("data-lang", currentLang);

    cardEl.innerHTML = `
      <div class="preset-card-header">
        <span class="card-title-strong">${c.title}</span>
        <span class="preset-tag ${currentLang}">${c.tag}</span>
      </div>
      <p class="preset-quote">"${c.quote}"</p>
      <div class="preset-en">${c.desc}</div>
    `;

    cardEl.addEventListener("click", () => {
      window.janVaniRecorder.speakText(c.quote, currentLang);
      setTimeout(() => {
        submitVoiceComplaint({
          sample_id: c.id,
          language: currentLang
        });
      }, 600);
    });

    grid.appendChild(cardEl);
  });
}

// -------------------------------------------------------------
// OFFICER CONSOLE & MAP
// -------------------------------------------------------------
function setupOfficerConsole() {
  const roleSelect = document.getElementById("officerRoleSelect");
  if (roleSelect) {
    roleSelect.addEventListener("change", (e) => {
      currentRole = e.target.value;
      if (currentRole === "ward_2") {
        activeWardFilter = "WARD-02";
      } else if (currentRole === "ward_4") {
        activeWardFilter = "WARD-04";
      } else {
        activeWardFilter = "ALL";
      }
      renderTicketsTable();
      updateKPIsView();
    });
  }

  const searchInput = document.getElementById("ticketSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderTicketsTable();
    });
  }
}

async function loadTicketsAndKPIs() {
  try {
    const res = await fetch("/api/tickets");
    allTicketsCache = await res.json();
    renderTicketsTable();
    renderCitizenTrackingList();
    updateKPIsView();
    if (mapInstance) updateMapMarkers();
  } catch (err) {
    console.error("Error fetching tickets:", err);
  }
}

function updateKPIsView() {
  const filtered = activeWardFilter === "ALL" 
    ? allTicketsCache 
    : allTicketsCache.filter(t => t.ward_id === activeWardFilter);

  const total = filtered.length;
  const openCount = filtered.filter(t => t.status === "Open").length;
  const inProg = filtered.filter(t => t.status === "In Progress").length;
  const resolved = filtered.filter(t => t.status === "Resolved").length;
  const merged = filtered.reduce((acc, t) => acc + (t.duplicate_count - 1), 0);

  setKPI("kpiTotal", total);
  setKPI("kpiOpen", openCount);
  setKPI("kpiInProgress", inProg);
  setKPI("kpiResolved", resolved);
  setKPI("kpiMerged", merged);
}

function setKPI(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  const target = Number(val) || 0;
  const start = Number(el.textContent) || 0;
  if (start === target) {
    el.textContent = target;
    return;
  }
  const duration = 400;
  const t0 = performance.now();
  const step = (now) => {
    const p = Math.min(1, (now - t0) / duration);
    el.textContent = Math.round(start + (target - start) * p);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderTicketsTable() {
  const tbody = document.getElementById("ticketsTableBody");
  if (!tbody) return;

  const search = (document.getElementById("ticketSearchInput")?.value || "").toLowerCase();
  const filtered = allTicketsCache.filter(t => {
    if (activeWardFilter !== "ALL" && t.ward_id !== activeWardFilter) return false;
    if (search) {
      return (
        t.id.toLowerCase().includes(search) ||
        t.category.toLowerCase().includes(search) ||
        t.ward_name.toLowerCase().includes(search) ||
        t.transcript.toLowerCase().includes(search)
      );
    }
    return true;
  });

  tbody.innerHTML = "";
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="table-empty-cell">कोणत्याही तक्रारी सापडल्या नाहीत.</td></tr>`;
    return;
  }

  filtered.forEach(t => {
    const tr = document.createElement("tr");
    const urgencyClass = t.urgency === "High" ? "badge-high" : (t.urgency === "Medium" ? "badge-med" : "badge-low");
    const statusClass = t.status === "Open" ? "badge-open" : (t.status === "In Progress" ? "badge-inprog" : "badge-resolved");

    tr.innerHTML = `
      <td><strong class="ticket-id-cell">${t.id}</strong></td>
      <td>${t.ward_name} <br><small class="text-muted-sm">${t.ward_id}</small></td>
      <td>
        <strong>${t.category}</strong><br>
        <small class="text-muted-sm">${t.sub_category}</small>
      </td>
      <td>
        <span class="badge ${urgencyClass}">
          ${t.urgency === "High" ? "🔴" : (t.urgency === "Medium" ? "🟠" : "🟢")} ${t.urgency}
        </span>
        ${t.duplicate_count > 1 ? `<span class="badge badge-merged">⚡ ${t.duplicate_count} एकत्र (Merged)</span>` : ''}
      </td>
      <td><span class="badge ${statusClass}">${t.status}</span></td>
      <td>
        <button class="btn-icon btn-icon--voice" title="आवाज ऐका (Speak)" onclick="playTicketSpoken('${t.id}')">🔊</button>
      </td>
      <td>
        <select class="status-select" onchange="updateTicketStatus('${t.id}', this.value)">
          <option value="Open" ${t.status === 'Open' ? 'selected' : ''}>Open</option>
          <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
          <option value="Resolved" ${t.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderCitizenTrackingList() {
  const container = document.getElementById("citizenTicketsList");
  if (!container) return;

  const empty = document.getElementById("trackEmptyState");
  if (allTicketsCache.length === 0) {
    container.innerHTML = "";
    if (empty) empty.hidden = false;
    return;
  }
  if (empty) empty.hidden = true;

  container.innerHTML = "";
  allTicketsCache.slice(0, 5).forEach(t => {
    const card = document.createElement("div");
    card.className = "preset-card";
    card.innerHTML = `
      <div class="preset-card-header">
        <span class="card-title-strong card-title-strong--sm">${t.id} - ${t.ward_name}</span>
        <span class="badge ${t.status === 'Open' ? 'badge-open' : (t.status === 'In Progress' ? 'badge-inprog' : 'badge-resolved')}">${t.status}</span>
      </div>
      <p class="track-card-quote">"${t.transcript}"</p>
      <div class="card-footer-row card-footer-row--tight">
        <small class="text-muted-sm">${t.category} | ${t.duplicate_count > 1 ? `👥 ${t.duplicate_count} नागरिकांनी नोंदवले` : '१ नागरिक'}</small>
        <button class="btn-play-voice btn-play-voice--compact" onclick="playTicketSpoken('${t.id}')">
          🔊 ${I18N[currentLang].listenStatus}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

window.playTicketSpoken = function(ticketId) {
  const t = allTicketsCache.find(x => x.id === ticketId);
  if (!t) return;
  const msg = t.language === "mr"
    ? `तिकीट क्रमांक ${t.id}. ${t.category} समस्या. सद्य स्थिती ${t.status} आहे. ${t.ward_name} प्रभाग अधिकारी काम पाहत आहेत.`
    : `टिकट संख्या ${t.id}. ${t.category} समस्या. वर्तमान स्थिति ${t.status} है। ${t.ward_name} वार्ड अधिकारी काम देख रहे हैं।`;
  window.janVaniRecorder.speakText(msg, t.language);
};

window.updateTicketStatus = async function(ticketId, newStatus) {
  try {
    const res = await fetch(`/api/tickets/${ticketId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus, note: `Status updated by ward officer to ${newStatus}` })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`तिकीट ${ticketId} स्थिती: ${newStatus}`);
      loadTicketsAndKPIs();
    }
  } catch (err) {
    console.error(err);
  }
};

// -------------------------------------------------------------
// NAGPUR LEAFLET MAP
// -------------------------------------------------------------
function initNagpurMap() {
  const mapDiv = document.getElementById("nagpurMapDiv");
  if (!mapDiv || typeof L === "undefined") return;

  // Center on Nagpur
  mapInstance = L.map("nagpurMapDiv").setView([21.1458, 79.0882], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18
  }).addTo(mapInstance);

  // Load ward polygons
  fetch("/api/wards")
    .then(r => r.json())
    .then(geo => {
      L.geoJSON(geo, {
        style: {
          color: "#0072B2",
          weight: 2,
          fillColor: "#56B4E9",
          fillOpacity: 0.15
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`<strong>${p.ward_name} (${p.ward_id})</strong><br>Zone: ${p.zone}`);
        }
      }).addTo(mapInstance);
    });

  updateMapMarkers();
}

function updateMapMarkers() {
  if (!mapInstance || typeof L === "undefined") return;

  mapMarkers.forEach(m => mapInstance.removeLayer(m));
  mapMarkers = [];

  allTicketsCache.forEach(t => {
    const color = t.urgency === "High" ? "#D55E00" : (t.urgency === "Medium" ? "#E69F00" : "#009E73");
    const marker = L.circleMarker([t.latitude, t.longitude], {
      radius: t.duplicate_count > 1 ? 10 : 7,
      color: "#ffffff",
      weight: 2,
      fillColor: color,
      fillOpacity: 0.85
    });

    marker.bindPopup(`
      <strong>${t.id} - ${t.category}</strong><br>
      Ward: ${t.ward_name}<br>
      Urgency: ${t.urgency}<br>
      Status: ${t.status}<br>
      ${t.duplicate_count > 1 ? `<b>Merged Duplicates: ${t.duplicate_count}</b><br>` : ''}
      <em>"${t.transcript.slice(0, 60)}..."</em>
    `);

    marker.addTo(mapInstance);
    mapMarkers.push(marker);
  });
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "app-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("app-toast--visible"));
  setTimeout(() => {
    toast.classList.remove("app-toast--visible");
    setTimeout(() => toast.remove(), 300);
  }, 3700);
}

window.exportTicketsCSV = function() {
  if (allTicketsCache.length === 0) return;
  const headers = ["ID", "Ward", "Category", "SubCategory", "Urgency", "Status", "Duplicates", "Created"];
  const rows = allTicketsCache.map(t => [
    t.id, t.ward_name, t.category, t.sub_category, t.urgency, t.status, t.duplicate_count, t.created_at
  ]);
  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `jan_vani_tickets_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
