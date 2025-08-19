import json
import os
import requests
from langchain_community.vectorstores.faiss import FAISS
from langchain.embeddings.base import Embeddings
import numpy as np
from typing import List, Dict, Any
import gc
import psutil
from model2vec import StaticModel

# Global model instance to avoid reloading
_embed_model = None

def get_embedding_model():
    """Load the Model2Vec embedding model (8MB memory usage)"""
    global _embed_model
    if _embed_model is None:
        print("Loading Model2Vec (minishlab/potion-base-8M)")
        _embed_model = StaticModel.from_pretrained('minishlab/potion-base-8M')
    return _embed_model

class MemoryEfficientEmbedding(Embeddings):
    """Memory-efficient embedding class using Model2Vec"""
    
    def __init__(self, batch_size: int = 16):
        self.batch_size = batch_size
    
    def embed_query(self, text: str) -> List[float]:
        model = get_embedding_model()
        embedding = model.encode([text])
        return embedding[0].tolist() if hasattr(embedding[0], 'tolist') else embedding[0]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Process documents in batches using Model2Vec"""
        model = get_embedding_model()
        all_embeddings = []
        
        print(f"Embedding {len(texts)} schemes using Model2Vec in batches of {self.batch_size}")
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_start = i + 1
            batch_end = min(i + self.batch_size, len(texts))
            
            # Model2Vec batch processing
            batch_embeddings = model.encode(batch)
            
            # Convert to list format expected by FAISS
            if hasattr(batch_embeddings, 'tolist'):
                all_embeddings.extend(batch_embeddings.tolist())
            else:
                all_embeddings.extend([emb.tolist() if hasattr(emb, 'tolist') else emb for emb in batch_embeddings])
            
            # Force garbage collection after each batch
            del batch_embeddings
            gc.collect()
            
            current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            print(f"✓ Embedded batch {i//self.batch_size + 1}: schemes {batch_start}-{batch_end}/{len(texts)}. Memory: {current_memory:.1f}MB")
        
        print(f"✓ COMPLETED: Embedded all {len(texts)} schemes. Total embeddings: {len(all_embeddings)}")
        return all_embeddings

def preprocess_schemes(schemes: List[Dict], user_location: str) -> tuple:
    """
    Efficiently filter and prepare schemes data
    Each scheme is processed as a complete unit (no fragmentation)
    Returns: (texts, metadatas, filtered_count)
    """
    user_location_lower = user_location.lower()
    texts = []
    metadatas = []
    processed_schemes = set()  # Track processed schemes to avoid duplicates
    
    for scheme in schemes:
        # Filter during iteration to save memory
        state_specific = scheme.get("State_specific_Schemes", "").strip().lower()
        if state_specific not in ("no", user_location_lower):
            continue
        
        # Use URL as unique identifier, fallback to name
        scheme_id = scheme.get("URL", "").strip() or scheme.get("Name", "")
        if scheme_id in processed_schemes:
            continue  # Skip duplicate schemes
        
        # Choose content efficiently - complete scheme content only
        content = scheme.get("Summarized_content", "").strip()
        if not content:
            content = scheme.get("content", "").strip()
        
        if content:  # Only process schemes with content
            texts.append(content)  # Complete scheme content as single text
            metadatas.append({
                "Name": scheme.get("Name", "Unknown"),
                "URL": scheme.get("URL", ""),
                "Summarized_content": scheme.get("Summarized_content", "")
            })
            processed_schemes.add(scheme_id)
    
    print(f"Preprocessed {len(texts)} unique schemes from {len(schemes)} total schemes")
    return texts, metadatas, len(texts)

def create_vector_store_efficiently(texts: List[str], metadatas: List[Dict]) -> FAISS:
    """Create FAISS store optimized for Model2Vec"""
    embeddings = MemoryEfficientEmbedding(batch_size=16)
    
    # With Model2Vec's low memory footprint, we can process larger batches
    if len(texts) <= 50:
        # Process all schemes at once if 50 or fewer
        print(f"Processing all {len(texts)} schemes in single batch")
        vector_store = FAISS.from_texts(
            texts=texts, 
            embedding=embeddings, 
            metadatas=metadatas
        )
        gc.collect()
        return vector_store
    else:
        # Use larger batches of 50 schemes due to Model2Vec's efficiency
        batch_size = 50
        vector_stores = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            
            batch_store = FAISS.from_texts(
                texts=batch_texts, 
                embedding=embeddings, 
                metadatas=batch_metadatas
            )
            vector_stores.append(batch_store)
            gc.collect()
            print(f"Processed batch {i//batch_size + 1}: {len(batch_texts)} schemes")
        
        # Merge batches
        print(f"Merging {len(vector_stores)} vector store batches...")
        main_store = vector_stores[0]
        for j, store in enumerate(vector_stores[1:], 1):
            main_store.merge_from(store)
            del store
            gc.collect()
        
        return main_store

def semantic_search_optimized(vector_store: FAISS, query: str, top_k: int = 3) -> List[Dict]:
    """Optimized semantic search for small dataset with deduplication"""
    # For ~70 schemes, we can afford to search for a few extra results
    search_k = min(top_k + 2, vector_store.index.ntotal)
    docs_and_scores = vector_store.similarity_search_with_score(query, k=search_k)
    
    results = []
    seen_schemes = set()  # Track unique schemes by URL or Name
    
    for doc, score in docs_and_scores:
        scheme_name = doc.metadata.get("Name", "Unknown")
        scheme_url = doc.metadata.get("URL", "")
        
        # Use URL as primary identifier, fallback to name
        scheme_id = scheme_url if scheme_url else scheme_name
        
        # Skip if we've already seen this scheme
        if scheme_id in seen_schemes:
            continue
            
        seen_schemes.add(scheme_id)
        results.append({
            "Name": scheme_name,
            "URL": scheme_url,
            "Summarized_content": doc.metadata.get("Summarized_content", ""),
            "content": doc.page_content,
            "score": float(score)  # Convert numpy float to Python float
        })
        
        # Stop once we have enough unique schemes
        if len(results) >= top_k:
            break
    
    # Clean up
    del docs_and_scores
    gc.collect()
    
    print(f"Found {len(results)} unique relevant schemes")
    return results

def call_gemini_api_optimized(prompt: str, api_key: str) -> str:
    """Optimized Gemini API call with error handling"""
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        "X-goog-api-key": api_key, 
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 2048,  # Limit output to save bandwidth
            "temperature": 0.1  # Lower temperature for more consistent output
        }
    }
    
    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def contextual_rerank_optimized(query: str, top_schemes: List[Dict], api_key: str) -> str:
    """Memory-optimized reranking"""
    
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
        content = scheme.get('content', '')
        if scheme.get('Summarized_content'):
            content = scheme['Summarized_content']
        
        user_prompt += (
            f"\nScheme {i}:\n"
            f"Name: {scheme['Name']}\n"
            f"URL: {scheme['URL']}\n"
            f"Content: {content}\n"
            f"(Relevance score: {scheme['score']:.3f})\n"
        )
    
    user_prompt += "\nNow output ONLY the JSON object as instructed."
    
    return call_gemini_api_optimized(user_prompt, api_key)

def quick_memory_check(label=""):
    """Enhanced memory monitoring"""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"{label}: {mem_mb:.2f} MB")
    return mem_mb

def get_schemes(schemes: List[Dict], user_location: str, query: str, top_k: int = 3, api_key: str = "") -> Dict:
    """
    Ultra memory-optimized main function using Model2Vec (8MB model)
    """

    quick_memory_check("START")
    try:
        # Step 1: Preprocess schemes efficiently
        texts, metadatas, filtered_count = preprocess_schemes(schemes, user_location)
        
        if not texts:
            return {"error": "No schemes found for the specified location"}
        
        print(f"Processing {filtered_count} filtered schemes with Model2Vec")
        
        quick_memory_check("After preprocessing")

        # Step 2: Create vector store with ultra-low memory usage
        vector_store = create_vector_store_efficiently(texts, metadatas)
        
        # Clean up intermediate data
        del texts, metadatas
        gc.collect()

        quick_memory_check("After vector store (Model2Vec)")
        
        # Step 3: Perform semantic search
        top_schemes = semantic_search_optimized(vector_store, query, top_k)
        
        quick_memory_check("After search")

        # Step 4: Clean up vector store
        del vector_store
        gc.collect()
        
        # Step 5: Rerank with Gemini
        response_text = contextual_rerank_optimized(query, top_schemes, api_key)
        
        # Step 6: Parse response
        cleaned_response = response_text.strip()
        quick_memory_check("After reranking")
        
        # Remove markdown fences if present
        if cleaned_response.startswith("```"):
            lines = cleaned_response.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_response = '\n'.join(lines)
        
        try:
            recommended_schemes = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Fallback: create basic recommendations from top schemes
            print(f"JSON parsing failed: {e}")
            recommended_schemes = {}
            for scheme in top_schemes:
                recommended_schemes[scheme['Name']] = {
                    "URL": scheme['URL'],
                    "Reason": f"Relevant match for: {query}"
                }
        
        # Final cleanup
        del top_schemes
        gc.collect()
        
        quick_memory_check("Final Recommendation schemes sent")
        
        return recommended_schemes
        
    except Exception as e:
        # Ensure cleanup even on error
        gc.collect()
        raise Exception(f"Error in get_schemes: {str(e)}")

def eligibility_check(rec_schemes: Dict, schemes: List[Dict]) -> Dict:
    """
    Memory-optimized eligibility check
    """
    QA_checks = {}
    
    # Create URL lookup for efficiency
    url_to_qa = {}
    for scheme in schemes:
        
        url = scheme.get("URL", "").strip()
        if url:
            url_to_qa[url] = scheme.get("Eligibility_QA", {})

    
    # print(url_to_qa['https://agriculture.vikaspedia.in/viewcontent/schemesall/schemes-for-farmers/pm-kisan-maan-dhan-yojana?lgn=en'])
    # Match recommended schemes
    for rec_name, rec_data in rec_schemes.items():
        rec_url = rec_data.get("URL", "").strip()
        print(f"Checking eligibility for {rec_name} with URL: {rec_url}")
        if rec_url in url_to_qa:
            QA_checks[rec_name] = url_to_qa[rec_url]

    quick_memory_check("Eligiblity Questions sent")
    print(f"Eligibility checks for {len(QA_checks)} schemes completed")
    
    return QA_checks

def compare_scheme_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Optimized dictionary comparison
    """
    all_keys = set(dict1.keys()) | set(dict2.keys())
    quick_memory_check("Eligiblity Check done")
    return {
        key: "Yes" if dict1.get(key) == dict2.get(key) else "No"
        for key in all_keys
    }