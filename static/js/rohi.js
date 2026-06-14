console.log("Rohi JS Loaded");

console.log("Course:", window.COURSE_SLUG);
console.log("Lesson:", window.LESSON_SLUG);
document.addEventListener("DOMContentLoaded", () => {

const courseSlug = window.COURSE_SLUG;
const lessonSlug = window.LESSON_SLUG;

console.log(courseSlug);
console.log(lessonSlug);

    const sendBtn = document.getElementById("rohi-send");
    const input = document.getElementById("rohi-input");
    const messages = document.getElementById("rohi-messages");

    const toggle = document.getElementById("rohi-toggle");
    const chat = document.getElementById("rohi-chat");

    console.log("toggle:", toggle);
    console.log("chat:", chat);

    // Toggle Chat
    if (toggle && chat) {
        toggle.addEventListener("click", () => {
            console.log("Rohi Toggle Clicked");
            chat.classList.toggle("show");
            if (chat.classList.contains("show")) {
                toggle.innerHTML = "✕";
                toggle.classList.add("active");
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
            messages.innerHTML = welcomeHtml;
            input.value = "";
            try {
                await fetch("/api/rohi-chat/clear", {
                    method: "POST"
                });
            } catch (err) {
                console.error("Error clearing conversation history:", err);
            }
        });
    }

    // Send Message
    if (sendBtn) {

        sendBtn.addEventListener("click", async () => {

            const message = input.value.trim();

            if (!message) return;

            messages.innerHTML += `
                <div class="rohi-user">
                    ${message}
                </div>
            `;

            input.value = "";

            try {

                const res = await fetch(
                    "/api/rohi-chat",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
    message: message,
    course_slug: courseSlug,
    lesson_slug: lessonSlug
})
                    }
                );

                const data = await res.json();

                if (data.limit_reached) {

    if (data.limit_reached) {

    document
        .getElementById("rohi-limit-modal")
        .style.display = "flex";

    return;
}
    if (goToSignup) {
        window.location.href = "/register";
    } else {
        window.location.href = "/login";
    }

    return;
}
                
                
                messages.innerHTML += `
                    <div class="rohi-ai">
                        ${data.reply}
                    </div>
                `;


                messages.scrollTop =
                    messages.scrollHeight;

            } catch (err) {

                console.error("Rohi Error:", err);

                messages.innerHTML += `
                    <div class="rohi-ai">
                        Sorry, I encountered an error.
                    </div>
                `;
            }

        });

    }

});