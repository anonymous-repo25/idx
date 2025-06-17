document.addEventListener('DOMContentLoaded', function () {
    const fileSelect = document.getElementById('file-select');
    const questionSelect = document.getElementById('question-select');
    const selectedQuestionTextElement = document.getElementById('selected-question-text');
    const selectedQuestionSearchingAreaElement = document.getElementById('selected-question-searching-area');
    const selectedQuestionDescriptionElement = document.getElementById('selected-question-description');
    const viewPdfLink = document.getElementById('viewPdfLink');
    const pdfModal = document.getElementById('pdfModal');
    const pdfViewer = document.getElementById('pdfViewer');
    const pdfModalTitle = document.getElementById('pdfModalTitle');
    const modalCloseButton = document.querySelector('.modal-close-button');
    const pdfFallbackLink = document.getElementById('pdfFallbackLink');
    const pdfFallbackLinkContainer = document.getElementById('pdfFallbackLinkContainer');

    const fileLoader = document.getElementById('file-loader');
    const questionLoader = document.getElementById('question-loader');

    const modelTextareas = {
        'Model1': document.getElementById('model1-answer'),
        'Model2': document.getElementById('model2-answer'),
        'Model3': document.getElementById('model3-answer'),
        'Model4': document.getElementById('model4-answer')
    };
    const modelRatingGroups = {
        'Model1': document.querySelectorAll('input[name="model1_rating"]'),
        'Model2': document.querySelectorAll('input[name="model2_rating"]'),
        'Model3': document.querySelectorAll('input[name="model3_rating"]'),
        'Model4': document.querySelectorAll('input[name="model4_rating"]')
    };

    const prefix = "NO INTRODUCTION IS REQUIRED, JUST DIRECTLY PROVIDE THE ANSWER. ANSWER BASED ON THE GIVEN TEXT ONLY. IF THE ANSWER IS NOT MENTIONED, PLEASE RETURN 'NOT MENTIONED'.";

    function cleanQuestionText(text) {
        if (!text) return '';
        const normalized = text.trim().toUpperCase();
        if (normalized.startsWith(prefix.toUpperCase())) {
            return text.slice(prefix.length).trim();
        }
        return text.trim();
    }

    function resetModelInputs() {
        Object.values(modelTextareas).forEach(area => area.value = '');
        Object.values(modelRatingGroups).forEach(group => {
            group.forEach(radio => {
                radio.checked = (radio.value === 'VB');
            });
        });
    }

    function resetQuestionDisplay() {
        if (selectedQuestionTextElement) selectedQuestionTextElement.textContent = 'Selected Question: (None)';
        if (selectedQuestionSearchingAreaElement) selectedQuestionSearchingAreaElement.textContent = 'Searching area: (None)';
        if (selectedQuestionDescriptionElement) selectedQuestionDescriptionElement.textContent = 'Description: (None)';
        const displayArea = document.getElementById('selected-question-display-area');
        if (displayArea) displayArea.style.display = 'none';
        if (viewPdfLink) viewPdfLink.style.display = 'none';
        if (selectedQuestionTextElement) selectedQuestionTextElement.style.color = '';
    }

    function loadPromptsForFile(fileId, preSelectedPromptId = null) {
        questionSelect.innerHTML = '<option value="">-- Loading Questions --</option>';
        resetModelInputs();
        resetQuestionDisplay();

        const selectedFileOption = fileSelect.options[fileSelect.selectedIndex];
        const selectedFileName = selectedFileOption?.dataset.filename;

        if (selectedFileName && viewPdfLink) {
            const pdfUrl = `/static/pdfs/${selectedFileName}`;
            viewPdfLink.href = pdfUrl;
            viewPdfLink.dataset.pdfsrc = pdfUrl;
            viewPdfLink.dataset.pdftitle = selectedFileName;
            viewPdfLink.style.display = 'inline-block';
        }

        if (!fileId) return;

        if (fileLoader) fileLoader.style.display = 'inline-block';

        fetch(`/get_prompts_for_file/${fileId}`)
            .then(res => res.json())
            .then(data => {
                if (fileLoader) fileLoader.style.display = 'none';
                questionSelect.innerHTML = '<option value="">-- Select a Question --</option>';

                if (!Array.isArray(data)) {
                    questionSelect.innerHTML = '<option value="">Invalid response</option>';
                    return;
                }

                data.forEach(prompt => {
                    const option = document.createElement('option');
                    option.value = prompt.pid;
                    const cleanedText = cleanQuestionText(prompt.displayText);

                    option.textContent = prompt.is_evaluated ? `✔ ${cleanedText}` : cleanedText;
                    option.dataset.fullText = prompt.fullPromptText;
                    option.dataset.searchingArea = prompt.searching_area || '(Not specified)';
                    option.dataset.description = prompt.description || '(No description)';
                    if (prompt.is_evaluated) {
                        option.dataset.evaluated = 'true';
                    }

                    questionSelect.appendChild(option);
                });

                if (preSelectedPromptId) {
                    questionSelect.value = preSelectedPromptId;
                    questionSelect.dispatchEvent(new Event('change'));
                }
            })
            .catch(err => {
                if (fileLoader) fileLoader.style.display = 'none';
                questionSelect.innerHTML = `<option value="">Error loading: ${err.message}</option>`;
            });
    }

    function handleQuestionChange() {
        const fileId = fileSelect.value;
        const promptId = questionSelect.value;
        resetModelInputs();

        const selectedOption = questionSelect.options[questionSelect.selectedIndex];
        const fullText = selectedOption?.dataset.fullText || '';
        const searchingArea = selectedOption?.dataset.searchingArea || '(None)';
        const isEvaluated = selectedOption?.dataset.evaluated === 'true';
        const cleanedText = cleanQuestionText(fullText);
        const description = selectedOption?.dataset.description || '(None)';

        selectedQuestionTextElement.textContent = `Selected Question: ${cleanedText}`;
        selectedQuestionTextElement.style.color = isEvaluated ? 'red' : '';
        selectedQuestionSearchingAreaElement.textContent = `Searching area: ${searchingArea}`;
        selectedQuestionDescriptionElement.textContent = `Description: ${description}`;

        document.getElementById('selected-question-display-area').style.display = 'block';

        if (fileId && promptId) {
            if (questionLoader) questionLoader.style.display = 'inline-block';

            fetch(`/get_model_responses/${fileId}/${promptId}`)
                .then(res => res.json())
                .then(data => {
                    if (questionLoader) questionLoader.style.display = 'none';
                    for (const key in modelTextareas) {
                        if (data[key]) {
                            modelTextareas[key].value = data[key];
                        }
                    }
                })
                .catch(err => {
                    if (questionLoader) questionLoader.style.display = 'none';
                    console.error("Model response fetch error:", err);
                });
        }
    }

    // Event Bindings
    fileSelect.addEventListener('change', function () {
        loadPromptsForFile(this.value);
    });

    questionSelect.addEventListener('change', handleQuestionChange);

    // PDF Modal Logic
    if (viewPdfLink && pdfModal && modalCloseButton && pdfViewer) {
        viewPdfLink.addEventListener('click', function (e) {
            e.preventDefault();
            const pdfSrc = this.dataset.pdfsrc;
            const pdfTitle = this.dataset.pdftitle || 'PDF Document';

            if (pdfSrc) {
                pdfViewer.src = pdfSrc;
                pdfModalTitle.textContent = pdfTitle;
                pdfModal.style.display = 'block';

                if (pdfFallbackLink && pdfFallbackLinkContainer) {
                    pdfFallbackLink.href = pdfSrc;
                    pdfViewer.onload = () => pdfFallbackLinkContainer.style.display = 'none';
                    pdfViewer.onerror = () => pdfFallbackLinkContainer.style.display = 'block';
                }
            } else {
                alert('Invalid or missing PDF.');
            }
        });

        modalCloseButton.addEventListener('click', () => {
            pdfModal.style.display = 'none';
            pdfViewer.src = '';
        });

        window.addEventListener('click', function (e) {
            if (e.target === pdfModal) {
                pdfModal.style.display = 'none';
                pdfViewer.src = '';
            }
        });
    }

    // Initial load
    if (fileSelect.value) {
        loadPromptsForFile(fileSelect.value);
    } else {
        resetModelInputs();
        resetQuestionDisplay();
    }
});
