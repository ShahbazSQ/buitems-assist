from flask import session,Blueprint
import sqlite3
import spacy
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import google.generativeai as genai
import datetime
from timetable import get_timetable_response
from typing import Dict, Any, List
from engine import TimetableEngine
from entities import EntityExtractor
import pandas as pd

timetable_df = pd.read_csv("cleaned_fict_timetable.csv")
timetable_df.columns = timetable_df.columns.str.strip().str.lower().str.replace(" ", "_")
entity_extractor = EntityExtractor(timetable_df)


WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
db_file = "chatbot.db"
index = faiss.IndexFlatL2(384)
database_questions = []

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
class BUITEMSIntelligentAssistant:
    def __init__(self, timetable_df, nlp, course_aliases, program_aliases):
        self.intent_detector = IntentDetector()
        self.user_sessions = UserSessionManager()
        self.analytics = analytics_engine
        self.entity_extractor = AdvancedEntityExtractor(nlp, course_aliases, program_aliases)
        self.timetable_engine = TimetableEngine(timetable_df)
    def get_session_id(self):
        session_id = session.get('user_session_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['user_session_id'] = session_id
        return session_id

    # def process_query(self, user_input):
    #     timetable_answer = get_timetable_response(user_input)
    #     entities = self.entity_extractor.extract(user_input)

    #     if timetable_answer:
    #         return timetable_answer
    #     user_vector = embedding_model.encode([user_input])
    #     distances, indices = index.search(np.array(user_vector, dtype=np.float32), k=1)
    #     if indices[0][0] != -1 and distances[0][0] < 0.9:
    #         matched_question = database_questions[indices[0][0]]
    #         conn = sqlite3.connect(db_file)
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT answer FROM faqs WHERE question = ?", (matched_question,))
    #         result = cursor.fetchone()
    #         conn.close()
    #         if result:
    #             return result[0]
    #     return ask_gemini(user_input)
    # def process_query(self, user_input):
    #     # Step 1: Detect intent
    #     intent = self.intent_detector.detect_intent(user_input)

    #     # Step 2: If intent is timetable-related → use timetable logic
    #     if intent in ["timetable", "next_class", "labs_today", "teacher_lookup", "room_lookup", "time_lookup"]:
    #         timetable_answer = get_timetable_response(user_input)
    #         if timetable_answer and not timetable_answer.lower().startswith("please be more specific"):
    #             return timetable_answer

    #     # Step 3: Otherwise → fallback to FAQ / Gemini
    #     user_vector = embedding_model.encode([user_input])
    #     distances, indices = index.search(np.array(user_vector, dtype=np.float32), k=1)
    #     if indices[0][0] != -1 and distances[0][0] < 0.9:
    #         matched_question = database_questions[indices[0][0]]
    #         conn = sqlite3.connect(db_file)
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT answer FROM faqs WHERE question = ?", (matched_question,))
    #         result = cursor.fetchone()
    #         conn.close()
    #         if result:
    #             return result[0]

    #     # Step 4: Default → Gemini assistant
    #     return ask_gemini(user_input)


    def process_query(self, user_input):
        intent = self.intent_detector.detect_intent(user_input)
        entities = self.entity_extractor.extract(user_input)

        # Step 1: Prefer timetable if entities indicate it's about classes
        if intent in ["timetable", "next_class", "labs_today", "teacher_lookup", "room_lookup", "time_lookup"] \
        or entities.get("course") or entities.get("program") or entities.get("day"):
            timetable_answer = get_timetable_response(user_input)
            
            # If timetable has a meaningful answer → return it
            if timetable_answer and not timetable_answer.lower().startswith(("please be more specific", "no class found")):
                return timetable_answer
            # If entities exist but answer is vague → still guide user instead of dumping to Gemini
            if entities.get("course") or entities.get("program"):
                return timetable_answer

        # Step 2: FAQ match
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

        # Step 3: Consultation / General → Gemini
        return ask_gemini(user_input)


    def smart_handle_query(self, user_query: str) -> str:
        session_id = self.get_session_id()
        prefs = self.user_sessions.get_session(session_id).get("preferences", {})
        intent = self.intent_detector.detect_intent(user_query)
        advanced_entities = self.entity_extractor.extract(user_query)
        legacy_response = self.process_query(user_query)
        ambiguous = (
            legacy_response.lower().startswith("please be more specific")
            or legacy_response.lower().startswith("please specify")
            or legacy_response.lower().startswith("no class found")
            or legacy_response.lower().startswith("no")
            or "not found" in legacy_response.lower()
            or "please refine" in legacy_response.lower()
        )
        if ambiguous or not legacy_response:
            response = None
            if intent == "greeting":
                response = "Hello! How can I help you today?"
            elif intent == "timetable":
                if prefs.get("section") or prefs.get("program"):
                    response = self.timetable_engine.personalized_summary(prefs)
                else:
                    response = "Please specify your section or program for a personalized timetable."
            elif intent == "next_class":
                response = self.timetable_engine.find_next_class(
                    section=prefs.get("section"),
                    program=prefs.get("program")
                )
            elif intent == "labs_today":
                response = get_timetable_response("labs for today")
            elif intent == "farewell":
                response = "Goodbye! Have a great day."
            elif intent == "teacher_lookup":
                if advanced_entities.get("course"):
                    response = get_timetable_response(f"who teaches {advanced_entities['course']}")
                else:
                    response = "Please specify the course for teacher lookup."
            elif intent == "event_query":
                response = ask_gemini("Are there any events or seminars this week at BUITEMS?")
            else:
                response = self.legacy_fallback(user_query)
            self.analytics.log_query(session_id, user_query, response, intent)
            self.user_sessions.add_history(session_id, user_query, response)
            return response
        else:
            self.analytics.log_query(session_id, user_query, legacy_response, intent)
            self.user_sessions.add_history(session_id, user_query, legacy_response)
            return legacy_response
    def update_user_preferences(self, **prefs):
        session_id = self.get_session_id()
        self.user_sessions.update_preferences(session_id, **prefs)
    def legacy_fallback(self, user_input):
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
        return ask_gemini(user_input)
    

    
class IntentDetector:
    COMMON_INTENTS = {
        'timetable': ["timetable", "class schedule", "my classes", "when", "schedule", "next class", "class time"],
        'teacher_lookup': ["who teaches", "teacher", "professor", "instructor"],
        'room_lookup': ["where", "room", "location"],
        'event_query': ["event", "seminar", "conference"],
        'greeting': ["hello", "hi", "salam", "assalam", "thank", "thanks"],
        'labs_today': ["labs for today", "all labs", "lab schedule"],
        'farewell': ["bye", "goodbye", "khuda hafiz"],
        'admin': ["admin", "faq", "dashboard", "analytics"],
    }
    def __init__(self):
        self._last_intent = None
    def detect_intent(self, query: str) -> str:
        query_lc = query.lower()
        for intent, keywords in self.COMMON_INTENTS.items():
            for keyword in keywords:
                if keyword in query_lc:
                    self._last_intent = intent
                    logger.info(f"Intent '{intent}' detected in query '{query}'.")
                    return intent
        self._last_intent = "general"
        logger.info(f"Defaulting to 'general' intent for query '{query}'.")
        return "general"

class UserSessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.sessions.setdefault(session_id, {"history": [], "preferences": {}})
    def update_preferences(self, session_id: str, **prefs):
        session = self.get_session(session_id)
        session["preferences"].update(prefs)
        logger.info(f"Updated preferences for session '{session_id}': {prefs}")
    def add_history(self, session_id: str, user_input: str, system_response: str):
        session = self.get_session(session_id)
        session["history"].append({"input": user_input, "response": system_response})
        logger.info(f"Session '{session_id}' logged history event.")

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")
class AnalyticsEngine:
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
    def log_query(self, user_id: str, query: str, response: str, intent: str):
        event = {
            "user_id": user_id,
            "query": query,
            "response": response,
            "intent": intent,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.queries.append(event)
        logger.info(f"Analytics logged: {event}")
    def top_queries(self, n=5) -> List[str]:
        from collections import Counter
        all_qs = [q["query"] for q in self.queries]
        return [q for q, _ in Counter(all_qs).most_common(n)]
    def unanswered_queries(self) -> List[str]:
        return [q["query"] for q in self.queries if "not sure" in q["response"].lower() or "no class" in q["response"].lower()]

analytics_engine = AnalyticsEngine()

class AdvancedEntityExtractor:
    def __init__(self, nlp_model,course_aliases, program_aliases):
        self.nlp = nlp_model
        self.course_aliases = course_aliases
        self.program_aliases = program_aliases

    def extract(self, text: str) -> Dict[str, Any]:
        doc = self.nlp(text)
        entities = {"course": None, "day": None, "teacher": None, "section": None, "program": None}
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                entities["day"] = ent.text.lower()
            if ent.label_ == "PERSON":
                entities["teacher"] = ent.text
        tokens = [token.text.lower() for token in doc]
        for tok in tokens:
            if tok in WEEKDAYS:
                entities["day"] = tok
            if tok in self.course_aliases:
                entities["course"] = self.course_aliases[tok]
            if tok in self.program_aliases:
                entities["program"] = self.program_aliases[tok]
        return entities

def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction="""
            You are BUITEMS Assist — a friendly, helpful, and intelligent chatbot.
            - BUITEMS queries → formal, reliable answers.
            - General queries → friendly, supportive guidance.
            If you cannot answer a BUITEMS-specific question, politely advise contacting the BUITEMS administration.
            """
        )

        # Lightweight user prompt (no huge block every time)
        user_prompt = f"""
        User query: {prompt}

        Example BUITEMS Query → Answer:
        Q: When is the BS-IT 4th semester exam?
        A: The exam schedule for BS-IT 4th semester will be announced by the BUITEMS Examination Department.

        Example General Query → Answer:
        Q: Can you help me create a study plan for finals?
        A: Sure! Break your syllabus into topics and allocate daily study blocks.
        """

        # ✅ Use streaming
        response_stream = model.generate_content(user_prompt, stream=True)

        answer = ""
        for chunk in response_stream:
            if chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        answer += part.text

        return answer.strip() if answer else "I'm not sure how to answer that right now."

    except Exception as e:
        print("Error with Gemini:", str(e))
        return "Our BUITEMS assistant is currently unavailable."



import logging
import uuid
from flask import Blueprint
from typing import Dict, Any, List

logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("BUITEMS-ASSIST-UPGRADE")
