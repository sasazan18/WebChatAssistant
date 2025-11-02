// Extension popup JavaScript matching content.js functionality
const API_URL = 'http://localhost:8000';

let currentUrl = '';
let currentPageInfo = null;

// Get current page information when popup opens
async function getCurrentPageInfo() {
    try {
        // Query the active tab directly (no content script needed)
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        currentPageInfo = {
            url: tab.url,
            title: tab.title,
            domain: new URL(tab.url).hostname
        };
        currentUrl = tab.url;
        
        // Update UI with current page info
        const pageInfoElement = document.getElementById('webchat-page-info');
        if (pageInfoElement) {
            pageInfoElement.textContent = currentPageInfo.title || currentPageInfo.domain;
            pageInfoElement.title = currentPageInfo.url; // Show full URL on hover
        }
        
        // Initialize chat for this page
        initializeChat();
        
        return currentPageInfo;
    } catch (error) {
        console.error('Error getting page info:', error);
        showError('Unable to get current page information. Please refresh the page and try again.');
        return null;
    }
}

function initializeChat() {
    // Just setup event listeners for the existing HTML elements
    setupSuggestionListeners();
}

function setupSuggestionListeners() {
    const suggestionBtns = document.querySelectorAll('.webchat-suggestion-btn');
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            const queryInput = document.getElementById('webchat-query');
            queryInput.value = query;
            sendMessage();
        });
    });
}

function addMessage(content, isUser = false) {
    const messagesContainer = document.getElementById('webchat-messages');
    
    // Remove suggestions after first user message
    if (isUser) {
        const suggestions = messagesContainer.querySelector('.webchat-suggestions');
        if (suggestions) {
            suggestions.remove();
        }
    }
    
    const messageGroup = document.createElement('div');
    messageGroup.className = isUser ? 'webchat-user-message-group' : 'webchat-bot-message-group';
    
    if (isUser) {
        messageGroup.innerHTML = `
            <div class="webchat-message-bubble webchat-user-bubble">
                <div class="webchat-message-content">${content}</div>
            </div>
        `;
    } else {
        messageGroup.innerHTML = `
            <div class="webchat-message-bubble webchat-bot-bubble">
                <div class="webchat-message-content">${content}</div>
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageGroup);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showError(message) {
    const messagesContainer = document.getElementById('webchat-messages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'webchat-error';
    errorDiv.textContent = message;
    messagesContainer.appendChild(errorDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('webchat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'webchat-typing-indicator';
    typingDiv.id = 'webchat-typing-indicator';
    typingDiv.innerHTML = `
        <div class="webchat-typing-bubble">
            <div class="webchat-typing-dot"></div>
            <div class="webchat-typing-dot"></div>
            <div class="webchat-typing-dot"></div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('webchat-typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const queryInput = document.getElementById('webchat-query');
    const sendBtn = document.getElementById('webchat-send');
    const query = queryInput.value.trim();
    
    if (!query) return;
    
    if (!currentUrl) {
        showError('Unable to get current page URL. Please refresh and try again.');
        return;
    }
    
    // Add user message to chat
    // Add user message
    addMessage(query, true);
    
    // Clear input and disable button
    queryInput.value = '';
    sendBtn.disabled = true;
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl,
                query: query
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Check if the backend returned an error
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Add bot response with slight delay for realism
        setTimeout(() => {
            addMessage(data.answer);
        }, 300);
        
    } catch (error) {
        console.error('WebChat Error:', error);
        
        
        showError(`Error: ${error.message}. Make sure WebChat backend is running.`);
        
    } finally {
        // Re-enable send button but keep it disabled until user types
        setTimeout(() => {
            const queryInput = document.getElementById('webchat-query');
            queryInput.focus();
        }, 100);
    }
}

async function clearChat() {
    try {
        // Call the reset endpoint using the same format as content.js
        await fetch(`${API_URL}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl
            })
        });
        
        // Reinitialize chat
        initializeChat();
        
    } catch (error) {
        console.error('Error clearing chat:', error);
        showError('Failed to clear chat on server, but local chat has been cleared.');
        
        // Clear locally anyway
        initializeChat();
    }
}

// Setup event listeners for the popup
function setupEventListeners() {
    const sendBtn = document.getElementById('webchat-send');
    const queryInput = document.getElementById('webchat-query');
    const minimizeBtn = document.getElementById('webchat-minimize');
    
    // Send message
    sendBtn.addEventListener('click', sendMessage);
    
    // Enable/disable send button based on input
    queryInput.addEventListener('input', () => {
        const hasText = queryInput.value.trim().length > 0;
        sendBtn.disabled = !hasText;
    });
    
    // Enter key to send
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (queryInput.value.trim()) {
                sendMessage();
            }
        }
    });
    
    // Minimize button - close the popup
    minimizeBtn.addEventListener('click', () => {
        window.close();
    });
    
    // Focus input after a short delay
    setTimeout(() => queryInput.focus(), 300);
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', async function() {
    // Get current page info
    await getCurrentPageInfo();
    
    // Setup event listeners
    setupEventListeners();
});