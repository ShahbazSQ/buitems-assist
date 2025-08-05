from flask import request, jsonify, render_template, redirect, url_for, session
from app import app, assistant_controller, db_file
from assistant import load_questions_into_faiss, analytics_bp, analytics_engine
import sqlite3
import datetime
import pandas as pd

# Load timetable
timetable_df = pd.read_csv("cleaned_fict_timetable.csv")
timetable_df.columns = timetable_df.columns.str.strip().str.lower().str.replace(' ', '_')

# === Admin Config ===
ADMIN_USERNAME = "shehzi"
ADMIN_PASSWORD = "shehzi123"

# === Stateless, Secure Admin ===
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_once'] = True
            return redirect(url_for('admin_protected'))
        else:
            return render_template("admin_login.html", error="Invalid credentials.")
    return render_template("admin_login.html")

@app.route('/admin/protected')
def admin_protected():
    if not session.pop("admin_once", False):
        return redirect(url_for('admin'))
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer FROM faqs")
    faqs = cursor.fetchall()
    conn.close()
    return render_template("admin.html", faqs=faqs)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin'))

@app.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

# === Public Routes ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# === Timetable Logic ===
@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get("message")

    if isinstance(user_input, dict):
        intent = user_input.get("intent")
        program = user_input.get("program")
        semester = user_input.get("semester")
        today = datetime.datetime.now().strftime('%A').lower()

        if intent == "today_classes":
            if not program:
                programs = timetable_df['program'].dropna().unique().tolist()
                return jsonify({
                    "prompt": "Select your department:",
                    "buttons": programs,
                    "followup_intent": "today_classes",
                    "context": {}
                })

            if program and not semester:
                semesters = timetable_df[timetable_df['program'].str.lower() == program.lower()]['semester'].dropna().unique().tolist()
                return jsonify({
                    "prompt": f"Select semester for {program.upper()}:",
                    "buttons": semesters,
                    "followup_intent": "today_classes",
                    "context": {"program": program}
                })

            df = timetable_df[
                (timetable_df['program'].str.lower() == program.lower()) &
                (timetable_df['semester'].str.lower().str.strip() == semester.lower()) &
                (timetable_df['day'].str.lower() == today)
            ]
            if df.empty:
                return jsonify(message=f"No classes today for {program.upper()} {semester}.")

            cards = [
                f"{row['course'].title()} - {row['start_time']} to {row['end_time']} in {row['room'].upper()} with {row['teacher'].title()}"
                for _, row in df.iterrows()
            ]
            return jsonify(
                    message=f"Today's classes for {program.upper()} {semester}:",
                    classes=cards
                )


    if isinstance(user_input, str) and "today" in user_input.lower() and "classes for" in user_input.lower():
        today = datetime.datetime.now().strftime('%A').lower()
        dept = user_input.lower().split("classes for")[-1].strip()
        program_map = {
            "bs-it": "bs-it",
            "bs-cs": "bs-cs",
            "bs-se": "bs-se",
            "bs-ee": "bs-ee",
            "bs-ai": "bs-ai"
        }
        target_prog = program_map.get(dept.lower())
        if target_prog:
            filtered = timetable_df[
                (timetable_df['program'].str.lower() == target_prog) &
                (timetable_df['day'].str.lower() == today)
            ]
            if filtered.empty:
                return jsonify(response=f"No classes found for {dept.upper()} today.")
            msgs = [
                f"📘 {row['course']} ({row.get('course_code', '')}) - {row.get('semester', '')} Semester, Section {row.get('section', '')} at {row.get('start_time')} in {row.get('room', '')} with {row.get('teacher', '')}"
                for _, row in filtered.iterrows()
            ]
            return jsonify(message="\n\n".join(msgs))

    if not user_input:
        return jsonify({"response": "Please provide a valid query."})

    response = assistant_controller.smart_handle_query(user_input)
    return jsonify({"response": response})

# === Admin Q&A Actions ===
@app.route('/admin/add', methods=['POST'])
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
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:faq_id>')
def delete_entry(faq_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()
    load_questions_into_faiss()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:faq_id>')
def edit_entry(faq_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer FROM faqs WHERE id = ?", (faq_id,))
    faq = cursor.fetchone()
    conn.close()
    return render_template("edit.html", faq=faq)

@app.route('/admin/update/<int:faq_id>', methods=['POST'])
def update_entry(faq_id):
    question = request.form.get("question")
    answer = request.form.get("answer")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE faqs SET question = ?, answer = ? WHERE id = ?", (question, answer, faq_id))
    conn.commit()
    conn.close()
    load_questions_into_faiss()
    return redirect(url_for('admin'))

# === Analytics Blueprint ===
@analytics_bp.route('/top', methods=['GET'])
def get_top_queries():
    top = analytics_engine.top_queries()
    return jsonify({"top_queries": top})

@analytics_bp.route('/unanswered', methods=['GET'])
def get_unanswered():
    unanswered = analytics_engine.unanswered_queries()
    return jsonify({"unanswered_queries": unanswered})

app.register_blueprint(analytics_bp)

if __name__ == '__main__':
    app.run(debug=True)
