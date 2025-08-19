import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FaMicrophone, FaMicrophoneSlash } from "react-icons/fa";
import axios from "axios";
import "../../App.css";
import "../Schemes/Schemes.css";

function Schemes() {

  const translations = {
    english: {
      title: "🏛 Government Schemes",
      description: "View agriculture-related schemes and subsidies available for your region.",
      inputPlaceholder: "Describe your needs...",
      submit: "Submit",
      back: "⬅ Back",
      loading: "Loading...",
      schemeName: "Scheme Name",
      reason: "Reason",
      link: "Link",
      checkEligibility: "Check Eligibility",
      submitEligibility: "Submit Eligibility",
      recommendationTitle: "Recommendation",
      linkText: "Link",
      alertEnterNeeds: "Please enter your needs",
      alertFetchError: "Error fetching schemes",
      alertEligibilityError: "Error fetching eligibility questions",
      alertCheckError: "Error checking eligibility",
      yes: "Yes", no: "No" 
    },
    hindi: {
      title: "🏛 सरकारी योजनाएँ",
      description: "अपने क्षेत्र में उपलब्ध कृषि संबंधित योजनाओं और सब्सिडी देखें।",
      inputPlaceholder: "अपनी आवश्यकताओं का विवरण दें...",
      submit: "जमा करें",
      back: "⬅ वापस",
      loading: "लोड हो रहा है...",
      schemeName: "योजना का नाम",
      reason: "कारण",
      link: "लिंक",
      checkEligibility: "पात्रता जाँचें",
      submitEligibility: "पात्रता जमा करें",
      recommendationTitle: "सिफ़ारिश",
      linkText: "लिंक",
      alertEnterNeeds: "कृपया अपनी आवश्यकताएँ दर्ज करें",
      alertFetchError: "योजनाएँ लाने में त्रुटि",
      alertEligibilityError: "पात्रता प्रश्न लाने में त्रुटि",
      alertCheckError: "पात्रता जाँच में त्रुटि",
      yes: "हाँ", no: "नहीं" 
    },
    tamil: {
      title: "🏛 அரசு திட்டங்கள்",
      description: "உங்கள் பிரதேசத்திற்கு கிடைக்கக்கூடிய விவசாய தொடர்புடைய திட்டங்கள் மற்றும் உதவித்தொகைகளைப் பார்க்கவும்.",
      inputPlaceholder: "உங்கள் தேவைகளை விவரிக்கவும்...",
      submit: "சமர்ப்பிக்கவும்",
      back: "⬅ பின்னுக்கு",
      loading: "போடுகிறது...",
      schemeName: "திட்டத்தின் பெயர்",
      reason: "காரணம்",
      link: "இணைப்பு",
      checkEligibility: "தகுதி சரிபார்க்கவும்",
      submitEligibility: "தகுதி சமர்ப்பிக்கவும்",
      recommendationTitle: "பரிந்துரை",
      linkText: "இணைப்பு",
      alertEnterNeeds: "தயவுசெய்து உங்கள் தேவைகளை உள்ளிடவும்",
      alertFetchError: "திட்டங்களை பெறுவதில் பிழை",
      alertEligibilityError: "தகுதி கேள்விகளை பெறுவதில் பிழை",
      alertCheckError: "தகுதியை சரிபார்ப்பதில் பிழை",
      yes: "ஆம்", no: "இல்லை"
    },
    telugu: {
      title: "🏛 ప్రభుత్వ పథకాలు",
      description: "మీ ప్రాంతంలో అందుబాటులో ఉన్న వ్యవసాయ సంబంధిత పథకాలు మరియు సబ్సిడీలను వీక్షించండి.",
      inputPlaceholder: "మీ అవసరాలను వివరించండి...",
      submit: "సమర్పించండి",
      back: "⬅ వెనక్కి",
      loading: "లోడింగ్...",
      schemeName: "యోజన పేరు",
      reason: "కారణం",
      link: "లింక్", 
      checkEligibility: "అర్హతను తనిఖీ చేయండి",
      submitEligibility: "అర్హత సమర్పించండి",
      recommendationTitle: "సిఫార్సు",
      linkText: "లింక్",
      alertEnterNeeds: "దయచేసి మీ అవసరాలను నమోదు చేయండి",
      alertFetchError: "పథకాలను పొందడంలో లోపం",
      alertEligibilityError: "అర్హత ప్రశ్నలను పొందడంలో లోపం",
      alertCheckError: "అర్హత తనిఖీలో లోపం",
      yes: "అవును", no: "కాదు" 
    },
    punjabi: {
      title: "🏛 ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ",
      description: "ਆਪਣੇ ਖੇਤਰ ਲਈ ਉਪਲਬਧ ਖੇਤੀ-ਸਬੰਧੀ ਯੋਜਨਾਵਾਂ ਅਤੇ ਸਬਸਿਡੀਆਂ ਵੇਖੋ।",
      inputPlaceholder: "ਆਪਣੀਆਂ ਜ਼ਰੂਰਤਾਂ ਬਿਆਨ ਕਰੋ...",
      submit: "ਜਮ੍ਹਾ ਕਰੋ",
      back: "⬅ ਵਾਪਸ",
      loading: "ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...",
      schemeName: "ਯੋਜਨਾ ਦਾ ਨਾਮ",
      reason: "ਕਾਰਣ",
      link: "ਲਿੰਕ",
      checkEligibility: "ਅਰਹਿਤਾ ਚੈੱਕ ਕਰੋ",
      submitEligibility: "ਅਰਹਿਤਾ ਜਮ੍ਹਾਂ ਕਰੋ",
      recommendationTitle: "ਸਿਫਾਰਸ਼",
      linkText: "ਲਿੰਕ",
      alertEnterNeeds: "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀਆਂ ਜ਼ਰੂਰਤਾਂ ਦਰਜ ਕਰੋ",
      alertFetchError: "ਯੋਜਨਾਵਾਂ ਲਿਆਉਣ ਵਿੱਚ ਗਲਤੀ",
      alertEligibilityError: "ਅਰਹਿਤਾ ਪ੍ਰਸ਼ਨਾਂ ਨੂੰ ਲਿਆਉਣ ਵਿੱਚ ਗਲਤੀ",
      alertCheckError: "ਅਰਹਿਤਾ ਜਾਂਚਣ ਵਿੱਚ ਗਲਤੀ",
      yes: "ਹਾਂ", no: "ਨਹੀਂ"
    },
    marathi: {
      title: "🏛 सरकारी योजना",
      description: "आपल्या क्षेत्रासाठी उपलब्ध कृषी-संबंधित योजना आणि सबसिडी पहा.",
      inputPlaceholder: "आपल्या गरजांचा तपशील द्या...",
      submit: "सबमिट करा",
      back: "⬅ मागे",
      loading: "लोड करत आहे...",
      schemeName: "योजनेचे नाव",
      reason: "कारण",
      link: "दुवा",
      checkEligibility: "अर्हता तपासा",
      submitEligibility: "अर्हता सबमिट करा",
      recommendationTitle: "शिफारस",
      linkText: "लिंक",
      alertEnterNeeds: "कृपया आपल्या गरजा प्रविष्ट करा",
      alertFetchError: "योजना आणण्यात त्रुटी",
      alertEligibilityError: "अर्हता प्रश्न आणण्यात त्रुटी",
      alertCheckError: "अर्हता तपासण्यात त्रुटी",
      yes: "होय", no: "नाही" 
    }
};

  const API_URL = process.env.REACT_APP_API_URL;
  const navigate = useNavigate();
  const location = useLocation();
  const { stateName, language } = location.state || {};
  const t = translations[language || "english"];
  const [inputText, setInputText] = useState("");
  const [schemes, setSchemes] = useState(null);
  const [loadingSubmit, setLoadingSubmit] = useState(false);
  const [loadingCheck, setLoadingCheck] = useState(false);
  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [eligibilityQuestions, setEligibilityQuestions] = useState(null);
  const [responses, setResponses] = useState({});
  const [recommendation, setRecommendation] = useState(null);

  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  // Initialize Speech Recognition
useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;

    switch (language) {
      case "hindi": recognitionRef.current.lang = "hi-IN"; break;
      case "tamil": recognitionRef.current.lang = "ta-IN"; break;
      case "telugu": recognitionRef.current.lang = "te-IN"; break;
      case "punjabi": recognitionRef.current.lang = "pa-IN"; break;
      case "marathi": recognitionRef.current.lang = "mr-IN"; break;
      default: recognitionRef.current.lang = "en-US";
    }

    recognitionRef.current.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInputText(transcript);
    };

    recognitionRef.current.onend = () => {
      if (listening) recognitionRef.current.start();
    };
  }, [language]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    if (!listening) {
      recognitionRef.current.start();
    } else {
      recognitionRef.current.stop();
    }
    setListening(prev => !prev);
  };

  const handleSubmit = async () => {
    if (!inputText.trim()) return alert(t.alertEnterNeeds);
    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      setListening(false);
    }
    setLoadingSubmit(true);
    try {
      const response = await axios.post(
        `${API_URL}/rec_schemes`,
        { location: stateName, query: inputText, top_k: 3, language },
        { withCredentials: true }
      );
      setSchemes(response.data);
    } catch (err) {
      console.error(err);
      alert(t.alertFetchError);
    } finally {
      setLoadingSubmit(false);
      // ensure microphone is muted after submit
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        setListening(false);
      }
    }
  };
  const checkEligibility = async () => {
    if (!schemes) return;
    setLoadingCheck(true);
    try {
      const response = await axios.post(
        `${API_URL}/questions`,
        {
          rec_scheme: schemes,
          language: language,
        },
        {
          withCredentials: true, // 👈 correct place
        }
      );
      const questions = response.data;

      const defaultResponses = {};
      Object.entries(questions).forEach(([schemeName, questionSet]) => {
        defaultResponses[schemeName] = {};
        Object.entries(questionSet).forEach(([question, data]) => {
          defaultResponses[schemeName][question] = { answer: "No" };
          if (data.follow_ups) {
            defaultResponses[schemeName][question].follow_ups = {};
            Object.keys(data.follow_ups).forEach((fq) => {
              defaultResponses[schemeName][question].follow_ups[fq] = "No";
            });
          }
        });
      });
      setResponses(defaultResponses);
      setEligibilityQuestions(questions);
    } catch (err) {
      console.error(err);
      alert("Error fetching eligibility questions");
    } finally {
      setLoadingCheck(false);
    }
  };

  const handleResponse = (scheme, question, answer) => {
    setResponses((prev) => ({
      ...prev,
      [scheme]: {
        ...prev[scheme],
        [question]: { ...prev[scheme]?.[question], answer },
      },
    }));
  };

  const handleFollowUpResponse = (scheme, question, followQ, answer) => {
    setResponses((prev) => ({
      ...prev,
      [scheme]: {
        ...prev[scheme],
        [question]: {
          ...prev[scheme]?.[question],
          follow_ups: {
            ...prev[scheme]?.[question]?.follow_ups,
            [followQ]: answer,
          },
        },
      },
    }));
  };

  const submitEligibility = async () => {
    setLoadingEligibility(true);
    try {
      const response = await axios.post(`${API_URL}/check_schemes`, {
        exp_qa: eligibilityQuestions,
        user_qa: responses,
      });
      setRecommendation(response.data);
    } catch (err) {
      console.error(err);
      alert("Error checking eligibility");
    } finally {
      setLoadingEligibility(false);
    }
  };

  return (
    <div className="page-container">
      <h1>{t.title}</h1>
      <p style={{ width: "95%", margin: "0 25px 10px", padding: "10px" }}>
        {t.description}
      </p>
      <div style={{ position: "relative", width: "100%" }}>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={t.inputPlaceholder}
          rows={4}
          style={{ width: "95%", margin: "0 25px 10px", padding: "10px" }}
        />

        <button
            onClick={toggleListening}
            style={{
              position: "absolute",
              right: "5px",
              top: "20%",
              transform: "translateY(-50%)",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              fontSize: "20px",
              color: listening ? "black" : "red"
            }}
          >
            {listening ? <FaMicrophone /> : <FaMicrophoneSlash />}
          </button>
      </div>
      <div className="button-row">
        <button className="submit-btn" onClick={handleSubmit} disabled={loadingSubmit}>
          {loadingSubmit ? t.loading : t.submit}
        </button>
        <button className="back-btn" onClick={() => navigate("/")}>{t.back}</button>
      </div>

      {schemes && (
        <div style={{ marginTop: "20px" }}>
          <table style={{ borderCollapse: "collapse", width: "95%", marginLeft: "25px" }}>
            <thead>
              <tr>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>#</th>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>{t.schemeName}</th>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>{t.reason}</th>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>{t.link}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(schemes).map(([schemeName, details], idx) => (
                <tr key={idx}>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>{idx + 1}</td>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>{schemeName}</td>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>{details.Reason}</td>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>
                    <a href={details.URL} target="_blank" rel="noreferrer">{t.link}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="submit-btn"
            style={{ marginLeft: "50px", marginTop: "15px" }}
            onClick={checkEligibility}
            disabled={loadingCheck}
          >
            {loadingCheck ? t.loading : t.checkEligibility}
          </button>
        </div>
      )}

      {eligibilityQuestions && (
        <div className="eligibility-container">
          {Object.entries(eligibilityQuestions).map(([schemeName, questionSet], idx) => (
            <div key={idx} className="scheme-section">
              <h3>{schemeName}</h3>
              {Object.entries(questionSet).map(([question, data], qIdx) => (
                <div key={qIdx} className="question-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={responses[schemeName]?.[question]?.answer === "Yes"}
                      onChange={(e) =>
                        handleResponse(schemeName, question, e.target.checked ? "Yes" : "No")
                      }
                    />
                    {question}
                  </label>
                  {data.follow_ups && responses[schemeName]?.[question]?.answer === "Yes" && (
                    <div className="followup-list" style={{ marginLeft: "20px" }}>
                      {Object.entries(data.follow_ups).map(([followQ], fIdx) => (
                        <div key={fIdx} className="followup-item">
                          <label>
                            <input
                              type="checkbox"
                              checked={responses[schemeName]?.[question]?.follow_ups?.[followQ] === "Yes"}
                              onChange={(e) =>
                                handleFollowUpResponse(
                                  schemeName,
                                  question,
                                  followQ,
                                  e.target.checked ? "Yes" : "No"
                                )
                              }
                            />
                            {followQ}
                          </label>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
          <button
            className="submit-btn"
            style={{ marginLeft: "15px", marginTop: "15px" }}
            onClick={submitEligibility}
            disabled={loadingEligibility}
          >
            {loadingEligibility ? t.loading : t.submitEligibility}
          </button>
        </div>
      )}

      {recommendation && (
        <div className="recommendation-card">
          <h3 className="rec-title">{t.recommendationTitle}</h3>
          <div className="rec-list">
            {Object.entries(recommendation).map(([scheme, status]) => (
              <div key={scheme} className="rec-item">
                <span className="rec-scheme">{scheme}</span>
                <span className={`rec-status ${status === "Yes" ? "yes" : "no"}`}>
                  {status === "Yes" ? t.yes : t.no}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Schemes;
