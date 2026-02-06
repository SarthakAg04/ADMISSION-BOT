from flask import Flask, render_template, request, jsonify
import requests
import json
import re

app = Flask(__name__)

# Load admission data
with open("admissions_data.txt", "r") as f:
    ADMISSION_CONTEXT = f.read()

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

# Quick response patterns for common questions
QUICK_RESPONSES = {
    "gpa": "GPA requirement: Minimum 6.0/10 CGPA",
    "gre": "GRE is required for most postgraduate programs",
    "ielts": "IELTS/TOEFL required for international students",
    "application fee": "Please check the university website for exact fee amount",
    "documents": "Required: Transcripts, ID proof, SOP, Resume, Test scores",
    "eligibility": "Undergrad: 60% in 12th grade. Postgrad: Bachelor's + CGPA 6.0/10",
    "application process": "1) Choose program 2) Check eligibility 3) Prepare docs 4) Submit 5) Track status",
    "sor": "Statement of Purpose (SOP) - Write about your goals and why this program",
    "lor": "Letters of Recommendation - Typically 2-3 letters from professors/mentors",
    "deadline": "Please check your program's specific deadline on the university website"
}

def get_quick_answer(question):
    """Check for quick response patterns"""
    q_lower = question.lower()
    for keyword, response in QUICK_RESPONSES.items():
        if keyword in q_lower:
            return response
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_question = request.json.get("question", "").strip()
        if not user_question:
            return jsonify({"error": "Question cannot be empty"}), 400

        # Try quick response first for faster replies
        quick_answer = get_quick_answer(user_question)
        if quick_answer:
            return jsonify({"answer": quick_answer})

        # Use AI for complex questions with instructions for short answers
        prompt = f"""You are a university admissions assistant. Answer BRIEFLY and CONCISELY (1-3 sentences max).

Admission Info:
{ADMISSION_CONTEXT}

Question: {user_question}

Answer briefly:"""

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3  # Lower temperature for more focused answers
            },
            timeout=20  # Reduced timeout for faster responses
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from AI model"}), 500

        answer = response.json().get("response", "No response generated").strip()
        
        return jsonify({"answer": answer})
    except requests.exceptions.RequestException:
        return jsonify({"error": "Cannot connect to AI model. Is Ollama running?"}), 503
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/suggestions", methods=["GET"])
def get_suggestions():
    """Return common questions for quick access"""
    suggestions = [
        {"text": "GPA Requirements", "emoji": "📊"},
        {"text": "What is GRE?", "emoji": "📝"},
        {"text": "IELTS/TOEFL", "emoji": "🌍"},
        {"text": "Required Documents", "emoji": "📄"},
        {"text": "Application Process", "emoji": "📋"},
        {"text": "What is SOP?", "emoji": "✍️"},
        {"text": "Eligibility", "emoji": "✅"},
        {"text": "Application Fee", "emoji": "💰"}
    ]
    return jsonify({"suggestions": suggestions})

if __name__ == "__main__":
    app.run(debug=True)
