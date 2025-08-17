from flask import Flask, jsonify, request , session
from flask_cors import CORS
import requests
import os
from pymongo import MongoClient
import secrets
from scheme_recommendation.translation import translate_dict
from scheme_recommendation.fetch_schemes import create_database
from scheme_recommendation.recommendation import (
    get_schemes,
    eligibility_check,
    compare_scheme_dicts,
)
from crop_recommender_backend.CropPlanner import (
    generate_crop_plan_with_gemini,
    calculate_score,
    crop_data_translator,
    FORECAST_WEATHER_URL,
    HISTORICAL_WEATHER_URL,
)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError("MONGO_URI environment variable not set. Please check your .env file.")

LANGUAGE_MAP = {
    'english': 'en',
    'hindi': 'hi',
    'tamil': 'ta',
    'telugu': 'te',
    'bengali': 'bn',
    'gujarati': 'gu',
    'marathi': 'mr',
    'kannada': 'kn',
    'malayalam': 'ml',
    'punjabi': 'pa',
}

def get_language_code(language_input):
    """Convert language name to proper language code"""
    if not language_input:
        return 'en'  # Default to English
    
    # Convert to lowercase for comparison
    lang_lower = language_input.lower().strip()
    
    # If it's already a language code, return as is
    if len(lang_lower) == 2 and lang_lower in LANGUAGE_MAP.values():
        return lang_lower
    
    # Otherwise, map from full name to code
    return LANGUAGE_MAP.get(lang_lower, 'en')  # Default to English if not found

def fetch_schemes_as_name_keyed_dict(connection_string, database_name, collection_name):
    """
    Fetch all documents from MongoDB and return as:
    {
        "<scheme_name>": {<other_fields>},
        ...
    }
    """
    try:
        client = MongoClient(connection_string)
        db = client[database_name]
        collection = db[collection_name]

        # Fetch all documents
        data = list(collection.find({}))

        # Remove MongoDB's _id field if you don't need it
        for doc in data:
            doc.pop("_id", None)

        print(f"✅ Fetched {len(data)} documents from MongoDB.")
        return data

    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return []
    finally:
        client.close()

@app.route('/schemes.json', methods=['POST'])
def get_schemes_json():
    CONNECTION_STRING = "mongodb+srv://vedantkul30:PYQTbwRTUzisGmYo@cluster0.agmksey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    create_database(CONNECTION_STRING, database_name, collection_name)
    return jsonify({"message": "Schemes saved successfully"})

@app.route('/rec_schemes.json', methods=['POST'])
def get_recommd_json():
    data = request.get_json()
    loc = data.get('location', '')
    query = data.get('query', '')
    top_k = data.get('top_k', 3)
    language = data.get('language', 'english')
    
    # Convert language to proper code
    lang_code = get_language_code(language)
    print(f"🌍 Language requested: {language} -> Using code: {lang_code}")
    
    # Store language in session for use in subsequent requests
    
    CONNECTION_STRING = "mongodb+srv://vedantkul30:PYQTbwRTUzisGmYo@cluster0.agmksey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    rec_schemes = get_schemes(schemes, loc, query, top_k, "AIzaSyBcg_7ZoX3AjjjPqvYecB_S80WfJhRxjqg")
    
    # Only translate if not English
    if lang_code != 'en':
        translated_schemes = translate_dict(rec_schemes, lang_code)
    else:
        translated_schemes = rec_schemes
    
    return jsonify(translated_schemes)

@app.route('/questions.json', methods=['POST'])
def get_questons():
    # Get language from session (set by previous /rec_schemes.json call)
    
    
    # Get schemes from request data
    data = request.get_json()
    language = data.get('language', 'english')
    rec_schemes = data.get('rec_scheme', {})
    
    # Convert language to proper code
    lang_code = get_language_code(language)
    print(f"🌍 Language requested: {language} -> Using code: {lang_code}")
    
    

    CONNECTION_STRING = "mongodb+srv://vedantkul30:PYQTbwRTUzisGmYo@cluster0.agmksey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    questions = eligibility_check(rec_schemes, schemes)
    
    # Only translate if not English
    if lang_code != 'en':
        translated_questions = translate_dict(questions, lang_code)
    else:
        translated_questions = questions
    
    return jsonify(translated_questions)

@app.route('/check_schemes.json', methods=['POST'])
def check_schemes():
    data = request.get_json()
    exp_qa = data.get('exp_qa', {})
    user_qa = data.get('user_qa', {})

    comparison_result = compare_scheme_dicts(exp_qa, user_qa)

    return jsonify(comparison_result)


@app.route("/recommend-crop", methods=["POST"])
def recommend_crop():
    crops_collection = fetch_schemes_as_name_keyed_dict(
        mongo_uri, "agri_marketplace", "crops"
    )
    if not crops_collection:
        return jsonify({"error": "Database connection not available"}), 500

    user_input = request.get_json()

    try:
        historical_params = {
            "latitude": user_input["lat"],
            "longitude": user_input["lon"],
            "start_date": "1991-01-01",
            "end_date": "2020-12-31",
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto",
        }
        forecast_params = {
            "latitude": user_input["lat"],
            "longitude": user_input["lon"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto",
        }
        lang_param="english"
        historical_response = requests.get(HISTORICAL_WEATHER_URL, params=historical_params)
        forecast_response = requests.get(FORECAST_WEATHER_URL, params=forecast_params)

        historical_data = historical_response.json().get("daily", {})
        forecast_data = forecast_response.json().get("daily", {})
    except Exception as e:
        return jsonify({"error": f"Weather fetch error: {str(e)}"}), 503

    # crops_collection is already a list of dicts
    all_crops = crops_collection
    if not all_crops:
        return jsonify({"error": "No crop data found"}), 404

    best_crop, best_score = None, -1
    for crop in all_crops:
        score = calculate_score(crop, user_input, historical_data)
        if score > best_score:
            best_crop, best_score = crop, score

    if not best_crop or best_score <= 0:
        return jsonify({"error": "No suitable crop found"}), 404

    best_crop.pop("_id", None)

    weather_data_combined = {
        "historical_data": historical_data,
        "forecast_data": forecast_data,
    }
    crop_plan_report = generate_crop_plan_with_gemini(best_crop, user_input, weather_data_combined, lang_param)
    crop_details = crop_data_translator(best_crop, lang_param)
 
    return jsonify(
        {
            "message": "Crop recommendation and plan generated successfully!",
            "recommended_crop_details": crop_details,
            "suitability_score": best_score,
            "crop_plan_report": crop_plan_report,
        }
    )



@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Welcome to the AgriBrain API! The API is healthy."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
