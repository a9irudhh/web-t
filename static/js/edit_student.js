document.addEventListener('DOMContentLoaded', function() {
    // Confirm before saving
    window.confirmSave = function() {
        return confirm("Are you sure you want to save these changes?");
    };

    // Add a new semester
    window.addSemester = function() {
        const semContainer = document.getElementById('semesters');
        const semCount = semContainer.children.length + 1;
        const semHTML = `
            <div class="edit-student-semester" id="semester-${semCount}">
                <h2 class="edit-student-semester-title">Semester ${semCount}</h2>
                <table class="edit-student-table">
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
                            <td><input type="text" name="semesters[${semCount-1}][subjects][0][name]" required></td>
                            <td><input type="number" name="semesters[${semCount-1}][subjects][0][marks_obtained]" required></td>
                            <td><input type="number" name="semesters[${semCount-1}][subjects][0][max_marks]" value="100" required></td>
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
    window.removeSemester = function(button) {
        button.closest('.edit-student-semester').remove();
    };

    // Add a new subject to a semester
    window.addSubject = function(button) {
        const semCount = button.getAttribute('data-semester');
        const subjectContainer = document.getElementById(`subjects-${semCount}`);
        const subjectCount = subjectContainer.children.length;
        const subjectHTML = `
            <tr>
                <td><input type="text" name="semesters[${semCount-1}][subjects][${subjectCount}][name]" required></td>
                <td><input type="number" name="semesters[${semCount-1}][subjects][${subjectCount}][marks_obtained]" required></td>
                <td><input type="number" name="semesters[${semCount-1}][subjects][${subjectCount}][max_marks]" value="100" required></td>
                <td><button type="button" onclick="removeSubject(this)">Remove Subject</button></td>
            </tr>
        `;
        subjectContainer.insertAdjacentHTML('beforeend', subjectHTML);
    };

    // Remove a subject row
    window.removeSubject = function(button) {
        button.closest('tr').remove();
    };

    // Handle form submission
    const form = document.querySelector('.edit-student-form');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission

            if (!confirmSave()) {
                return;
            }

            const formData = new FormData(form);
            const data = {};

            formData.forEach((value, key) => {
                const keys = key.match(/([^\[\]]+)/g);
                keys.reduce((acc, curr, index) => {
                    if (index === keys.length - 1) {
                        acc[curr] = value;
                    } else {
                        if (!acc[curr]) acc[curr] = {};
                    }
                    return acc[curr];
                }, data);
            });

            // Format data
            const formattedData = {
                name: data.name,
                age: data.age,
                phone_number: data.phone_number,
                srn: data.srn,
                semesters: []
            };

            // Process the data
            Object.keys(data).forEach(key => {
                if (key.startsWith('semesters')) {
                    const match = key.match(/^semesters\[(\d+)\]/);
                    if (match) {
                        const semIndex = parseInt(match[1], 10);
                        if (!formattedData.semesters[semIndex]) {
                            formattedData.semesters[semIndex] = { semester: semIndex + 1, subjects: [] };
                        }

                        const subjectMatch = key.match(/subjects\[(\d+)\]/);
                        if (subjectMatch) {
                            const subjectIndex = parseInt(subjectMatch[1], 10);
                            if (!formattedData.semesters[semIndex].subjects[subjectIndex]) {
                                formattedData.semesters[semIndex].subjects[subjectIndex] = {};
                            }

                            const field = key.split('[').pop().split(']')[0];
                            formattedData.semesters[semIndex].subjects[subjectIndex][field] = value;
                        }
                    }
                }
            });

            // Remove empty semesters if any
            formattedData.semesters = formattedData.semesters.filter(sem => sem.subjects.length > 0);
            console.log(formattedData);
            // Send the data
            fetch(form.action, {
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
                    window.location.href = result.redirect || '/';
                }
            })
            .catch(error => {
                alert('An unexpected error occurred. Please try again.');
            });            
        });
    }
});
