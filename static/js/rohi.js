console.log("Rohi JS Loaded");

document.addEventListener("DOMContentLoaded", () => {
    const courseSlug = window.COURSE_SLUG;
    const lessonSlug = window.LESSON_SLUG;

    console.log("Rohi initialized with courseSlug:", courseSlug, "lessonSlug:", lessonSlug);

    const sendBtn = document.getElementById("rohi-send");
    const input = document.getElementById("rohi-input");
    const messages = document.getElementById("rohi-messages");
    const toggle = document.getElementById("rohi-toggle");
    const chat = document.getElementById("rohi-chat");

    const scrollToBottom = () => {
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    };

    // Toggle Chat
    if (toggle && chat) {
        toggle.addEventListener("click", () => {
            console.log("Rohi Toggle Clicked");
            chat.classList.toggle("show");
            if (chat.classList.contains("show")) {
                toggle.innerHTML = "✕";
                toggle.classList.add("active");
                scrollToBottom();
                if (input) input.focus();
            } else {
                toggle.innerHTML = "🤖";
                toggle.classList.remove("active");
            }
        });
    }

    // New Chat handler
    const newChatBtn = document.getElementById("rohi-new-chat");
    if (newChatBtn) {
        newChatBtn.addEventListener("click", async () => {
            console.log("Rohi New Chat Clicked");
            const welcomeHtml = `
                <div class="rohi-ai">
                    Hi 👋 I'm Rohi. Ask me anything about AI, Python, or prompting.
                </div>
            `;
            if (messages) messages.innerHTML = welcomeHtml;
            if (input) {
                input.value = "";
                input.focus();
            }
            try {
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
                await fetch("/api/rohi-chat/clear", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    }
                });
            } catch (err) {
                console.error("Error clearing conversation history:", err);
            }
        });
    }

    // Enter Key Send Handler
    if (input && sendBtn) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendBtn.click();
            }
        });
    }

    // Send Message
    if (sendBtn && input && messages) {
        sendBtn.addEventListener("click", async () => {
            const message = input.value.trim();
            if (!message) return;

            // Render User Message
            messages.innerHTML += `
                <div class="rohi-user">
                    ${escapeHtml(message)}
                </div>
            `;
            input.value = "";
            scrollToBottom();

            // Render Typing Indicator
            const typingHtml = `
                <div class="rohi-ai typing-indicator" id="rohi-typing">
                    <span></span><span></span><span></span>
                </div>
            `;
            messages.innerHTML += typingHtml;
            scrollToBottom();

            try {
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
                
                const res = await fetch("/api/rohi-chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({
                        message: message,
                        course_slug: courseSlug,
                        lesson_slug: lessonSlug
                    })
                });

                // Remove Typing Indicator
                const typingIndicator = document.getElementById("rohi-typing");
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                const contentType = res.headers.get("content-type");
                let data = null;
                if (contentType && contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const errorText = await res.text();
                    throw new Error(`Server returned non-JSON response (status ${res.status}): ${errorText.substring(0, 200)}`);
                }

                // Handle Rate Limits / Guest Limits
                if (data.limit_reached) {
                    if (data.message && data.message.includes("limit of 20 messages")) {
                        messages.innerHTML += `
                            <div class="rohi-ai error-msg">
                                ${data.message}
                            </div>
                        `;
                        scrollToBottom();
                        return;
                    }
                    const limitModal = document.getElementById("rohi-limit-modal");
                    if (limitModal) {
                        limitModal.style.display = "flex";
                    }
                    return;
                }

                // Handle Custom Rate Limiter Errors (429)
                if (data.success === false && data.message) {
                    messages.innerHTML += `
                        <div class="rohi-ai error-msg">
                            ${data.message}
                        </div>
                    `;
                    scrollToBottom();
                    return;
                }

                // Render AI Reply (Parsed with Marked if available)
                let parsedReply = "";
                if (window.marked && typeof window.marked.parse === 'function') {
                    parsedReply = window.marked.parse(data.reply);
                } else {
                    parsedReply = escapeHtml(data.reply).replace(/\n/g, '<br>');
                }

                messages.innerHTML += `
                    <div class="rohi-ai">
                        ${parsedReply}
                    </div>
                `;
                scrollToBottom();

            } catch (err) {
                console.error("Rohi Error:", err);
                const typingIndicator = document.getElementById("rohi-typing");
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                messages.innerHTML += `
                    <div class="rohi-ai error-msg">
                        Sorry, I encountered an error. Please try again.
                    </div>
                `;
                scrollToBottom();
            }
        });
    }

    // Helper function to escape HTML
    function escapeHtml(text) {
        if (!text) return "";
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
});