const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");

const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = "en-US";

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
        }, 20);
    });
}

// Auto-scroll to latest message
function scrollToBottom() {
    chatbox.scrollTop = chatbox.scrollHeight;
}

function addSmartSuggestions() {
    const suggestionDiv = document.createElement("div");
    suggestionDiv.className = "smart-suggestions";

    const suggestions = [
        "📚 Today's Classes",
        "👨‍🏫 Faculty Info",
        "🗺️ Campus Map",
        "📝 Exam Schedule",
        "📅 View Timetable"
    ];

    suggestions.forEach((text, i) => {
        const button = document.createElement("button");
        button.innerText = text;
        button.style.animation = `slideUpFadeIn 0.4s ease-out forwards`;
        button.style.animationDelay = `${i * 0.1}s`;
        button.onclick = () => handleSuggestion(text);
        suggestionDiv.appendChild(button);
    });

    chatbox.appendChild(suggestionDiv);
    scrollToBottom();
}
function toggleMenu() {
    const menu = document.getElementById("mobileMenu");
    menu.classList.toggle("visible");
}



function handleSuggestion(text) {
    addMessage('user', text);

    const staticReplies = {
        "🗺️ Campus Map": "Here's the <a href='https://www.google.com/maps/place/Balochistan+University+of+Information+Technology,+Engineering+and+Management+Sciences/@30.2689375,66.9440625,17z/data=!3m1!4b1!4m6!3m5!1s0x3ed31e4e8de39e87:0xdcf9f2538ac2317d!8m2!3d30.2689375!4d66.9440625!16zL20vMDlrXzZ3?entry=ttu&g_ep=EgoyMDI1MDcwNi4wIKXMDSoASAFQAw%3D%3D' target='_blank'>BUITEMS Campus Map</a>",
        "👨‍🏫 Faculty Info": "Visit our <a href='https://www.buitms.edu.pk/Faculty-of-ICT' target='_blank'>Faculty Directory</a>",
        "📅 View Timetable": null,// handled by opening PDF directly
        "📝 Exam Schedule":"Final exams are likely to start around July 17, 2025."
    };

    if (staticReplies[text]) {
        typeMessage(staticReplies[text], 'bot', true);
    } else if (text === "📅 View Timetable") {
        window.open('static/timetable.pdf', '_blank');
    } else if (text === "📚 Today's Classes") {
        sendToBackend({ intent: "today_classes" });
    }
    else {
        sendToBackend(text);
    }

    document.querySelector('.smart-suggestions')?.remove();
}

function showDepartmentOptions() {
    const deptDiv = document.createElement("div");
    deptDiv.className = "smart-suggestions";

    const departments = [
        "BS-CS", "BS-SE", "BS-IT", "BS-EE", "BS-AI"
    ];

    departments.forEach((dept, i) => {
        const button = document.createElement("button");
        button.innerText = dept;
        button.style.animation = `slideUpFadeIn 0.4s ease-out forwards`;
        button.style.animationDelay = `${i * 0.1}s`;
        button.onclick = () => {
            addMessage("user", `Today's classes for ${dept}`);
            sendToBackend(`Today's classes for ${dept}`);
            deptDiv.remove();
        };
        deptDiv.appendChild(button);
    });

    chatbox.appendChild(deptDiv);
    scrollToBottom();
}

function addMessage(sender, message) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = message;
    chatbox.appendChild(messageDiv);
    scrollToBottom();
}

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
    if (data.buttons) {
        typeMessage(data.prompt, 'bot').then(() => {
            showDynamicButtons(data.buttons, data.followup_intent || null, data.context || {});
        });
        return;
    } else if (data.classes) {
        const classCards = data.classes.map(c => `<div class="card">${c}</div>`).join("");
        typeMessage(data.message + "<br><br>" + classCards, 'bot', true);
    } else {
        typeMessage(data.response || data.message, 'bot');
    }
    })
    .catch(error => {
        typeMessage("Sorry, something went wrong.", 'bot');
        console.error('Error:', error);
    });
}

function showDynamicButtons(buttons, followupIntent = null, context = {}) {
    const container = document.createElement("div");
    container.className = "smart-suggestions";

    buttons.forEach((btnText, i) => {
        const button = document.createElement("button");
        button.innerText = btnText;
        button.style.animation = `slideUpFadeIn 0.4s ease-out forwards`;
        button.style.animationDelay = `${i * 0.1}s`;

        button.onclick = () => {
            addMessage("user", btnText);
            const payload = {
                intent: followupIntent || "today_classes",
                ...context
            };

            // Determine if it's a program or semester selection
            if (!context.program) {
                payload.program = btnText;
            } else {
                payload.semester = btnText;
            }

            sendToBackend(payload);
            container.remove();
        };

        container.appendChild(button);
    });

    chatbox.appendChild(container);
    scrollToBottom();
}

sendBtn.addEventListener("click", () => {
    const userMessage = userInput.value.trim();
    if (userMessage) {
        addMessage("user", userMessage);
        sendToBackend(userMessage);
        userInput.value = "";
    }
});

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

window.addEventListener('DOMContentLoaded', async () => {
    await typeMessage("👋 Hi! I'm your BUITEMS assistant. How can I help you today?", 'bot');
    addSmartSuggestions();
});
