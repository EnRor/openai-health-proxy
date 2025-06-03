from flask import Flask, request, jsonify
import openai
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализация планировщика
scheduler = BackgroundScheduler()
scheduler.start()
print("[INFO] Планировщик APScheduler запущен")

@app.route("/", methods=["POST"])
def handle_request():
    print("[OPENAI DEBUG] Получен POST-запрос на /")
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

@app.route("/", methods=["GET"])
def health_check():
    return "🤖 HealthMate AI is live", 200

def send_reminder(user_id, message):
    print(f"[INFO] Отправка напоминания пользователю {user_id}: {message}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message
    }
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print(f"[SUCCESS] Напоминание успешно отправлено пользователю {user_id}")
        else:
            print(f"[ERROR] Ошибка отправки напоминания: статус {resp.status_code}, ответ: {resp.text}")
    except Exception as e:
        print(f"[EXCEPTION] Исключение при отправке напоминания: {e}")

@app.route("/schedule_reminder", methods=["POST"])
def schedule_reminder():
    data = request.json
    try:
        delay_minutes = int(data.get("delay_minutes", "60"))
    except (ValueError, TypeError):
        return jsonify({"error": "delay_minutes должно быть числом"}), 400

    user_id = data.get("user_id")
    message = data.get("message", "Напоминание от HealthMate AI!")

    if not user_id:
        return jsonify({"error": "user_id обязателен"}), 400

    run_time = datetime.now() + timedelta(minutes=delay_minutes)
    job_id = f"reminder_{user_id}_{datetime.now().timestamp()}"

    scheduler.add_job(
        func=send_reminder,
        trigger="date",
        run_date=run_time,
        args=[user_id, message],
        id=job_id,
        replace_existing=True
    )

    print(f"[SCHEDULER] Задача {job_id} добавлена: user_id={user_id}, задержка={delay_minutes} минут, сообщение='{message}'")

    return jsonify({"status": "success", "message": "Напоминание запланировано"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
