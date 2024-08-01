from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import json, math

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

    # Pagination settings
    page = int(request.args.get('page', 1))
    per_page = 3
    skip = (page - 1) * per_page

    # Get the search query from the request
    query = request.args.get('query', '')

    # Search filter
    filter_query = {}
    if query:
        filter_query = {
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'srn': {'$regex': query, '$options': 'i'}},
                {'phone_number': {'$regex': query, '$options': 'i'}},
                {'grade': {'$regex': query, '$options': 'i'}}
            ]
        }

    total_students = students.count_documents(filter_query)
    total_pages = math.ceil(total_students / per_page)

    student_list = list(students.find(filter_query).skip(skip).limit(per_page))
    
    is_admin = session.get('username') == 'admin@oneOrigin'

    return render_template('index.html', students=student_list, is_admin=is_admin, page=page, total_pages=total_pages, query=query)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        srn = data['srn']
        
        if students.find_one({'srn': srn}):
            flash('A student with this SRN already exists.', 'error')
            return redirect(url_for('add_student'))

        total_marks_obtained = 0
        total_max_marks = 0
        semesters = []

        sem_count = 0
        while f'sem{sem_count + 1}_subject1_name' in data:
            sem_count += 1
        
        for sem in range(1, sem_count + 1):
            subjects = []
            idx = 1
            while f'sem{sem}_subject{idx}_name' in data:
                subject_name = data.get(f'sem{sem}_subject{idx}_name')
                marks_obtained = int(data.get(f'sem{sem}_subject{idx}_marks_obtained'))
                max_marks = 100  # Default max_marks is 100

                subjects.append({
                    'subject': subject_name,
                    'marks_obtained': marks_obtained,
                    'max_marks': max_marks
                })
                total_marks_obtained += marks_obtained
                total_max_marks += max_marks

                idx += 1

            semesters.append({'semester': sem, 'subjects': subjects})

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

    is_admin = session.get('username') == 'admin@oneOrigin'

    if request.method == 'POST':
        try:
            # Ensure the content type is JSON
            if request.content_type != 'application/json':
                return {'error': 'Content-Type must be application/json'}, 400

            # Get JSON data from the request
            data = request.get_json()
            print("Data:", data)  # Debugging line to check the data
            
            # Extract and format SRN
            srn_value = data.get('srn', '')
            print("SRN Value:", srn_value)  # Debugging line to check the data
            numeric_srn = ''.join(filter(str.isdigit, srn_value))
            srn = f"SRN{int(numeric_srn):03d}" if numeric_srn else 'SRN000'

            # Check for duplicate SRN
            if students.find_one({'srn': srn, '_id': {'$ne': ObjectId(id)}}):
                return {'error': 'A student with this SRN already exists.'}, 400

            total_marks_obtained = 0
            total_max_marks = 0
            semesters = data.get('semesters', [])
            print("debugging", semesters)

            # Extract semester data from the JSON
            for i, sem in semesters:
                semester_number = sem.get('semester', i + 1)
                print("debugging",sem)
                subjects = []
                for j, subj in enumerate(sem.get('subjects', [])):
                    print("debugging",subj)
                    subject_name = subj.get('subject', '')
                    marks_obtained = int(subj.get('marks_obtained', 0))
                    max_marks = int(subj.get('max_marks', 100))

                    total_marks_obtained += marks_obtained
                    total_max_marks += max_marks

                    subjects.append({
                        'subject': subject_name,
                        'marks_obtained': marks_obtained,
                        'max_marks': max_marks
                    })

                semesters.append({
                    'semester': semester_number,
                    'subjects': subjects
                })

            # Update student document
            result = students.update_one(
                {'_id': ObjectId(id)},
                {
                    '$set': {
                        'name': data.get('name', ''),
                        'age': int(data.get('age', 0)),
                        'phone_number': data.get('phone_number', ''),
                        'srn': srn,
                        'total_marks_obtained': total_marks_obtained,
                        'total_max_marks': total_max_marks,
                        'semesters': semesters
                    }
                }
            )

            if result.matched_count > 0:
                if result.modified_count > 0:
                    return {'message': 'Student details updated successfully!'}
                else:
                    return {'message': 'No changes made to the student details.'}
            else:
                return {'error': 'Failed to update student details. Student not found.'}, 404

        except Exception as e:
            return {'error': f'An error occurred: {str(e)}'}, 500

    return render_template('edit_student.html', student=student, is_admin=is_admin)


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



