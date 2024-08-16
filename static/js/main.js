pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.9.359/pdf.worker.min.js';

let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 3;
let mode = 'flashcard';
let apiKey = '';
let currentFileName = '';
let currentPage = 1;
let selectedModel = 'claude-3-haiku-20240307';
let lastProcessedQuery = '';
let lastRequestTime = 0;
const cooldownTime = 1000; // 1 second cooldown

const fileInput = document.getElementById('file-input');
const pdfViewer = document.getElementById('pdf-viewer');
const modeToggle = document.getElementById('mode-toggle');
const systemPrompt = document.getElementById('system-prompt');
const submitBtn = document.getElementById('submit-btn');
const flashcardsContainer = document.getElementById('flashcards');
const apiKeyInput = document.getElementById('api-key-input');
const modelSelect = document.getElementById('model-select');
const recentPdfList = document.getElementById('pdf-list');

function renderPage(num) {
    pageRendering = true;
    pdfDoc.getPage(num).then(function (page) {
        const viewport = page.getViewport({ scale: scale });
        const pixelRatio = window.devicePixelRatio || 1;
        const adjustedViewport = page.getViewport({ scale: scale * pixelRatio });

        const pageDiv = document.createElement('div');
        pageDiv.className = 'page';
        pageDiv.dataset.pageNumber = num;
        pageDiv.style.width = `${viewport.width}px`;
        pageDiv.style.height = `${viewport.height}px`;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.height = adjustedViewport.height;
        canvas.width = adjustedViewport.width;
        canvas.style.width = `${viewport.width}px`;
        canvas.style.height = `${viewport.height}px`;

        const renderContext = {
            canvasContext: ctx,
            viewport: adjustedViewport,
            enableWebGL: true,
            renderInteractiveForms: true,
        };

        const renderTask = page.render(renderContext);

        renderTask.promise.then(function () {
            pageRendering = false;
            if (pageNumPending !== null) {
                renderPage(pageNumPending);
                pageNumPending = null;
            }
        });

        pageDiv.appendChild(canvas);

        const textLayerDiv = document.createElement('div');
        textLayerDiv.className = 'text-layer';
        textLayerDiv.style.width = `${viewport.width}px`;
        textLayerDiv.style.height = `${viewport.height}px`;
        pageDiv.appendChild(textLayerDiv);

        page.getTextContent().then(function (textContent) {
            pdfjsLib.renderTextLayer({
                textContent: textContent,
                container: textLayerDiv,
                viewport: viewport,
                textDivs: []
            });
        });

        pdfViewer.appendChild(pageDiv);

        attachLanguageModeListener(pageDiv);

        if (num < pdfDoc.numPages && pdfViewer.scrollHeight <= window.innerHeight * 2) {
            renderPage(num + 1);
        }
    });
}

function loadPDF(file) {
    const fileReader = new FileReader();
    fileReader.onload = function () {
        const typedarray = new Uint8Array(this.result);

        pdfjsLib.getDocument(typedarray).promise.then(function (pdf) {
            pdfDoc = pdf;
            pdfViewer.innerHTML = '';
            currentFileName = file.name;
            const lastPage = localStorage.getItem(`lastPage_${currentFileName}`);
            pageNum = lastPage ? Math.max(parseInt(lastPage) - 2, 1) : 1;
            renderPage(pageNum);
            updateCurrentPage(pageNum);
            hideHeaderPanel();
        });
    };
    fileReader.readAsArrayBuffer(file);
}

function hideHeaderPanel() {
    document.getElementById('top-bar').style.display = 'none';
}

function goToPage(num) {
    if (num >= 1 && num <= pdfDoc.numPages) {
        pageNum = num;
        pdfViewer.innerHTML = '';
        renderPage(pageNum);
        updateCurrentPage(pageNum);
        localStorage.setItem(`lastPage_${currentFileName}`, pageNum);
    } else {
        alert('Invalid page number');
    }
}

function updateCurrentPage(num) {
    if (num !== currentPage) {
        currentPage = num;
        document.getElementById('current-page').textContent = `Page: ${num}`;
        document.getElementById('page-input').value = num;
        localStorage.setItem(`lastPage_${currentFileName}`, num);
    }
}

document.getElementById('left-panel').addEventListener('scroll', function () {
    if (this.scrollTop + this.clientHeight >= this.scrollHeight - 500) {
        if (pageNum < pdfDoc.numPages) {
            pageNum++;
            renderPage(pageNum);
        }
    }

    const pages = document.querySelectorAll('.page');
    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        const rect = page.getBoundingClientRect();
        if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
            const newPageNum = parseInt(page.dataset.pageNumber);
            updateCurrentPage(newPageNum);
            break;
        }
    }
});

function handleLanguageMode(event, targetLanguage) {
    if (mode !== 'language') return;

    event.preventDefault();
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const selectedText = selection.toString().trim();
        if (selectedText) {
            const phrase = getPhrase(range);
            const currentTime = Date.now();
            if (phrase !== lastProcessedQuery && currentTime - lastRequestTime >= cooldownTime) {
                lastProcessedQuery = phrase;
                lastRequestTime = currentTime;
                generateLanguageFlashcard(selectedText, phrase, targetLanguage);
            }
        }
    }
}

function getPhrase(range) {
    const sentenceStart = /[.!?]\s+[A-Z]|^[A-Z]/;
    const sentenceEnd = /[.!?](?=\s|$)/;

    let startNode = range.startContainer;
    let endNode = range.endContainer;
    let startOffset = range.startOffset;
    let endOffset = range.endOffset;

    while (startNode && startNode.textContent && !sentenceStart.test(startNode.textContent.slice(0, startOffset))) {
        if (startNode.previousSibling) {
            startNode = startNode.previousSibling;
            startOffset = startNode.textContent ? startNode.textContent.length : 0;
        } else if (startNode.parentNode && startNode.parentNode.previousSibling) {
            startNode = startNode.parentNode.previousSibling.lastChild;
            startOffset = startNode && startNode.textContent ? startNode.textContent.length : 0;
        } else {
            break;
        }
    }

    while (endNode && endNode.textContent && !sentenceEnd.test(endNode.textContent.slice(endOffset))) {
        if (endNode.nextSibling) {
            endNode = endNode.nextSibling;
            endOffset = 0;
        } else if (endNode.parentNode && endNode.parentNode.nextSibling) {
            endNode = endNode.parentNode.nextSibling.firstChild;
            endOffset = 0;
        } else {
            break;
        }
    }

    if (startNode && startNode.nodeType === Node.TEXT_NODE &&
        endNode && endNode.nodeType === Node.TEXT_NODE &&
        startNode.textContent && endNode.textContent) {
        const phraseRange = document.createRange();
        phraseRange.setStart(startNode, startOffset);
        phraseRange.setEnd(endNode, endOffset);
        return phraseRange.toString().trim();
    } else {
        return range.toString().trim();
    }
}

async function generateLanguageFlashcard(word, phrase, targetLanguage) {
    if (!apiKey) {
        alert('Please enter your Claude API key first.');
        return;
    }

    const prompt = document.getElementById('language-prompt').value
        .replace('{word}', word)
        .replace('{phrase}', phrase)
        .replace('{targetLanguage}', targetLanguage);

    try {
        const response = await callClaudeAPI(prompt);
        if (response.flashcard) {
            const flashcard = response.flashcard;
            const formattedFlashcard = {
                question: flashcard.question,
                answer: flashcard.answer,
                word: flashcard.word,
                translation: flashcard.translation
            };
            displayLanguageFlashcard(formattedFlashcard);
        } else {
            throw new Error('Invalid response from API');
        }
    } catch (error) {
        console.error('Error calling Claude API:', error);
        alert('Failed to generate language flashcard. Please check your API key and try again.');
    }
}

async function generateContent() {
    if (!apiKey) {
        alert('Please enter your Claude API key first.');
        return;
    }

    const selection = window.getSelection();
    if (selection.rangeCount > 0 && selection.toString().trim() !== '') {
        const selectedText = selection.toString();
        let prompt;
        
        if (mode === 'flashcard') {
            prompt = `${systemPrompt.value}\n\n${selectedText}`;
        } else if (mode === 'explain') {
            const explainPromptValue = document.getElementById('explain-prompt').value;
            prompt = `${explainPromptValue}\n\n${selectedText}`;
        } else {
            return;
        }

        submitBtn.disabled = true;
        submitBtn.style.backgroundColor = '#808080';
        const notification = document.createElement('div');
        notification.textContent = 'Generating...';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px';
        notification.style.backgroundColor = 'rgba(0, 128, 0, 0.7)';
        notification.style.color = 'white';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '1000';
        document.body.appendChild(notification);

        try {
            const response = await callClaudeAPI(prompt);
            if (mode === 'flashcard' && response.flashcards) {
                displayFlashcards(response.flashcards, true);
            } else if (mode === 'explain' && response.explanation) {
                displayExplanation(response.explanation);
            } else {
                throw new Error('Invalid response from API');
            }
        } catch (error) {
            console.error('Error calling Claude API:', error);
            alert(`Failed to generate ${mode === 'flashcard' ? 'flashcards' : 'explanation'}. Please check your API key and try again.`);
        } finally {
            setTimeout(() => {
                document.body.removeChild(notification);
                submitBtn.disabled = false;
                submitBtn.style.backgroundColor = '';
            }, 3000);
        }
    } else {
        alert(`Please select some text from the PDF to generate ${mode === 'flashcard' ? 'flashcards' : 'an explanation'}.`);
    }
}

function displayExplanation(explanation) {
    const explanationElement = document.createElement('div');
    explanationElement.className = 'explanation';
    explanationElement.innerHTML = `
        <h3>Explanation</h3>
        <div class="explanation-content">${explanation}</div>
        <button class="remove-btn">Remove</button>
    `;
    explanationElement.querySelector('.remove-btn').addEventListener('click', function () {
        explanationElement.remove();
    });
    flashcardsContainer.appendChild(explanationElement);

    const modal = document.getElementById('explanationModal');
    const modalContent = document.getElementById('explanationModalContent');
    const closeBtn = document.getElementsByClassName('close')[0];

    const converter = new showdown.Converter();
    const htmlContent = converter.makeHtml(explanation);

    modalContent.innerHTML = htmlContent;
    modal.style.display = 'block';

    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

async function callClaudeAPI(prompt) {
    const response = await fetch('/generate_flashcard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
        },
        body: JSON.stringify({ 
            prompt: prompt,
            model: selectedModel,
            mode: mode
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

modelSelect.addEventListener('change', function () {
    selectedModel = this.value;
});

function displayFlashcards(flashcards, append = false) {
    if (!append) {
        flashcardsContainer.innerHTML = '';
    }
    flashcards.forEach(flashcard => {
        const flashcardElement = document.createElement('div');
        flashcardElement.className = 'flashcard';
        flashcardElement.innerHTML = `
            <strong>Q: ${flashcard.question}</strong><br>
            A: ${flashcard.answer}
            <button class="remove-btn">Remove</button>
        `;
        flashcardElement.querySelector('.remove-btn').addEventListener('click', function () {
            flashcardElement.remove();
            updateExportButtonVisibility();
        });
        flashcardsContainer.appendChild(flashcardElement);
    });
    updateExportButtonVisibility();
}

function displayLanguageFlashcard(flashcard) {
    const flashcardElement = document.createElement('div');
    flashcardElement.className = 'flashcard language-flashcard';
    flashcardElement.dataset.question = flashcard.question;
    flashcardElement.dataset.word = flashcard.word;
    flashcardElement.dataset.translation = flashcard.translation;
    flashcardElement.dataset.answer = flashcard.answer;
    flashcardElement.innerHTML = `
        <div style="font-size: 1.2em; margin-bottom: 10px;">${flashcard.question}</div>
        <div>- ${flashcard.answer}</div>
        <button class="remove-btn">Remove</button>
    `;
    flashcardElement.querySelector('.remove-btn').addEventListener('click', function () {
        flashcardElement.remove();
        updateExportButtonVisibility();
    });
    flashcardsContainer.appendChild(flashcardElement);
    updateExportButtonVisibility();
}

let collectionCount = 0;
let collectedFlashcards = [];

function addToCollection() {
    const newFlashcards = Array.from(document.querySelectorAll('.flashcard:not(.in-collection)')).map(flashcard => {
        if (flashcard.classList.contains('language-flashcard')) {
            const word = flashcard.dataset.word;
            const translation = flashcard.dataset.translation;
            const answer = flashcard.dataset.answer;
            const question = flashcard.dataset.question;
            return {
                phrase: question,
                translationAnswer: `${translation.trim()}\n${answer.trim()}`
            };
        } else {
            const question = flashcard.querySelector('strong').textContent.slice(3);
            const answer = flashcard.innerHTML.split('<br>')[1].split('<button')[0].trim().slice(3);
            return {
                phrase: question,
                translationAnswer: answer
            };
        }
    });

    collectedFlashcards = collectedFlashcards.concat(newFlashcards);
    updateCollectionCount(newFlashcards.length);
    clearDisplayedFlashcards();
    updateExportButtonVisibility();
}

function clearDisplayedFlashcards() {
    flashcardsContainer.innerHTML = '';
}

function updateCollectionCount(change) {
    collectionCount += change;
    const addToCollectionBtn = document.getElementById('add-to-collection-btn');
    addToCollectionBtn.textContent = `Add to Collection (${collectionCount})`;
    localStorage.setItem('collectionCount', collectionCount);
    localStorage.setItem('collectedFlashcards', JSON.stringify(collectedFlashcards));
}

collectionCount = parseInt(localStorage.getItem('collectionCount')) || 0;
collectedFlashcards = JSON.parse(localStorage.getItem('collectedFlashcards')) || [];
document.getElementById('add-to-collection-btn').textContent = `Add to Collection (${collectionCount})`;

document.getElementById('add-to-collection-btn').addEventListener('click', addToCollection);

function updateExportButtonVisibility() {
    const exportButton = document.getElementById('export-csv-btn');
    exportButton.style.display = collectedFlashcards.length > 0 ? 'block' : 'none';
}

function exportToCSV() {
    let csvContent = "data:text/csv;charset=utf-8,";

    collectedFlashcards.forEach(flashcard => {
        csvContent += `"${flashcard.phrase}";"${flashcard.translationAnswer}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "flashcards.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

document.getElementById('export-csv-btn').addEventListener('click', exportToCSV);

function clearCollection() {
    if (confirm('Are you sure you want to clear the entire collection? This action cannot be undone.')) {
        collectedFlashcards = [];
        collectionCount = 0;
        updateCollectionCount(0);
        updateExportButtonVisibility();
        localStorage.removeItem('collectedFlashcards');
        localStorage.removeItem('collectionCount');
    }
}

document.getElementById('clear-collection-btn').addEventListener('click', clearCollection);

updateExportButtonVisibility();

function addRecentPDF(filename) {
    let recentPDFs = JSON.parse(localStorage.getItem('recentPDFs')) || [];
    recentPDFs = recentPDFs.filter(pdf => pdf.filename !== filename);
    recentPDFs.unshift({ filename: filename, date: new Date().toISOString() });
    recentPDFs = recentPDFs.slice(0, 5);
    localStorage.setItem('recentPDFs', JSON.stringify(recentPDFs));
    updateRecentPDFsList();
}

function updateRecentPDFsList() {
    const recentPDFs = JSON.parse(localStorage.getItem('recentPDFs')) || [];
    recentPdfList.innerHTML = '';
    recentPDFs.forEach(pdf => {
        const li = document.createElement('li');
        li.textContent = `${pdf.filename} (${new Date(pdf.date).toLocaleDateString()})`;
        recentPdfList.appendChild(li);
    });
}

fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file.type !== 'application/pdf') {
        console.error('Error: Not a PDF file');
        return;
    }
    loadPDF(file);
    addRecentPDF(file.name);
    this.nextElementSibling.textContent = file.name;
});

const fileNameDisplay = document.createElement('span');
fileNameDisplay.style.marginLeft = '10px';
fileInput.parentNode.insertBefore(fileNameDisplay, fileInput.nextSibling);

function handleGoToPage() {
    const pageInput = document.getElementById('page-input');
    const pageNumber = parseInt(pageInput.value);
    goToPage(pageNumber);
}

document.getElementById('go-to-page-btn').addEventListener('click', handleGoToPage);

document.getElementById('page-input').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        handleGoToPage();
    }
});

const modeButtons = document.querySelectorAll('.mode-btn');
modeButtons.forEach(button => {
    button.addEventListener('click', function() {
        modeButtons.forEach(btn => btn.classList.remove('selected'));
        this.classList.add('selected');
        mode = this.dataset.mode;
        pdfViewer.style.cursor = mode === 'language' ? 'text' : 'default';
        document.getElementById('language-buttons').style.display = mode === 'language' ? 'flex' : 'none';
        systemPrompt.style.display = mode === 'flashcard' ? 'block' : 'none';
        document.getElementById('explain-prompt').style.display = mode === 'explain' ? 'block' : 'none';
        document.getElementById('language-prompt').style.display = mode === 'language' ? 'block' : 'none';
        submitBtn.style.display = mode === 'language' ? 'none' : 'block';
        submitBtn.textContent = mode === 'flashcard' ? 'Generate Flashcards' : 'Generate Explanation';
    });
});

const languageButtons = document.querySelectorAll('#language-buttons .mode-btn');
languageButtons.forEach(button => {
    button.addEventListener('click', function(event) {
        event.preventDefault();
        languageButtons.forEach(btn => btn.classList.remove('selected'));
        this.classList.add('selected');
        const targetLanguage = this.dataset.language;
        document.querySelector('.mode-btn[data-mode="language"]').classList.add('selected');
        document.getElementById('language-buttons').style.display = 'flex';
        submitBtn.style.display = 'none';
        mode = 'language';
    });
});

function attachLanguageModeListener(pageDiv) {
    pageDiv.addEventListener('dblclick', function(event) {
        if (mode === 'language') {
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);
            const word = selection.toString().trim();
            
            if (word !== '') {
                const selectedLanguageButton = document.querySelector('#language-buttons .mode-btn.selected');
                if (selectedLanguageButton) {
                    const targetLanguage = selectedLanguageButton.dataset.language;
                    const phrase = getPhrase(range, word);
                    generateLanguageFlashcard(word, phrase, targetLanguage);
                } else {
                    console.error('No language selected');
                }
            }
        }
    });
}

function getPhrase(range, word) {
    let startNode = range.startContainer;
    let endNode = range.endContainer;
    let startOffset = Math.max(0, range.startOffset - 50);
    let endOffset = Math.min(endNode.length, range.endOffset + 50);

    let phrase = '';
    let currentNode = startNode;
    while (currentNode) {
        if (currentNode.nodeType === Node.TEXT_NODE) {
            const text = currentNode.textContent;
            const start = currentNode === startNode ? startOffset : 0;
            const end = currentNode === endNode ? endOffset : text.length;
            phrase += text.slice(start, end);
        }
        if (currentNode === endNode) break;
        currentNode = currentNode.nextSibling;
    }

    const wordRegex = new RegExp(`\\b${word}\\b`, 'gi');
    phrase = phrase.replace(wordRegex, `<b>$&</b>`);

    return phrase.trim();
}

submitBtn.addEventListener('click', generateContent);

apiKeyInput.addEventListener('change', function () {
    apiKey = this.value;
    localStorage.setItem('lastWorkingAPIKey', apiKey);
});

const lastWorkingAPIKey = localStorage.getItem('lastWorkingAPIKey');
if (lastWorkingAPIKey) {
    apiKeyInput.value = lastWorkingAPIKey;
    apiKey = lastWorkingAPIKey;
}

document.getElementById('left-panel').addEventListener('scroll', function () {
    if (this.scrollTop + this.clientHeight >= this.scrollHeight - 500) {
        if (pageNum < pdfDoc.numPages) {
            pageNum++;
            renderPage(pageNum);
        }
    }
});

function loadRecentPDFs() {
    const recentPDFs = JSON.parse(localStorage.getItem('recentPDFs')) || [];
    const pdfList = document.getElementById('pdf-list');
    pdfList.innerHTML = '';
    recentPDFs.forEach(pdf => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = `${pdf.filename} (${new Date(pdf.date).toLocaleDateString()})`;
        a.addEventListener('click', function(e) {
            e.preventDefault();
            fetch(`/open_pdf/${pdf.filename}`)
                .then(response => response.blob())
                .then(blob => {
                    const file = new File([blob], pdf.filename, { type: 'application/pdf' });
                    loadPDF(file);
                })
                .catch(error => console.error('Error:', error));
        });
        li.appendChild(a);
        pdfList.appendChild(li);
    });
}

window.addEventListener('beforeunload', function() {
    if (currentFileName) {
        localStorage.setItem(`lastPage_${currentFileName}`, pageNum);
    }
});

window.onload = function() {
    loadRecentPDFs();
    
    document.getElementById('settings-icon').addEventListener('click', function() {
        const settingsPanel = document.getElementById('settings-panel');
        settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
    });
};

fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file.type !== 'application/pdf') {
        console.error('Error: Not a PDF file');
        return;
    }
    uploadPDF(file);
});

function uploadPDF(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload_pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            console.log(data.message);
            loadPDF(file);
            loadRecentPDFs();
        } else {
            console.error(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
