
from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["POST"])
def handle_request():
    data = request.json
    user_info = data.get("user_info", "No user data provided.")

    prompt = f"""На основе следующих данных: {user_info}, составь индивидуальные рекомендации по здоровью, питанию и физической активности."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — персональный ассистент по здоровью. Учитывай привычки, физическую активность и цели пользователя."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
