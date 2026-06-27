# 🤖 Day 3 — Give Your Agent Memory

### AI Agent Course — RohithBuilds

Today we will build a persistent conversation loop that saves memory to a JSON file.

## Step 1 — Create Memory Chat Script

Run the following command in your terminal to create and open a new file named `memory_agent.py` inside VS Code:

```cmd
code memory_agent.py
```

Paste the following code inside your new file:

```python
import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load env variables and initialize client
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define a JSON file name where our chat logs will be saved/loaded
MEMORY_FILE = "memory.json"

# Step A: Load previous chat history if the file exists, otherwise start with an empty memory list
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
        print(f"Loaded {len(memory)} messages from history.")
else:
    memory = []

# Step B: Set up the system prompt to guide the AI's role, rules, and personality
system_prompt = {
    "role": "system", 
    "content": "You are a helpful AI assistant named Rohi. You are friendly, concise, and always answer clearly."
}

print("🤖 Chat agent Rohi is ready! Type 'exit' to quit.\n")

# Step C: Start a continuous loop to chat interactively in the terminal
while True:
    # 1. Get input query from the user
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        # 2. Save the memory list to the JSON file before exiting
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
        print("Chat history saved to file. Goodbye!")
        break
        
    # 3. Add the user's message to the memory list
    memory.append({"role": "user", "content": user_input})
    
    # 4. Prepend the system instructions so the model remembers its persona and rules on every call
    messages = [system_prompt] + memory
    
    try:
        # 5. Send the entire conversation history (context) to the API
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages
        )
        reply = response.choices[0].message.content
        print(f"\nRohi: {reply}\n")
        
        # 6. Append the model's reply to the memory list so it remembers it in the next turn
        memory.append({"role": "assistant", "content": reply})
    except Exception as e:
        print("Error during chat completion:", e)
```

Run your memory script:
```cmd
python memory_agent.py
```
Exit the program and check that `memory.json` has been created with your chat logs.