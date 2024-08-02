from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import json, math, re, io, csv

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

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    print("This is file", file)
    
    # is_admin = session.get('username') == 'admin@oneOrigin'
    
    # if 'username' not in session or is_admin:
    #     return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in the request'}), 400

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected for uploading'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'Please upload a CSV file'}), 400


    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        header = next(csv_input)  # Read header row

        print("This is header", header)
        print("This is csv_input", csv_input)
        print("This is csv_input", csv_input)
        
        
        for row in csv_input:
            if not row or len(row) < 4:
                continue  # Skip invalid rows

            name = row[0].strip()
            print("This is name", name)
            age = int(row[1].strip())
            print("This is age", age)
            srn = row[2].strip()
            print("This is srn", srn)
            phone_number = row[3].strip()
            print("This is phone_number", phone_number)
            
            # Extract subjects and marks dynamically
            semesters = []
            subjects = []
            semester_index = 1

            for i in range(4, len(row), 3):  # Start from index 4 and process every 3 columns
                # if i + 2 >= len(row):
                #     break  # Ensure there are enough columns for subject data

                subject_name = row[i].strip()
                print("This is subject_name", subject_name)
                marks_obtained = int(row[i + 1].strip())
                print("This is marks_obtained", marks_obtained)
                max_marks = 100  # Default max_marks is 100

                if subject_name and marks_obtained and max_marks:
                    subjects.append({
                        'subject': subject_name,
                        'marks_obtained': marks_obtained,
                        'max_marks': max_marks
                    })

                print("This is subjects", subjects)
                # Check if next set of subject columns exists
                if i + 3 >= len(row) or not row[i + 3].strip():
                    if subjects:
                        semesters.append({'semester': semester_index, 'subjects': subjects})
                        subjects = []  # Reset subjects for next semester
                        semester_index += 1

            # Add any remaining subjects for the last semester
            if subjects:
                semesters.append({'semester': semester_index, 'subjects': subjects})
            
            print("This is semesters", semesters)

            # Calculate percentage and grade
            total_marks_obtained = sum(subject['marks_obtained'] for sem in semesters for subject in sem['subjects'])
            total_max_marks = sum(subject['max_marks'] for sem in semesters for subject in sem['subjects'])
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

            print("This is total_marks_obtained", total_marks_obtained)
            print("This is total_max_marks", total_max_marks)
            
            print("This is percentage", percentage)
            print("This is grade", grade)
            student_data = {
                'name': name,
                'age': age,
                'srn': srn,
                'phone_number': phone_number,
                'semesters': semesters,
                'percentage': percentage,
                'grade': grade
            }
            print(f"Attempting to insert/update: {student_data}")

            try:
                students.update_one({'srn': srn}, {'$set': student_data}, upsert=True)
                print(f"Successfully inserted/updated: {student_data}")
            except Exception as insert_exception:
                print(f"Error inserting/updating document: {insert_exception}")
                return jsonify({'success': False, 'message': 'Failed to insert/update student data'}), 500

        return jsonify({'success': True, 'message': 'File successfully uploaded'})

    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'success': False, 'message': 'Failed to process file'}), 500


@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '')
    grade_filter = request.args.get('grade', '')
    percentage_filter = request.args.get('percentage', '')

    # Convert query to regex for case-insensitive matching
    query_regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    filter_criteria = {
        '$or': [
            {'name': query_regex},
            {'srn': query_regex},
            {'phone_number': query_regex}
        ]
    }

    if grade_filter:
        filter_criteria['grade'] = grade_filter

    if percentage_filter:
        # Example percentage filter format: '10-20'
        min_percent, max_percent = map(int, percentage_filter.split('-'))
        filter_criteria['percentage'] = {'$gte': min_percent, '$lte': max_percent}

    # Count total number of students matching the filter criteria
    total_count = students.count_documents(filter_criteria)
    
    # Pagination logic
    page = int(request.args.get('page', 1))
    per_page = 5
    total_pages = (total_count + per_page - 1) // per_page
    skip = (page - 1) * per_page
    
    students_list = students.find(filter_criteria).skip(skip).limit(per_page)
    is_admin = session.get('username') == 'admin@oneOrigin'

    return render_template('index.html', 
                           students=students_list, 
                           query=query, 
                           page=page, 
                           total_pages=total_pages, 
                           grade=grade_filter,
                           percentage=percentage_filter,
                           is_admin=is_admin)

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
        print("This is Student data", student_data)
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
    # Check if the student exists
    student = students.find_one({'_id': ObjectId(id)})
    if not student:
        flash('Student not found.')
        return redirect(url_for('index'))

    is_admin = session.get('username') == 'admin@oneOrigin'
    if 'username' in session and session['username'] != 'admin@oneOrigin':
        flash('You are not authorized to edit students.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Debug: Print request data
            print("Request form data:", request.form)

            # Check if request is JSON or form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            # Debug: Print parsed data
            print("Parsed data:", data)

            # Validate and format SRN
            srn_value = data.get('srn', '')
            print("This is srn_value", srn_value)
            numeric_srn = ''.join(filter(str.isdigit, srn_value))
            print("This is numeric_srn", numeric_srn)
            srn = f"SRN{int(numeric_srn):03d}" if numeric_srn else 'SRN000'
            print("This is srn", srn)
            # Check for duplicate SRN
            if students.find_one({'srn': srn, '_id': {'$ne': ObjectId(id)}}):
                flash('A student with this SRN already exists.', 'error')
                return redirect(url_for('edit_student', id=id))

            
            # Process semesters and subjects
            total_marks_obtained = 0
            total_max_marks = 0
            semesters = data.get('semesters', [])
            print("This is semesters", semesters)
            for sem in semesters:
                sem['semester'] = int(sem.get('semester', 0))
                print("This is sem", sem)
                for subject in sem.get('subjects', []):
                    print("This is subject", subject)
                    total_marks_obtained += int(subject.get('marks_obtained', 0))
                    total_max_marks += int(subject.get('max_marks', 100))

            percentage = (total_marks_obtained / total_max_marks) * 100 if total_max_marks > 0 else 0
            print("This is percentage", percentage)
            # Determine grade based on percentage
            grade = 'F'
            if percentage >= 90:
                grade = 'A'
            elif percentage >= 80:
                grade = 'B'
            elif percentage >= 70:
                grade = 'C'
            elif percentage >= 60:
                grade = 'D'

            # Prepare student data to be updated
            print("This is grade", grade)
            
            student_data = {
                'name': data.get('name', ''),
                'age': int(data.get('age', 0)),
                'phone_number': data.get('phone_number', ''),
                'srn': srn,
                'semesters': semesters,
                'percentage': percentage,
                'grade': grade
            }

            # Debug: Print student data to be updated
            print("Student data to be updated:", student_data)

            # Update student data in the database
            result = students.update_one(
                {'_id': ObjectId(id)},
                {'$set': student_data}
            )

            print("This is result", result)
            if result.matched_count > 0:
                if result.modified_count > 0:
                    flash('Student details updated successfully!', 'success')
                else:
                    flash('No changes made to the student details.', 'info')
            else:
                flash('Failed to update student details. Student not found.', 'error')

            return jsonify({'message': 'Student updated successfully', 'redirect': url_for('index')})

        except Exception as e:
            # Handle any other exceptions
            print(f"An error occurred: {str(e)}")            
            flash(f'An error occurred: {str(e)}', 'error')
            return jsonify({'error': 'An unexpected error occurred.'}), 500

    # Render the edit student page for GET requests
    return render_template('edit_student.html', student=student, is_admin=is_admin)


@app.route('/delete_student/<id>')
def delete_student(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'username' in session and session['username'] != 'admin@oneOrigin':
        flash('You are not authorized to delete students.', 'error')
        return redirect(url_for('index'))
    
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



