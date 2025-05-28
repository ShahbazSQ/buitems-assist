from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import spacy
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import openai
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from datetime import timedelta

# ===== Load environment variables =====
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "super_secret_key"
CORS(app)

# ===== Load Timetable CSV =====
timetable_df = pd.read_csv("timetable_cleaned.csv")
timetable_df.columns = timetable_df.columns.str.strip().str.capitalize()
timetable_df = timetable_df.astype(str).apply(lambda x: x.str.strip().str.capitalize())

print("Timetable Columns:", timetable_df.columns.tolist())

# ===== NLP Models =====
nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ===== Database =====
db_file = "chatbot.db"

# ===== FAISS Index =====
index = faiss.IndexFlatL2(384)
database_questions = []

# ===== Mappings =====
COURSE_ALIASES = {
    "PF": "Programming Fundamentals",
    "OOP": "Object Oriented Programming",
    "DSA": "Data Structures And Algorithms",
}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]

# ===== Timetable Logic =====
def get_timetable_response(query):
    query = query.lower()
    today = datetime.datetime.today().strftime('%A').capitalize()
    timetable_df.columns = timetable_df.columns.str.strip().str.lower()

    for _, row in timetable_df.iterrows():
        course = str(row['course']).lower()
        day = str(row['day']).capitalize()

        if course and course in query:
            for weekday in WEEKDAYS:
                if weekday in query:
                    day = weekday.capitalize()
            if str(row['day']).lower() == day.lower():
                start = row['class strating time']
                end = row['class ending time']
                room = row['room']
                return f"📘 '{course.title()}' is on {day} from {start} to {end} in room {room}."
    
    return None

def process_query(user_input):
    timetable_answer = get_timetable_response(user_input)
    if timetable_answer:
        return timetable_answer

    user_vector = embedding_model.encode([user_input])
    distances, indices = index.search(np.array(user_vector, dtype=np.float32), k=1)
    if indices[0][0] != -1 and distances[0][0] < 0.9:
        matched_question = database_questions[indices[0][0]]
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT answer FROM faqs WHERE question = ?", (matched_question,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]

    return ask_openai(user_input)

DAY_ALIASES = {
    "monday": "Mon",
    "tuesday": "Tue",
    "wednesday": "Wed",
    "thursday": "Thu",
    "friday": "Fri"
}

def extract_course_entities(user_input):
    doc = nlp(user_input.lower())
    course = day = department = None

    for token in doc:
        if token.text in WEEKDAYS:
            day = token.text.capitalize()
        if token.text.upper() in COURSE_ALIASES:
            course = COURSE_ALIASES[token.text.upper()]
        elif token.text.upper().startswith("CS-"):
            course = token.text.upper()
        if token.text in ["cs", "computer", "software", "electrical", "civil"]:
            department = token.text.capitalize()

    if not day:
        day = datetime.datetime.now().strftime("%A")
    return {"course": course, "day": day, "department": department}

def fetch_timetable_from_db(course, day, department=None):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    query = "SELECT time, room, instructor FROM timetable WHERE 1=1"
    params = []

    if course:
        query += " AND course_code LIKE ?"
        params.append(f"%{course}%")
    if day:
        query += " AND day = ?"
        params.append(day)
    if department:
        query += " AND department LIKE ?"
        params.append(f"%{department}%")

    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()

    if result:
        return f"{course} class on {day} is in room {result[1]} at {result[0]} with {result[2]}."
    else:
        return f"No class found for {course or 'your query'} on {day}."

def load_questions_into_faiss():
    global database_questions
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT question FROM faqs")
    database_questions = [row[0] for row in cursor.fetchall()]
    conn.close()
    if database_questions:
        vectors = embedding_model.encode(database_questions)
        index.reset()
        index.add(np.array(vectors, dtype=np.float32))

load_questions_into_faiss()

def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful university chatbot. Keep responses short and clear."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("Error with OpenAI:", str(e))
        return "Our AI assistant is currently unavailable."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Please provide a valid query."})
    response = process_query(user_input)
    return jsonify({"response": response})

# Admin Panel
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("admin_login.html", error="Invalid credentials.")
    return render_template("admin_login.html")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

def login_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer FROM faqs")
    faqs = cursor.fetchall()
    conn.close()
    return render_template("admin.html", faqs=faqs)

@app.route('/admin/add', methods=['POST'])
@login_required
def add_entry():
    question = request.form.get("question")
    answer = request.form.get("answer")
    if question and answer:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO faqs (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
        conn.close()
        load_questions_into_faiss()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:faq_id>')
@login_required
def delete_entry(faq_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()
    load_questions_into_faiss()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:faq_id>')
@login_required
def edit_entry(faq_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer FROM faqs WHERE id = ?", (faq_id,))
    faq = cursor.fetchone()
    conn.close()
    return render_template("edit.html", faq=faq)

@app.route('/admin/update/<int:faq_id>', methods=['POST'])
@login_required
def update_entry(faq_id):
    question = request.form.get("question")
    answer = request.form.get("answer")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE faqs SET question = ?, answer = ? WHERE id = ?", (question, answer, faq_id))
    conn.commit()
    conn.close()
    load_questions_into_faiss()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
