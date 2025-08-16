import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../../App.css";
import "../CropPlanner/CropPlanner.css";

function CropPlanner() {
  const navigate = useNavigate();
  const location = useLocation();
  const { lat, lon } = location.state || {};
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
    lat: lat,
    lon: lon
  });
    const [responseData, setResponseData] = useState(null);

  const toggleSection = (section) => {
    setExpanded(expanded === section ? null : section);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async () => {
    try {
      // const res = await fetch("/api/crop-data", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify(formData),
      // });
      // const data = await res.json();
      console.log("Form Data:", formData);
      const data = { message: "Success" };
      setResponseData(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const AccordionHeader = ({ section, title }) => (
    <button className={`accordion-header ${expanded === section ? "active" : ""}`} onClick={() => toggleSection(section)}>
      <span>{title}</span>
      <span className="arrow">▶</span>
    </button>
  );

  return (
    <div className="crop-container">
      <h1>🌱 Crop Planner</h1>
      <p>Plan your crops based on climate, season & AI recommendations.</p>

      {/* Farming Location and Environment */}
      <div className="accordion">
        <AccordionHeader section={1} title="Farming Location and Environment" />
        {expanded === 1 && (
          <div className="accordion-content">
            <label>Soil Type:</label>
            <select name="soilType" value={formData.soilType} onChange={handleChange}>
              <option value="">Select</option>
              <option value="Clay">Clay</option>
              <option value="Loam">Loam</option>
              <option value="Sandy">Sandy</option>
            </select>

            <label>Soil pH: {formData.soilPH}</label>
            <input type="range" min="0" max="14" step="0.1" name="soilPH" value={formData.soilPH} onChange={handleChange} />

            <label>Soil EC:</label>
            <input type="number" step="0.01" name="soilEC" value={formData.soilEC} onChange={handleChange} />

            <label>Land Topography:</label>
            <input type="text" name="landTopo" value={formData.landTopo} onChange={handleChange} />
          </div>
        )}
      </div>

      {/* Land and Financial Information */}
      <div className="accordion">
        <AccordionHeader section={2} title="Land and Financial Information" />
        {expanded === 2 && (
          <div className="accordion-content">
            <label>Land Area (acres):</label>
            <input type="number" name="landArea" value={formData.landArea} onChange={handleChange} />

            <label>Budget:</label>
            <input type="number" name="budget" value={formData.budget} onChange={handleChange} />

            <label>Labor Availability:</label>
            <input type="text" name="labor" value={formData.labor} onChange={handleChange} />
          </div>
        )}
      </div>

      {/* Farming Practices and Challenges */}
      <div className="accordion">
        <AccordionHeader section={3} title="Farming Practices and Challenges" />
        {expanded === 3 && (
          <div className="accordion-content">
            <label>Irrigation System:</label>
            <select name="irrigation" value={formData.irrigation} onChange={handleChange}>
              <option value="">Select</option>
              <option value="Flood">Flood</option>
              <option value="Drip">Drip</option>
              <option value="Sprinkler">Sprinkler</option>
            </select>

            <label>Fertilizer Used:</label>
            <input type="text" name="fertilizer" value={formData.fertilizer} onChange={handleChange} />

            <label>Pest & Disease Issues:</label>
            <input type="text" name="pestDisease" value={formData.pestDisease} onChange={handleChange} />
          </div>
        )}
      </div>

      <button className="submit-btn" onClick={handleSubmit}>Submit</button>
      <button className="back-btn" onClick={() => navigate("/")}>Back</button>

      {responseData && (
        <div className="api-response">
          <h3>Recommendation</h3>
          <pre>{JSON.stringify(responseData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default CropPlanner;
