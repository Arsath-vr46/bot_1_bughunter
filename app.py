import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

CHATBOT_TITLE = "BugHunter"
CHATBOT_PURPOSE = "Code Debugger & StackTrace Expert"
SYSTEM_PROMPT = """You are BugHunter, a specialized Code Debugger & StackTrace Expert.
Analyze stack traces, memory leaks, and syntax/logical errors across Python, C++, and JS.
- Strictly refuse any off-topic queries outside this field.
- Format all technical output and math formulas cleanly using Markdown and LaTeX ($...$ or $$...$$).
"""

@app.route("/")
def index():
    return render_template("index.html", chatbot_title=CHATBOT_TITLE, chatbot_purpose=CHATBOT_PURPOSE)

@app.route("/api/config")
def config():
    return jsonify({"title": CHATBOT_TITLE, "purpose": CHATBOT_PURPOSE})

@app.route("/api/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({"error": "GEMINI_API_KEY is not configured."}), 500
    
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    contents = []
    for item in history[-10:]:
        role = "user" if item.get("role") == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=item.get("content", ""))]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3
            )
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": f"Model Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
