import requests
import asyncio
from playwright.async_api import async_playwright
import json
import os
import time
import urllib3
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def create_database(connection_string,database_name, collection_name):

    schemes = []  # Global variable to store results
    MIN_DELAY_BETWEEN_CALLS = 2.0  # seconds between API calls
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 3  # seconds
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    _last_call_time = 0

    BASE_API = "https://data.vikaspedia.in/api/public/content/page-content?ctx="

    def clear_collection(connection_string,database_name, collection_name):
        """
        Removes all documents from the agricultural_schemes collection.
        
        Args:
            connection_string (str): MongoDB connection string.
        """
        try:
            client = MongoClient(connection_string)
            db = client[database_name]
            collection = db[collection_name]

            result = collection.delete_many({})
            print(f"Deleted {result.deleted_count} documents from agricultural_schemes collection.")

        except Exception as e:
            print(f"Failed to clear collection: {e}")
        finally:
            client.close()

    def extract_folder_context_paths(api_url):
        try:
            
            resp = requests.get(api_url, verify=False)
            resp.raise_for_status()
            data = resp.json()
            folder_context_paths = []
            content_list = data.get("contentList", [])
            for item in content_list:
                # Some items may be nested lists:
                if isinstance(item, list):
                    for subitem in item:
                        if subitem.get("context_type") == "folder":
                            folder_context_paths.append(subitem["context_path"])
                elif isinstance(item, dict):
                    if item.get("context_type") == "folder":
                        folder_context_paths.append(item["context_path"])
            return folder_context_paths
        except Exception as e:
            print(f"Error processing {api_url}: {e}")
            return []
    def extract_folder_context_paths_lower(api_url):
        try:
            resp = requests.get(api_url, verify=False)
            resp.raise_for_status()
            data = resp.json()

            folder_context_paths = []

            for item in data.get("contentList", []):
                # If this level is a dictionary
                if isinstance(item, dict):
                    if item.get("context_type") == "document":
                        folder_context_paths.append(item["context_path"])
                # If this level is a list of dictionaries
                elif isinstance(item, list):
                    for subitem in item:
                        if isinstance(subitem, dict) and subitem.get("context_type") == "document":
                            folder_context_paths.append(subitem["context_path"])

            return folder_context_paths
        except Exception as e:
            print(f"Error processing {api_url}: {e}")
            return []

    async def extract_toc_sections(page):
        # Find the Table of Contents "Benefits", "Eligibility", etc. in anchor tags
        try:
            toc_selector = 'ul.MuiList-root'  # Adjust as per the actual TOC class/id seen in your screenshots
            toc_list = await page.query_selector(toc_selector)
            if not toc_list:
                return []  # No TOC found

            anchors = await toc_list.query_selector_all('a')
            toc_sections = []
            for a in anchors:
                try:
                    text = (await a.inner_text()).strip()
                    if text:
                        toc_sections.append(text)
                except Exception as e:
                    print(f"Error extracting TOC anchor text: {e}")
            return toc_sections
        except Exception as e:
            print(f"Error extracting TOC sections: {e}")
            return []

    async def extract_section_text_by_heading(page, heading_text):
        # [same as your previous code, unchanged]
        try:
            heading_handle = await page.query_selector(
                f"xpath=//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6][contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{heading_text.lower()}')]"
            )
            if not heading_handle:
                return None

            texts = []
            element_handle = heading_handle
            while True:
                try:
                    element_handle = await element_handle.evaluate_handle("el => el.nextElementSibling")
                    if not element_handle or await element_handle.evaluate("el => el === null"):
                        break
                    tag_name = await element_handle.evaluate("el => el.tagName && el.tagName.toLowerCase()")
                    if not tag_name:
                        break
                    if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    if tag_name in ['p', 'ul', 'ol', 'div', 'li']:
                        text = (await element_handle.inner_text()).strip()
                        if text:
                            texts.append(text)
                    elif tag_name == 'table':
                        table_html = await element_handle.inner_html()
                        from bs4 import BeautifulSoup
                        from bs4.element import Tag
                        soup = BeautifulSoup(table_html, 'html.parser')
                        table_text = []
                        for row in soup.find_all('tr'):
                            if isinstance(row, Tag):
                                cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td']) if isinstance(cell, Tag)]
                                if cells:
                                    table_text.append('\t'.join(cells))
                        if table_text:
                            texts.append('\n'.join(table_text))
                except Exception as e:
                    print(f"Error extracting section sibling: {e}")
                    break
            return "\n".join(texts).strip() if texts else None
        except Exception as e:
            print(f"Error extracting section by heading '{heading_text}': {e}")
            return None

    async def scrape_scheme_sections(url):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.goto(url, wait_until="networkidle", timeout=100000)
                except Exception as e:
                    print(f"Error loading {url}: {e}")
                    await browser.close()
                    return {}
                await page.wait_for_timeout(10000)

                # Step 1: Extract section names from Table of Contents
                sections_to_extract = await extract_toc_sections(page)
                print(f"Sections found in TOC: {sections_to_extract}")

                # Step 2: Extract content for each section
                results = {}
                for section in sections_to_extract:
                    try:
                        text = await extract_section_text_by_heading(page, section)
                        results[section] = text or "[Section not found]"
                    except Exception as e:
                        print(f"Error extracting section '{section}': {e}")
                        results[section] = "[Section not found]"

                await browser.close()
                return results
        except Exception as e:
            print(f"Error in scrape_scheme_sections for {url}: {e}")
            return {}

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    GEMINI_API_KEY = os.environ.get("VEDU_GEMINI_API_KEY")  # replace with your key or set env var

    def call_gemini_api_safe(prompt: str) -> str:
        """
        Calls Gemini API with rate limiting and retry logic to avoid hitting 429 errors.
        """
        nonlocal _last_call_time

        api_key = GEMINI_API_KEY
        headers = {"X-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        retries = 0
        while retries <= MAX_RETRIES:
            # Enforce delay between API calls
            elapsed = time.time() - _last_call_time
            if elapsed < MIN_DELAY_BETWEEN_CALLS:
                time.sleep(MIN_DELAY_BETWEEN_CALLS - elapsed)

            try:
                response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
                if response.status_code == 429:
                    # Backoff on rate limit
                    wait_time = INITIAL_BACKOFF * (2 ** retries)
                    print(f"[Gemini] 429 Too Many Requests. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                # Raise for any other HTTP errors
                response.raise_for_status()

                data = response.json()
                _last_call_time = time.time()  # Update last call time
                return data['candidates'][0]['content']['parts'][0]['text']

            except requests.exceptions.RequestException as e:
                if retries < MAX_RETRIES:
                    wait_time = INITIAL_BACKOFF * (2 ** retries)
                    print(f"[Gemini] Error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print("[Gemini] Max retries reached. Skipping this request.")
                    raise e

        return ""

    class GeminiChatAgent:
        def __init__(self, name):
            self.name = name
        def chat(self, messages):
            prompt = ""
            for msg in messages:
                prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
            return call_gemini_api_safe(prompt)
        
    def generate_eligibility_qa_pairs(scheme_name, scheme_url, eligibility_text):
        """
        For a given scheme, generate yes/no question–answer pairs covering all eligibility rules.
        Output: dict {question: expected_answer ("Yes" or "No")}
        If eligibility_text is empty, returns an empty dict without calling Gemini.
        """
        # If eligibility text is empty or only whitespace, return empty dict
        if not eligibility_text or not eligibility_text.strip():
            return {}

        prompt = (
            f"You will generate question–answer pairs for the eligibility criteria of an agricultural scheme.\n"
            f"Scheme Name: {scheme_name}\n"
            f"Scheme URL: {scheme_url}\n"
            f"Eligibility details:\n{eligibility_text}\n\n"
            "Your task:\n"
            "- Extract each clear eligibility rule as a main question.\n"
            "- For each rule, give the expected answer ('Yes' or 'No').\n"
            "- If there are follow-up questions that apply only if the main answer is 'Yes' (often marked as 'if applicable'),\n"
            "  nest them under that main question in a sub-dictionary:\n"
            "  {\n"
            '    "Main question": {\n'
            '      "answer": "Yes",\n'
            '      "follow_ups": {\n'
            '        "Conditional question 1": "Yes",\n'
            '        "Conditional question 2": "No"\n'
            '      }\n'
            '    }\n'
            "  }\n"
            "- If no follow-ups, just output the main question key with its Yes/No answer.\n"
            "- Only output a valid JSON object, no extra text.\n"
        )

        agent = GeminiChatAgent(name="EligibilityQAAgent")
        response_text = agent.chat([{"role": "user", "content": prompt}])

        lines = response_text.split('\n')

        # Remove first and last line (which are the markdown code fences)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]

        # Join back into a clean JSON string
        cleaned_response = '\n'.join(lines)

        try:
            qa_pairs = json.loads(cleaned_response)
        except Exception:
            print(f"[Warning] Gemini output was not valid JSON for scheme: {scheme_name}")
            print("Raw output:", cleaned_response)
            qa_pairs = {}

        return qa_pairs

    def summarize_section_with_gemini(section_title, section_content):
        """
        For a given section, use Gemini to summarize the topic content.
        Returns the summarized section as a string.
        """
        if not section_content or section_content.strip() == "[Section not found]":
            return ""  # skip empty or not found sections

        prompt = (
            f"You are an assistant that summarizes Indian government scheme documentation for easy farmer understanding.\n"
            f"Summarize the following scheme section, keeping any critical eligibility, benefit, or application insights. Do not omit important details.\n"
            f"Section Title: {section_title}\n"
            f"Section Content:\n{section_content.strip()}\n\n"
            "Output:\nA concise, paragraph-style summary of this section in clear, simple language. Do not include the title in the summary."
        )
        try:
            summarized = call_gemini_api_safe(prompt)
            return summarized.strip()
        except Exception as e:
            print(f"[Summarization error] {section_title}: {e}")
            return ""

    def safe_summarize(topic, section_text):
        retries = 0
        while retries < 3:
            try:
                return summarize_section_with_gemini(topic, section_text)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2 ** retries
                    print(f"Hit rate limit. Waiting {wait} seconds before retry...")
                    time.sleep(wait)
                    retries += 1
                else:
                    raise
        return ""

    def add_schemes_to_mongo(scheme, connection_string,database_name="scheme_db", collection_name="agricultural_schemes"):
        """
        Inserts a list of scheme dictionaries into MongoDB.
        
        Args:
            schemes (list): List of scheme dictionaries.
            connection_string (str): MongoDB connection string.
        """
        try:
            client = MongoClient(connection_string)
            db = client[database_name]  # Database name
            collection = db[collection_name]  # Collection name

            if not schemes:
                print("No schemes to insert into MongoDB.")
                return

            # Bulk insert
            collection.insert_one(scheme)
            print(f"Inserted scheme into MongoDB.")

        except Exception as e:
            print(f"MongoDB insertion failed: {e}")
        finally:
            client.close()


        
        clear_collection(connection_string, database_name, collection_name)
        # Step 1: Get top-level folders (states)
        root_api = "https://data.vikaspedia.in/api/public/content/page-content?ctx=/agriculture/state-specific-schemes-for-farmers&lgn=en"
        top_folder_paths = extract_folder_context_paths(root_api)

        
        # Step 2: Build API URLs for each folder
        folder_api_urls = [f"{BASE_API}{path}&lgn=en" for path in top_folder_paths]

        # Step 3: For each state folder, get its subfolders and save to state_schemes
        for api_url in folder_api_urls:
            # Extract key: last segment after "/" in context_path
            key = api_url.split("/")[-1]
            # Sometimes context_path may end with trailing segments; clean up:
            if "&lgn=" in key:
                key = key.split("&lgn=")[0]
            # Also, if path has wildcards, use only the state name
            if "?" in key:
                key = key.split("?")[0]
            
            subfolder_paths = extract_folder_context_paths_lower(api_url)
            final_subfolder_paths = [f"https://agriculture.vikaspedia.in/viewcontent{path}?lgn=en" for path in subfolder_paths]
            for path in final_subfolder_paths:
                curr = {
                "State_specific_Schemes": key,
                "URL": path
                }
                schemes.append(curr)
            
        
        central_root_url = "https://data.vikaspedia.in/api/public/content/page-content?ctx=/schemesall/schemes-for-farmers&lgn=en"
        central_folder_paths = extract_folder_context_paths_lower(central_root_url)

        # Step 2: Build API URLs for each folder
        paths = [f"https://agriculture.vikaspedia.in/viewcontent{path}?lgn=en" for path in central_folder_paths]
        for path in paths:
            curr = {
                "State_specific_Schemes": "NO",
                "URL": path
            }
            schemes.append(curr)
            
        for scheme in schemes:
            try:
                url = scheme["URL"]
                print(url)
                sections = asyncio.run(scrape_scheme_sections(url))
                scheme.update(sections)
                content = "\n\n".join([f"##{sec}## \n {text}" for sec, text in sections.items()])
                scheme["content"] = content if content else "No content found"

                summarized_sections = []
                for topic, section_text in sections.items():
                    summarized =  safe_summarize(topic, section_text)
                    if summarized:
                        summarized_sections.append(f"##{topic}##\n{summarized}")
                scheme["Summarized_content"] = "\n\n".join(summarized_sections)

                url_no_query = url.split('?')[0]

                # Step 2: Extract the last part of the path after the last '/'
                last_segment = url_no_query.split('/')[-1]

                # Step 3: Replace hyphens '-' with spaces ' '
                title = last_segment.replace('-', ' ')
                scheme["Name"] = title

                merged_text_parts = []
                # Iterate through keys in recommended_schemes
                    
                        # Check if scheme has 'Eligibility'
                if "Eligibility" in scheme and scheme["Eligibility"]:
                    merged_text_parts.append(str(scheme["Eligibility"]).strip())
                        
                        # Check if scheme has 'Documents'
                if "Documents" in scheme and scheme["Documents"]:
                    merged_text_parts.append(str(scheme["Documents"]).strip())

                        # If we have any content, join and save into recommended_schemes
                    
                scheme["Merged_Eligibility"] = "\n\n".join(merged_text_parts)

                if "Merged_Eligibility" in scheme:
                    eligibility_text = scheme["Merged_Eligibility"]
                    scheme_name = key
                    scheme_url = scheme.get("URL", "")
                    qa_pairs = generate_eligibility_qa_pairs(scheme_name, scheme_url, eligibility_text)
                    scheme["Eligibility_QA"] = qa_pairs
                else:
                    scheme["Eligibility_QA"] = {}
                
                
                add_schemes_to_mongo(scheme, connection_string,database_name, collection_name)

            except Exception as e:
                print(f"Error processing scheme {scheme.get('URL', '')}: {e}")
        

    # with open("schemes.json", "w", encoding="utf-8") as f:
    #     json.dump(schemes, f, ensure_ascii=False, indent=4)


