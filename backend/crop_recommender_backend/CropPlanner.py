# CropPlanner.py

import os
import re
import json
import gc
import requests
from dotenv import load_dotenv
# from flask_cors import CORS  # not needed here

# Load environment variables from .env if present
load_dotenv()

# Gemini API config
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
)
GEMINI_API_KEY = os.environ.get("VISHU_GEMINI_API_KEY")

# Weather API URLs
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def calculate_score(crop, user_input, historical_data):
    """
    Lightweight, transparent scoring with tolerant string matching.

    - Soil type: keyword / substring-based matching
    - Soil pH: inside crop's min-max range
    - Climate: historical avg temp/rain vs crop min/max
    - Irrigation: keyword / substring-based matching
    """
    score = 0.0

    # --- Soil type match (substring/keyword based) ---
    user_soil = str(user_input.get("soilType", "")).lower().strip()
    crop_soils = [str(s).lower() for s in crop.get("soil_type", []) if isinstance(s, str)]

    if user_soil:
        # Exact/whole-string containment
        if any(user_soil in cs or cs in user_soil for cs in crop_soils):
            score += 50
        else:
            # Partial / keyword match on user words
            for s_type in re.split(r"[,\s]+", user_soil):
                s_type = s_type.strip()
                if not s_type:
                    continue
                if any(s_type in cs or cs in s_type for cs in crop_soils):
                    score += 25
                    break

    # --- Soil pH check ---
    try:
        min_ph = float(crop.get("soil_ph_min", 0.0))
    except Exception:
        min_ph = 0.0
    try:
        max_ph = float(crop.get("soil_ph_max", 14.0))
    except Exception:
        max_ph = 14.0

    try:
        soil_ph = float(user_input.get("soilPH", 7.0))
    except Exception:
        soil_ph = 7.0

    if min_ph <= soil_ph <= max_ph:
        score += 30
    else:
        if soil_ph < min_ph:
            score -= (min_ph - soil_ph) * 5
        else:
            score -= (soil_ph - max_ph) * 5

    # --- Climate check (temperature & rainfall) ---
    def _safe_float(val, repl_chars=("°C", "mm")):
        try:
            s = str(val)
            for ch in repl_chars:
                s = s.replace(ch, "")
            return float(s.strip())
        except Exception:
            return 0.0

    crop_min_temp = _safe_float(crop.get("min_temperature", "0"))
    crop_max_temp = _safe_float(crop.get("max_temperature", "0"))
    crop_min_rain = _safe_float(crop.get("min_rainfall", "0"))
    crop_max_rain = _safe_float(crop.get("max_rainfall", "0"))

    temps = historical_data.get("temperature_2m_max", []) or []
    rains = historical_data.get("rain_sum", []) or []

    avg_temp = (sum(temps) / len(temps)) if temps else 0.0
    avg_rain = (sum(rains) / len(rains)) if rains else 0.0

    if crop_min_temp <= avg_temp <= crop_max_temp:
        score += 15
    if crop_min_rain <= avg_rain <= crop_max_rain:
        score += 15

    # --- Irrigation match (substring/keyword based) ---
    crop_irrigation = (
        str(crop.get("irrigation", {}).get("general", "")).lower().strip()
    )
    user_irrigation = str(user_input.get("irrigation", "")).lower().strip()

    if user_irrigation and crop_irrigation:
        # Whole-string containment either way
        if user_irrigation in crop_irrigation or crop_irrigation in user_irrigation:
            score += 10
        else:
            # Keyword-based on user words
            for word in re.split(r"[,\s]+", user_irrigation):
                word = word.strip()
                if word and word in crop_irrigation:
                    score += 10
                    break

    return score


def crop_data_translator(crop_data, target_language):
    """
    Translate only VALUES of the crop JSON to target_language using Gemini.
    Keys are preserved. Returns dict (best effort), or an error dict.
    Includes gc.collect() to reduce memory footprint after large responses.
    """
    if str(target_language).lower() == "english":
        return crop_data

    if not GEMINI_API_KEY:
        return {"error": "Gemini API Key not set. Please check your .env file."}

    prompt_text = f"""
    Translate only the VALUES of the following JSON into {target_language}.
    Do not translate the KEYS.
    Return only valid JSON, nothing else.

    {json.dumps(crop_data, ensure_ascii=False, indent=2)}
    """

    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            data=json.dumps(payload),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if "candidates" not in result or not result["candidates"]:
            return {"error": "Failed to translate crop data. Please try again."}

        translated_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # --- Cleanup Gemini formatting (```json ... ```, etc.) ---
        cleaned = translated_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```json|^```|```$", "", cleaned, flags=re.MULTILINE
            ).strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            translated_json = json.loads(cleaned)
            return translated_json
        except json.JSONDecodeError:
            kv_pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', cleaned)
            if kv_pairs:
                reconstructed = {k: v for k, v in kv_pairs}
                return reconstructed

            return {
                "error": "Gemini did not return valid JSON, and cleanup failed.",
                "raw_output": translated_text,
            }

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {"error": "Error translating crop data."}
    finally:
        # Free large locals like prompt_text / translated_text
        gc.collect()


def translate_user_input(fertilizer_value, pest_disease_value):
    """
    Translate two short fields to English via Gemini.
    Returns (fertilizer_en, pestDisease_en).
    """
    data_to_translate = {
        "fertilizer": fertilizer_value,
        "pestDisease": pest_disease_value,
    }

    prompt_text = f"""
    Translate only the VALUES of the following JSON into English.
    Do not translate the KEYS.
    Return only valid JSON, nothing else.

    {json.dumps(data_to_translate, ensure_ascii=False, indent=2)}
    """

    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            data=json.dumps(payload),
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()

        if "candidates" not in result or not result["candidates"]:
            print("Gemini API returned an unexpected response.")
            return fertilizer_value, pest_disease_value

        translated_text = result["candidates"][0]["content"]["parts"][0]["text"]

        fertilizer_match = re.search(r'"fertilizer"\s*:\s*"([^"]*)"', translated_text)
        pest_disease_match = re.search(r'"pestDisease"\s*:\s*"([^"]*)"', translated_text)

        translated_fertilizer = (
            fertilizer_match.group(1) if fertilizer_match else fertilizer_value
        )
        translated_pest_disease = (
            pest_disease_match.group(1) if pest_disease_match else pest_disease_value
        )

        return translated_fertilizer, translated_pest_disease

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error calling Gemini API for translation: {e}")
        return fertilizer_value, pest_disease_value
    finally:
        gc.collect()


def generate_crop_plan_with_gemini(recommended_crop, user_input, weather_data, language):
    """
    Create a structured crop plan using Gemini.
    We try to keep the prompt compact and clean up memory after the call.
    """
    if not GEMINI_API_KEY:
        return "Gemini API Key not set. Please check your .env file."

    # Prepare compact weather summaries to keep prompt size reasonable
    hist_t = weather_data.get("historical_data", {}).get("temperature_2m_max", [])
    hist_r = weather_data.get("historical_data", {}).get("rain_sum", [])
    fc_t = weather_data.get("forecast_data", {}).get("temperature_2m_max", [])
    fc_r = weather_data.get("forecast_data", {}).get("rain_sum", [])

    hist_avg_t = (sum(hist_t) / len(hist_t)) if hist_t else "N/A"
    hist_avg_r = (sum(hist_r) / len(hist_r)) if hist_r else "N/A"
    fc_avg_t = (sum(fc_t) / len(fc_t)) if fc_t else "N/A"
    fc_sum_r = (sum(fc_r)) if fc_r else "N/A"

    # Build the prompt
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
    - Average Max Temperature: {hist_avg_t}°C
    - Average Rainfall: {hist_avg_r} mm

    ### Forecast Weather Data:
    - Next 7 Days Average Max Temp: {fc_avg_t}°C
    - Next 7 Days Total Rainfall: {fc_sum_r} mm

    ### Instructions for the Gemini API:
    - Your report should be in Markdown format but no bold words and size of all words should be same.
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

    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            data=json.dumps(payload),
            timeout=45,
        )
        response.raise_for_status()
        result = response.json()
        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        return "Failed to generate crop plan. Please try again."
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error generating crop plan."
    finally:
        # Free large locals like prompt_text/result/text
        gc.collect()
