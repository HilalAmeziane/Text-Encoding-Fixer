document.addEventListener('DOMContentLoaded', function() {
    const MAX_CHARS = 5000;
    const inputText = document.getElementById('input-text');
    const outputText = document.getElementById('output-text');
    const charCount = document.getElementById('char-count');
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const copyButton = document.getElementById('copy-button');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    const processingStatus = document.getElementById('processing-status');
    const convertButton = document.getElementById('convert-button');

    // Fonction pour encoder le texte avant l'envoi
    function encodeText(text) {
        // Convertir le texte en UTF-8 bytes
        const encoder = new TextEncoder();
        const bytes = encoder.encode(text);
        
        // Convertir les bytes en chaîne base64
        return btoa(String.fromCharCode.apply(null, bytes));
    }

    // Fonction pour décoder le texte reçu
    function decodeText(base64) {
        // Décoder la chaîne base64 en bytes
        const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
        
        // Convertir les bytes en texte UTF-8
        const decoder = new TextDecoder('utf-8');
        return decoder.decode(bytes);
    }

    // Synchronize vertical scrolling between textareas
    let isScrolling = false;
    
    function syncScroll(source, target) {
        if (!isScrolling) {
            isScrolling = true;
            
            // Calculate vertical scroll percentage
            const scrollPercentage = source.scrollTop / (source.scrollHeight - source.clientHeight);
            target.scrollTop = Math.round(scrollPercentage * (target.scrollHeight - target.clientHeight));
            
            setTimeout(() => isScrolling = false, 10);
        }
    }

    inputText.addEventListener('scroll', () => syncScroll(inputText, outputText));
    outputText.addEventListener('scroll', () => syncScroll(outputText, inputText));
    
    // Function to update character count
    function updateCharCount(text) {
        const count = text.length;
        charCount.textContent = `${count}/${MAX_CHARS} characters`;
        charCount.className = count > MAX_CHARS 
            ? 'text-sm text-red-500 mt-2 font-medium' 
            : 'text-sm text-indigo-600 mt-2 font-medium';
    }

    // Function to copy converted text
    window.copyToClipboard = function() {
        outputText.select();
        document.execCommand('copy');
        
        // Visual feedback for copy action
        const originalText = copyButton.querySelector('.button-text').textContent;
        copyButton.querySelector('.button-text').textContent = 'Copied!';
        copyButton.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
        copyButton.classList.add('bg-green-500', 'hover:bg-green-600');
        
        setTimeout(() => {
            copyButton.querySelector('.button-text').textContent = originalText;
            copyButton.classList.remove('bg-green-500', 'hover:bg-green-600');
            copyButton.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
        }, 2000);
    };

    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            fileInfo.classList.remove('hidden');
            convertButton.disabled = false;
        } else {
            resetFileUpload();
        }
    });

    // Handle file removal
    removeFile.addEventListener('click', function() {
        resetFileUpload();
    });

    function resetFileUpload() {
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        fileName.textContent = '';
        convertButton.disabled = true;
        processingStatus.classList.add('hidden');
    }

    // Real-time text conversion with debouncing
    let conversionTimeout;
    inputText.addEventListener('input', function(e) {
        const text = e.target.value;
        updateCharCount(text);
        
        if (text.length > MAX_CHARS) {
            outputText.value = 'Error: text too long (limit: 5000 characters)';
            return;
        }

        // Clear previous timeout
        if (conversionTimeout) {
            clearTimeout(conversionTimeout);
        }

        // Set new timeout for conversion
        conversionTimeout = setTimeout(async () => {
            try {
                // Encoder le texte en base64
                const encodedText = encodeText(text);
                
                const response = await fetch('/convert-text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Accept': 'application/json; charset=utf-8'
                    },
                    body: JSON.stringify({ 
                        text: encodedText,
                        isBase64: true,
                        encoding: document.characterSet || 'UTF-8'
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.error) {
                        outputText.value = `Error: ${result.error}`;
                        return;
                    }
                    
                    // Décoder le texte reçu
                    const decodedText = decodeText(result.converted_text);
                    
                    outputText.value = decodedText;
                    
                    // Synchronize scroll position after text update
                    setTimeout(() => {
                        // Scroll to bottom if input is at bottom
                        if (inputText.scrollHeight - inputText.scrollTop === inputText.clientHeight) {
                            outputText.scrollTop = outputText.scrollHeight;
                        } else {
                            // Otherwise maintain relative scroll position
                            const scrollPercentage = inputText.scrollTop / (inputText.scrollHeight - inputText.clientHeight);
                            outputText.scrollTop = Math.round(scrollPercentage * (outputText.scrollHeight - outputText.clientHeight));
                        }
                    }, 0);
                } else {
                    const errorText = await response.text();
                    outputText.value = `Error: ${errorText}`;
                }
            } catch (error) {
                outputText.value = `Server connection error: ${error.message}`;
            }
        }, 300); // Wait 300ms after last input before converting
    });

    // Handle paste event specifically
    inputText.addEventListener('paste', function() {
        // Wait for the paste to complete
        setTimeout(() => {
            // Scroll input to bottom
            inputText.scrollTop = inputText.scrollHeight;
            // Force sync scroll to output
            syncScroll(inputText, outputText);
        }, 0);
    });

    // File upload handling
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        // Show processing status
        processingStatus.classList.remove('hidden');
        convertButton.disabled = true;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'fixed_' + file.name;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                
                // Reset form after successful download
                resetFileUpload();
            } else {
                const errorText = await response.text();
                alert(errorText || 'Error converting file');
            }
        } catch (error) {
            alert('Server connection error');
        } finally {
            processingStatus.classList.add('hidden');
            convertButton.disabled = false;
        }
    });

    // Initialize form state
    resetFileUpload();
});
