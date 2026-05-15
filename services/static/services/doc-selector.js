const DocumentSelector = (() => {
    const state = {
        allDocs: [
            "Aadhaar Card",
            "Passport Size Photo",
            "PAN Card",
            "10th Marksheet",
            "12th Marksheet",
            "Degree Certificate",
            "Transfer Certificate (TC)",
            "Income Certificate",
            "Community Certificate",
            "EWS Certificate",
            "Ration Card",
            "Voter ID",
            "Driving License",
            "Bank Passbook",
            "Cancelled Cheque",
            "Passport",
            "Birth Certificate",
            "Residence Certificate",
            "Disability Certificate",
            "Experience Certificate",
            "Marriage Certificate",
            "Hospital Records",
            "Police Clearance Certificate",
            "Signature",
            "Address Proof",
            "father's Aadhaar",
            "mother's Aadhaar",
            "son's Aadhaar",
            "daughter's Aadhaar",
            "guardian's Aadhaar",
            "father's PAN",
            "mother's PAN",
            "son's PAN",
            "daughter's PAN",
            "guardian's PAN",
            "father's Passport",
            "mother's Passport",
            "son's Passport",
            "daughter's Passport",
            "father's Birth Certificate",
            "mother's Birth Certificate",
            "son's Birth Certificate",
            "daughter's Birth Certificate",
            "father's Income Certificate",
            "mother's Income Certificate",
            "son's Income Certificate",
            "daughter's Income Certificate",
            "father's Disability Certificate",
            "mother's Disability Certificate",
            "son's Disability Certificate",
            "daughter's Disability Certificate",
            "father's Experience Certificate",
            "mother's Experience Certificate",
            "son's Experience Certificate",
            "daughter's Experience Certificate",
            "father's community certificate",
            "mother's community certificate",
            "son's community certificate",
            "daughter's community certificate"
        ],
        selectedDocs: [],
        elements: {},
        showAll: false
    };

    const normalize = (value) => {
        return value
            .trim()
            .toLowerCase()
            .replace(/["'`´‘’]/g, '')
            .replace(/[^a-z0-9\s]/g, ' ')
            .replace(/\s+/g, ' ');
    };

    const updateHiddenField = () => {
        state.elements.hiddenField.value = state.selectedDocs.join(',');
    };

    const isSelected = (doc) => {
        const normalizedDoc = normalize(doc);
        return state.selectedDocs.some(item => normalize(item) === normalizedDoc);
    };

    const levenshteinDistance = (a, b) => {
        const matrix = Array.from({ length: b.length + 1 }, (_, index) => [index]);
        for (let i = 0; i <= a.length; i += 1) {
            matrix[0][i] = i;
        }

        for (let i = 1; i <= b.length; i += 1) {
            for (let j = 1; j <= a.length; j += 1) {
                if (b[i - 1] === a[j - 1]) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j - 1] + 1
                    );
                }
            }
        }
        return matrix[b.length][a.length];
    };

    const findBestMatch = (inputValue) => {
        const normalizedInput = normalize(inputValue);
        if (!normalizedInput) {
            return null;
        }

        let bestMatch = null;
        let bestDistance = Number.POSITIVE_INFINITY;

        state.allDocs.forEach((doc) => {
            const normalizedDoc = normalize(doc);
            if (normalizedDoc === normalizedInput) {
                bestMatch = doc;
                bestDistance = 0;
                return;
            }

            const distance = levenshteinDistance(normalizedInput, normalizedDoc);
            const threshold = Math.max(1, Math.floor(Math.min(normalizedInput.length, normalizedDoc.length) * 0.2));
            if (distance <= threshold && distance < bestDistance) {
                bestMatch = doc;
                bestDistance = distance;
            }
        });

        return bestMatch;
    };

    const addDoc = (rawValue) => {
        const value = rawValue.trim();
        if (!value) {
            return;
        }

        const existingDoc = findBestMatch(value) || value;
        const normalizedExisting = normalize(existingDoc);

        if (!state.allDocs.some(doc => normalize(doc) === normalizedExisting)) {
            state.allDocs.push(existingDoc);
        }

        if (isSelected(existingDoc)) {
            state.elements.input.value = '';
            renderDocList();
            return;
        }

        state.selectedDocs.push(existingDoc);
        state.elements.input.value = '';

        renderDocList();
        renderTags();
    };

    const removeDoc = (docValue) => {
        const normalizedDoc = normalize(docValue);
        state.selectedDocs = state.selectedDocs.filter(doc => normalize(doc) !== normalizedDoc);
        renderDocList();
        renderTags();
    };

    const renderDocList = () => {
        state.elements.docList.innerHTML = '';

        const limit = 10;
        const docsToRender = state.showAll ? state.allDocs : state.allDocs.slice(0, limit);

        docsToRender.forEach((doc) => {
            const span = document.createElement('span');
            span.className = 'doc-item';
            span.textContent = doc;
            span.tabIndex = 0;
            span.setAttribute('role', 'button');
            span.setAttribute('aria-pressed', isSelected(doc));
            span.addEventListener('click', () => addDoc(doc));
            span.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    addDoc(doc);
                }
            });

            if (isSelected(doc)) {
                span.classList.add('selected');
            }

            state.elements.docList.appendChild(span);
        });

        if (!state.showAll && state.allDocs.length > limit) {
            const moreBtn = document.createElement('span');
            moreBtn.className = 'doc-item more-btn';
            moreBtn.textContent = 'More...';
            moreBtn.style.color = '#2563eb';
            moreBtn.style.fontWeight = 'bold';
            moreBtn.addEventListener('click', () => {
                state.showAll = true;
                renderDocList();
            });
            state.elements.docList.appendChild(moreBtn);
        }

        if (state.showAll && state.allDocs.length > limit) {
            const lessBtn = document.createElement('span');
            lessBtn.className = 'doc-item less-btn';
            lessBtn.textContent = 'Less...';
            lessBtn.style.color = '#2563eb';
            lessBtn.style.fontWeight = 'bold';
            lessBtn.addEventListener('click', () => {
                state.showAll = false;
                renderDocList();
            });
            state.elements.docList.appendChild(lessBtn);
        }
    };

    const renderTags = () => {
        state.elements.tagBox.innerHTML = '';

        state.selectedDocs.forEach((doc) => {
            const tag = document.createElement('div');
            tag.className = 'tag';
            tag.textContent = doc;

            const removeButton = document.createElement('span');
            removeButton.textContent = '×';
            removeButton.setAttribute('role', 'button');
            removeButton.setAttribute('aria-label', `Remove ${doc}`);
            removeButton.addEventListener('click', () => removeDoc(doc));
            tag.appendChild(removeButton);
            state.elements.tagBox.appendChild(tag);
        });

        state.elements.tagBox.appendChild(state.elements.input);
        updateHiddenField();
    };

    const addDocsFromInput = () => {
        const values = state.elements.input.value
            .split(',')
            .map(value => value.trim())
            .filter(Boolean);

        values.forEach(addDoc);
        state.elements.input.value = '';
    };

    const handleInputKeydown = (event) => {
        const value = state.elements.input.value.trim();
        if (event.key === 'Enter' || event.key === ',') {
            event.preventDefault();
            if (value) {
                addDocsFromInput();
            }
        }
    };

    const handleInputBlur = () => {
        if (state.elements.input.value.trim()) {
            addDocsFromInput();
        }
    };

    const handleDocumentClick = (event) => {
        const isInside = state.elements.tagBox.contains(event.target) || state.elements.docList.contains(event.target);
        if (!isInside) {
            addDoc(state.elements.input.value);
        }
    };

    const init = () => {
        state.elements.docList = document.getElementById('docList');
        state.elements.tagBox = document.getElementById('tagBox');
        state.elements.input = document.getElementById('customInput');
        state.elements.hiddenField = document.getElementById('finalDocs');

        if (!state.elements.docList || !state.elements.tagBox || !state.elements.input || !state.elements.hiddenField) {
            return;
        }

        const existingValue = state.elements.hiddenField.value;
        if (existingValue) {
            state.selectedDocs = existingValue.split(',').map(doc => doc.trim()).filter(Boolean);
            state.selectedDocs.forEach((doc) => {
                if (!state.allDocs.some(existing => normalize(existing) === normalize(doc))) {
                    state.allDocs.push(doc);
                }
            });
        }

        state.elements.input.addEventListener('keydown', handleInputKeydown);
        state.elements.input.addEventListener('blur', handleInputBlur);
        document.addEventListener('click', handleDocumentClick);

        renderDocList();
        renderTags();
    };

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', DocumentSelector.init);
} else {
    DocumentSelector.init();
}
