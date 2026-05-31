import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def improve_prompt(user_prompt):

    if not client:
        return "Error: GROQ_API_KEY environment variable is not configured. Please set it in your environment or .env file."

    system_prompt = """
    You are an expert AI prompt optimizer.

    Rewrite the user's prompt into a clearer,
    more detailed, structured,
    high-performing AI prompt.

    Keep the intent same.
    Make it more specific and useful.
    """

    try:

        chat_completion = client.chat.completions.create(

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": user_prompt
                }

            ],

            model="llama-3.3-70b-versatile",
        )

        return chat_completion.choices[0].message.content

    except Exception as e:

        return f"Error: {str(e)}"

def rohi_chat(
    message,
    course_name="RohithBuilds",
    lesson_title="General Learning",
    lesson_content=""
):

    if not client:
        return "Rohi is currently unavailable."

    system_prompt = f"""
You are Rohi, the AI tutor inside RohithBuilds.

Rules:

- Keep answers SHORT.
- Maximum 80 words.
- Prefer 1-4 sentences.
- Explain simply like a mentor.
- Focus on helping students learn.
- Do not write long essays.
- Do not use large markdown blocks.
- Be friendly and encouraging.
- If the question is unrelated to learning, gently redirect.


Current Course:
{course_name}

Current Lesson:
{lesson_title}

Lesson Content:
{lesson_content}
"""

    try:

        chat_completion = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": message
                }

            ],

            temperature=0.7,
            max_tokens=200

        )

        return chat_completion.choices[0].message.content

    except Exception as e:

        return f"Rohi Error: {str(e)}"