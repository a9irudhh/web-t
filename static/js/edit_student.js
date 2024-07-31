document.addEventListener('DOMContentLoaded', function() {
    // Confirm Save
    window.confirmSave = function() {
        return confirm("Are you sure you want to save these changes?");
    };

    // Add Semester
    window.addSemester = function() {
        const semContainer = document.getElementById('semesters');
        const semCount = semContainer.children.length + 1;
        const semHTML = `
            <div class="edit-student-semester" id="semester-${semCount}">
                <h2 class="edit-student-semester-title">Semester ${semCount}</h2>
                <table class="edit-student-table">
                    <thead>
                        <tr>
                            <th>Marks Obtained</th>
                            <th>Max Marks</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="subjects-${semCount}">
                        <tr>
                            <td><input type="number" name="semesters[${semCount-1}][subjects][0][marks_obtained]" required></td>
                            <td><input type="number" name="semesters[${semCount-1}][subjects][0][max_marks]" value="100" required></td>
                            <td><button type="button" onclick="removeSubject(this)">Remove Subject</button></td>
                        </tr>
                    </tbody>
                </table>
                <button type="button" class="add-subject-button" data-semester="${semCount}">Add Subject</button>
                <button type="button" class="remove-semester-button" onclick="removeSemester(this)">Remove Semester</button>
            </div>
        `;
        semContainer.insertAdjacentHTML('beforeend', semHTML);
    };

    // Remove Semester
    window.removeSemester = function(button) {
        button.parentElement.remove();
    };

    // Add Subject
    window.addSubject = function(semCount) {
        const subjectContainer = document.getElementById(`subjects-${semCount}`);
        const subjectCount = subjectContainer.children.length;
        const subjectHTML = `
            <tr>
                <td><input type="number" name="semesters[${semCount-1}][subjects][${subjectCount}][marks_obtained]" required></td>
                <td><input type="number" name="semesters[${semCount-1}][subjects][${subjectCount}][max_marks]" value="100" required></td>
                <td><button type="button" onclick="removeSubject(this)">Remove Subject</button></td>
            </tr>
        `;
        subjectContainer.insertAdjacentHTML('beforeend', subjectHTML);
    };

    // Remove Subject
    window.removeSubject = function(button) {
        button.parentElement.parentElement.remove();
    };

    // Attach click handlers for dynamically added "Add Subject" buttons
    document.addEventListener('click', function(event) {
        if (event.target.matches('.add-subject-button')) {
            const semCount = event.target.getAttribute('data-semester');
            addSubject(parseInt(semCount, 10));
        }
    });
});
