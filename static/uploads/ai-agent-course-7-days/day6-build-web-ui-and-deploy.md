# 🌐 Day 6 — Build a Web UI

### AI Agent Course — RohithBuilds

Wrap your Python backend Research Agent in a Flask web application to run research visually in a browser.

## Step 1 — Create app.py

Run the following command in your terminal to create and open a new file named `app.py` inside VS Code:

```cmd
code app.py
```

Paste the Flask backend server code inside your new file:

```python
import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

# Initialize Flask web server
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Web search tool logic
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            # Combine title and body into bullet points for the LLM
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception:
        return "Could not perform web search."

# Step A: Define homepage route serving the index.html GUI page
@app.route("/")
def index():
    return render_template("index.html")

# Step B: Define API route endpoint which receives AJAX requests to run research
@app.route("/research", methods=["POST"])
def research():
    data = request.json or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # 1. Fetch live web sources
    search_data = search_web(topic)
    
    # 2. Call the AI model to compile a markdown report
    prompt = f"Write a professional markdown research report on: '{topic}' using this source data:\n{search_data}"
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        report = response.choices[0].message.content
        # Return generated report as JSON response
        return jsonify({"report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Step C: Start local server when script is executed
if __name__ == "__main__":
    app.run(debug=True)
```

## Step 2 — Create the HTML Template

Run the following commands in your terminal to create the `templates` directory and open the new template HTML file inside VS Code:

```cmd
mkdir templates
code templates/index.html
```

Paste the HTML interface structure below inside your new file:

```html
&lt;!DOCTYPE html&gt;
&lt;html lang="en"&gt;
&lt;head&gt;
    &lt;meta charset="UTF-8"&gt;
    &lt;title&gt;AI Research Agent Dashboard&lt;/title&gt;
    &lt;link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/dark.css"&gt;
&lt;/head&gt;
&lt;body&gt;
    &lt;h1&gt;🔬 AI Research Agent&lt;/h1&gt;
    &lt;p&gt;Enter any topic below to run automated web research and write a structured report.&lt;/p&gt;
    
    &lt;input type="text" id="topic" placeholder="e.g., Quantum Computing or AI Agents" style="width: 100%;"&gt;
    &lt;button onclick="startResearch()" style="margin-top: 10px;"&gt;Conduct Research&lt;/button&gt;
    
    &lt;div id="loader" style="display: none; margin-top: 20px;"&gt;🕵️‍♂️ Researching the web and writing report... Please wait.&lt;/div&gt;
    &lt;pre id="output" style="white-space: pre-wrap; margin-top: 20px; background: #222; padding: 15px; border-radius: 5px; display: none;"&gt;&lt;/pre&gt;

    &lt;script&gt;
        async function startResearch() {
            const topic = document.getElementById("topic").value.trim();
            if (!topic) return alert("Please enter a topic");
            
            // Show loader indicator, hide previous output
            document.getElementById("loader").style.display = "block";
            document.getElementById("output").style.display = "none";
            
            try {
                // Post JSON payload to the Flask route endpoint
                const res = await fetch("/research", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic: topic })
                });
                const data = await res.json();
                document.getElementById("loader").style.display = "none";
                
                if (data.report) {
                    // Populate and display result report pre-element block
                    document.getElementById("output").innerText = data.report;
                    document.getElementById("output").style.display = "block";
                } else {
                    alert("Error: " + (data.error || "failed"));
                }
            } catch(e) {
                alert("Request failed: " + e);
                document.getElementById("loader").style.display = "none";
            }
        }
    &lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;
```

Run the application locally:
```cmd
python app.py
```
Open `http://localhost:5000` in your web browser.