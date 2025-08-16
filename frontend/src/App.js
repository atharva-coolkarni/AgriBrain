import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import CropPlanner from "./pages/CropPlanner/CropPlanner";
import Home from "./pages/Home/Home";
import Schemes from "./pages/Schemes/Schemes";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/crop-planner" element={<CropPlanner />} />
        <Route path="/government-schemes" element={<Schemes />} />
      </Routes>
    </Router>
  );
}

export default App;
