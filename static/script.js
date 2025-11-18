// Simple Chatbot JavaScript
document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const inputContainer = document.querySelector('.input-container');

    // Auto-resize textarea functionality
    function autoResizeTextarea() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }

    // Add input listener for auto-resize
    messageInput.addEventListener('input', autoResizeTextarea);

    // Handle Enter key for form submission (Shift+Enter for new line)
    messageInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Set initial time for greeting message
    const initialTimeElement = document.getElementById('initialTime');
    if (initialTimeElement) {
        initialTimeElement.textContent = getCurrentTime();
    }

    // Improve input container click behavior
    if (inputContainer) {
        inputContainer.addEventListener('click', function (e) {
            // If clicking anywhere in the input container, focus the input
            if (e.target !== messageInput && !messageInput.contains(e.target)) {
                messageInput.focus();
            }
        });
    }

    // Handle form submission
    chatForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message) {
            // Show a brief visual feedback instead of validation tooltip
            inputContainer.style.borderColor = '#ff6b6b';
            inputContainer.style.boxShadow = '0 0 0 2px rgba(255, 107, 107, 0.2)';
            setTimeout(() => {
                inputContainer.style.borderColor = '';
                inputContainer.style.boxShadow = '';
            }, 1500);
            messageInput.focus();
            return;
        }

        // Add user message to chat
        addMessage(message, 'user');

        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Show typing indicator
        showTypingIndicator();

        try {
            // Send message to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Hide typing indicator
            hideTypingIndicator();

            // Add bot response to chat
            setTimeout(() => {
                addMessage(data.response, 'bot');
            }, 500); // Small delay for more natural feel

        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    });

    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (sender === 'user') {
            messageContent.innerHTML = `<strong>You:</strong> ${escapeHtml(message)}`;
        } else {
            // Format bot message with proper line breaks and formatting
            const formattedMessage = formatBotMessage(message);
            messageContent.innerHTML = `<strong>Assistant:</strong><div class="bot-response">${formattedMessage}</div>`;
        }

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = getCurrentTime();

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const existingIndicator = document.querySelector('.typing-indicator');
        if (existingIndicator) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.textContent = 'Bot is typing...';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatBotMessage(message) {
        // The backend already formats the message with HTML tags, so we just return it as-is
        // This allows <br>, <strong>, <em>, and other HTML tags to render properly
        return message;
    }

    // Focus on input field when page loads
    messageInput.focus();

    // Handle Enter key in input field
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
});