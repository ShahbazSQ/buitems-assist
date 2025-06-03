import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

# Test query: Replace "hello" with a question from your database
user_input = "hello".lower()
cursor.execute("SELECT answer FROM faqs WHERE question = ?", (user_input,))
result = cursor.fetchone()

conn.close()

# Print the result
if result:
    print("Response from DB:", result[0])
else:
    print("No response found for the input:", user_input)
