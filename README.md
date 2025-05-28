
# BUITEMS Assist 🧠🎓

A smart, AI-powered chatbot built for BUITEMS University students — created over 3 semesters of dedication, learning, and experimentation.

This isn’t just another chatbot.

It’s my Final Year Project — a full-stack intelligent assistant that answers timetable questions, FAQs, and university-related queries using:
- 🧠 OpenAI GPT-3.5 Turbo
- 📚 FAISS + Sentence Transformers
- 📅 Pandas-powered timetable queries
- 💬 Natural Language Processing (SpaCy)
- 🛠️ Flask + SQLite + HTML/CSS/JS

> Built completely from scratch — with love, frustration, failure, and learning.
> ⚠️ This version is not production-ready. It’s a working prototype under development, with known UI issues and partial database content.

---

## 📌 Features

- 🕐 Ask for class timings like "When is DSA on Tuesday?"
- ❓ Ask university FAQs like "Where is the cafeteria?"
- 🤖 GPT fallback for open-ended queries
- 🔐 Admin panel to manage FAQs
- ⚙️ Built-in FAISS vector search for speed

---

## 🚀 How to Use This Project

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/buitems-assist.git
cd buitems-assist
```

### 2. Set Up Environment

Install required libraries:

```bash
pip install -r requirements.txt
```

### 3. Add Your OpenAI Key

Create a file named `.env` in the root folder:

```
OPENAI_API_KEY=your-key-here
```



---

### 4. Run the App

```bash
python app.py
```

Then open `http://localhost:5000` in your browser.

---

## 🗂️ Project Structure

```
app.py                 # Main Flask app
templates/             # HTML pages
static/                # CSS / JS
chatbot.db             # SQLite database (FAQs)
timetable_cleaned.csv  # Timetable data
requirements.txt       # All dependencies
.gitignore             # Ignore unnecessary files
.env                   # Your OpenAI key (not uploaded)
```

---

## ⚠️ Notes

- You must have Python 3.7+ installed.
- Internet is required for OpenAI responses.
- FAISS and sentence-transformers must be installed correctly.

---

## ❤️ A Note from the Developer

> This project wasn’t easy. I built this while managing full-time studies, assignments, and other responsibilities.  
>  
> I failed a lot. Fixed bugs that made no sense. Tried features that didn’t work.  
> But I kept going.  
>  
> If this repo helps you — as a student, a developer, or a dreamer — it was all worth it.

You’re free to use it, extend it, or just learn from it.

**— Built by Shahbaz siddiqui for BUITEMS, 2025**

---

## 📫 Contact

If you want to say thanks or have questions:

📧 Email: theshahbaz081@gmail.com 
🐙 GitHub: [@shahbazSQ](https://github.com/ShahbazSQ)

---

## 🏁 License

This project is open-source. Feel free to fork, learn, and build on top of it. Attribution appreciated.
