import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

# Ensure the 'faqs' table exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
''')

# Additional questions and answers to insert
faq_data = [
    ("how can i access the library", "You can access the library during its working hours by showing your university ID at the entrance."),
    ("what are the library timings", "The library is open from 8:00 AM to 8:00 PM on weekdays and 9:00 AM to 2:00 PM on Saturdays. It is closed on Sundays."),
    ("how do i apply for hostel accommodation", "You can apply for hostel accommodation by visiting the hostel office in Building A or by submitting an application through the university portal."),
    ("who is the dean of computer science", "The current dean of the Computer Science department is Dr. Ahmed Khan. You can reach him at ahmed.khan@buitems.edu."),
    ("where is the sports complex", "The sports complex is located near Building E, behind the main parking area."),
    ("how can i access the student portal", "You can access the student portal by visiting portal.buitems.edu.pk and logging in with your student credentials."),
    ("where can i get my ID card", "You can collect your university ID card from the registrar's office in Building A, Room 102."),
    ("where is the exam controller office", "The exam controller's office is located in Building C, Room 301."),
    ("how do i pay my fees", "You can pay your fees online through the student portal or at the designated bank branches. Visit the accounts office for more details."),
    ("how can i submit a complaint", "You can submit a complaint through the student portal under the 'Feedback' section or visit the student affairs office in Building C."),
    ("what is the grading system in buitems", "The grading system at BUITEMS follows a GPA scale, with A being the highest grade and F being a failing grade."),
    ("where can i find the transportation schedule", "The transportation schedule is available on the BUITEMS website under the 'Services' section or at the transport office in Building B."),
    ("how do i apply for an internship", "You can apply for internships through the career services office in Building D, Room 204, or check opportunities posted on the student portal."),
    ("how can i join the robotics club", "You can join the Robotics Club by attending their introductory session or contacting the club advisor at robotics@buitems.edu."),
    ("how do i find my class counselor", "Your class counselor's contact details are available on the student portal under the 'Counselor Info' section."),
    ("what is the attendance policy at buitems", "Students are required to maintain at least 75% attendance in each course to be eligible to sit for the final exams."),
    ("what is the maximum credit hour limit per semester", "Students can register for a maximum of 18 credit hours per semester. For exceptions, please contact the registrar's office."),
    ("how do i withdraw from a course", "You can withdraw from a course by submitting a withdrawal form to the registrar's office before the withdrawal deadline."),
    ("where can i find research publications", "Research publications are available in the library's digital repository or on the BUITEMS research portal."),
    ("how can i access online learning resources", "Online learning resources are available through the BUITEMS eLearning platform. Use your student credentials to log in."),
    ("where can i report lost items", "You can report lost items at the security office located near the main gate."),
    ("how do i register for makeup exams", "Makeup exams can be registered for by submitting an application to the exam controller's office with a valid reason."),
    ("where can i get a no-objection certificate", "You can request a No-Objection Certificate (NOC) from the registrar's office in Building A, Room 204."),
    ("how do i request a leave of absence", "Submit a leave request form to the student affairs office with a valid reason and supporting documents."),
    ("where is the health center", "The health center is located in Building E, Ground Floor, near the main auditorium."),
    ("how do i apply for degree verification", "Degree verification requests can be submitted to the registrar's office. The form is available on the university website."),
    ("how can i get a duplicate ID card", "You can apply for a duplicate ID card at the registrar's office. A fee will apply."),
    ("what is the procedure for changing a course", "To change a course, fill out the course change form and submit it to the registrar's office before the add/drop deadline."),
    ("where can i find hostel rules and regulations", "Hostel rules and regulations are available in the hostel office or on the BUITEMS website."),
    ("how do i participate in workshops and seminars", "Workshops and seminars are announced on the BUITEMS website and notice boards. Contact the relevant department for registration."),
    ('What is the admission process?', 'The admission process involves submitting an online application, followed by document verification and an entry test.'),
    ('How can I apply for a scholarship?', 'You can apply for scholarships through the BUITEMS student portal under the scholarship section.'),
    ('Where is the library located?', 'The library is located in the central building, next to the administration block.'),
    ('What are the library timings?', 'The library is open from 8:00 AM to 8:00 PM, Monday to Friday.'),
    ('How can I reset my student portal password?', 'To reset your password, click on "Forgot Password" on the portal login page and follow the instructions.'),
    ('Where can I find the academic calendar?', 'The academic calendar is available on the official BUITEMS website under the "Academics" section.'),
    ('What are the cafeteria timings?', 'The cafeteria is open from 8:00 AM to 5:00 PM, Monday to Friday.'),
    ('Who is the class counselor for CS department?', 'The class counselor for the CS department is Mr. Ahmed. His office is in Room 205, Building A.'),
    ('What is the process to add or drop a course?', 'You can add or drop courses through the student portal during the first two weeks of the semester.'),
    ('Where can I find my timetable?', 'Your timetable is available on the student portal under the "Schedule" section.'),
    ('How can I get my attendance report?', 'Attendance reports are available on the student portal under the "Attendance" section.'),
    ('What is the fee structure for undergraduate programs?', 'The fee structure is available on the BUITEMS website under the "Admissions" section.'),
    ('Where can I park my car?', 'Student parking is available near the main entrance and behind Building C.'),
    ('What is the grading policy?', 'The grading policy includes A for 85% and above, A- for 80% to 84%, and so on, as per BUITEMS regulations.'),
    ('How can I contact the admin office?', 'You can contact the admin office at +92-123-456-789 or visit the admin block during office hours.'),
    ('Where can I submit my assignments?', 'Assignments are submitted through the student portal or directly to your course instructor.'),
    ('What is the Wi-Fi password?', 'The Wi-Fi password is provided at the IT support desk in Building B.'),
    ('How can I access online classes?', 'Online classes are accessed through the LMS platform. Login credentials are provided at the start of the semester.'),
    ('What is the procedure for getting an internship?', 'Internships are managed by the Career Services Office. Visit their office in Building D for details.'),
    ('Where can I find the examination schedule?', 'The examination schedule is posted on the student portal and the notice board outside the admin block.'),
    ('Who do I contact for technical issues with the student portal?', 'For technical issues, contact the IT support team at it.support@buitems.edu.pk.'),
    ('What is the dress code policy?', 'Students are required to wear modest attire as outlined in the student handbook.'),
    ('How can I join a student society?', 'You can join student societies by filling out the membership form available in the Student Affairs Office.'),
    ('Where can I find the list of courses offered?', 'The list of courses is available on the BUITEMS website under the "Programs" section.'),
    ('What is the procedure to get a transcript?', 'You can request a transcript from the registrar’s office or through the student portal.'),
    ('Where is the medical center located?', 'The medical center is located near the main gate, next to the cafeteria.'),
    ('What are the medical center timings?', 'The medical center is open from 8:00 AM to 4:00 PM, Monday to Friday.'),
    ('How can I report a lost item?', 'Report lost items to the Lost and Found desk in the admin block.'),
    ('What is the process for rechecking exam papers?', 'Submit a rechecking form to the Examination Office within two weeks of result announcement.'),
    ('Where can I find course prerequisites?', 'Course prerequisites are listed in the course catalog available on the BUITEMS website.'),
    ('What are the transportation options?', 'BUITEMS provides bus services. Timings and routes are available on the notice board.'),
    ('How can I get a duplicate ID card?', 'Submit a request to the admin office along with a fee of PKR 500 for a duplicate ID card.'),
    ('Where is the auditorium?', 'The auditorium is located in Building E, next to the library.'),
    ('What are the rules for using the library?', 'Library rules include maintaining silence, no food or drinks, and returning books on time.'),
    ('How can I change my contact information?', 'Update your contact information through the student portal under the "Profile" section.'),
    ('Where can I find the IT lab?', 'The IT lab is located on the second floor of Building A.'),
    ('What is the minimum CGPA required to graduate?', 'The minimum CGPA required for graduation is 2.5.'),
    ('Where can I get my degree certificate?', 'Degree certificates are collected from the registrar’s office after graduation.'),
    ('What is the policy for late fee submission?', 'Late fees incur a fine of PKR 100 per day after the due date.'),
    ('How can I register for workshops or seminars?', 'Workshop registrations are available through the BUITEMS event portal.'),
    ('Where can I find the BUITEMS handbook?', 'The student handbook is available on the BUITEMS website under the "Resources" section.'),
    ('How can I withdraw from a course?', 'Submit a course withdrawal form to the registrar’s office before the withdrawal deadline.'),
    ('What is the policy for semester breaks?', 'Semester breaks are outlined in the academic calendar available on the website.'),
    ('Where can I get career counseling?', 'Career counseling services are available in the Career Services Office in Building D.'),
    ('How do I check my grades?', 'Grades are available on the student portal under the "Grades" section.'),
    ('What is the process for updating my photo in the student portal?', 'Submit a request to the IT department to update your photo in the portal.'),
    ('What is the duration of the semester?', 'A semester typically lasts 16 weeks, including exams.'),
    ('why is this chatbot made?','This Chatbot is made for your any possible assitance and help <3'),
    ('where is the cafeteria?','The cafeteria is lcoated at the back of block c right at the stationaries.')

]

# Insert the additional questions and answers into the 'faqs' table
cursor.executemany("INSERT INTO faqs (question, answer) VALUES (?, ?)", faq_data)

# Commit changes and close the connection
conn.commit()
conn.close()

print("All additional data has been inserted into the database!")
