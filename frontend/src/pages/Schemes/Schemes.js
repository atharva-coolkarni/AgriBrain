import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../../App.css";
import "../Schemes/Schemes.css";

function Schemes() {
  const navigate = useNavigate();
  const location = useLocation();
  const stateFromLocation = location.state?.stateName || "";
  const [inputText, setInputText] = useState("");
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [eligibilityQuestions, setEligibilityQuestions] = useState(null);
  const [responses, setResponses] = useState({});
  const [recommendation, setRecommendation] = useState(null);

  const handleSubmit = async () => {
    if (!inputText.trim()) return alert("Please enter your needs");
    setLoading(true);
    try {
      console.log("State from location:", stateFromLocation);
      const res = [
        { scheme: "PM-Kisan Samman Nidhi", url: "https://pmkisan.gov.in" },
        { scheme: "Kisan Credit Card", url: "https://www.nabard.org" }
      ];
      setSchemes(res);
    } catch (err) {
      console.error(err);
      alert("Error fetching schemes");
    }
    setLoading(false);
  };

  const checkEligibility = async () => {
    try {
      const mockQuestions = {
        "National Scheme of Welfare of Fishermen": {
          "Is the applicant a member of a functional local fishers cooperative society/Federation/any other registered body?": {
            answer: "Yes"
          },
          "Is the applicant Below Poverty Line (BPL)?": {
            answer: "Yes",
            follow_ups: {
              "Is the applicant between 18 and 60 years of age?": "Yes"
            }
          },
          "Is the beneficiary fisher willing to save Rs. 1500 over a period of 9 months during the fishing season annually towards their contribution with a bank designated by the State/UT Department of Fisheries?": {
            answer: "Yes"
          }
        }
      };
      // Initialize all responses to "No"
      const defaultResponses = {};
      Object.entries(mockQuestions).forEach(([schemeName, questionSet]) => {
        defaultResponses[schemeName] = {};
        Object.entries(questionSet).forEach(([question, data]) => {
          defaultResponses[schemeName][question] = { answer: "No" };
          if (data.follow_ups) {
            defaultResponses[schemeName][question].follow_ups = {};
            Object.keys(data.follow_ups).forEach(fq => {
              defaultResponses[schemeName][question].follow_ups[fq] = "No";
            });
          }
        });
      });
      setResponses(defaultResponses);
      setEligibilityQuestions(mockQuestions);
    } catch (err) {
      console.error(err);
    }
  };

  const handleResponse = (scheme, question, answer) => {
    setResponses(prev => ({
      ...prev,
      [scheme]: {
        ...prev[scheme],
        [question]: { ...prev[scheme]?.[question], answer }
      }
    }));
  };

  const handleFollowUpResponse = (scheme, question, followQ, answer) => {
    setResponses(prev => ({
      ...prev,
      [scheme]: {
        ...prev[scheme],
        [question]: {
          ...prev[scheme]?.[question],
          follow_ups: {
            ...prev[scheme]?.[question]?.follow_ups,
            [followQ]: answer
          }
        }
      }
    }));
  };

  const submitEligibility = async () => {
    try {
      console.log("Submitting eligibility responses:", responses);
      setRecommendation("You are eligible for PM-Kisan Samman Nidhi");
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="page-container">
      <h1>🏛 Government Schemes</h1>
      <p style={{ width: "95%", marginLeft: "25px", marginRight: "25px", padding: "10px", marginBottom: "10px" }}
        >View agriculture-related schemes and subsidies available for your region.</p>

      <textarea
        value={inputText}
        onChange={e => setInputText(e.target.value)}
        placeholder="Describe your needs..."
        rows={4}
        style={{ width: "95%", marginLeft: "25px", marginRight: "25px", padding: "10px", marginBottom: "10px" }}
      />

      <div className="button-row">
        <button className="submit-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? "Loading..." : "Submit"}
        </button>
        <button className="back-btn" onClick={() => navigate("/")}>⬅ Back</button>
      </div>

      {schemes.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>#</th>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>Scheme Name</th>
                <th style={{ border: "1px solid #ccc", padding: "8px" }}>Link</th>
              </tr>
            </thead>
            <tbody>
              {schemes.map((s, idx) => (
                <tr key={idx}>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>{idx + 1}</td>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>{s.scheme}</td>
                  <td style={{ border: "1px solid #ccc", padding: "8px" }}>
                    <a href={s.url} target="_blank" rel="noreferrer">{s.url}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className="submit-btn" style={{ marginLeft: "50px", marginTop: "15px" }} onClick={checkEligibility}>
            Check Eligibility
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
                      onChange={(e) => {
                        const ans = e.target.checked ? "Yes" : "No";
                        handleResponse(schemeName, question, ans);
                      }}
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
          <button className="submit-btn" style={{ marginLeft: "50px", marginTop: "15px" }} onClick={submitEligibility}>Submit Eligibility</button>
        </div>
      )}

      {recommendation && (
        <div style={{ marginTop: "20px", padding: "10px", background: "#e8f5e9", borderRadius: "8px" }}>
          <h3>Recommendation</h3>
          <p>{recommendation}</p>
        </div>
      )}
    </div>
  );
}

export default Schemes;
