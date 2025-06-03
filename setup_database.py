import sqlite3

# Connect to SQLite database (this will create the chatbot.db file if it doesn't exist)
conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

# Create a table for FAQs
cursor.execute('''
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
''')

# Insert sample data into the table
cursor.executemany('''
INSERT INTO faqs (question, answer) VALUES (?, ?)
''', [
    ("hello", "Hi! How can I assist you today?"),
    ("where is the computer science department", "The Computer Science department is in Building A, Room 101."),
    ("what time is the math class", "Math class is at 10:00 AM in Room B203."),
    ("where is the cafeteria", "The cafeteria is located near Building C, on the ground floor."),
    ("who is the class counselor for cs101", "The class counselor for CS101 is Mr. John Doe. You can contact him at john.doe@buitems.edu.")
])

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database setup completed successfully! 'chatbot.db' has been created with sample data.")
