import datetime
import pandas as pd
import re
from difflib import get_close_matches
from aliases import course_aliases, program_aliases
from entities import EntityExtractor, normalize_program, normalize_section
from rapidfuzz import fuzz
import pandas as pd

timetable_df = pd.read_csv("cleaned_fict_timetable.csv")
timetable_df.columns = timetable_df.columns.str.strip().str.lower().str.replace(" ", "_")

CLEAN_COLUMNS = ['course', 'course_code', 'teacher', 'program', 'section', 'day']
TIME_COLUMNS = ['start_time', 'end_time', 'class_start', 'class_end']

for col in CLEAN_COLUMNS:
    if col in timetable_df.columns:
        timetable_df[col] = timetable_df[col].astype(str).str.strip().str.lower()
        timetable_df[col] = timetable_df[col].replace({'n/a': '', 'nan': '', 'none': ''})

for col in TIME_COLUMNS:
    if col in timetable_df.columns:
        timetable_df[col] = timetable_df[col].astype(str).str.strip()
        timetable_df[col] = timetable_df[col].replace({'n/a': '', 'nan': '', 'none': ''})

timetable_df = timetable_df.fillna("N/A")
timetable_df.replace({'NAN': None, 'Nan': None, 'nan': None}, inplace=True)
timetable_df['section'] = timetable_df['section'].fillna('')
timetable_df['teacher'] = timetable_df['teacher'].fillna('')

entity_extractor = EntityExtractor(timetable_df)

INTENT_PATTERNS = {
    "teacher_lookup": [r"\bwho teaches\b", r"\bprofessor\b", r"\binstructor\b", r"\bwho is teaching\b"],
    "room_lookup": [r"\bwhere\b", r"\broom\b", r"\bclassroom\b"],
    "time_lookup": [r"\bwhen\b", r"\bwhat time\b", r"\bclass timing\b"],
}
def detect_intent(query_lc):
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, query_lc):
                return intent
    return None

def clean(s):
    return re.sub(r'[\s\-\_]', '', s.lower())

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
    if len(code) == 1:
        forms.add(code[0].lower())
    for alias in forms:
        course_aliases[alias] = canon

class TimetableMatcher:
    def __init__(self, timetable_df, course_manager):
        self.df = timetable_df
        self.course_manager = course_manager

    def match(self, entities):
        df = self.df
        filters = []
        # Course/Lab matching
        if entities['course']:
            course_norm = entities['course'].lower()
            if entities['lab_requested']:
                filters.append(df['course'].str.lower().str.contains('lab'))
            filters.append(df['course'].str.lower().str.contains(re.escape(course_norm)))
        elif entities['lab_requested']:
            filters.append(df['course'].str.lower().str.contains('lab'))
        # Program
        if entities['program']:
            filters.append(df['program'].str.lower() == entities['program'].lower())
        # Section
        if entities['section']:
            filters.append(df['section'].str.lower() == entities['section'].lower())
        # Day
        if entities['day']:
            filters.append(df['day'].str.lower() == entities['day'])
        # Teacher
        if entities['teacher']:
            filters.append(df['teacher'].str.lower().str.contains(entities['teacher']))
        if filters:
            for f in filters:
                df = df[f]
        return df
    
    def detect_intent(query_lc):
        for intent, patterns in INTENT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, query_lc):
                    return intent
        return None
    
def get_timetable_response(query):
    
    entities = entity_extractor.extract(query)
    if query.lower().strip() in ["hi", "hello", "hey", "salam", "aoa"]:
        return "👋 Hello! How can I help you with your class timetable?"

    intent = detect_intent(query.lower())
    lab_requested = entities.get('lab_requested', False)
    course_entity = entities.get('course')
    day_entity = entities.get('day')
    # Fallback day parsing if entity extractor failed
    if not day_entity:
        for weekday in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'today']:
            if weekday in query.lower():
                day_entity = weekday
                break

    section_entity = entities.get('section')
    program_entity = entities.get('program')
    teacher_entity = entities.get('teacher')
    semester_entity = entities.get('semester')
    timetable = timetable_df.copy()
    timetable = timetable.fillna("N/A")
    query_lc = query.lower()
    print(f"\n[DEBUG] Query: {query}")
    print("[DEBUG] Extracted Entities:", entities)
    def contains_ci(series, keyword):
        return series.str.lower().str.contains(keyword.lower(), na=False)
    def smart_course_match(row, course, lab_requested=False):
        course_in_row = row['course'].strip().lower()
        course = course.strip().lower() if course else ""
        is_lab_row = "lab" in course_in_row
        course_core = re.sub(r"[\s\(\)]", "", course.replace("lab", ""))
        row_core = re.sub(r"[\s\(\)]", "", course_in_row.replace("lab", ""))
        alias_match = False
        for alias, fullname in course_aliases.items():
            if (course_core == fullname.lower().replace(" ", "")) and (alias.lower() in row_core):
                alias_match = True
            if (course_core == alias.lower()) and (fullname.lower().replace(" ", "") in row_core):
                alias_match = True

        fuzzy_match = False
        if not alias_match and course and course_in_row:
            fuzzy_score = fuzz.token_set_ratio(course, course_in_row)
            if fuzzy_score >= 85:
                fuzzy_match = True


        if lab_requested:
            return (course_core in row_core and is_lab_row) or (not course_core and is_lab_row) or (alias_match and is_lab_row) or (fuzzy_match and is_lab_row)
        else:
            if not course_core and lab_requested:
                return is_lab_row
        return (course_core in row_core and not is_lab_row) or (alias_match and not is_lab_row) or (fuzzy_match and not is_lab_row)
    if not any([course_entity, teacher_entity, day_entity, semester_entity, program_entity]) and section_entity:
        return "Please specify a course or program along with the section."
    if not any([course_entity, teacher_entity, day_entity, semester_entity, section_entity, program_entity]):
        return "Please be more specific: type a course, teacher, day, or section."
    if course_entity or lab_requested:
        timetable = timetable[timetable.apply(lambda row: smart_course_match(row, course_entity or '', lab_requested), axis=1)]
        if timetable.empty:
            msg = f"No {course_entity or 'lab'} class found."
            return msg
    if day_entity and day_entity.lower() in ['saturday', 'sunday']:
        return f"📌 No regular classes scheduled on {day_entity.capitalize()}."
    if not timetable.empty and day_entity and 'day' in timetable.columns:
        if day_entity.lower() == "today":
            actual_day = datetime.datetime.now().strftime('%A').lower()
            timetable = timetable[timetable['day'].str.lower() == actual_day]
        else:
            timetable = timetable[timetable['day'].str.lower() == day_entity.lower()]
    if not timetable.empty and program_entity and 'program' in timetable.columns:
        normalized_program = normalize_program(program_entity)
        timetable = timetable[timetable['program'].apply(lambda p: normalize_program(p) == normalized_program)]

    if not timetable.empty and section_entity and 'section' in timetable.columns:
        normalized_section = normalize_section(section_entity)
        timetable = timetable[timetable['section'].apply(lambda s: normalize_section(s) == normalized_section)]

    if not timetable.empty and semester_entity and 'semester' in timetable.columns:
        timetable = timetable[contains_ci(timetable['semester'], semester_entity)]

    if not timetable.empty and teacher_entity and 'teacher' in timetable.columns:
        timetable = timetable[contains_ci(timetable['teacher'], teacher_entity)]

    # if timetable.empty and course_entity:
    #     all_courses = timetable_df['course'].dropna().unique().tolist()
    #     match = get_close_matches(course_entity, all_courses, n=1, cutoff=0.6)
    #     if match:
    #         timetable = timetable_df[timetable_df['course'].str.lower() == match[0].lower()]
    
    if timetable.empty and course_entity:
        user_input_clean = course_entity.lower().strip()
        all_courses = timetable_df['course'].dropna().str.lower().unique().tolist()

        # Step 1: Try exact match first (to support 'pf', 'oop', etc.)
        if user_input_clean in all_courses:
            timetable = timetable_df[timetable_df['course'].str.lower() == user_input_clean]

        # Step 2: Only fuzzy match if input is at least 3 letters
        elif len(user_input_clean) >= 3:
            match = get_close_matches(user_input_clean, all_courses, n=1, cutoff=0.8)
            if match:
                timetable = timetable_df[timetable_df['course'].str.lower() == match[0].lower()]
    n = len(timetable)
    if n > 3 and not section_entity and not program_entity:
        options = timetable['section'].dropna().unique().tolist()
        prog_options = timetable['program'].dropna().unique().tolist()
        return (
            f"Multiple classes found for your query. "
            f"Please specify section (options: {', '.join(options)}) "
            f"or program (options: {', '.join(prog_options)})."
        )
    if timetable.empty:
        msg = f"No {course_entity or 'class'} found"
        if day_entity:
            if day_entity.lower() == "today":
                actual_day = datetime.datetime.now().strftime('%A')
                msg += f" on {actual_day}"
            else:
                msg += f" on {day_entity.capitalize()}"
        msg += "."
        return msg
    
    if intent == "today_classes":
        if not program_entity:
            programs = timetable_df['program'].dropna().unique().tolist()
            return {"prompt": "Select your department:", "buttons": programs}
        if program_entity and not semester_entity:
            return {"prompt": f"Select semester for {program_entity.upper()}:", "buttons": ["2nd", "4th", "6th", "8th"]}
        if program_entity and semester_entity:
            today = datetime.datetime.now().strftime('%A').lower()
            df = timetable_df[
                (timetable_df['program'].str.lower() == program_entity.lower()) &
                (timetable_df['semester'].str.contains(semester_entity[0], case=False)) &
                (timetable_df['day'].str.lower() == today)
            ]
            if df.empty:
                return {"message": f"No classes today for {program_entity} {semester_entity}."}
            cards = []
            for _, row in df.iterrows():
                cards.append(
                    f"{row['course'].title()} - {row['start_time']} to {row['end_time']} in {row['room'].upper()} with {row['teacher'].title()}"
                )
            return {"message": f"Today's classes for {program_entity} {semester_entity}:", "classes": cards}

    if intent == "teacher_lookup" and course_entity and not timetable.empty:
        if timetable.empty:
            return f"❌ No class found for {course_entity.upper()}."
        
        teachers = timetable['teacher'].dropna().unique()
        if not teachers.any():
            return f"❌ Teacher info not available for {course_entity.upper()}."

        response = f"👨‍🏫 *{course_entity.upper()}* is taught by:\n"
        for _, row in timetable.iterrows():
            response += f"• {row['teacher'].title()} on {row['day'].title()} from {row['start_time']} to {row['end_time']} in {row['room'].upper()}\n"
        return response.strip()

    #     return f"📍 {course} is in {room_out}."
    if intent == "room_lookup" and course_entity and not timetable.empty:
        if timetable.empty:
            return f"❌ No room found for {course_entity.upper()}."

        grouped_rooms = []
        for _, row in timetable.iterrows():
            room = row.get('room', '').upper()
            room_display = room if room and room.lower() not in ['n/a', '', 'nan'] else "Room not assigned"
            grouped_rooms.append(
                f"• {row['day'].title()}: {room_display} from {row['start_time']} to {row['end_time']}"
            )
        
        response = f"📍 *{course_entity.upper()}* room details:\n" + "\n".join(grouped_rooms)
        return response.strip()

    if intent == "time_lookup" and course_entity and not timetable.empty:
        if timetable.empty:
            return f"❌ No timing found for {course_entity.upper()}."

        time_slots = []
        for _, row in timetable.iterrows():
            time_slots.append(
                f"• {row['day'].title()}: {row['start_time']} to {row['end_time']} in {row['room'].upper()} with {row['teacher'].title()}"
            )

        response = f"⏰ *{course_entity.upper()}* class timings:\n" + "\n".join(time_slots)
        return response.strip()
    
    if lab_requested and not course_entity and day_entity and not timetable.empty:
        if day_entity.lower() == "today":
            actual_day = datetime.datetime.now().strftime('%A').lower()
            timetable = timetable[timetable['day'].str.lower() == actual_day]
        else:
            timetable = timetable[timetable['day'].str.lower() == day_entity.lower()]

        labs_today = timetable[timetable['course'].str.contains("lab", case=False, na=False)]
        
        if not labs_today.empty:
            summary = []
            for _, row in labs_today.iterrows():
                summary.append(
                    f"{row['course'].title()} - {row['start_time']} to {row['end_time']} ({row['section'].upper()} {row['program'].upper()})"
                )
            return "🧪 Labs scheduled: " + "; ".join(summary)
        else:
            return f"🧪 No labs found on {day_entity.capitalize()}."

        
    if not course_entity and n > 0:
        weekend_days = ['saturday', 'sunday']
        timetable_days = timetable['day'].str.lower().unique().tolist()
        if all(day in weekend_days for day in timetable_days):
            return "📌 Note: There are no regular classes scheduled on weekends (Saturday or Sunday)."

        from collections import defaultdict
        grouped = defaultdict(list)

        for _, row in timetable.iterrows():
            
            day = row['day'].capitalize()
            line = f"• {row['course'].title()} ({row['section'].upper()}/{row['program'].upper()}) - {row['start_time']} to {row['end_time']} in {row['room'].upper()} with {row['teacher'].title()}"
            grouped[day].append(line)

        total_classes = sum(len(classes) for classes in grouped.values())

        result = f"📊 Total classes this week: {total_classes}\n\nTimetable:\n\n"
        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in ordered_days:
            if day in grouped:
                result += f"📅 {day}:\n" + "\n".join(grouped[day]) + "\n\n"

        return result.strip()
    # if not course_entity and n > 0:
    #     from collections import defaultdict
    #     grouped = defaultdict(list)
    
    #     for _, row in timetable.iterrows():
    #         day = row['day'].capitalize()
    #         line = f"• {row['course'].title()} ({row['section'].upper()}/{row['program'].upper()}) - {row['start_time']} to {row['end_time']} in {row['room'].upper()} with {row['teacher'].title()}"
    #         grouped[day].append(line)

    #     result = "Timetable:\n\n"
    #     ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    #     for day in ordered_days:
    #         if day in grouped:
    #             result += f"📅 {day}:\n" + "\n".join(grouped[day]) + "\n\n"

    #     return result.strip()

    


    results = []
    for i, (_, row) in enumerate(timetable.iterrows()):
        if i == 5 and n > 6:
            results.append(f"...and {n - i} more results. Please refine your query.")
            break
        course = row.get('course', 'N/A').title()
        code = row.get('course_code', 'N/A').upper()
        room = row.get('room', 'N/A').upper()
        teacher = row.get('teacher', 'N/A').title()
        start = row.get('start_time', 'N/A')
        end = row.get('end_time', 'N/A')
        day = row.get('day', 'N/A').capitalize()
        sem = row.get('semester', 'N/A')
        sec = row.get('section', 'N/A').upper()
        prog = row.get('program', 'N/A').upper()
        teacher_out = teacher if teacher not in ["N/A", "", "Nan"] else "No teacher assigned"
        room_out = room if room not in ["N/A", "", "Nan"] else "Room not assigned"
        results.append(
            f"📘 {course} ({code}) for {prog} {sem} - Section {sec} is on {day} "
            f"from {start} to {end} in {room_out} with {teacher_out}."
        )
    
    return " ".join(results)
    

