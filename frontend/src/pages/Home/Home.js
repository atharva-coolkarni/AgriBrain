import axios from "axios";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import { FaLandmark, FaMapMarkerAlt, FaSeedling } from "react-icons/fa";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import "weather-icons/css/weather-icons.css";
import "../../App.css";
import logo from "../../assets/agribrain-logo.jpg";
import "../Home/Home.css";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function LocationMarker({ onSelect }) {
  useMapEvents({
    click(e) {
      onSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function Home() {
  const [lat, setLat] = useState(null);
  const [lon, setLon] = useState(null);
  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [mode, setMode] = useState("default");
  const [manualCity, setManualCity] = useState("");
  const [showMap, setShowMap] = useState(false);
  const [locationName, setLocationName] = useState("");
  const [showPopup, setShowPopup] = useState(false);

  const navigate = useNavigate();

  const fetchLocationName = async (latitude, longitude) => {
    try {
      const res = await axios.get(
        `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`
      );
      if (res.data && res.data.address) {
        const addr = res.data.address;
        const village = addr.village || addr.hamlet || addr.town || addr.city || "";
        const district = addr.county || addr.state_district || "";
        const state = addr.state || "";
        const country = addr.country || "";
        let locationText = [village, district, state, country].filter(Boolean).join(", ");
        setLocationName(locationText);
      } else {
        setLocationName("Unknown Location");
      }
    } catch {
      setLocationName("Unknown Location");
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude);
          setLon(pos.coords.longitude);
          fetchLocationName(pos.coords.latitude, pos.coords.longitude);
          setMode("default");
        },
        () => alert("Location access denied")
      );
    }
  };

  useEffect(() => {
    getCurrentLocation();
  }, []);

  const fetchManualCity = async () => {
    if (!manualCity.trim()) return;
    const res = await axios.get(
      `https://nominatim.openstreetmap.org/search?city=${manualCity}&format=json&limit=1`
    );
    if (res.data.length) {
      const { lat: latitude, lon: longitude, display_name } = res.data[0];
      setLat(latitude);
      setLon(longitude);
      setLocationName(display_name);
    } else {
      alert("Location not found");
    }
  };


    useEffect(() => {
        if (lat && lon) {
        axios
            .get(
            `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=relative_humidity_2m,precipitation,soil_temperature_0cm,soil_moisture_0_1cm&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode&timezone=auto`
            )
            .then((res) => {
            setWeather({
                temperature: res.data.current_weather.temperature,
                windspeed: res.data.current_weather.windspeed,
                winddirection: res.data.current_weather.winddirection,
                weathercode: res.data.current_weather.weathercode,
                humidity: res.data.hourly.relative_humidity_2m[0],
                precipitation: res.data.hourly.precipitation[0],
                soilTemp: res.data.hourly.soil_temperature_0cm[0],
                soilMoisture: res.data.hourly.soil_moisture_0_1cm[0],
                time: res.data.current_weather.time,
            });
            setForecast(res.data.daily);
            });
        }
    }, [lat, lon]);

  const getWeatherIcon = (code) => {
    if ([0].includes(code)) return "wi-day-sunny";
    if ([1, 2, 3].includes(code)) return "wi-day-cloudy";
    if ([45, 48].includes(code)) return "wi-fog";
    if ([51, 53, 55, 56, 57].includes(code)) return "wi-showers";
    if ([61, 63, 65, 80, 81, 82].includes(code)) return "wi-rain";
    if ([71, 73, 75, 77, 85, 86].includes(code)) return "wi-snow";
    if ([95, 96, 99].includes(code)) return "wi-thunderstorm";
    return "wi-na";
  };

  return (
    <div className="app-container">

      {/* Location icon with tooltip */}
      <button
        className="location-button"
        onClick={() => setShowPopup(true)}
        data-tooltip="Select Location"
      >
        <FaMapMarkerAlt />
      </button>

      {/* Logo + Title */}
      <div className="app-header">
        <img src={logo} alt="AgriBrain Logo" className="app-logo" />
      </div>
    <div>
        <h1 className="app-title">AgriBrain</h1>
    </div>


      {/* Selected location */}
      {locationName && (
        <p className="location-text">📍 Selected Location: {locationName}</p>
      )}

      {/* Manual input */}
      {mode === "manual" && (
        <div className="manual-input">
          <input
            type="text"
            placeholder="Enter city..."
            value={manualCity}
            onChange={(e) => setManualCity(e.target.value)}
          />
          <button onClick={fetchManualCity}>Submit</button>
        <button
          className="cancel-manual-btn"
          onClick={() => {
            setMode("default");
            setManualCity("");
          }}
        >
          Cancel
        </button>

        </div>
      )}

      {/* Map Picker */}
      {showMap && mode === "map" && (
        <div className="map-container">
          <MapContainer center={[20, 78]} zoom={4} style={{ width: "100%", height: "100%" }}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution="&copy; OpenStreetMap contributors"
            />
            <LocationMarker
              onSelect={(latitude, longitude) => {
                setLat(latitude);
                setLon(longitude);
                fetchLocationName(latitude, longitude);
                setShowMap(false);
              }}
            />
            {lat && lon && <Marker position={[lat, lon]} icon={markerIcon} />}
          </MapContainer>
          {/* Cancel button */}
          <button
            className="cancel-map-btn"
            onClick={() => {
              setShowMap(false);
              setMode("default");
            }}
          >
            Cancel
          </button>

        </div>
      )}

      {/* Weather Display */}
      {weather && (
        <div className="weather-cards">
            <div className="weather-card">
                <i className="wi wi-thermometer"></i>
                <h3>Temperature</h3>
                <p>{weather.temperature}°C</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-strong-wind"></i>
                <h3>Wind Speed</h3>
                <p>{weather.windspeed} km/h</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-wind-direction"></i>
                <h3>Wind Direction</h3>
                <p>{weather.winddirection}°</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-humidity"></i>
                <h3>Humidity</h3>
                <p>{weather.humidity}%</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-raindrop"></i>
                <h3>Precipitation</h3>
                <p>{weather.precipitation} mm</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-hot"></i>
                <h3>Soil Temp</h3>
                <p>{weather.soilTemp}°C</p>
            </div>
            <div className="weather-card">
                <i className="wi wi-sprinkle"></i>
                <h3>Soil Moisture</h3>
                <p>{weather.soilMoisture} m³/m³</p>
            </div>
        </div>
      )}

      {forecast && (
        <div className="forecast-section">
          <h2>7-Day Forecast</h2>
          <div className="forecast-cards">
            {forecast.time.map((day, index) => (
              <div key={day} className="forecast-card">
                <p className="forecast-date">{day}</p>
                <i className={`wi ${getWeatherIcon(forecast.weathercode[index])}`}></i>
                <p>Max: {forecast.temperature_2m_max[index]}°C</p>
                <p>Min: {forecast.temperature_2m_min[index]}°C</p>
                <p>Rain: {forecast.precipitation_sum[index]} mm</p>
                <p>Wind: {forecast.windspeed_10m_max[index]} km/h</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="feature-buttons">
        <button
          className="feature-btn"
          onClick={() => navigate("/crop-planner", { state: { lat, lon } })}
        >
          <FaSeedling /> Crop Planner
        </button>
        <button
          className="feature-btn"
          onClick={() =>
            navigate("/government-schemes", {
              state: { stateName: locationName.split(",").slice(-2, -1)[0] || "" },
            })
          }
        >
          <FaLandmark /> Government Schemes
        </button>
      </div>


      {/* Popup */}
      {showPopup && (
        <div className="popup-overlay" onClick={() => setShowPopup(false)}>
          <div className="popup-content" onClick={(e) => e.stopPropagation()}>
            <h3>Select Location Method</h3>
            <button onClick={() => { getCurrentLocation(); setShowPopup(false); }}>
                Use Current Location
            </button>
            <button onClick={() => { setMode("manual"); setShowPopup(false); }}>
              Type Manually
            </button>
            <button onClick={() => { setMode("map"); setShowMap(true); setShowPopup(false); }}>
              Select on Map
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;
