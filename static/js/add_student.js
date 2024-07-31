function addSemester() {
    const semestersContainer = document.getElementById('semesters-container');
    const semesterCount = semestersContainer.children.length + 1;

    const semesterDiv = document.createElement('div');
    semesterDiv.className = 'semester-wrapper';
    semesterDiv.id = `semester-${semesterCount}`;
    semesterDiv.innerHTML = `
        <h2>Semester ${semesterCount}</h2>
        <div id="subjects-container-${semesterCount}" class="subjects-container">
            <!-- Subjects will be added dynamically here -->
        </div>
        <button type="button" onclick="addSubject(${semesterCount})" class="add-subject-button">Add Subject</button>
        <button type="button" onclick="removeSemester(${semesterCount})" class="remove-semester-button">Remove Semester</button>
    `;

    semestersContainer.appendChild(semesterDiv);
}

function removeSemester(semesterId) {
    const semesterDiv = document.getElementById(`semester-${semesterId}`);
    if (semesterDiv) {
        semesterDiv.remove();
    }
}

function addSubject(semesterId) {
    const subjectsContainer = document.getElementById(`subjects-container-${semesterId}`);
    const subjectCount = subjectsContainer.children.length + 1;

    const subjectDiv = document.createElement('div');
    subjectDiv.className = 'subject-wrapper';
    subjectDiv.id = `subject-${semesterId}-${subjectCount}`;
    subjectDiv.dataset.subjectIndex = subjectCount;
    subjectDiv.innerHTML = `
        <h3>Subject ${subjectCount}</h3>
        <input type="text" name="sem${semesterId}_subject${subjectCount}_name" placeholder="Subject Name" required class="form-input">
        <input type="number" name="sem${semesterId}_subject${subjectCount}_marks_obtained" placeholder="Marks Obtained" required class="form-input">
        <input type="hidden" name="sem${semesterId}_subject${subjectCount}_max_marks" value="100">
        <button type="button" onclick="removeSubject(${semesterId}, ${subjectCount})" class="remove-subject-button">Remove Subject</button>
    `;

    subjectsContainer.appendChild(subjectDiv);
}

function removeSubject(semesterId, subjectCount) {
    const subjectDiv = document.getElementById(`subject-${semesterId}-${subjectCount}`);
    if (subjectDiv) {
        subjectDiv.remove();
    }
}
