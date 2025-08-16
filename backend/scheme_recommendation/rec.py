import json
import os
import requests
from langchain_community.vectorstores.faiss import FAISS
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient



def get_schemes(schemes ,user_location, query, top_k=3, api_key=None):
    """
    Main function to:
      1. Load schemes.json
      2. Filter schemes by location
      3. Create FAISS vector store
      4. Perform semantic search
      5. Rerank results with Gemini
      6. Save recommendations to file
    Returns:
      dict: recommended_schemes
    """

    # ========= GEMINI CONFIG =========
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY_GEMINI", "")
    if not api_key:
        raise ValueError("Google API Key for Gemini not provided.")

    def call_gemini_api(prompt: str) -> str:
        headers = {"X-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']

    class GeminiChatAgent:
        def __init__(self, name):
            self.name = name
        def chat(self, messages):
            prompt = ""
            for msg in messages:
                prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
            return call_gemini_api(prompt)

    # ========= Embedding setup =========
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    def embedding_function(texts):
        return embed_model.encode(texts, normalize_embeddings=True).tolist()

    class CustomEmbedding(Embeddings):
        def embed_query(self, text):
            return embedding_function([text])[0]
        def embed_documents(self, texts):
            return embedding_function(texts)

    # ========= Semantic search =========
    def semantic_search_faiss(vector_store, query, top_k=3):
        docs_and_scores = vector_store.similarity_search_with_score(query, k=top_k)
        results = []
        for doc, score in docs_and_scores:
            results.append({
                "Name": doc.metadata.get("Name", "Unknown"),
                "URL": doc.metadata.get("URL", ""),
                "Summarized_content": doc.metadata.get("Summarized_content", ""),
                "content": doc.page_content,
                "score": score
            })
        return results

    # ========= Contextual re-ranking with Gemini =========
    def contextual_rerank_gemini(query, top_schemes):
        user_prompt = (
            "You are an expert assistant recommending agricultural schemes.\n"
            f"User query: {query}\n"
            "Given the following candidate schemes, output ONLY a valid JSON object.\n"
            "The JSON format must be exactly:\n"
            "{\n"
            '  "SCHEME_NAME": {\n'
            '    "URL": "SCHEME_URL",\n'
            '    "Reason": "reason for recommendation based on user query"\n'
            "  },\n"
            "   ... (for each recommended scheme)\n"
            "}\n"
            "Rules:\n"
            "- Use the exact 'Name' value from the provided metadata as the JSON key.\n"
            "- Do not include any extra text outside the JSON.\n"
        )

        for i, scheme in enumerate(top_schemes, 1):
            user_prompt += (
                f"\nScheme {i}:\n"
                f"Name: {scheme['Name']}\n"
                f"URL: {scheme['URL']}\n"
                f"Content: {scheme['content'] if scheme['Summarized_content'] == '' else scheme['Summarized_content']}\n"
                f"(Relevance score: {scheme['score']:.3f})\n"
            )

        user_prompt += "\nNow output ONLY the JSON object as instructed."

        agent = GeminiChatAgent(name="SchemeRecommender")
        completion = agent.chat([{"role": "user", "content": user_prompt}])
        return completion
    
    

    # ========= Step 1: Load and filter schemes =========
    
    
    filtered_schemes = [
        scheme for scheme in schemes
        if scheme.get("State_specific_Schemes", "").strip().lower() in ("no", user_location.lower())
    ]

    # ========= Step 2: Prepare texts and metadata =========
    texts = [
        scheme["content"] if scheme.get("Summarized_content", "") == "" 
        else scheme["Summarized_content"]
        for scheme in filtered_schemes
    ]
    metadatas = [
        {
            "Name": scheme["Name"],
            "URL": scheme["URL"],
            "Summarized_content": scheme.get("Summarized_content", "")
        }
        for scheme in filtered_schemes
    ]

    # ========= Step 3: Create FAISS store =========
    embeddings = CustomEmbedding()
    vector_store = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)

    # ========= Step 4: Search and rerank =========
    top_schemes = semantic_search_faiss(vector_store, query, top_k)
    response_text = contextual_rerank_gemini(query, top_schemes)

    # Clean markdown fences if present
    lines = response_text.split('\n')
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    cleaned_response = '\n'.join(lines)

    recommended_schemes = json.loads(cleaned_response)

    # ========= Step 5: Save recommendations =========
    with open("recommended_schemes.json", "w", encoding="utf-8") as f:
        json.dump(recommended_schemes, f, ensure_ascii=False, indent=4)

    return recommended_schemes


def eligibility_check(rec_schemes ,schemes):
    """
    Matches recommended schemes with eligibility Q&A from original schemes.json
    """

    QA_checks = {}
    for scheme in schemes:
        scheme_url = scheme.get("URL", "").strip()
        for rec_name, rec_data in rec_schemes.items():
            if rec_data.get("URL", "").strip() == scheme_url:
                QA_checks[rec_name] = scheme.get("Eligibility_QA", {})

    return QA_checks

def compare_scheme_dicts(dict1, dict2):
    """
    Compare two scheme dictionaries key-wise.
    Returns {<key>: "Yes"/"No"} depending on if contents match exactly.
    """
    result = {}
    all_keys = set(dict1.keys()) | set(dict2.keys())  # union of keys from both dicts

    for key in all_keys:
        val1 = dict1.get(key, None)
        val2 = dict2.get(key, None)
        result[key] = "Yes" if val1 == val2 else "No"

    return result