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

# --- Step B: Build the router prompt instructing the LLM on tool selection ---

router_prompt = """
You are an assistant that has access to tools. 
You must decide whether to use a tool to answer the user's question.
Available tools:
- search_web(query): Use when asked about recent news, current events, or real-time information.
- calculate(expression): Use for math calculations.

Respond ONLY in one of the following formats:
- If you need a tool: TOOL: name(arguments)
- If you don't need a tool: ANSWER: your direct response
"""

# --- Step C: Main Agent Orchestration function ---

def run_agent(user_input):
    # Prepare payload for the tool decision step
    messages = [
        {"role": "system", "content": router_prompt},
        {"role": "user", "content": user_input}
    ]
    
    # Query the LLM to get a routing decision (TOOL or ANSWER)
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages
    )
    decision = response.choices[0].message.content.strip()
    print(f"Decision: {decision}")
    
    # Check if the LLM decided to call a tool
    if decision.startswith("TOOL:"):
        # Extract the tool signature (e.g. "TOOL: calculate(125 * 45)" -> tool_name="calculate", args="125 * 45")
        tool_call = decision[5:].strip()
        tool_name = tool_call.split("(")[0]
        args = tool_call.split("(")[1].rstrip(")")
        
        # Execute the corresponding Python function
        if tool_name == "search_web":
            print(f"Executing web search for: {args}")
            tool_result = search_web(args)
        elif tool_name == "calculate":
            print(f"Executing calculation for: {args}")
            tool_result = calculate(args)
        else:
            tool_result = "Unknown tool"
            
        # Synthesize final response: Feed the raw tool result back to the LLM to format a conversational reply
        synthesis_messages = [
            {"role": "system", "content": "You are a helpful assistant. Synthesize the tool result into a clear, natural answer for the user."},
            {"role": "user", "content": f"User asked: {user_input}\nTool Result: {tool_result}"}
        ]
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=synthesis_messages
        )
        return final_response.choices[0].message.content
    else:
        # If no tool is needed, return the assistant's direct text answer
        return decision[7:].strip()

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