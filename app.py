from flask import Flask, request, jsonify
import openai
import os
import threading
import time
import requests  # добавлено

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # добавлено

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

@app.route("/", methods=["GET"])
def health_check():
    return "🤖 HealthMate AI is live", 200

def send_reminder_after_delay(delay_minutes, user_id, message):
    print(f"[DEBUG] Запуск фонового потока для user_id={user_id} с задержкой {delay_minutes} минут")

    print(f"[INFO] Фоновый поток запущен: напоминание через {delay_minutes} минут для пользователя {user_id}")

    time.sleep(delay_minutes * 60)

    print(f"[INFO] Время вышло. Отправка напоминания пользователю {user_id}: {message}")

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

    print(f"[INFO] Фоновый поток для пользователя {user_id} завершён")


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

    thread = threading.Thread(target=send_reminder_after_delay, args=(delay_minutes, user_id, message))
    thread.daemon = True
    thread.start()

    print(f"Запланировано напоминание для пользователя {user_id} через {delay_minutes} минут с сообщением: {message}")

    return jsonify({"status": "success", "message": "Напоминание запланировано"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
