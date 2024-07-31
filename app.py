from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = '&%#$@56'  # Replace with a strong secret key

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')  # Adjust if needed
db = client['student_management']  # Replace with your database name
students = db['students']  # Replace with your collection name
users = db['users']  # Collection for user credentials

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if users.find_one({'username': username}):
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        users.insert_one({'username': username, 'password': hashed_password})
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch all student documents from the database
    student_list = list(students.find())
    print("Student List:", student_list)  # Debugging line to check the data

    return render_template('index.html', students=student_list)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        srn = data['srn']
        
        # Check if the student already exists
        if students.find_one({'srn': srn}):
            flash('A student with this SRN already exists.', 'error')
            return redirect(url_for('add_student'))

        total_marks_obtained = 0
        total_max_marks = 0
        semesters = []

        # Determine the number of semesters
        sem_keys = [key for key in data.keys() if key.startswith('sem') and '_subject' in key]
        sem_count = max(int(key.split('_')[0].replace('sem', '')) for key in sem_keys) if sem_keys else 0
        
        for sem in range(1, sem_count + 1):
            subjects = []
            subject_names = []
            marks_obtained = []

            # Extract subject names and marks for the current semester
            idx = 1
            while f'sem{sem}_subject{idx}_name' in data:
                subject_names.append(data.get(f'sem{sem}_subject{idx}_name'))
                marks_obtained.append(data.get(f'sem{sem}_subject{idx}_marks_obtained'))
                idx += 1

            max_marks = [100] * len(subject_names)  # Default max_marks is 100

            for name, obtained in zip(subject_names, marks_obtained):
                subjects.append({
                    'subject': name,
                    'marks_obtained': int(obtained),
                    'max_marks': 100
                })
                total_marks_obtained += int(obtained)
                total_max_marks += 100

            semesters.append({'semester': sem, 'subjects': subjects})

        # Calculate percentage and grade
        percentage = (total_marks_obtained / total_max_marks) * 100 if total_max_marks > 0 else 0

        grade = 'F'
        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'

        student_data = {
            'srn': srn,
            'name': data['name'],
            'age': data['age'],
            'phone_number': data['number'],
            'semesters': semesters,
            'percentage': percentage,
            'grade': grade
        }
        students.insert_one(student_data)

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_student.html')

@app.route('/view_student/<id>')
def view_student(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    student = students.find_one({'_id': ObjectId(id)})
    if student:
        return render_template('view_student.html', student=student)
    flash('Student not found.')
    return redirect(url_for('index'))



@app.route('/edit_student/<id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    student = students.find_one({'_id': ObjectId(id)})
    if not student:
        flash('Student not found.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.form

        # Extract and format SRN
        srn_value = data.get('srn', '')
        numeric_srn = ''.join(filter(str.isdigit, srn_value))
        srn = f"SRN{int(numeric_srn):03d}" if numeric_srn else 'SRN000'

        # Check for duplicate SRN
        if students.find_one({'srn': srn, '_id': {'$ne': ObjectId(id)}}):
            flash('A student with this SRN already exists.', 'error')
            return redirect(url_for('edit_student', id=id))

        total_marks_obtained = 0
        total_max_marks = 0
        semesters = []

        # Extract semester data from the form
        sem_keys = [key for key in data.keys() if 'semesters[' in key]
        sem_count = len(set(int(key.split('[')[1].split(']')[0]) for key in sem_keys))

        for sem in range(sem_count):
            subjects = []
            subject_names = [data.get(f'semesters[{sem}][subjects][{i}][subject]') for i in range(len(data.getlist(f'semesters[{sem}][subjects][0][subject]')))]
            marks_obtained = [int(data.get(f'semesters[{sem}][subjects][{i}][marks_obtained]')) for i in range(len(subject_names))]
            max_marks = [int(data.get(f'semesters[{sem}][subjects][{i}][max_marks]')) for i in range(len(subject_names))]
            
            for name, obtained, max_mark in zip(subject_names, marks_obtained, max_marks):
                subjects.append({
                    'subject': name,
                    'marks_obtained': obtained,
                    'max_marks': max_mark
                })
                total_marks_obtained += obtained
                total_max_marks += max_mark
            
            semesters.append({'semester': sem + 1, 'subjects': subjects})

        # Calculate percentage and grade
        percentage = (total_marks_obtained / total_max_marks) * 100 if total_max_marks > 0 else 0
        grade = 'F'
        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'

        # Update student record in database
        result = students.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'srn': srn,
                'name': data.get('name'),
                'age': int(data.get('age')),
                'phone_number': data.get('phone_number'),
                'semesters': semesters,
                'percentage': percentage,
                'grade': grade
            }}
        )

        if result.matched_count > 0:
            if result.modified_count > 0:
                flash('Student details updated successfully!', 'success')
            else:
                flash('No changes made to the student details.', 'warning')
        else:
            flash('Failed to update student details. Student not found.', 'error')
        
        return redirect(url_for('index'))

    return render_template('edit_student.html', student=student)



@app.route('/delete_student/<id>')
def delete_student(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    result = students.delete_one({'_id': ObjectId(id)})
    if result.deleted_count > 0:
        flash('Student deleted successfully.')
    else:
        flash('Student not found.')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)



