# 🛠️ Day 4 — Give Your Agent Tools

### AI Agent Course — RohithBuilds

Connect your AI agent to external tools so it can search the live web and solve math calculations.

## Step 1 — Create the Tool-Using Agent

Run the following command in your terminal to create and open a new file named `tools_agent.py` inside VS Code:

```cmd
code tools_agent.py
```

Paste the following codebase inside your new file:

```python
import os
import json
from groq import Groq
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Step A: Define the Python functions that represent our Tools ---

def search_web(query):
    """Search the web using DuckDuckGo and return a JSON list of the top 3 results."""
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=3)]
        return json.dumps(results)

def calculate(expression):
    """Evaluate basic mathematical calculations safely in Python."""
    try:
        # Sanitize input: allow only basic numbers and operators
        allowed = "0123456789+-*/(). "
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Invalid characters in expression"
    except Exception as e:
        return f"Error: {e}"

# --- Step B: Build the router prompt using a classification style to bypass native tool calling ---
router_prompt = """
You are a classifier. Your job is to classify the user's input.
Choose one of the three options below:

1. If the question requires a math calculation, reply exactly in this format:
RUN_CALCULATION: <mathematical expression here>
Example: RUN_CALCULATION: 125 * 45

2. If the question requires real-time information or news, reply exactly in this format:
RUN_SEARCH: <search query here>
Example: RUN_SEARCH: current AI news

3. If it is a normal question that you can answer directly, reply exactly in this format:
ANSWER: <your response here>

Respond ONLY in one of the formats above. Do not output code or JSON.
"""

# --- Step C: Main Agent Orchestration function ---

def run_agent(user_input):
    messages = [
        {"role": "system", "content": router_prompt},
        {"role": "user", "content": user_input}
    ]
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.0
    )
    decision = response.choices[0].message.content.strip()
    print(f"Decision: {decision}")
    
    if decision.startswith("RUN_SEARCH:"):
        query = decision[11:].strip()
        print(f"Executing web search for: {query}")
        tool_result = search_web(query)
        
        synthesis_messages = [
            {"role": "system", "content": "You are a helpful assistant. Synthesize the search result into a clear, natural answer for the user."},
            {"role": "user", "content": f"User asked: {user_input}\nTool Result: {tool_result}"}
        ]
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=synthesis_messages
        )
        return final_response.choices[0].message.content

    elif decision.startswith("RUN_CALCULATION:"):
        expression = decision[16:].strip()
        print(f"Executing calculation for: {expression}")
        tool_result = calculate(expression)
        
        synthesis_messages = [
            {"role": "system", "content": "You are a helpful assistant. Synthesize the calculation result into a clear, natural answer for the user."},
            {"role": "user", "content": f"User asked: {user_input}\nTool Result: {tool_result}"}
        ]
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=synthesis_messages
        )
        return final_response.choices[0].message.content

    else:
        if decision.startswith("ANSWER:"):
            return decision[7:].strip()
        return decision

# --- Step D: Test Runs ---
print("--- Test Math Tool ---")
print(run_agent("What is 125 * 45?"))
print("\n" + "="*40 + "\n")
print("--- Test Search Tool ---")
print(run_agent("Who won the latest cricket match or what is the current AI news?"))
```

Run the file:
```cmd
python tools_agent.py
```