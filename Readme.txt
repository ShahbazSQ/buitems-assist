# 🧠 AI Chatbot using Flask & Gemini API

This is a Buitems AI chatbot built using **Flask** and **Google Gemini API**, capable of responding to user queries using natural language understanding. It also supports a simple admin dashboard (if configured) for managing FAQs.

---

## 🚀 Features

- Conversational AI powered by **Google Gemini**
- Built with **Flask (Python backend)**
- SQLite database for optional FAQ storage
- Supports semantic search using **FAISS** (optional)
- Modular code structure
- Easy to deploy (Render, Replit, Streamlit, etc.)

---

## 🛠️ Setup & Installation

### ✅ Prerequisites

- Python 3.8+
- Google Gemini API key (via Google AI Studio)
- Git (optional)

---

### 📥 1. Clone the Repository

```bash
git clone https://github.com/ShahbazSQ/buitems-assist
cd ai-chatbot-flask
📦 2. Install Dependencies
Make sure you have a virtual environment (recommended):

Install your virtual env:
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

Install required packages:
pip install -r requirements.txt

🔐 3. Set Up Environment Variables
Create a .env file in the project root:
GEMINI_API_KEY=your_google_gemini_api_key_here

▶️ 4. Run the Application
python app.py

📁 Project Structure
bash
Copy
Edit
buitems-assist/
├── app.py               # Flask application
├── utils.py             # Gemini API functions
├── database.py          # (Optional) DB & FAISS setup
├── templates/           # HTML templates (if UI exists)
├── static/              # CSS, JS, etc.
├── requirements.txt
├── .env                 # Environment variables (not committed)
└── README.md
