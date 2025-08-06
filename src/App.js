import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import MapModal from './MapModal';

// Fetch weather using Open-Meteo API
const fetchWeather = async (lat, lon) => {
  try {
    const response = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=precipitation,soil_moisture_0_to_1cm,evapotranspiration`
    );
    const data = await response.json();

    return {
      temperature: data.current_weather.temperature,
      windspeed: data.current_weather.windspeed,
      precipitation: data.hourly.precipitation?.[0] ?? "N/A",
      soilMoisture: data.hourly.soil_moisture_0_to_1cm?.[0] ?? "N/A",
      evapotranspiration: data.hourly.evapotranspiration?.[0] ?? "N/A"
    };
  } catch (error) {
    console.error("Error fetching weather:", error);
    return null;
  }
};


function App() {
  const [activeButton, setActiveButton] = useState('Button1');
  const [showAddFarmModal, setShowAddFarmModal] = useState(false);
  const [farms, setFarms] = useState([]);
  const [weatherData, setWeatherData] = useState(null);

  const [farmName, setFarmName] = useState('');
  const [farmSize, setFarmSize] = useState('');
  const [farmLocation, setFarmLocation] = useState('');
  const [soilType, setSoilType] = useState('');
  const [farmImage, setFarmImage] = useState(null);
  const [predictedSoilType, setPredictedSoilType] = useState('');
  const [imagePreview, setImagePreview] = useState('');

  const [showMapModal, setShowMapModal] = useState(false);
  const [coordinates, setCoordinates] = useState(null);

  // When coordinates are selected, fetch location + weather
  useEffect(() => {
    const fetchLocationAndWeather = async () => {
      if (coordinates) {
        const { lat, lng } = coordinates;

        // Get human-readable location
        const locationRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
        const locationData = await locationRes.json();

        const locationName =
          locationData.address.city ||
          locationData.address.town ||
          locationData.address.village ||
          locationData.display_name;

        setFarmLocation(locationName);

        // Fetch actual weather data
        const weather = await fetchWeather(lat, lng);

        if (weather) {
          setWeatherData({
            temperature: `${weather.temperature} °C`,
            windSpeed: `${weather.windspeed} km/h`,
            precipitation: `${weather.precipitation} mm`,
            soilMoisture: `${weather.soilMoisture} %`,
            evapotranspiration: `${weather.evapotranspiration} mm`,
            location: locationName
          });
        }
      }
    };

    fetchLocationAndWeather();
  }, [coordinates]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFarmImage(file);

      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        setTimeout(() => {
          const soilTypes = ['Clay', 'Sandy', 'Loamy', 'Peaty', 'Silty'];
          const randomType = soilTypes[Math.floor(Math.random() * soilTypes.length)];
          setPredictedSoilType(randomType);
          setSoilType(randomType);
        }, 1000);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAddFarm = () => {
    if (!farmName || !farmSize || !farmLocation || !soilType) {
      alert('Please fill all fields');
      return;
    }

    const newFarm = {
      id: Date.now(),
      name: farmName,
      size: farmSize,
      location: farmLocation,
      soilType: soilType,
      image: farmImage?.name || ''
    };

    setFarms([...farms, newFarm]);

    // Reset form
    setFarmName('');
    setFarmSize('');
    setFarmLocation('');
    setSoilType('');
    setFarmImage(null);
    setImagePreview('');
    setPredictedSoilType('');
    setShowAddFarmModal(false);

    alert('Farm added successfully!');
  };

  return (
    <div className="app-container">
      {/* NAV */}
      <div className="navigation">
        <button onClick={() => setActiveButton('Button1')}>Button1</button>
        <button onClick={() => setActiveButton('Button2')}>Button2</button>
        <button onClick={() => setActiveButton('Button3')}>Button3</button>
      </div>

      <div className="main-content">
        {/* HEADER */}
        <div className="header">
          <h1>Farm Management Dashboard</h1>
          <button className="add-farm-btn" onClick={() => setShowAddFarmModal(true)}>+ Add Farm</button>
        </div>

        {/* WEATHER CARD */}
        {weatherData && (
          <div className="farm-card">
            <div className="weather-card">
              <div className="weather-header">
                <h2>Weather Details</h2>
                <span>Location: {weatherData.location}</span>
              </div>
              <div className="weather-box">
                <div className="weather-item">
                  <h3>🌡️ Temperature (°C)</h3>
                  <p>{weatherData.temperature}</p>
                </div>
                <div className="weather-item">
                  <h3>💧 Rainfall (mm)</h3>
                  <p>{weatherData.precipitation}</p>
                </div>
                <div className="weather-item">
                  <h3>🪨 Soil Moisture (%)</h3>
                  <p>{weatherData.soilMoisture}</p>
                </div>
                <div className="weather-item">
                  <h3>☀️ Evapotranspiration (mm)</h3>
                  <p>{weatherData.evapotranspiration}</p>
                </div>
                <div className="weather-item">
                  <h3>💨 Wind Speed (km/h)</h3>
                  <p>{weatherData.windSpeed}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* FARMS */}
        <div>
          {farms.length > 0 ? (
            <div>
              <h2>Your Farms</h2>
              {farms.map(farm => (
                <div key={farm.id} className="farm-card">
                  <div className="weather-card">
                    <h3>{farm.name}</h3>
                    <p>Size: {farm.size} acres</p>
                    <p>Location: {farm.location}</p>
                    <p>Soil Type: {farm.soilType}</p>
                    {farm.image && (
                      <div className="farm-image-preview">
                        <img src={imagePreview || 'https://placehold.co/400x300'} alt={`Farm ${farm.name}`} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="farm-card">
              <div className="weather-card">
                <p>No farms added yet. Click "Add Farm" to get started.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MODAL */}
      {showAddFarmModal && (
        <div className="modal">
          <div className="modal-content">
            <h2>Add New Farm</h2>

            <div className="form-group">
              <label>Farm Name</label>
              <input value={farmName} onChange={e => setFarmName(e.target.value)} placeholder="Enter farm name" />
            </div>

            <div className="form-group">
              <label>Farm Size (acres)</label>
              <input type="number" value={farmSize} onChange={e => setFarmSize(e.target.value)} placeholder="Enter farm size" />
            </div>

            <div className="form-group">
              <label>Location</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input type="text" value={farmLocation} readOnly placeholder="Pick from map" />
                <button className="btn btn-secondary" onClick={() => setShowMapModal(true)}>📍 Pick</button>
              </div>
            </div>

            <div className="form-group">
              <label>Farm Image</label>
              <input type="file" onChange={handleImageChange} accept="image/*" />
              {imagePreview && (
                <div className="farm-image-preview">
                  <img src={imagePreview} alt="Uploaded preview" />
                </div>
              )}
            </div>

            {predictedSoilType && (
              <div className="soil-prediction">Predicted Soil Type: {predictedSoilType}</div>
            )}

            <div className="form-group">
              <label>Soil Type</label>
              <select value={soilType} onChange={e => setSoilType(e.target.value)}>
                <option value="">Select soil type</option>
                <option value="Clay">Clay</option>
                <option value="Sandy">Sandy</option>
                <option value="Loamy">Loamy</option>
                <option value="Peaty">Peaty</option>
                <option value="Silty">Silty</option>
              </select>
            </div>

            <div className="form-actions">
              <button className="btn btn-secondary" onClick={() => setShowAddFarmModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleAddFarm}>Add Farm</button>
            </div>
          </div>
        </div>
      )}

      {/* MAP MODAL */}
      {showMapModal && (
        <MapModal
          setCoordinates={setCoordinates}
          closeModal={() => setShowMapModal(false)}
        />
      )}
    </div>
  );
}

export default App;
