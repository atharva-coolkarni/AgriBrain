# 🌱 AgriBrain

AgriBrain is an **AI-powered agricultural support platform** designed to empower Indian farmers with **data-driven insights, multilingual support, and government scheme recommendations**.  
The solution focuses on addressing crop selection uncertainty, market price volatility, and lack of awareness about government schemes — ensuring financial sustainability and profitability for small and medium-scale farmers.

---

## 🚀 Features

### 1. **Home Page & Multilingual Interface**
- Farmers can set their location via **GPS, manual input, or Google Maps**.
- Real-time and **7-day weather forecasts** (via Open-Meteo API).
- Multilingual support: **English, Hindi, Punjabi, Tamil, Telugu, Marathi**.
- Both frontend and backend adapt to the farmer’s preferred language.

### 2. **Crop Planner**
- Matches crops with **soil type, pH, weather, and farm resources**.
- Uses a **custom scoring algorithm** to suggest the best-fit crop.
- Generates a **step-by-step crop plan** with Gemini API.
- Provides actionable insights in a **conversational, multilingual format**.

### 3. **Government Scheme Recommendations**
- Personalized scheme suggestions based on **location and farmer needs**.
- Interactive **eligibility Q&A** flow for accurate matching.
- Data pipeline scrapes and summarizes schemes from **authoritative sources (e.g., Vikaspedia)**.
- Stored in **MongoDB Atlas** for scalability and retrieval.

---

## 🛠️ Tech Stack

### Backend
- **Flask (Python)**
- **MongoDB / MongoDB Atlas**
- **LangChain, FAISS, SentenceTransformers**
- **Gemini API** (translation, summarization, contextual Q&A)
- **Open-Meteo API** (real-time weather + 7-day forecast)

### Frontend
- **React.js**
- Multilingual UI + **voice input integration**

---

## 🌟 Innovation Highlights
- **Multilingual & voice-enabled platform** for inclusivity.  
- **Weather-integrated crop planning** for hyper-local accuracy.  
- **AI-driven personalization** using Gemini API.  
- **Scalable, modular design** with Flask + MongoDB.  

---

## 📊 Success Metrics
- **User Satisfaction**: Clear, easy-to-use guidance.  
- **Accuracy**: Verified against real crop outcomes and official schemes.  
- **Inclusivity**: Farmers across multiple Indian languages.  
- **Efficiency**: Fast responses and scalable backend.  

---

## 🏗️ System Architecture

```text
               ┌─────────────────────────┐
               │        Frontend         │
               │        React.js         │
               │  Multilingual + Voice   │
               └───────────┬────────────┘
                           │
                           ▼
               ┌─────────────────────────┐
               │        Backend          │
               │ Flask (Python) + APIs   │
               └───────────┬────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐   ┌────────────────┐   ┌──────────────────────┐
│ Weather API   │   │ Gemini API     │   │ MongoDB / MongoDB Atlas │
│ (Open-Meteo)  │   │ (LLM: plans,   │   │ (crops, schemes,      │
│ Real-time +   │   │ translation,   │   │ eligibility rules)     │
│ 7-day forecast│   │ Q&A)           │   │                      │
└──────────────┘   └────────────────┘   └──────────────────────┘
```
