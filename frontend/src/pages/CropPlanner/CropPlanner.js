import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../../App.css";
import "../CropPlanner/CropPlanner.css";

function CropPlanner() {

  const translations = {
  english: {
    title: "🌱 Crop Planner",
    soilTypeOptions: {
      Loamy: "Loamy",
      Clay: "Clay",
      Sandy: "Sandy",
      Silty: "Silty"
    },
    subtitle: "Plan your crops based on climate, season & AI recommendations.",
    farmingLocationEnv: "Farming Location and Environment",
    soilType: "Soil Type",
    soilPH: "Soil pH",
    soilEC: "Soil EC [dS/m]",
    ecOptions: {
      Low:"Low [0 - 0.8]",
      Medium: "Medium [0.8 - 2.0]",
      High: "High [> 2.0]"},
    landTopo: "Land Topography",
    landTopoOptions: {
      flat:"Flat", 
      sloped: "Sloped",
      undulating: "Undulating",
      terraced: "Terraced"
    },
    landFinInfo: "Land and Financial Information",
    budgetOptions: {
      Low: "Low (₹0 - ₹50,000)",
      Medium: "Medium (₹50,001 - ₹2,00,000)",
      High: "High (> ₹2,00,000)"
    },
    landArea: "Land Area (acres)",
    budget: "Budget",
    labor: "Labor Availability",
    farmPractices: "Farming Practices and Challenges",
    irrigation: "Irrigation System",
    irrigationOptions: {
      Flood: "Flood",
      Drip: "Drip",
      Sprinkler: "Sprinkler",
      Canal: "Canal",
      Well: "Well",
      Rainfed: "Rainfed"
    },
    fertilizer: "Fertilizer Used",
    pestDisease: "Pest & Disease Issues",
    submit: "Submit",
    back: "Back",
    recommendCropPlan: "🌾 Recommended Crop Plan",
    suitabilityScore: "Suitability Score",
    cropDetails: "Crop Details",
    selectOption: "-- Select an option --",
    landAreaPlaceholder: "Enter land area...",
    fertilizerPlaceholder: "Enter fertilizers used...",
    pestDiseasePlaceholder: "Enter pest/disease issues...",
    laborPlaceholder: "e.g., 3 workers / day",
    loading: "Submitting...",
    recommendedCrop: "Recommended Crop",
    noReport: "No report generated.",
    farmingPracticesChallenges: "Farming Practices and Challenges",
    financialInfo:"Land and Financial Information",
    soilPHRange: "Soil pH Range",
    temperatureRange: "Temperature Range",
    rainfallRequirement: "Rainfall Requirement",
    irrigation: "Irrigation",
    aiCropPlanReport: "AI Crop Plan Report"
  },

  hindi: {
    title: "🌱 फसल योजनाकार",
    soilTypeOptions: {
      Loamy: "दोमट",
      Clay: "चिकनी",
      Sandy: "बलुई",
      Silty: "गादयुक्त"
    },
    subtitle: "जलवायु, मौसम और एआई सुझावों के आधार पर अपनी फसलें योजना बनाएं।",
    farmingLocationEnv: "खेती का स्थान और पर्यावरण",
    soilType: "मिट्टी का प्रकार",
    soilPH: "मिट्टी का pH",
    soilEC: "मिट्टी की EC [dS/m]",
    ecOptions: {
      Low:"कम [0 - 0.8]",
      Medium: "मध्यम [0.8 - 2.0]",
      High: "उच्च [> 2.0]"
    },
    landTopo: "भूमि की स्थलाकृति",
    landTopoOptions: {
      flat: "समतल",
      sloped: "ढलान",
      undulating: "तरंगित",
      terraced: "सीढ़ीदार"
    },
    landFinInfo: "भूमि और वित्तीय जानकारी",
    budgetOptions: {
      Low: "कम (₹0 - ₹50,000)",
      Medium: "मध्यम (₹50,001 - ₹2,00,000)",
      High: "उच्च (> ₹2,00,000)"
    },
    landArea: "भूमि क्षेत्र (एकड़)",
    budget: "बजट",
    labor: "श्रम की उपलब्धता",
    farmPractices: "खेती के तरीके और चुनौतियाँ",
    irrigation: "सिंचाई प्रणाली",
    irrigationOptions: {
      Flood: "बाढ़",
      Drip: "ड्रिप",
      Sprinkler: "स्प्रिंकलर",
      Canal: "नहर",
      Well: "कुआँ",
      Rainfed: "वर्षा पर आधारित"
    },
    fertilizer: "उपयोग की गई खाद",
    pestDisease: "कीट और रोग की समस्याएँ",
    submit: "जमा करें",
    back: "वापस",
    recommendCropPlan: "🌾 अनुशंसित फसल योजना",
    suitabilityScore: "उपयुक्तता स्कोर",
    cropDetails: "फसल विवरण",
    selectOption: "-- विकल्प चुनें --",
    landAreaPlaceholder: "भूमि क्षेत्र दर्ज करें...",
    fertilizerPlaceholder: "खाद दर्ज करें...",
    pestDiseasePlaceholder: "समस्याएँ दर्ज करें...",
    laborPlaceholder: "उदा., 3 मजदूर/दिन",
    loading: "जमा हो रहा है...",
    recommendedCrop: "अनुशंसित फसल",
    noReport: "कोई रिपोर्ट तैयार नहीं की गई।",
    farmingPracticesChallenges: "कृषि प्रथाएँ और चुनौतियाँ",
    financialInfo: "भूमि और वित्तीय जानकारी",
    soilPHRange: "मिट्टी का pH सीमा",
    temperatureRange: "तापमान सीमा",
    rainfallRequirement: "वर्षा की आवश्यकता",
    irrigation: "सिंचाई",
    aiCropPlanReport: "एआई फसल योजना रिपोर्ट"
  },

  tamil: {
    title: "🌱 பயிர் திட்டம்",
    soilTypeOptions: {
      Loamy: "களிமண்",
      Clay: "சிகப்பு மண்",
      Sandy: "மணற்பாங்கு",
      Silty: "சேற்று"
    },
    subtitle: "காலநிலை, பருவம் மற்றும் AI பரிந்துரைகளின் அடிப்படையில் உங்கள் பயிர்களை திட்டமிடுங்கள்.",
    farmingLocationEnv: "விவசாய இடம் மற்றும் சூழல்",
    soilType: "மண் வகை",
    soilPH: "மண் pH",
    soilEC: "மண் EC [dS/m]",
    ecOptions: {
      Low: "குறைந்த [0 - 0.8]",
      Medium: "நடுத்தரம் [0.8 - 2.0]",
      High: "அதிக [> 2.0]"
    },
    landTopo: "நிலப்பரப்பு",
    landTopoOptions: {
      flat: "சமத்தளம்",
      sloped: "சரிவு",
      undulating: "அலைபோல் நிலம்",
      terraced: "படிகட்ட அமைப்பு"
    },
    landFinInfo: "நிலம் மற்றும் நிதி தகவல்",
    budgetOptions: {
      Low: "குறைந்த (₹0 - ₹50,000)",
      Medium: "நடுத்தரம் (₹50,001 - ₹2,00,000)",
      High: "அதிக (> ₹2,00,000)"
    },
    landArea: "நிலப் பரப்பு (ஏக்கர்)",
    budget: "செலவுத் திட்டம்",
    labor: "தொழிலாளர் கிடைக்கும் நிலை",
    farmPractices: "விவசாய முறைகள் மற்றும் சவால்கள்",
    irrigation: "பாசன அமைப்பு",
    irrigationOptions: {
      Flood: "பேராறுதல்",
      Drip: "டிரிப்",
      Sprinkler: "ஸ்பிரிங்க்லர்",
      Canal: "கால்வாய்",
      Well: "கிணறு",
      Rainfed: "மழை சார்ந்த"
    },
    fertilizer: "உரங்கள் பயன்படுத்தப்பட்டது",
    pestDisease: "பூச்சி மற்றும் நோய் பிரச்சினைகள்",
    submit: "சமர்ப்பிக்கவும்",
    back: "பின்னுக்கு",
    recommendCropPlan: "🌾 பரிந்துரைக்கப்பட்ட பயிர் திட்டம்",
    suitabilityScore: "பொருத்தமான மதிப்பெண்",
    cropDetails: "பயிர் விவரங்கள்",
    selectOption: "-- தேர்ந்தெடுக்கவும் --",
    landAreaPlaceholder: "நிலப் பரப்பை உள்ளிடவும்...",
    fertilizerPlaceholder: "உரங்களை உள்ளிடவும்...",
    pestDiseasePlaceholder: "பிரச்சினைகளை உள்ளிடவும்...",
    laborPlaceholder: "உ.பி., 3 தொழிலாளர்கள்/நாள்",
    loading: "சமர்ப்பிக்கப்படுகிறது...",
    recommendedCrop: "பரிந்துரைக்கப்பட்ட பயிர்",
    noReport: "அறிக்கை உருவாக்கப்படவில்லை.",
    farmingPracticesChallenges: "விவசாய முறைகள் மற்றும் சவால்கள்",
    financialInfo: "நிலம் மற்றும் நிதி தகவல்",
    soilPHRange: "மண் pH வரம்பு",
    temperatureRange: "வெப்பநிலை வரம்பு",
    rainfallRequirement: "மழை தேவையா?",
    irrigation: "நீர்ப்பாசனம்",
    aiCropPlanReport: "AI பயிர் திட்ட அறிக்கை"
  },

  telugu: {
    title: "🌱 పంట ప్రణాళిక",
    soilTypeOptions: {
      Loamy: "లోమి",
      Clay: "మట్టి",
      Sandy: "ఇసుక",
      Silty: "గాదె"
    },
    subtitle: "వాతావరణం, సీజన్ మరియు AI సిఫార్సుల ఆధారంగా మీ పంటలను ప్రణాళిక చేయండి.",
    farmingLocationEnv: "వ్యవసాయ స్థలం మరియు పర్యావరణం",
    soilType: "మట్టి రకం",
    soilPH: "మట్టి pH",
    soilEC: "మట్టి EC [dS/m]",
    ecOptions: {
      Low: "తక్కువ [0 - 0.8]",
      Medium: "మధ్యస్థ [0.8 - 2.0]",
      High: "అధిక [> 2.0]"
    },
    landTopo: "భూమి భౌగోళికం",
    landTopoOptions: {
      flat: "సమతల",
      sloped: "వంకరభూమి",
      undulating: "తరంగాకార భూభాగం",
      terraced: "కట్టిన పొలాలు"
    },
    landFinInfo: "భూమి మరియు ఆర్థిక సమాచారం",
    budgetOptions: {
      Low: "తక్కువ (₹0 - ₹50,000)",
      Medium: "మధ్యస్థ (₹50,001 - ₹2,00,000)",
      High: "అధిక (> ₹2,00,000)"
    },
    landArea: "భూమి విస్తీర్ణం (ఎకరాలు)",
    budget: "బడ్జెట్",
    labor: "కూలీల లభ్యత",
    farmPractices: "వ్యవసాయ పద్ధతులు మరియు సవాళ్లు",
    irrigation: "పొలాల నీటిపారుదల",
    irrigationOptions: {
      Flood: "పోటు",
      Drip: "డ్రిప్",
      Sprinkler: "స్ప్రింక్లర్",
      Canal: "కాలువ",
      Well: "వెళ్",
      Rainfed: "వాన ఆధారితం"
    },
    fertilizer: "ఎరువులు ఉపయోగించబడ్డాయి",
    pestDisease: "కీటకాలు మరియు వ్యాధి సమస్యలు",
    submit: "సమర్పించండి",
    back: "వెనక్కి",
    recommendCropPlan: "🌾 సిఫార్సు చేయబడిన పంట ప్రణాళిక",
    suitabilityScore: "సరిపోయే స్కోరు",
    cropDetails: "పంట వివరాలు",
    selectOption: "-- ఒకదాన్ని ఎంచుకోండి --",
    landAreaPlaceholder: "భూమి విస్తీర్ణం నమోదు చేయండి...",
    fertilizerPlaceholder: "ఎరువులు నమోదు చేయండి...",
    pestDiseasePlaceholder: "సమస్యలు నమోదు చేయండి...",
    laborPlaceholder: "ఉదా., 3 కార్మికులు/రోజు",
    loading: "సమర్పిస్తున్నారు...",
    recommendedCrop: "సిఫార్సు చేసిన పంట",
    noReport: "నివేదిక రూపొందించబడలేదు.",
    farmingPracticesChallenges: "వ్యవసాయ పద్ధతులు మరియు సవాళ్లు",
    financialInfo: "భూమి మరియు ఆర్థిక సమాచారం",
    soilPHRange: "మట్టికి pH పరిధి",
    temperatureRange: "ఉష్ణోగ్రత పరిధి",
    rainfallRequirement: "వర్షపాతం అవసరం",
    irrigation: "పొలాల నీటిపారుదల",
    aiCropPlanReport: "AI పంట ప్రణాళిక నివేదిక"
  },

  punjabi: {
    title: "🌱 ਫਸਲ ਯੋਜਕ",
    soilTypeOptions: {
      Loamy: "ਦੋਮਟ",
      Clay: "ਚਿਕਣੀ",
      Sandy: "ਰੇਤਲੀ",
      Silty: "ਗਾਦੀ"
    },
    subtitle: "ਮੌਸਮ, ਰੁੱਤ ਅਤੇ AI ਦੀਆਂ ਸਿਫਾਰਸ਼ਾਂ ਦੇ ਆਧਾਰ 'ਤੇ ਆਪਣੀਆਂ ਫਸਲਾਂ ਦੀ ਯੋਜਨਾ ਬਣਾਓ।",
    farmingLocationEnv: "ਖੇਤੀਬਾੜੀ ਦੀ ਥਾਂ ਅਤੇ ਵਾਤਾਵਰਣ",
    soilType: "ਮਿੱਟੀ ਦੀ ਕਿਸਮ",
    soilPH: "ਮਿੱਟੀ pH",
    soilEC: "ਮਿੱਟੀ EC [dS/m]",
    ecOptions: {
      Low: "ਘੱਟ [0 - 0.8]",
      Medium: "ਮੱਧਮ [0.8 - 2.0]",
      High: "ਵੱਧ [> 2.0]"
    },
    landTopo: "ਜ਼ਮੀਨ ਦੀ ਬਣਾਵਟ",
    landTopoOptions: {
      flat: "ਸਮਤਲ",
      sloped: "ਢਲਾਨ ਵਾਲੀ",
      undulating: "ਲਹਿਰਦਾਰ",
      terraced: "ਸੀੜੀਵਾਰ"
    },
    landFinInfo: "ਜ਼ਮੀਨ ਅਤੇ ਵਿੱਤੀ ਜਾਣਕਾਰੀ",
    budgetOptions: {
      Low: "ਘੱਟ (₹0 - ₹50,000)",
      Medium: "ਮੱਧਮ (₹50,001 - ₹2,00,000)",
      High: "ਵੱਧ (> ₹2,00,000)"
    },
    landArea: "ਜ਼ਮੀਨ ਖੇਤਰ (ਏਕੜ)",
    budget: "ਬਜਟ",
    labor: "ਮਜ਼ਦੂਰ ਉਪਲਬਧਤਾ",
    farmPractices: "ਖੇਤੀਬਾੜੀ ਅਭਿਆਸ ਅਤੇ ਚੁਣੌਤੀਆਂ",
    irrigation: "ਸਿੰਚਾਈ ਪ੍ਰਣਾਲੀ",
    irrigationOptions: {
      Flood: "ਬाढ़",
      Drip: "ਡ੍ਰਿਪ",
      Sprinkler: "ਸਪ੍ਰਿੰਕਲਰ",
      Canal: "ਨਹਿਰ",
      Well: "ਕੂਆਂ",
      Rainfed: "ਬਰਸਾਤੀ"
    },
    fertilizer: "ਖਾਦ ਵਰਤੀ ਗਈ",
    pestDisease: "ਕੀੜੇ ਅਤੇ ਬਿਮਾਰੀ ਸਮੱਸਿਆਵਾਂ",
    submit: "ਜਮ੍ਹਾ ਕਰੋ",
    back: "ਵਾਪਸ",
    recommendCropPlan: "🌾 ਸਿਫਾਰਸ਼ ਕੀਤੀ ਫਸਲ ਯੋਜਨਾ",
    suitabilityScore: "ਉਚਿਤਤਾ ਸਕੋਰ",
    cropDetails: "ਫਸਲ ਵੇਰਵੇ",
    selectOption: "-- ਇੱਕ ਚੋਣ ਕਰੋ --",
    landAreaPlaceholder: "ਜ਼ਮੀਨ ਖੇਤਰ ਦਰਜ ਕਰੋ...",
    fertilizerPlaceholder: "ਖਾਦ ਦਰਜ ਕਰੋ...",
    pestDiseasePlaceholder: "ਸਮੱਸਿਆਵਾਂ ਦਰਜ ਕਰੋ...",
    laborPlaceholder: "ਜਿਵੇਂ 3 ਮਜ਼ਦੂਰ/ਦਿਨ",
    loading: "ਜਮ੍ਹਾਂ ਹੋ ਰਿਹਾ ਹੈ...",
    recommendedCrop: "ਸਿਫਾਰਸ਼ ਕੀਤੀ ਫਸਲ",
    noReport: "ਕੋਈ ਰਿਪੋਰਟ ਤਿਆਰ ਨਹੀਂ ਕੀਤੀ ਗਈ।",
    farmingPracticesChallenges: "ਖੇਤੀ ਪ੍ਰਥਾਵਾਂ ਅਤੇ ਚੁਣੌਤੀਆਂ",
    financialInfo: "ਜ਼ਮੀਨ ਅਤੇ ਵਿੱਤੀ ਜਾਣਕਾਰੀ",
    soilPHRange: "ਮਿੱਟੀ ਦਾ pH ਸੀਮਾ",
    temperatureRange: "ਤਾਪਮਾਨ ਸੀਮਾ",
    rainfallRequirement: "ਵਰਖਾ ਦੀ ਲੋੜ",
    irrigation: "ਸਿੰਚਾਈ",
    aiCropPlanReport: "AI ਫਸਲ ਯੋਜਨਾ ਰਿਪੋਰਟ"
  },

  marathi: {
    title: "🌱 पिक नियोजक",
    soilTypeOptions: {
      Loamy: "दोमट",
      Clay: "चिकण",
      Sandy: "वालुकामय",
      Silty: "गाळयुक्त"
    },
    subtitle: "हवामान, हंगाम आणि AI शिफारसींवर आधारित तुमच्या पिकांचे नियोजन करा.",
    farmingLocationEnv: "शेतीचे ठिकाण आणि वातावरण",
    soilType: "मातीचा प्रकार",
    soilPH: "मातीचा pH",
    soilEC: "माती EC [dS/m]",
    ecOptions: {
      Low: "कमी [0 - 0.8]",
      Medium: "मध्यम [0.8 - 2.0]",
      High: "जास्त [> 2.0]"
    },
    landTopo: "जमिनीची भौगोलिक रचना",
    landTopoOptions: {
      flat: "सपाट",
      sloped: "उतार",
      undulating: "लहरी",
      terraced: "सिंचित/तिहेरी पायऱ्या"
    },
    landFinInfo: "जमीन आणि आर्थिक माहिती",
    budgetOptions: {
      Low: "कमी (₹0 - ₹50,000)",
      Medium: "मध्यम (₹50,001 - ₹2,00,000)",
      High: "जास्त (> ₹2,00,000)"
    },
    landArea: "जमिनीचे क्षेत्रफळ (एकर)",
    budget: "बजेट",
    labor: "मजूर उपलब्धता",
    farmPractices: "शेती पद्धती आणि आव्हाने",
    irrigation: "सिंचन पद्धती",
    irrigationOptions: {
      Flood: "पाणीपुरवठा",
      Drip: "ड्रिप",
      Sprinkler: "स्प्रिंकलर",
      Canal: "कालवा",
      Well: "विहीर",
      Rainfed: "पावसावर अवलंबून"
    },
    fertilizer: "वापरलेले खत",
    pestDisease: "कीड व रोग समस्या",
    submit: "सबमिट करा",
    back: "मागे",
    recommendCropPlan: "🌾 शिफारस केलेली पिक योजना",
    suitabilityScore: "योग्यतेचा स्कोर",
    cropDetails: "पिकाची माहिती",
    selectOption: "-- पर्याय निवडा --",
    landAreaPlaceholder: "जमिनीचे क्षेत्रफळ भरा...",
    fertilizerPlaceholder: "वापरलेली खते भरा...",
    pestDiseasePlaceholder: "कीड/रोग समस्या भरा...",
    laborPlaceholder: "उदा., ३ कामगार / दिवस",
    loading: "सबमिट करत आहोत...",
    recommendedCrop: "शिफारस केलेले पीक",
    noReport: "अहवाल तयार केलेला नाही.",
    farmingPracticesChallenges: "शेती पद्धती आणि आव्हाने",
    financialInfo: "जमीन आणि आर्थिक माहिती",
    oilPHRange: "मातीचा pH श्रेणी",
    temperatureRange: "तापमान श्रेणी",
    rainfallRequirement: "पावसाचे प्रमाण आवश्यक",
    irrigation: "सिंचन",
    aiCropPlanReport: "एआय पिक नियोजन अहवाल"
  },
  
};


  const navigate = useNavigate();
  const location = useLocation();
  const { lat, lon, language } = location.state || {};
  const t = translations[language || "english"];
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [formData, setFormData] = useState({
    soilType: "",
    soilPH: 7,
    soilEC: "",
    landTopo: "",
    landArea: "",
    budget: "",
    labor: "",
    irrigation: "",
    fertilizer: "",
    pestDisease: "",
    lat: lat || 0, // fallback to 0
    lon: lon || 0, // fallback to 0
    language: language || "english", // fallback to English
  });

  const [responseData, setResponseData] = useState(null);

  const toggleSection = (section) => {
    setExpanded(expanded === section ? null : section);
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === "number" || name === "soilPH" ? Number(value) : value,
    });
  };

  const handleSubmit = async () => {
    try {
      console.log(formData);
      const res = await fetch("http://127.0.0.1:5000/recommend-crop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      console.log("Form Data:", formData);
      console.log(`Response Data: ${JSON.stringify(data)}`);
      setResponseData(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const AccordionHeader = ({ section, title }) => (
    <button
      className={`accordion-header ${expanded === section ? "active" : ""}`}
      onClick={() => toggleSection(section)}
    >
      <span>{title}</span>
      <span className={`arrow ${expanded === section ? "rotate" : ""}`}>▶</span>
    </button>
  );

  return (
    <div className="crop-container">
      <h1>{t.title}</h1>
      <p>{t.subtitle}</p>

      {/* Farming Location and Environment */}
      <div className="accordion">
        <AccordionHeader section={1} title={t.farmingLocationEnv} />
        {expanded === 1 && (
          <div className="accordion-content">
            <label>{t.soilType}:</label>
            <select name="soilType" value={formData.soilType} onChange={handleChange}>
              <option value="">{t.selectOption}</option>
              <option value="Loamy soil">{t.soilTypeOptions.Loamy}</option>
              <option value="Sandy soil">{t.soilTypeOptions.Sandy}</option>
              <option value="Clay soil">{t.soilTypeOptions.Clay}</option>
              <option value="Silty soil">{t.soilTypeOptions.Silty}</option>
            </select>

            <label>{t.soilPH}: {formData.soilPH}</label>
            <input
              type="range"
              min="0"
              max="14"
              step="0.1"
              name="soilPH"
              value={formData.soilPH}
              onChange={handleChange}
            />

            <label>{t.soilEC}:</label>
            <select name="soilEC" value={formData.soilEC} onChange={handleChange}>
              <option value="">{t.selectOption}</option>
              <option value="Low (0-0.8 ds/m)">{t.ecOptions.Low}</option>
              <option value="Medium (0.8-1.2 ds/m)">{t.ecOptions.Medium}</option>
              <option value="High (>2.0 ds/m)">{t.ecOptions.High}</option>
            </select>

            <label>{t.landTopo}:</label>
            <select name="landTopo" value={formData.landTopo} onChange={handleChange}>
              <option value="">{t.selectOption}</option>
              <option value="Flat">{t.landTopoOptions.flat}</option>
              <option value="Sloped">{t.landTopoOptions.sloped}</option>
              <option value="Undulating">{t.landTopoOptions.undulating}</option>
              <option value="Terraced">{t.landTopoOptions.terraced}</option>
            </select>
          </div>
        )}
      </div>

      {/* Land and Financial Information */}
      <div className="accordion">
        <AccordionHeader section={2} title={t.financialInfo} />
        {expanded === 2 && (
          <div className="accordion-content">
            <label>{t.landArea}:</label>
            <input type="number" name="landArea" placeholder={t.landAreaPlaceholder} value={formData.landArea} onChange={handleChange} step={1} min={0} />

            <label>{t.budget}:</label>
            <select name="budget" value={formData.budget} onChange={handleChange}>
              <option value="">{t.selectOption}</option>
              <option value="Low (₹0 - ₹50,000)">{t.budgetOptions.Low}</option>
              <option value="Medium (₹50,001 - ₹2,00,000)">{t.budgetOptions.Medium}</option>
              <option value="High (>₹2,00,000)">{t.budgetOptions.High}</option>
            </select>

            <label>{t.labor}:</label>
            <input type="text" name="labor" value={formData.labor} onChange={handleChange} />
          </div>
        )}
      </div>

      {/* Farming Practices and Challenges */}
      <div className="accordion">
        <AccordionHeader section={3} title={t.farmingPracticesChallenges} />
        {expanded === 3 && (
          <div className="accordion-content">
            <label>{t.irrigation}:</label>
            <select name="irrigation" value={formData.irrigation} onChange={handleChange}>
              <option value="">{t.selectOption}</option>
              <option value="Flood">{t.irrigationOptions.Flood}</option>
              <option value="Drip">{t.irrigationOptions.Drip}</option>
              <option value="Sprinkler">{t.irrigationOptions.Sprinkler}</option>
              <option value="Canal">{t.irrigationOptions.Canal}</option>
              <option value="Well">{t.irrigationOptions.Well}</option>
              <option value="Rainfed">{t.irrigationOptions.Rainfed}</option>
            </select>

            <label>{t.fertilizer}:</label>
            <input type="text" name="fertilizer" placeholder={t.fertilizerPlaceholder} value={formData.fertilizer} onChange={handleChange} />

            <label>{t.pestDisease}:</label>
            <input type="text" name="pestDisease" placeholder={t.pestDiseasePlaceholder} value={formData.pestDisease} onChange={handleChange} />
          </div>
        )}
      </div>

      <button className="submit-btn" onClick={handleSubmit}>{t.submit}</button>
      <button className="back-btn" onClick={() => navigate("/")}>{t.back}</button>

      {responseData && (
        <div className="api-response">
          <h2>{t.recommendedCropPlan}</h2>

          {/* Recommended Crop */}
          <div className="crop-card">
            <h3>{responseData.recommended_crop_details?.crop_name || "Suitable crop not found"}</h3>
            <p>{responseData.message}</p>
          </div>

          {/* Suitability Score */}
          <div className="score-section">
            <label>{t.suitabilityScore}:</label>
            <div className="progress-bar">
              <div
                className="progress"
                style={{ width: `${Math.min(responseData.suitability_score || 0, 100)}%` }}
              ></div>
            </div>
            <span>
              {responseData.suitability_score !== undefined && responseData.suitability_score !== null
                ? responseData.suitability_score.toFixed(2)
                : "N/A"} / 100
            </span>
          </div>

          {/* Crop Details */}
          <div className="details">
            <h4>{t.cropDetails}</h4>
            <ul>
              <li>
                <strong>{t.soilType}:</strong> {Array.isArray(responseData.recommended_crop_details?.soil_type)
                  ? responseData.recommended_crop_details.soil_type.join(", ")
                  : responseData.recommended_crop_details?.soil_type || "N/A"}
              </li>
              <li><strong>{t.soilPHRange}:</strong> {responseData.recommended_crop_details?.soil_ph_min} - {responseData.recommended_crop_details?.soil_ph_max}</li>
              <li><strong>{t.temperatureRange}:</strong> {responseData.recommended_crop_details?.min_temperature} - {responseData.recommended_crop_details?.max_temperature}</li>
              <li><strong>{t.rainfallRequirement}:</strong> {responseData.recommended_crop_details?.min_rainfall} - {responseData.recommended_crop_details?.max_rainfall}</li>
              <li>
                <strong>{t.irrigation}:</strong> {typeof responseData.recommended_crop_details?.irrigation?.general === "string"
                  ? responseData.recommended_crop_details.irrigation.general
                  : JSON.stringify(responseData.recommended_crop_details?.irrigation?.general || "N/A")}
              </li>
            </ul>
          </div>

          {/* AI Crop Plan Report */}
          <div className="report">
            <h4>📋 {t.aiCropPlanReport}</h4>
            <div className="report-box">
              {responseData.crop_plan_report || "No report generated."}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default CropPlanner;
