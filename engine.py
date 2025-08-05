import pandas as pd
import datetime
import re
from typing import Optional, Dict
from difflib import get_close_matches, SequenceMatcher
from aliases import course_aliases as COURSE_ALIASES
from entities import normalize_course_query, normalize_code


class TimetableEngine:
    def __init__(self, timetable_df: pd.DataFrame):
        self.df = timetable_df.copy()
        self.df = self.df.fillna("N/A")

    def _to_time(self, time_str: str) -> Optional[datetime.time]:
        try:
            return datetime.datetime.strptime(time_str.strip(), "%H:%M").time()
        except:
            return None

    def _filter_df(self, section=None, program=None, day=None):
        df = self.df.copy()
        if section:
            df = df[df['section'].str.lower() == section.lower()]
        if program:
            df = df[df['program'].str.lower() == program.lower()]
        if day:
            df = df[df['day'].str.lower() == day.lower()]
        return df

    def find_next_class(self, section=None, program=None, after_time=None):
        now = after_time or datetime.datetime.now().time()
        today = datetime.datetime.today().strftime("%A").lower()

        df = self._filter_df(section, program, day=today)
        df["start_time_parsed"] = df["start_time"].apply(self._to_time)
        df = df[df["start_time_parsed"].notnull()]
        df = df[df["start_time_parsed"] > now]

        if df.empty:
            return "No more classes scheduled for today."

        row = df.sort_values("start_time_parsed").iloc[0]
        return (f"Next class: {row['course'].title()} at {row['start_time']} "
                f"in {row['room']} with {row['teacher'].title()}.")

    def classes_between(self, section=None, program=None, start=None, end=None):
        if not (start and end):
            return "Please provide both start and end times (HH:MM format)."

        start_time = self._to_time(start)
        end_time = self._to_time(end)
        if not (start_time and end_time):
            return "Invalid time format. Use HH:MM."

        today = datetime.datetime.today().strftime("%A").lower()
        df = self._filter_df(section, program, day=today)
        df["start_time_parsed"] = df["start_time"].apply(self._to_time)
        df["end_time_parsed"] = df["end_time"].apply(self._to_time)
        df = df[(df["start_time_parsed"] >= start_time) & (df["end_time_parsed"] <= end_time)]

        if df.empty:
            return "No classes found in this time range."

        out = []
        for _, row in df.iterrows():
            out.append(f"{row['course'].title()} ({row['start_time']}–{row['end_time']}) in Room {row['room']}")
        return "Classes between given time:\n" + "\n".join(out)

    def personalized_summary(self, prefs: Dict[str, str]):
        section = prefs.get("section")
        program = prefs.get("program")

        if not section and not program:
            return "Please provide your section or program for a personalized summary."

        df = self._filter_df(section, program)

        if df.empty:
            return "No classes found for the given section/program."

        summary = []
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            daily_df = df[df['day'].str.lower() == day]
            if not daily_df.empty:
                summary.append(f"\n📅 {day.capitalize()}:")
                for _, row in daily_df.iterrows():
                    summary.append(f"• {row['course']} ({row['start_time']}–{row['end_time']}) in Room {row['room']}")

        return "\n".join(summary) if summary else "No scheduled classes found for this week."


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
    
def smart_course_match(row, user_course):
    user_course_norm = normalize_course_query(user_course)
    row_course_norm = normalize_course_query(row['course'])
    if "lab" in user_course_norm and "lab" not in row_course_norm:
        return False
    if "lab" not in user_course_norm and "lab" in row_course_norm:
        return False
    if row_course_norm == user_course_norm or user_course_norm in row_course_norm:
        return True
    for alias, full in COURSE_ALIASES.items():
        if user_course_norm == normalize_course_query(alias):
            return row_course_norm == normalize_course_query(full)
    if row_course_norm == user_course_norm or user_course_norm in row_course_norm:
        return True
    if 'course_code' in row and normalize_code(row['course_code']) == normalize_code(user_course):
        return True
    if SequenceMatcher(None, user_course_norm, row_course_norm).ratio() > 0.8:
        return True
    return False

def fuzzy_match_course(query_course, timetable_courses):
    all_courses = list(set(timetable_courses))
    match = get_close_matches(query_course.lower(), [c.lower() for c in all_courses], n=1, cutoff=0.6)
    if match:
        for c in all_courses:
            if c.lower() == match[0]:
                return c
    return None