from flask import Flask
from flask_cors import CORS
import spacy
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import google.generativeai as genai
import pandas as pd
import os
from aliases import course_aliases, program_aliases
from assistant import BUITEMSIntelligentAssistant
from entities import EntityExtractor, clean

timetable_df = pd.read_csv("cleaned_fict_timetable.csv")
entity_extractor = EntityExtractor(timetable_df)


app = Flask(__name__)
app.secret_key = "super_secret_key"
CORS(app)

timetable_df = pd.read_csv("cleaned_fict_timetable.csv")



# --- Build Program Aliases ---
program_canonicals = timetable_df['program'].dropna().unique().tolist()
program_aliases = {}
for p in program_canonicals:
    canon = p.lower().strip()
    norm = clean(canon)
    # e.g. for 'bs-it'
    program_aliases[canon] = canon
    program_aliases[norm] = canon
    program_aliases[canon.replace('-', '')] = canon
    program_aliases[canon.replace('-', ' ')] = canon
    program_aliases[canon.replace(' ', '')] = canon
    # If it's like "BSIT", "BS-IT", "bs it", etc.
    program_aliases[canon.replace('-', '').replace(' ', '')] = canon
    # Add token split (e.g., 'bs', 'it')
    if '-' in canon:
        parts = canon.split('-')
        if len(parts) == 2:
            program_aliases[parts[0] + parts[1]] = canon
            program_aliases[parts[0] + ' ' + parts[1]] = canon

# --- Build Course Aliases ---
course_canonicals = timetable_df['course'].dropna().unique().tolist()
course_aliases = {}
for c in course_canonicals:
    canon = c.lower().strip()
    base = clean(canon)
    forms = set([
        canon, base, canon.replace('(', '').replace(')', '').replace('-', '').replace('_', '').replace(' ', ''),
    ])
    # Add first word (if multiword, e.g. "object oriented programming" → "object")
    tokens = canon.split()
    if len(tokens) > 1:
        forms.add(tokens[0])
    # Add course code as alias if present and unique
    code = timetable_df[timetable_df['course'].str.lower() == canon]['course_code'].unique()
    if len(code) == 1 and isinstance(code[0], str):
        forms.add(code[0].lower())
    elif len(code) == 1 and pd.notna(code[0]):
        forms.add(str(code[0]).lower())
    for alias in forms:
        course_aliases[alias] = canon






    
COURSE_ALIASES = course_aliases
PROGRAM_ALIASES = program_aliases
timetable_df = timetable_df.fillna('')
timetable_df.columns = timetable_df.columns.str.strip().str.lower().str.replace(' ', '_')
print("Timetable Columns:", timetable_df.columns.tolist())




    






nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
db_file = "chatbot.db"
index = faiss.IndexFlatL2(384)
database_questions = []



genai.configure(api_key=os.getenv("YOUR_GEMINI_API"))












# ==========================
# ===== UPGRADE LAYER  =====
# ==========================






WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

assistant_controller = BUITEMSIntelligentAssistant(timetable_df, nlp, course_aliases, program_aliases)




from routes import *

if __name__ == '__main__':
    app.run(debug=True)



# /FYP
# │
# ├── app.py                      ← main file, only imports others
# ├── routes.py      
# ├── assistant.py               ← contains BUITEMSIntelligentAssistant
# ├── engine.py                  ← TimetableEngine, TimetableMatcher
# ├── timetable.py               ← get_timetable_response, no df init
# ├── aliases.py                 ← course_aliases, program_aliases
# ├── entities.py                ← utility functions like `clean()`
# ├── cleaned_fict_timetable.csv ← timetable
# $env:GOOGLE_API_KEY = "AIzaSyD_RNyTGXyDXv9ZE3Wvc5npaiE_LuqChec"