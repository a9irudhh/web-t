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

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle form submission here if needed
        pass
    
    return render_template('index.html')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        srn = f"SRN{int(data['srn']):03d}"

        if students.find_one({'srn': srn}):
            flash('A student with this SRN already exists.', 'error')
            return redirect(url_for('add_student'))

        total_marks_obtained = 0
        total_max_marks = 0

        semesters = []
        for sem in range(1, 4):  # Assuming 3 semesters
            subjects = [{'subject': subj,
                         'marks_obtained': int(data[f'sem{sem}_{subj}_marks_obtained']),
                         'max_marks': int(data[f'sem{sem}_{subj}_max_marks'])}
                        for subj in ['Math', 'Science', 'English']]
            
            # Calculate total marks and max marks
            for subj in subjects:
                total_marks_obtained += subj['marks_obtained']
                total_max_marks += subj['max_marks']
            
            semesters.append({'semester': sem, 'subjects': subjects})

        # Calculate average percentage
        if total_max_marks > 0:
            percentage = (total_marks_obtained / total_max_marks) * 100
        else:
            percentage = 0

        # Determine the grade
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

        students.insert_one({
            'srn': srn,
            'name': data['name'],
            'age': int(data['age']),
            'number': data['number'],
            'semesters': semesters,
            'percentage': percentage,  # Store the calculated percentage
            'grade': grade             # Store the calculated grade
        })
        flash('Student added successfully.')
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

    if request.method == 'POST':
        data = request.form
        srn = data['srn'] 

        semesters = []
        for sem in range(1, 4):
            subjects = [{'subject': subj,
                         'marks_obtained': int(data[f'sem{sem}_{subj}_marks_obtained']),
                         'max_marks': int(data[f'sem{sem}_{subj}_max_marks'])}
                        for subj in ['Math', 'Science', 'English']]
            semesters.append({'semester': sem, 'subjects': subjects})

        students.update_one({'_id': ObjectId(id)}, {'$set': {
            'srn': srn,
            'name': data['name'],
            'age': int(data['age']),
            'number': data['number'],
            'semesters': semesters
        }})
        flash('Student updated successfully.')
        return redirect(url_for('index'))
    
    student = students.find_one({'_id': ObjectId(id)})
    if student:
        return render_template('edit_student.html', student=student)
    flash('Student not found.')
    return redirect(url_for('index'))

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
