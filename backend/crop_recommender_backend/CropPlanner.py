import os
import re
import json
import requests
from flask_cors import CORS
from dotenv import load_dotenv
# from pymongo import MongoClient

# Load environment variables
load_dotenv()

# # MongoDB setup
# db_client = None
# crops_collection = None

# mongo_uri = os.getenv("MONGO_URI")
# if not mongo_uri:
#     raise RuntimeError("MONGO_URI environment variable not set. Please check your .env file.")

# try:
#     db_client = MongoClient(mongo_uri)
#     db = db_client.get_database("agri_marketplace")  # Database name
#     crops_collection = db.get_collection("crops")
#     print("Connected to MongoDB successfully!")
# except Exception as e:
#     print(f"Failed to connect to MongoDB: {e}")

# Gemini API config
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Weather API URLs
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def calculate_score(crop, user_input, historical_data):
    score = 0.0

    # Soil type match
    if user_input["soilType"].lower() in [s.lower() for s in crop.get("soil_type", []) if isinstance(s, str)]:
        score += 50
    for s_type in re.split(r'[, ]+', user_input["soilType"]):
        if s_type.lower() in [s.lower() for s in crop.get("soil_type", []) if isinstance(s, str)]:
            score += 25
            break

    # Soil pH
    min_ph = float(crop.get("soil_ph_min", 0.0))
    max_ph = float(crop.get("soil_ph_max", 14.0))
    if min_ph <= user_input["soilPH"] <= max_ph:
        score += 30
    else:
        if user_input["soilPH"] < min_ph:
            score -= (min_ph - user_input["soilPH"]) * 5
        else:
            score -= (user_input["soilPH"] - max_ph) * 5

    # Climate
    try:
        crop_min_temp = float(crop.get("min_temperature", "0").replace("°C", "").strip())
        crop_max_temp = float(crop.get("max_temperature", "0").replace("°C", "").strip())
        crop_min_rain = float(crop.get("min_rainfall", "0").replace("mm", "").strip())
        crop_max_rain = float(crop.get("max_rainfall", "0").replace("mm", "").strip())
    except:
        crop_min_temp = crop_max_temp = crop_min_rain = crop_max_rain = 0

    avg_temp = sum(historical_data.get("temperature_2m_max", [])) / len(historical_data.get("temperature_2m_max", [])) if historical_data.get("temperature_2m_max") else 0
    avg_rain = sum(historical_data.get("rain_sum", [])) / len(historical_data.get("rain_sum", [])) if historical_data.get("rain_sum") else 0

    if crop_min_temp <= avg_temp <= crop_max_temp:
        score += 15
    if crop_min_rain <= avg_rain <= crop_max_rain:
        score += 15

    # Irrigation
    crop_irrigation_general = crop.get("irrigation", {}).get("general", "").lower()
    user_irrigation = user_input.get("irrigation", "").lower()
    if "rainfed" in crop_irrigation_general and "limited" in user_irrigation:
        score += 10
    elif "4-6 irrigations" in crop_irrigation_general and "full" in user_irrigation:
        score += 10

    return score


def generate_crop_plan_with_gemini(recommended_crop, user_input, weather_data):
    if not GEMINI_API_KEY:
        return "Gemini API Key not set. Please check your .env file."

    prompt_text = f"""
    You are an expert agricultural advisor for Indian farmers...
    (keep same as your FastAPI prompt, I skipped here for brevity)
    """

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            data=json.dumps(payload),
        )
        response.raise_for_status()
        result = response.json()
        if "candidates" in result and result["candidates"]:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        return "Failed to generate crop plan. Please try again."
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error generating crop plan."