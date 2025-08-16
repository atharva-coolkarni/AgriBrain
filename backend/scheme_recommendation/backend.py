from flask import Flask, jsonify , request
import json

from links import create_database   
from rec import get_schemes, eligibility_check , compare_scheme_dicts
from pymongo import MongoClient

app = Flask(__name__)

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
    database_name="scheme_db"
    collection_name="agricultural_schemes"
    create_database(CONNECTION_STRING, database_name, collection_name)
    return jsonify({"message": "Schemes saved successfully"})

@app.route('/rec_schemes.json', methods=['POST'])
def get_recommd_json():
    data = request.get_json()
    loc = data.get('location', '')
    query = data.get('query', '')
    top_k = data.get('top_k', 3)
    CONNECTION_STRING = "mongodb+srv://vedantkul30:PYQTbwRTUzisGmYo@cluster0.agmksey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name="scheme_db"
    collection_name="agricultural_schemes"
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    rec_schemes = get_schemes(schemes,loc,query, top_k,"AIzaSyBcg_7ZoX3AjjjPqvYecB_S80WfJhRxjqg")

    return jsonify(rec_schemes)

@app.route('/questions.json', methods=['POST'])
def get_questons():
    rec_schemes = request.get_json()
    CONNECTION_STRING = "mongodb+srv://vedantkul30:PYQTbwRTUzisGmYo@cluster0.agmksey.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name="scheme_db"
    collection_name="agricultural_schemes"
    schemes = fetch_schemes_as_name_keyed_dict(CONNECTION_STRING, database_name, collection_name)
    questions = eligibility_check(rec_schemes, schemes)

      # This will populate the global 'schemes' variable
    return jsonify(questions)

@app.route('/check_schemes.json', methods=['POST'])
def check_schemes():
    data = request.get_json()
    exp_qa = data.get('exp_qa', {})
    user_qa = data.get('user_qa', {})

    comparison_result = compare_scheme_dicts(exp_qa, user_qa)

    return jsonify(comparison_result)


if __name__ == "__main__":
    app.run(debug=True)