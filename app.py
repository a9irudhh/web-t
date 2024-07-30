from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps

app = Flask(__name__)
app.secret_key = '&%#$@56'  # Replace with a strong secret key

# Fixed username and password
USERNAME = 'Teacher@OneOrigin'
PASSWORD_HASH = generate_password_hash('OneOrigin@123')  # Password hash for security

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')  # Adjust if needed
db = client['student_management']  # Replace with your database name
students = db['students']  # Replace with your collection name


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')


@app.route('/dashboard', methods=['GET'])
def index():
    # Redirect to login if not authenticated
    if 'username' not in session:
        return redirect(url_for('login'))
    
    students_list = students.find()
    student_data = []
    
    for student in students_list:
        total_obtained_marks = 0
        total_max_marks = 0
        
        for sem in student.get('semesters', []):
            for subj in sem.get('subjects', []):
                total_obtained_marks += subj['marks_obtained']
                total_max_marks += subj['max_marks']
        
        if total_max_marks > 0:
            percentage = (total_obtained_marks / total_max_marks) * 100
        else:
            percentage = 0

        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        #add phone number to student data
        student_data.append({
            'id': str(student['_id']),
            'name': student.get('name', ''),
            'srn': student.get('srn', ''),
            'percentage': round(percentage, 2),
            'grade': grade,
            'age': student.get('age', 0),
            'number': student.get('number', 'Not Available')
        })
    
    return render_template('index.html', students=student_data)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        data = request.form
        srn = f"SRN{int(data['srn']):03d}"
        semesters = []
        for sem in range(1, 4):  # Assuming 3 semesters
            subjects = []
            for subj in ['Math', 'Science', 'English']:
                subjects.append({
                    'subject': subj,
                    'marks_obtained': int(data[f'sem{sem}_{subj}_marks_obtained']),
                    'max_marks': int(data[f'sem{sem}_{subj}_max_marks'])
                })
            semesters.append({
                'semester': sem,
                'subjects': subjects
            })
        students.insert_one({
            'srn': srn,
            'name': data['name'],
            'age': int(data['age']),
            'number': data['number'],  # Add phone number
            'semesters': semesters
        })
        return redirect(url_for('index'))
    return render_template('add_student.html')


@app.route('/view_student/<id>')
def view_student(id):
    student = students.find_one({'_id': ObjectId(id)})
    return render_template('view_student.html', student=student)

@app.route('/edit_student/<id>', methods=['GET', 'POST'])
def edit_student(id):
    if request.method == 'POST':
        data = request.form
        srn = data['srn']  # SRN is received from the hidden field
        semesters = []
        for sem in range(1, 4):  # Assuming 3 semesters
            subjects = []
            for subj in ['Math', 'Science', 'English']:
                subjects.append({
                    'subject': subj,
                    'marks_obtained': int(data[f'sem{sem}_{subj}_marks_obtained']),
                    'max_marks': int(data[f'sem{sem}_{subj}_max_marks'])
                })
            semesters.append({
                'semester': sem,
                'subjects': subjects
            })
        students.update_one({'_id': ObjectId(id)}, {'$set': {
            'srn': srn,
            'name': data['name'],
            'age': int(data['age']),
            'number': data['number'],  # Update phone number
            'semesters': semesters
        }})
        return redirect(url_for('index'))
    student = students.find_one({'_id': ObjectId(id)})
    return render_template('edit_student.html', student=student)


# Delete student route
@app.route('/delete_student/<id>')
def delete_student(id):
    students.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
