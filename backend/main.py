from flask import Flask, jsonify, request , session
from flask_cors import CORS
import requests
import os
from pymongo import MongoClient
import secrets
import psutil
import gc
from scheme_recommendation.translation import translate_dict , translate_query_to_english
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
    translate_user_input,
    FORECAST_WEATHER_URL,
    HISTORICAL_WEATHER_URL,
)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError("MONGO_URI environment variable not set. Please check your .env file.")



def log_memory(tag=""):
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"📊 Memory {tag}: {mem_mb:.2f} MB")




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

@app.route('/schemes', methods=['POST'])
def get_schemes_json():
    CONNECTION_STRING = mongo_uri
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    create_database(CONNECTION_STRING, database_name, collection_name)
    return jsonify({"message": "Schemes saved successfully"})

@app.route('/rec_schemes', methods=['POST'])
def get_recommd_json():
    data = request.get_json()
    loc = data.get('location', '')
    query = data.get('query', '')
    top_k = data.get('top_k', 3)
    language = data.get('language', 'english')

    language = language.lower()
    
    # Convert language to proper code
    
    print(f"🌍 Language requested: {language} ")

    if language != 'english':
        curr_query = {'query': query}
        result = translate_query_to_english(curr_query, language)
        # Handle if result is a dict, list, or str
        if isinstance(result, dict):
            query = result.get('query', query)
    
    # Store language in session for use in subsequent requests
    
    CONNECTION_STRING = mongo_uri
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    rec_schemes = get_schemes(schemes, loc, query, top_k, "AIzaSyBcg_7ZoX3AjjjPqvYecB_S80WfJhRxjqg")
    
    # Only translate if not English
    if language != 'english':
        translated_schemes = translate_dict(rec_schemes, language)
    else:
        translated_schemes = rec_schemes
    
    return jsonify(translated_schemes)

@app.route('/questions', methods=['POST'])
def get_questons():
    # Get language from session (set by previous /rec_schemes.json call)
    
    
    # Get schemes from request data
    data = request.get_json()
    language = data.get('language', 'english')
    rec_schemes = data.get('rec_scheme', {})
    
    # Convert language to proper code
    
    print(f"🌍 Language requested: {language} ")
    
    

    CONNECTION_STRING = mongo_uri
    database_name = "scheme_db"
    collection_name = "agricultural_schemes"
    
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    questions = eligibility_check(rec_schemes, schemes)
    
    # Only translate if not English
    if language != 'english':
        translated_questions = translate_dict(questions, language)
    else:
        translated_questions = questions
    
    return jsonify(translated_questions)

@app.route('/check_schemes', methods=['POST'])
def check_schemes():
    data = request.get_json()
    exp_qa = data.get('exp_qa', {})
    user_qa = data.get('user_qa', {})

    comparison_result = compare_scheme_dicts(exp_qa, user_qa)

    return jsonify(comparison_result)


@app.route("/recommend-crop", methods=["POST"])
def recommend_crop():
    log_memory("before recommendation")

    # fetch crops
    crops_collection = fetch_schemes_as_name_keyed_dict(
        mongo_uri, "agri_marketplace", "crops"
    )
    if not crops_collection:
        return jsonify({"error": "Database connection not available"}), 500

    user_input = request.get_json() or {}
    # safely translate fertilizer & pestDisease if keys exist
    fert_val = user_input.get("fertilizer", "")
    pest_val = user_input.get("pestDisease", "")
    user_input["fertilizer"], user_input["pestDisease"] = translate_user_input(fert_val, pest_val)
    print(user_input["fertilizer"], user_input["pestDisease"])

    try:
        historical_params = {
            "latitude": user_input.get("lat"),
            "longitude": user_input.get("lon"),
            "start_date": "1991-01-01",
            "end_date": "2020-12-31",
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto",
        }
        forecast_params = {
            "latitude": user_input.get("lat"),
            "longitude": user_input.get("lon"),
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
            "timezone": "auto",
        }
        lang_param = user_input.get("language", "english")

        # add timeouts so requests don’t hang forever
        historical_response = requests.get(HISTORICAL_WEATHER_URL, params=historical_params, timeout=20)
        forecast_response = requests.get(FORECAST_WEATHER_URL, params=forecast_params, timeout=20)

        historical_data = historical_response.json().get("daily", {})
        forecast_data = forecast_response.json().get("daily", {})
    except Exception as e:
        return jsonify({"error": f"Weather fetch error: {str(e)}"}), 503

    all_crops = crops_collection
    if not all_crops:
        return jsonify({"error": "No crop data found"}), 404

    # scoring loop
    best_crop, best_score = None, -1
    for crop in all_crops:
        try:
            score = calculate_score(crop, user_input, historical_data)
        except Exception as e:
            print(f"Error scoring crop {crop.get('crop_name')}: {e}")
            continue
        if score > best_score:
            best_crop, best_score = crop, score

    if not best_crop or best_score <= 0:
        return jsonify({"error": "No suitable crop found"}), 404

    best_crop = dict(best_crop)  # copy so we don’t mutate original
    best_crop.pop("_id", None)

    weather_data_combined = {
        "historical_data": historical_data,
        "forecast_data": forecast_data,
    }

    crop_plan_report = generate_crop_plan_with_gemini(
        best_crop, user_input, weather_data_combined, lang_param
    )
    crop_details = crop_data_translator(best_crop, lang_param)

    gc.collect()
    log_memory("after recommendation")

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
