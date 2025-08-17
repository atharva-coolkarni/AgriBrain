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

def crop_data_translator(crop_data, target_language):
    if target_language.lower() == "english":
        return crop_data

    if not GEMINI_API_KEY:
        return {"error": "Gemini API Key not set. Please check your .env file."}

    # Prompt
    prompt_text = f"""
    Translate only the VALUES of the following JSON into {target_language}.
    Do not translate the KEYS.
    Return only valid JSON, nothing else.

    {json.dumps(crop_data, ensure_ascii=False, indent=2)}
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

        if "candidates" not in result or not result["candidates"]:
            return {"error": "Failed to translate crop data. Please try again."}

        translated_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # --- Aggressive Cleanup ---
        cleaned = translated_text.strip()

        # Remove Markdown fences ```json ... ```
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```json|^```|```$", "", cleaned, flags=re.MULTILINE).strip()

        # Try to extract JSON object between { ... }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        # Parse JSON safely
        try:
            translated_json = json.loads(cleaned)
            return translated_json
        except json.JSONDecodeError:
            # --- Last Resort: rebuild key-value pairs manually ---
            kv_pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', cleaned)
            if kv_pairs:
                reconstructed = {k: v for k, v in kv_pairs}
                return reconstructed

            return {
                "error": "Gemini did not return valid JSON, and cleanup failed.",
                "raw_output": translated_text
            }

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {"error": "Error translating crop data."}

def generate_crop_plan_with_gemini(recommended_crop, user_input, weather_data, language):
    if not GEMINI_API_KEY:
        return "Gemini API Key not set. Please check your .env file."

    prompt_text = f"""
    You are an expert agricultural advisor for Indian farmers. Your goal is to provide a comprehensive, actionable, and conversational crop plan for a farmer.

    Based on the following data, generate a detailed report. Use a friendly and encouraging tone.

    ### Farmer's Land Information:
    - Soil Type: {user_input.get("soilType")}
    - Soil pH: {user_input.get("soilPH")}
    - Land Topography: {user_input.get("landTopo")}
    - Land Area: {user_input.get("landArea")}
    - Budget: {user_input.get("budget")}
    - Labor Availability: {user_input.get("labor")}
    - Irrigation Type: {user_input.get("irrigation")}
    - Fertilizer Usage: {user_input.get("fertilizer")}
    - Pest/Disease History: {user_input.get("pestDisease")}

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
        1.  *Why [Crop Name]?*: A brief explanation of why this crop is a great fit for their conditions.
        2.  *Land Preparation & Planting*: Step-by-step guidance on how to prepare the soil and plant the crop.
        3.  *Ongoing Care & Management*: Advice on fertilization, irrigation, and pest control.
        4.  *Weather Forecast*: A simple, human-readable summary of the upcoming weather and how it impacts their plan.
        5.  *A Friendly Conclusion*: A short, encouraging message to wrap up the report.
    - Do not use a conversational greeting like "Hello, I am an AI...". Get straight to the point.
    - Ensure all generated information is based only on the provided data.
    - Do not make up any information. If a piece of data is "N/A", acknowledge it gracefully.
    - Give response in {language}
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
