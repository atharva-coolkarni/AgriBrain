import os
import psutil


import requests
import json
import time
import re

def quick_memory_check(label=""):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"{label}: {mem_mb:.2f} MB")
    return mem_mb

# Example usage:
quick_memory_check("Start of translation.py")

# --- Gemini API Call ---
def call_gemini_api(prompt: str) -> str:
    headers = {"X-goog-api-key": "AIzaSyBcg_7ZoX3AjjjPqvYecB_S80WfJhRxjqg", "Content-Type": "application/json"}
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"API call failed: {e}")
        return ""


# --- Translation Agent (for English to other languages) ---
class TranslationAgent:
    def __init__(self, target_lang):
        self.target_lang = target_lang

    def translate_key_only(self, key: str) -> str:
        """Translate only a key"""
        prompt = f"""
Translate this JSON key into {self.target_lang} language using the NATIVE SCRIPT of {self.target_lang}.

IMPORTANT RULES:
1. Use the native script/writing system of {self.target_lang} (NOT English letters)
2. Do NOT transliterate – translate properly into native script
3. If Hindi, use Devanagari script (हिंदी में लिखें)
4. If Tamil, use Tamil script (தமிழில் எழுதுங்கள்)
5. If Telugu, use Telugu script (తెలుగులో వ్రాయండి)
6. If Bengali, use Bengali script (বাংলায় লিখুন)
7. If Gujarati, use Gujarati script (ગુજરાતીમાં લખો)
8. If Marathi, use Devanagari script (मराठीत लिहा)
9. If Kannada, use Kannada script (ಕನ್ನಡದಲ್ಲಿ ಬರಯಿರಿ)
10. If Malayalam, use Malayalam script (മലയാളത്തിൽ എഴുതൂ)
11. If Punjabi, use Gurmukhi script (ਪੰਜਾਬੀ ਵਿੱਚ ਲਿਖੋ)
12. If Arabic, use Arabic script (اكتب بالعربية)
13. Return ONLY the translated text in native script, no English letters

Text to translate: {key}

Translated key in {self.target_lang} native script:
"""

        output = call_gemini_api(prompt).strip()
        output = self._clean_output(output)
        
        # Check if output contains English letters (indicates transliteration issue)
        if self._contains_english_letters(output) and not self._is_english_language():
            # Retry with more specific prompt
            return self._retry_translation_key(key)
        
        # If translation failed or is empty, return original key
        if not output or output == key:
            print(f"Key translation failed for: {key}")
            return key
            
        return output

    def translate_value_only(self, value: str) -> str:
        """Translate only a value"""
        prompt = f"""
Translate this text into {self.target_lang} language using the NATIVE SCRIPT of {self.target_lang}.

IMPORTANT RULES:
1. Use the native script/writing system of {self.target_lang} (NOT English letters)
2. Do NOT transliterate – translate properly into native script
3. If Hindi, use Devanagari script (हिंदी में लिखें)
4. If Tamil, use Tamil script (தமிழில் எழுதுங்கள்)
5. If Telugu, use Telugu script (తెలుగులో వ్రాయండి)
6. If Bengali, use Bengali script (বাংলায় লিখুন)
7. If Gujarati, use Gujarati script (ગુજરાતીમાં લખો)
8. If Marathi, use Devanagari script (मराठीत लिहा)
9. If Kannada, use Kannada script (ಕನ್ನಡದಲ್ಲಿ ಬರಯಿರಿ)
10. If Malayalam, use Malayalam script (മലയാളത്തിൽ എഴുതൂ)
11. If Punjabi, use Gurmukhi script (ਪੰਜਾਬੀ ਵਿੱਚ ਲਿਖੋ)
12. If Arabic, use Arabic script (اكتب بالعربية)
13. Return ONLY the translated text in native script, no English letters

Text to translate: {value}

Translated text in {self.target_lang} native script:
"""

        output = call_gemini_api(prompt).strip()
        output = self._clean_output(output)
        
        # Check if output contains English letters (indicates transliteration issue)
        if self._contains_english_letters(output) and not self._is_english_language():
            # Retry with more specific prompt
            return self._retry_translation_value(value)
        
        # If translation failed or is empty, return original value
        if not output:
            print(f"Value translation failed for: {value}")
            return value
            
        return output

    def _contains_english_letters(self, text: str) -> bool:
        """Check if text contains English letters (indicates transliteration)"""
        import re
        # Check for English alphabets
        return bool(re.search(r'[a-zA-Z]', text))
    
    def _is_english_language(self) -> bool:
        """Check if target language is English"""
        return self.target_lang.lower() in ['en', 'english', 'eng']
    
    def _retry_translation_key(self, key: str) -> str:
        """Retry translation with more explicit prompt for keys"""
        language_examples = {
            'hindi': 'हिंदी में (जैसे: किसानों के लिए क्रेडिट सुविधा)',
            'tamil': 'தமிழில் (உதாரணம் போன்று)',
            'telugu': 'తెలుగులో (ఉదాహరణకు)',
            'bengali': 'বাংলায় (উদাহরণস্বরূপ)',
            'gujarati': 'ગુજરાતીમાં (ઉદાહરણ તરીકે)',
            'marathi': 'मराठीत (उदाहरणार्थ)',
            'kannada': 'ಕನ್ನಡದಲ್ಲಿ (ಉದಾಹರಣೆಗೆ)',
            'malayalam': 'മലയാളത്തിൽ (ഉദാഹരണത്തിന്)',
            'punjabi': 'ਪੰਜਾਬੀ ਵਿੱਚ (ਉਦਾਹਰਨ ਲਈ)'
        }
        
        example = language_examples.get(self.target_lang.lower(), f'in {self.target_lang} native script')
        
        prompt = f"""
CRITICAL: Translate this text into {self.target_lang} using ONLY the native script {example}.

DO NOT USE ENGLISH LETTERS AT ALL. Write completely in the native script of {self.target_lang}.

Examples of WRONG output (DO NOT DO THIS):
- "Kisaanon ke lie kredit suvidha" (This is transliteration - WRONG)
- "Farmer ke liye scheme" (This mixes languages - WRONG)

Examples of CORRECT output:
- For Hindi: "किसानों के लिए क्रेडिट सुविधा" (Pure Devanagari script)

Text to translate: {key}

Write the translation using ONLY {self.target_lang} native script:
"""
        
        output = call_gemini_api(prompt).strip()
        output = self._clean_output(output)
        
        # Final check - if still contains English, return original
        if self._contains_english_letters(output) and not self._is_english_language():
            print(f"❌ Retry failed, keeping original: {key}")
            return key
            
        return output if output else key
    
    def _retry_translation_value(self, value: str) -> str:
        """Retry translation with more explicit prompt for values"""
        language_examples = {
            'hindi': 'हिंदी में (जैसे: किसानों के लिए क्रेडिट सुविधा)',
            'tamil': 'தமிழில் (உதாரணம் போன்று)',
            'telugu': 'తెలుగులో (ఉదాహరణకు)',
            'bengali': 'বাংলায় (উদাহরণস্বরূপ)',
            'gujarati': 'ગુજરાતીમાં (ઉદાહરણ તરીકે)',
            'marathi': 'मराठीत (उदाहरणार्थ)',
            'kannada': 'ಕನ್ನಡದಲ್ಲಿ (ಉದಾಹರಣೆಗೆ)',
            'malayalam': 'മലയാളത്തിൽ (ഉദാഹരണത്തിന്)',
            'punjabi': 'ਪੰਜਾਬੀ ਵਿੱਚ (ਉਦਾਹਰਨ ਲਈ)'
        }
        
        example = language_examples.get(self.target_lang.lower(), f'in {self.target_lang} native script')
        
        prompt = f"""
CRITICAL: Translate this text into {self.target_lang} using ONLY the native script {example}.

DO NOT USE ENGLISH LETTERS AT ALL. Write completely in the native script of {self.target_lang}.

Text to translate: {value}

Write the translation using ONLY {self.target_lang} native script:
"""
        
        output = call_gemini_api(prompt).strip()
        output = self._clean_output(output)
        
        # Final check - if still contains English, return original
        if self._contains_english_letters(output) and not self._is_english_language():
            print(f"❌ Retry failed, keeping original: {value}")
            return value
            
        return output if output else value

    def should_translate_value(self, key: str) -> bool:
        """Determine if a value should be translated based on its key"""
        if not isinstance(key, str):
            return False
            
        # Only translate values for "Reason" key
        if key.lower() == 'reason':
            return True
            
        # Don't translate any other values
        return False

    def should_translate_key(self, key: str) -> bool:
        """Determine if a key should be translated"""
        if not isinstance(key, str):
            return False
            
        # Skip these keys from translation
        if key.lower() in ['answer', 'follow_ups', 'reason', 'url']:
            return False
            
        # Translate all other keys
        return True
    
    def _clean_output(self, text: str) -> str:
        """Clean the API response text"""
        # Remove code block markers
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) > 1:
                text = "\n".join(lines[1:])
        if text.endswith("```"):
            lines = text.splitlines()
            if len(lines) > 1:
                text = "\n".join(lines[:-1])
        
        # Remove extra quotes if present
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
            
        return text.strip()


# --- English Translation Agent (for other languages to English) ---
class EnglishTranslationAgent:
    def __init__(self):
        pass
    
    def detect_and_translate_to_english(self, text: str, language: str) -> str:
        """Translate text from a specified language to English"""
        prompt = f"""
You are a translation expert. Your task is to:

1. Translate the following text from {language} to English.
2. Provide a natural, accurate English translation.
3. Maintain the original meaning and context.
4. If the text is already in English, return it as-is.
5. Return ONLY the English translation, no explanations or additional text.

Text to translate ({language}): {text}

English translation:
"""
        output = call_gemini_api(prompt).strip()
        output = self._clean_output(output)
        # If translation failed or is empty, return original text
        if not output:
            print(f"English translation failed for: {text}")
            return text
        return output
    
    def _clean_output(self, text: str) -> str:
        """Clean the API response text"""
        # Remove code block markers
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) > 1:
                text = "\n".join(lines[1:])
        if text.endswith("```"):
            lines = text.splitlines()
            if len(lines) > 1:
                text = "\n".join(lines[:-1])
        
        # Remove extra quotes if present
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
            
        return text.strip()


# --- Function to translate query to English ---
def translate_query_to_english(content_dict, language):
    """
    Translate query value from a specified language to English
    Expected format: {'query': 'text in other language'}
    Args:
        content_dict: Dictionary with 'query' key
        language: The current language of the input query
    """
    if not isinstance(content_dict, dict) or 'query' not in content_dict:
        print("❌ Invalid format: Expected {'query': 'text'}")
        return content_dict
    print("🔄 Translating to English...")
    agent = EnglishTranslationAgent()
    original_query = content_dict['query']
    print(f"🔍 Original query: {original_query}")
    # Translate to English using the provided language
    translated_query = agent.detect_and_translate_to_english(original_query, language)
    print(f"🌍 Translated query: {translated_query}")
    # Return the updated dictionary
    quick_memory_check("End of translate_dict (to English)")
    return {'query': translated_query}


# --- Main recursive function (for English to other languages) ---
def translate_nested_dict(data, agent: TranslationAgent):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            
            # Only translate the key if it meets our criteria
            if agent.should_translate_key(k):
                new_key = agent.translate_key_only(k)
                time.sleep(0.3)  # Rate limiting
            else:
                new_key = k
            
            # Handle string values - check if we should translate based on the key
            if isinstance(v, str):
                if agent.should_translate_value(k):
                    new_value = agent.translate_value_only(v)
                    time.sleep(0.3)  # Rate limiting
                else:
                    new_value = v
                
                new_dict[new_key] = new_value

            elif isinstance(v, dict):
                # Recurse for dicts
                new_dict[new_key] = translate_nested_dict(v, agent)

            elif isinstance(v, list):
                # Recurse for lists
                new_dict[new_key] = [translate_nested_dict(item, agent) for item in v]

            else:
                # Keep other types as-is
                new_dict[new_key] = v

        return new_dict

    elif isinstance(data, list):
        return [translate_nested_dict(item, agent) for item in data]
        
    elif isinstance(data, str):
            # If we encounter a string directly in a list, don't translate it
        return data
        
    else:
        return data


# --- Main Translation Function ---
def translate_dict(content_dict, language):
    """
    Main translation function that handles both directions:
    1. English to other languages (existing functionality)
    2. Other languages to English (new functionality)
    
    Args:
        content_dict: Dictionary to translate
        language: Target language ('english'/'en' for translating TO English)
    
    Returns:
        Translated dictionary
    """
    
    print(f"🔄 Translating to {language}...")
    agent = TranslationAgent(target_lang=language)
    translated_dict = translate_nested_dict(content_dict, agent)
    quick_memory_check(f"End of translate_dict (to {language})")
    return translated_dict



    
