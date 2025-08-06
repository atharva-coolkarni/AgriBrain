// import React from 'react';
// import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
// import 'leaflet/dist/leaflet.css';

// function LocationPicker({ setCoordinates, closeModal }) {
//   useMapEvents({
//     click(e) {
//       const { lat, lng } = e.latlng;
//       setCoordinates({ lat, lng });
//       closeModal(); // Close modal after selecting
//     }
//   });
//   return null;
// }

// function MapModal({ setCoordinates, closeModal }) {
//   return (
//     <div className="modal">
//       <div className="modal-content">
//         <h2>Pick Location on Map</h2>
//         <MapContainer center={[20, 78]} zoom={5} style={{ height: '400px', width: '100%' }}>
//           <TileLayer
//             attribution='&copy; OpenStreetMap contributors'
//             url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
//           />
//           <LocationPicker setCoordinates={setCoordinates} closeModal={closeModal} />
//         </MapContainer>
//         <div className="form-actions">
//           <button className="btn btn-secondary" onClick={closeModal}>Cancel</button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default MapModal;


import React, { useState } from 'react';
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './MapModal.css';

function LocationPicker({ setCoordinates, closeModal }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setCoordinates({ lat, lng });
      closeModal(); // Close modal after selecting
    }
  });
  return null;
}

function MapModal({ setCoordinates, closeModal }) {
  const [manualLocation, setManualLocation] = useState('');
  const [mode, setMode] = useState(null); // 'live', 'manual', 'map'

  const handleLiveLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setCoordinates({ lat: latitude, lng: longitude });
        closeModal();
      },
      () => alert("Failed to get location")
    );
  };

  const handleManualSubmit = async () => {
    if (!manualLocation) return;
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${manualLocation}&format=json`);
      const data = await response.json();
      if (data.length > 0) {
        const { lat, lon } = data[0];
        setCoordinates({ lat: parseFloat(lat), lng: parseFloat(lon) });
        closeModal();
      } else {
        alert("Location not found.");
      }
    } catch (err) {
      alert("Error fetching location.");
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Select Location</h2>

        {/* Mode selector buttons */}
        <div className="location-mode">
          <button className="btn" onClick={() => setMode('live')}>📍 Use My Location</button>
          <button className="btn" onClick={() => setMode('manual')}>✏️ Type Location</button>
          <button className="btn" onClick={() => setMode('map')}>🗺️ Pick on Map</button>
        </div>

        {/* Live Location */}
        {mode === 'live' && (
          <div>
            <p>Fetching current location...</p>
            {handleLiveLocation()}
          </div>
        )}

        {/* Manual Location */}
        {mode === 'manual' && (
          <div className="manual-location-form">
            <input
              type="text"
              placeholder="Enter location (e.g., Chennai, India)"
              value={manualLocation}
              onChange={(e) => setManualLocation(e.target.value)}
            />
            <button className="btn" onClick={handleManualSubmit}>Submit</button>
          </div>
        )}

        {/* Map Selection */}
        {mode === 'map' && (
          <MapContainer center={[20, 78]} zoom={5} style={{ height: '400px', width: '100%' }}>
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LocationPicker setCoordinates={setCoordinates} closeModal={closeModal} />
          </MapContainer>
        )}

        <div className="form-actions">
          <button className="btn btn-secondary" onClick={closeModal}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default MapModal;

