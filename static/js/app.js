const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
// JavaScript



// Typing effect function
function typeMessage(text, className, isHTML = false) {
    return new Promise((resolve) => {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        chatbox.appendChild(msgDiv);

        if (isHTML) {
            msgDiv.innerHTML = text;
            scrollToBottom();
            resolve(); 
            return;
        }

        let index = 0;
        const interval = setInterval(() => {
            msgDiv.textContent += text.charAt(index);
            index++;
            if (index >= text.length) {
                clearInterval(interval);
                resolve();
            }
            scrollToBottom();
        }, 20); // Typing speed
    });
}

// Auto-scroll to latest message
function scrollToBottom() {
    chatbox.scrollTop = chatbox.scrollHeight;
}

// Smart suggestions
function addSmartSuggestions() {
    const suggestionDiv = document.createElement("div");
    suggestionDiv.className = "smart-suggestions";
    
    suggestionDiv.innerHTML = `
        <button onclick="handleSuggestion('Today\'s Classes')">📚 Today's Classes</button>
        <button onclick="handleSuggestion('Faculty Info')">👨‍🏫 Faculty Info</button>
        <button onclick="handleSuggestion('Campus Map')">🗺️ Campus Map</button>
        <button onclick="handleSuggestion('Exam Schedule')">📝 Exam Schedule</button>
        <button onclick="window.open('static/timetable.pdf', '_blank')">📅 View Timetable</button>
    `;

    chatbox.appendChild(suggestionDiv);
    scrollToBottom();
}

// Handle button click
function handleSuggestion(text) {
    addMessage('user', text);        // User message
    sendToBackend(text);             // Send to backend
    document.querySelector('.smart-suggestions')?.remove();
}

// Add user message
function addMessage(sender, message) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;
    msgDiv.textContent = message;
    chatbox.appendChild(msgDiv);
    scrollToBottom();
}

// Dummy backend send (you have your real sendToBackend)
function sendToBackend(message) {
    console.log("Sending to backend:", message);
}

// Load initial message and suggestions
window.addEventListener('DOMContentLoaded', async () => {
    await typeMessage("👋 Hi! I'm your BUITEMS assistant. How can I help you today?", 'bot');
    addSmartSuggestions();
});
// // Typing effect for bot message
// function typeMessage(text, className) {
//     const msgDiv = document.createElement("div");
//     msgDiv.className = `message ${className}`;
//     chatbox.appendChild(msgDiv);

//     let index = 0;
//     const interval = setInterval(() => {
//         msgDiv.textContent += text.charAt(index);
//         index++;
//         if (index >= text.length) clearInterval(interval);
//         scrollToBottom();
//     }, 20); // typing speed

    
// }


// // Scroll to bottom helper
// function scrollToBottom() {
//     chatbox.scrollTop = chatbox.scrollHeight;
// }

// Add static message (used for user message)
function addMessage(sender, message) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = message;
    chatbox.appendChild(messageDiv);
    scrollToBottom();
}

// Send user message to Flask backend
function sendToBackend(userMessage) {
    fetch('http://127.0.0.1:5000/get_response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Use typing animation for bot's reply
        typeMessage(data.response, 'bot');
    })
    .catch(error => {
        typeMessage("Sorry, something went wrong.", 'bot');
        console.error('Error:', error);
    });
}

// Handle send button click
sendBtn.addEventListener("click", () => {
    const userMessage = userInput.value.trim();
    if (userMessage) {
        addMessage("user", userMessage);
        sendToBackend(userMessage);
        userInput.value = "";
    }
});

// Handle Enter key press
userInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage("user", userMessage);
            sendToBackend(userMessage);
            userInput.value = "";
        }
    }
});


// Smart Greeting on Page Load
window.onload = () => {
    setTimeout(() => {
        typeMessage("Hi! I'm your BUITEMS assistant. Ask me about classes, schedules, or anything else.", 'bot');
    }, 500);
};


const micBtn = document.getElementById("micBtn");

const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = "en-US";

micBtn.addEventListener("click", () => {
    recognition.start();
    micBtn.classList.add("listening");
});

recognition.onresult = (event) => {
    const speech = event.results[0][0].transcript;
    userInput.value = speech;
    sendBtn.click();
};

recognition.onend = () => {
    micBtn.classList.remove("listening");
};

