import re
import datetime
from difflib import get_close_matches

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'today', 'tomorrow']


class EntityExtractor:
    STOPWORDS = set([
    'is', 'the', 'at', 'on', 'in', 'where', 'what', 'when', 'who', 'which', 'class', 'teach', 'teaches', 'teacher',
    'class', 'teach', 'teaches', 'teacher', 'course', 'subject', 'about', 'of'
    ])

    def __init__(self, timetable_df):
        self.df = timetable_df.copy()
        self.course_map = self._build_course_aliases()
        self.program_map = self._build_program_aliases()
        self.teacher_list = self.df['teacher'].dropna().astype(str).str.lower().unique().tolist()

    def _normalize(self, text):
        return re.sub(r'[\W_]+', '', text.lower())

    def _build_course_aliases(self):

        course_map = {}

        for idx, row in self.df.iterrows():
            course = str(row['course']).strip().lower()
            code = str(row.get('course_code', '')).strip().lower()

            canon = course
            norm_course = self._normalize(course)
            norm_code = self._normalize(code)

            # Primary mappings
            course_map[norm_course] = canon
            course_map[canon] = canon
            if norm_code:
                course_map[norm_code] = canon  # ✅ For queries like "CS114"

            # Variants
            variations = [
                canon.replace('lab', '').strip() + 'lab',
                canon.replace('(', '').replace(')', '').replace('-', '').replace('_', '').replace(' ', '')
            ]
            for v in variations:
                course_map[self._normalize(v)] = canon

            # If course has multiple tokens, map the first one too
            tokens = canon.split()
            if len(tokens) > 1:
                course_map[tokens[0]] = canon

        return course_map

    def _build_program_aliases(self):
        program_map = {}
        for prog in self.df['program'].dropna().unique():
            canon = prog.strip().lower()
            norm = self._normalize(canon)
            program_map[canon] = canon
            program_map[norm] = canon
            program_map[canon.replace('-', '')] = canon
            program_map[canon.replace(' ', '')] = canon
        return program_map

    def _fuzzy_match(self, token, candidates):
        match = get_close_matches(token.lower(), candidates, n=1, cutoff=0.8)
        return match[0] if match else None

    def extract(self, query):
        query_lc = query.lower()
        tokens = re.findall(r'\b\w+\b', query_lc)

        tokens = [t for t in tokens if t not in self.STOPWORDS]
        entities = {
            'course': None,
            'day': None,
            'teacher': None,
            'section': None,
            'program': None,
            'semester': None,
            'lab_requested': 'lab' in tokens
        }
        DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "today", "tomorrow"]
        for word in tokens:
            if word.lower() in DAYS:
                entities['day'] = word.lower()


        if 'lab' in tokens:
            tokens = [t for t in tokens if t != 'lab']

        # Handle day (today/tomorrow → real weekday)
        if 'today' in tokens:
            entities['day'] = datetime.datetime.now().strftime('%A').lower()
        elif 'tomorrow' in tokens:
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            entities['day'] = tomorrow.strftime('%A').lower()
        else:
            for token in tokens:
                if token in WEEKDAYS:
                    entities['day'] = token
                    break

        # Program (exact, cleaned, or fuzzy)
        for token in tokens:
            norm = self._normalize(token)
            if norm in self.program_map:
                entities['program'] = self.program_map[norm]
                break
        if not entities['program']:
            fuzzy_prog = self._fuzzy_match(query_lc, self.program_map.keys())
            if fuzzy_prog:
                entities['program'] = self.program_map[fuzzy_prog]

        # Section
        section_match = re.search(r'\bsection\s*([a-d])\b', query_lc)
        if not section_match:
            section_match = re.search(r'\b([a-d])\b', query_lc)
        if section_match:
            entities['section'] = section_match.group(1).upper()

        # Semester
        semester_match = re.search(r'\b(\d+(st|nd|rd|th))\b', query_lc)
        if semester_match:
            entities['semester'] = semester_match.group(1)

        # Course
        for i in range(len(tokens)):
            tok = tokens[i]
            norm_tok = self._normalize(tok)
            if norm_tok in self.course_map:
                entities['course'] = self.course_map[norm_tok]
                break
            if i < len(tokens) - 1:
                bigram = self._normalize(tok + tokens[i + 1])
                if bigram in self.course_map:
                    entities['course'] = self.course_map[bigram]
                    break

        if not entities['course']:
            for token in tokens:
                fuzzy = self._fuzzy_match(token, self.course_map.keys())
                if fuzzy:
                    entities['course'] = self.course_map[fuzzy]
                    break

        # Teacher (exact or fuzzy)
        for token in tokens:
            if token in self.teacher_list:
                entities['teacher'] = token
                break
        if not entities['teacher']:
            fuzzy_teacher = self._fuzzy_match(query_lc, self.teacher_list)
            if fuzzy_teacher:
                entities['teacher'] = fuzzy_teacher

        return entities

def normalize_section(sec):
    return re.sub(r'[^a-z0-9]', '', sec.lower()) if sec else ''

def normalize_program(name):
    return re.sub(r'[^a-z0-9]', '', name.lower()) if name else ''

def normalize_course_query(text):
    text = text.lower().strip()
    tokens = re.findall(r'\w+', text)
    tokens.sort()
    return " ".join(tokens)

def normalize_code(code):
    return re.sub(r'\W+', '', str(code)).lower()

def clean(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())
