# 🔍 Day 5 — Build the Research Agent

### AI Agent Course — RohithBuilds

Put memory and tools together to create a fully autonomous AI Research Agent that builds markdown reports.

## Step 1 — Create Research Agent Script

Run the following command in your terminal to create and open a new file named `research_agent.py` inside VS Code:

```cmd
code research_agent.py
```

Paste the complete workflow inside your new file:

```python
import os
import json
from groq import Groq
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Step A: Define search tool to collect real-time web source data
def search_web(topic):
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(topic, max_results=4)]
        return json.dumps(results)

# Step B: Define write report tool using prompt structuring instructions
def write_report(topic, research_data):
    prompt = f"""
    Write a professional, comprehensive markdown research report on the topic: "{topic}".
    Use this raw research data:
    {research_data}

    Structure the report with these sections:
    1. Overview
    2. Key Facts & Findings
    3. Latest Developments
    4. Conclusion
    """
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Step C: The autonomous research workflow orchestration
def conduct_research(topic):
    print(f"🔍 Starting research on: '{topic}'...")
    
    # 1. Search the web
    raw_results = search_web(topic)
    
    # 2. Compile raw data into structured markdown report
    print("✍️ Synthesizing findings and writing report...")
    report = write_report(topic, raw_results)
    
    # 3. Save report to a local markdown file named after the topic
    filename = f"{topic.lower().replace(' ', '_')}_report.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Research report successfully saved as: {filename}")
    return report

# Get research topic input from user and run
topic_query = input("Enter a research topic: ")
conduct_research(topic_query)
```

Run the file and type a research topic:
```cmd
python research_agent.py
```
Check your directory for the generated markdown report.