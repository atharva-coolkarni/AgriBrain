import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import requests
import asyncio
from dotenv import load_dotenv
from pymongo import MongoClient
from contextlib import asynccontextmanager
import re
import json

# Load environment variables from the .env file
load_dotenv()

# Global variables for the database client and collection
db_client = None
crops_collection = None

# Gemini API configuration
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Use the new lifespan context manager for startup and shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    global db_client, crops_collection
    try:
        # Connect to MongoDB on application startup
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError("MONGO_URI environment variable not set. Please check your .env file.")

        db_client = MongoClient(mongo_uri)
        db = db_client.get_database("agri_marketplace")  # Your database name
        crops_collection = db.get_collection("crops")
        print("Connected to MongoDB successfully!")
        
        yield  # The application will run between the 'yield' statements
        
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        db_client = None  # Ensure the client is None if connection fails
        
    finally:
        # Close the MongoDB connection on application shutdown
        if db_client:
            db_client.close()
            print("MongoDB connection closed.")


# Initialize the FastAPI app with the lifespan context manager
app = FastAPI(
    title="AgriBrain API",
    description="A backend API for crop recommendation and agricultural advice.",
    lifespan=lifespan
)

# Define a Pydantic model for the user's input.
class UserInput(BaseModel):
    soilType: str
    soilPH: float
    soilEC: Optional[str] = None
    landTopo: Optional[str] = None
    landArea: Optional[str] = None
    budget: Optional[str] = None
    labor: Optional[str] = None
    irrigation: Optional[str] = None
    fertilizer: Optional[str] = None
    pestDisease: Optional[str] = None
    lat: float
    lon: float

# --- Weather API URLs ---
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def calculate_score(
    crop: Dict[str, Any],
    user_input: UserInput,
    historical_data: Dict[str, List[float]]
) -> float:
    """
    Calculates a suitability score for a single crop based on user input and climate data.
    The higher the score, the better the fit.
    """
    score = 0.0

    # 1. Soil Type Match (High Priority)
    # Check if the user's soil type matches any of the crop's suitable soils.
    if user_input.soilType.lower() in [s.lower() for s in crop.get("soil_type", []) if isinstance(s, str)]:
        score += 50
    # Additional check for general soil types like "loamy"
    for s_type in re.split(r'[, ]+', user_input.soilType):
        if s_type.lower() in [s.lower() for s in crop.get("soil_type", []) if isinstance(s, str)]:
            score += 25
            break

    # 2. Soil pH Match (High Priority)
    # Calculate how close the user's soil pH is to the crop's ideal range.
    min_ph = float(crop.get("soil_ph_min", 0.0))
    max_ph = float(crop.get("soil_ph_max", 14.0))
    
    if min_ph <= user_input.soilPH <= max_ph:
        # Perfect match
        score += 30
    else:
        # Penalize for being outside the ideal range
        if user_input.soilPH < min_ph:
            score -= (min_ph - user_input.soilPH) * 5
        else:
            score -= (user_input.soilPH - max_ph) * 5

    # 3. Climate Match (Temperature and Rainfall) - Medium Priority
    # Compare the crop's climate needs to the location's historical data.
    try:
        crop_min_temp = float(crop.get("min_temperature", "0").replace("°C", "").strip())
        crop_max_temp = float(crop.get("max_temperature", "0").replace("°C", "").strip())
        crop_min_rain = float(crop.get("min_rainfall", "0").replace("mm", "").strip())
        crop_max_rain = float(crop.get("max_rainfall", "0").replace("mm", "").strip())
    except (ValueError, TypeError):
        # Handle cases where the data is not in the expected format
        crop_min_temp = 0
        crop_max_temp = 0
        crop_min_rain = 0
        crop_max_rain = 0

    avg_historical_temp = sum(historical_data.get("temperature_2m_max", [])) / len(historical_data.get("temperature_2m_max", [])) if historical_data.get("temperature_2m_max") else 0
    avg_historical_rain = sum(historical_data.get("rain_sum", [])) / len(historical_data.get("rain_sum", [])) if historical_data.get("rain_sum") else 0

    if crop_min_temp <= avg_historical_temp <= crop_max_temp:
        score += 15
    if crop_min_rain <= avg_historical_rain <= crop_max_rain:
        score += 15

    # 4. Irrigation Needs (Customizable - can be a higher priority based on user input)
    # Give a bonus if the crop is suitable for the user's irrigation level.
    crop_irrigation_general = crop.get("irrigation", {}).get("general", "").lower()
    user_irrigation = user_input.irrigation.lower() if user_input.irrigation else ""
    
    if "rainfed" in crop_irrigation_general and "limited" in user_irrigation:
        score += 10
    elif "4-6 irrigations" in crop_irrigation_general and "full" in user_irrigation:
        score += 10

    return score

async def generate_crop_plan_with_gemini(
    recommended_crop: Dict[str, Any],
    user_input: UserInput,
    weather_data: Dict[str, Any]
) -> str:
    """
    Generates a detailed, conversational crop plan using the Gemini API.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API Key is not set. Please check your .env file."
        )

    # Construct the prompt for the LLM.
    prompt_text = f"""
    You are an expert agricultural advisor for Indian farmers. Your goal is to provide a comprehensive, actionable, and conversational crop plan for a farmer.

    Based on the following data, generate a detailed report. Use a friendly and encouraging tone.

    ### Farmer's Land Information:
    - Soil Type: {user_input.soilType}
    - Soil pH: {user_input.soilPH}
    - Land Topography: {user_input.landTopo}
    - Land Area: {user_input.landArea}
    - Budget: {user_input.budget}
    - Labor Availability: {user_input.labor}
    - Irrigation Type: {user_input.irrigation}
    - Fertilizer Usage: {user_input.fertilizer}
    - Pest/Disease History: {user_input.pestDisease}

    ### Recommended Crop Information:
    - Crop Name: {recommended_crop.get("crop_name")}
    - Soil Type Suitability: {recommended_crop.get("soil_type")}
    - Ideal Soil pH: {recommended_crop.get("soil_ph_min", "N/A")} to {recommended_crop.get("soil_ph_max", "N/A")}
    - Ideal Temperature: {recommended_crop.get("min_temperature", "N/A")} to {recommended_crop.get("max_temperature", "N/A")}
    - Ideal Rainfall: {recommended_crop.get("min_rainfall", "N/A")} to {recommended_crop.get("max_rainfall", "N/A")}
    - Crop Variety: {recommended_crop.get("variety")}
    - Planting Season: {recommended_crop.get("timeline", {}).get("seasons_in_india", ["N/A"])[0]}
    - Maturity: {recommended_crop.get("maturity_days")}
    - Spacing: {recommended_crop.get("spacing")}
    - Seed Rate: {recommended_crop.get("seed_rate")}
    - Fertilization: {recommended_crop.get("fertilizer")}
    - Irrigation: {recommended_crop.get("irrigation")}
    - Common Pests: {', '.join(recommended_crop.get("pests", []))}
    - Common Diseases: {', '.join(recommended_crop.get("diseases", []))}

    ### Historical Climate Data (1991-2020):
    - Average Max Temperature: {sum(weather_data.get("historical_data", {}).get("temperature_2m_max", [])) / len(weather_data.get("historical_data", {}).get("temperature_2m_max", [])) if weather_data.get("historical_data", {}).get("temperature_2m_max") else 'N/A'}°C
    - Average Rainfall: {sum(weather_data.get("historical_data", {}).get("rain_sum", [])) / len(weather_data.get("historical_data", {}).get("rain_sum", [])) if weather_data.get("historical_data", {}).get("rain_sum") else 'N/A'} mm

    ### Forecast Weather Data:
    - Next 7 Days Average Max Temp: {sum(weather_data.get("forecast_data", {}).get("temperature_2m_max", [])) / len(weather_data.get("forecast_data", {}).get("temperature_2m_max", [])) if weather_data.get("forecast_data", {}).get("temperature_2m_max") else 'N/A'}°C
    - Next 7 Days Total Rainfall: {sum(weather_data.get("forecast_data", {}).get("rain_sum", [])) if weather_data.get("forecast_data", {}).get("rain_sum") else 'N/A'} mm

    ### Instructions for the Gemini API:
    - Your report should be in Markdown format.
    - Start with a clear heading like "Your Crop Plan for [Crop Name]".
    - Structure the report into clear sections:
        1.  **Why [Crop Name]?**: A brief explanation of why this crop is a great fit for their conditions.
        2.  **Land Preparation & Planting**: Step-by-step guidance on how to prepare the soil and plant the crop.
        3.  **Ongoing Care & Management**: Advice on fertilization, irrigation, and pest control.
        4.  **Weather Forecast**: A simple, human-readable summary of the upcoming weather and how it impacts their plan.
        5.  **A Friendly Conclusion**: A short, encouraging message to wrap up the report.
    - Do not use a conversational greeting like "Hello, I am an AI...". Get straight to the point.
    - Ensure all generated information is based only on the provided data.
    - Do not make up any information. If a piece of data is "N/A", acknowledge it gracefully.
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    { "text": prompt_text }
                ]
            }
        ]
    }
    
    try:
        response = await asyncio.to_thread(
            requests.post,
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        
        result = response.json()
        if "candidates" in result and result["candidates"]:
            # Extract the generated text from the response
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"Gemini API Response: {result}")
            return "Failed to generate a crop plan. Please try again."
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return "Failed to generate a crop plan due to a network error."


# Define the API endpoint that will receive the user's form data.
@app.post("/recommend-crop")
async def recommend_crop(user_input: UserInput) -> Dict[str, Any]:
    """
    Receives user input, fetches weather data, and recommends a suitable crop.
    """
    if not db_client:
        raise HTTPException(status_code=500, detail="Database connection not available.")

    # Fetch historical and forecast weather data concurrently
    try:
        historical_params = {
            "latitude": user_input.lat,
            "longitude": user_input.lon,
            "start_date": "1991-01-01",
            "end_date": "2020-12-31",
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto"
        }
        
        forecast_params = {
            "latitude": user_input.lat,
            "longitude": user_input.lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto"
        }

        # Use asyncio to run both API calls in parallel for efficiency
        historical_future = asyncio.to_thread(requests.get, HISTORICAL_WEATHER_URL, params=historical_params)
        forecast_future = asyncio.to_thread(requests.get, FORECAST_WEATHER_URL, params=forecast_params)

        historical_response, forecast_response = await asyncio.gather(historical_future, forecast_future)
        
        historical_response.raise_for_status()
        forecast_response.raise_for_status()
        
        historical_data = historical_response.json()["daily"]
        forecast_data = forecast_response.json()["daily"]

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error fetching weather data: {str(e)}")

    # --- Step 2: Database Query and Scoring ---
    # Fetch all crops from the MongoDB collection.
    all_crops = list(crops_collection.find({}))
    
    if not all_crops:
        raise HTTPException(status_code=404, detail="No crop data found in the database.")
        
    best_crop = None
    best_score = -1
    
    # Iterate through all crops and calculate their score.
    for crop in all_crops:
        score = calculate_score(crop, user_input, historical_data)
        if score > best_score:
            best_score = score
            best_crop = crop
            
    if best_crop is None or best_score <= 0:
        raise HTTPException(status_code=404, detail="No suitable crop found based on the provided conditions.")

    # Remove MongoDB's internal _id field for cleaner JSON output
    best_crop.pop("_id", None)
    
    # --- Step 3: Generate a conversational report using Gemini API ---
    weather_data_combined = {
        "historical_data": historical_data,
        "forecast_data": forecast_data
    }
    
    crop_plan_report = await generate_crop_plan_with_gemini(best_crop, user_input, weather_data_combined)

    return {
        "message": "Crop recommendation and plan generated successfully!",
        "recommended_crop_details": best_crop,
        "suitability_score": best_score,
        "crop_plan_report": crop_plan_report
    }

# Add a simple root endpoint for a health check
@app.get("/")
def read_root():
    return {"message": "Welcome to the AgriBrain API! The API is healthy."}
