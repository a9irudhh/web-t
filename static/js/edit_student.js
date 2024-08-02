document.addEventListener('DOMContentLoaded', function () {
    function saveStudentData() {
        // Check if user is admin
        const isAdmin = document.body.dataset.isAdmin === 'true'; // Updated here
        if (!isAdmin) {
            alert("You do not have permission to save changes.");
            return;
        }

        // Confirm before saving
        if (!confirm("Are you sure you want to save these changes?")) {
            return;
        }

        const form = document.querySelector('.edit-student-form');
        if (!form) return;

        const formData = new FormData(form);
        const data = {};

        // Process FormData into a nested object
        formData.forEach((value, key) => {
            const keys = key.match(/([^\[\]]+)/g);
            let temp = data;

            keys.forEach((k, index) => {
                if (index === keys.length - 1) {
                    temp[k] = value;
                } else {
                    if (!temp[k]) {
                        temp[k] = {};
                    }
                    temp = temp[k];
                }
            });
        });

        console.log('Processed Data:', data);

        // Format data for submission
        const formattedData = {
            name: data.name || '',
            age: data.age || '',
            phone_number: data.phone_number || '',
            srn: data.srn || '',
            semesters: []
        };

        // Process semesters and subjects
        Object.keys(data.semesters || {}).forEach(semIndex => {
            const sem = data.semesters[semIndex];
            const semester = {
                semester: parseInt(semIndex, 10) + 1,
                subjects: []
            };

            Object.keys(sem.subjects || {}).forEach(subjIndex => {
                const subj = sem.subjects[subjIndex];
                semester.subjects.push({
                    subject: subj.subject || '',
                    marks_obtained: subj.marks_obtained || '',
                    max_marks: subj.max_marks || 100
                });
            });

            formattedData.semesters.push(semester);
        });

        console.log('Formatted Data:', formattedData);

        // Get student ID from data attribute
        const studentId = form.dataset.studentId;
        if (!studentId) {
            alert('Student ID is missing.');
            return;
        }

        // Send the data
        fetch(`/edit_student/${studentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formattedData)
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                alert(result.error);
            } else {
                alert(result.message);
                window.location.href = result.redirect || `/view_student/${result.id}`;
            }
        })
        .catch(error => {
            alert('An unexpected error occurred. Please try again.');
            console.error('Error:', error);
        });
    }

    // Add a new semester
    window.addSemester = function () {
        const semContainer = document.getElementById('semesters-container');
        const semCount = semContainer.children.length;
        const semHTML = `
            <div class="semester-group" id="semester-${semCount}">
                <h2 class="semester-title">Semester ${semCount + 1}</h2>
                <table class="semester-table">
                    <thead>
                        <tr>
                            <th>Subject Name</th>
                            <th>Marks Obtained</th>
                            <th>Max Marks</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="subjects-${semCount}">
                        <tr>
                            <td><input type="text" name="semesters[${semCount}][subjects][0][subject]" required></td>
                            <td><input type="number" name="semesters[${semCount}][subjects][0][marks_obtained]" required></td>
                            <td><input type="number" name="semesters[${semCount}][subjects][0][max_marks]" value="100" required></td>
                            <td><button type="button" onclick="removeSubject(this)">Remove Subject</button></td>
                        </tr>
                    </tbody>
                </table>
                <button type="button" class="add-subject-button" data-semester="${semCount}" onclick="addSubject(this)">Add Subject</button>
                <button type="button" class="remove-semester-button" onclick="removeSemester(this)">Remove Semester</button>
            </div>
        `;
        semContainer.insertAdjacentHTML('beforeend', semHTML);
    };

    // Remove a semester
    window.removeSemester = function (button) {
        button.closest('.semester-group').remove();
    };

    // Add a new subject to a semester
    window.addSubject = function (button) {
        const semCount = button.getAttribute('data-semester');
        const subjectContainer = document.getElementById(`subjects-${semCount}`);
        const subjectCount = subjectContainer.children.length;
        const subjectHTML = `
            <tr>
                <td><input type="text" name="semesters[${semCount}][subjects][${subjectCount}][subject]" required></td>
                <td><input type="number" name="semesters[${semCount}][subjects][${subjectCount}][marks_obtained]" required></td>
                <td><input type="number" name="semesters[${semCount}][subjects][${subjectCount}][max_marks]" value="100" required></td>
                <td><button type="button" onclick="removeSubject(this)">Remove Subject</button></td>
            </tr>
        `;
        subjectContainer.insertAdjacentHTML('beforeend', subjectHTML);
    };

    // Remove a subject row
    window.removeSubject = function (button) {
        button.closest('tr').remove();
    };

    // Handle form submission
    const form = document.querySelector('.edit-student-form');
    if (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent default form submission
            saveStudentData(); // Call the function to handle data submission
        });
    }
});
