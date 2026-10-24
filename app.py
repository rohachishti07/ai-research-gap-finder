import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, jsonify, redirect
from google import genai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Change the model in .env if Google retires it or you hit its daily quota
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

PAYPAL_BASE = "https://api-m.sandbox.paypal.com"  # sandbox only (fake money)
CLIENT_ID = os.environ["PAYPAL_CLIENT_ID"]
SECRET = os.environ["PAYPAL_SECRET"]

FREE_LIMIT, PREMIUM_LIMIT = 3, 10
PREMIUM_PRICE = "5.00"
MAX_TOPIC_LENGTH = 200


def paypal_token():
    r = requests.post(f"{PAYPAL_BASE}/v1/oauth2/token",
                      auth=(CLIENT_ID, SECRET),
                      data={"grant_type": "client_credentials"},
                      timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def parse_sections(text):
    keys = {
        "RESEARCH GAPS": "research_gaps",
        "THESIS TOPICS": "thesis_topics",
        "FUTURE TRENDS": "future_trends",
        "RESEARCH QUESTIONS": "research_questions",
    }
    sections = {v: [] for v in keys.values()}
    current = None
    for line in text.splitlines():
        line = line.replace("*", "").replace("#", "").strip()
        if not line:
            continue
        heading = line.rstrip(":").strip().upper()
        if heading in keys:
            current = keys[heading]
        elif current:
            sections[current].append(line.lstrip("-• ").strip())
    return sections


@app.route("/", methods=["GET", "POST"])
def home():
    topic, result, error = "", "", ""
    used = session.get("used", 0)
    limit = PREMIUM_LIMIT if session.get("premium") else FREE_LIMIT

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()[:MAX_TOPIC_LENGTH]
        if not topic:
            error = "Please enter a research topic."
        elif used >= limit:
            error = "Limit reached. Upgrade to premium for more researches."
        else:
            prompt = f"""Topic: {topic}
Provide exactly these sections:
RESEARCH GAPS:
- 3 items
THESIS TOPICS:
- 3 items
FUTURE TRENDS:
- 3 items
RESEARCH QUESTIONS:
- 3 items
Keep each item short. Do not use markdown."""
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL, contents=prompt)
                result = response.text
                session["used"] = used = used + 1
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    error = "The AI service is busy right now. Please try again in a few minutes."
                else:
                    error = "Something went wrong generating results. Please try again."
                print("GEMINI ERROR:", e)

    sections = parse_sections(result)
    return render_template("index.html", topic=topic, result=result,
                           error=error, used=used, limit=limit,
                           premium=session.get("premium", False),
                           paypal_client_id=CLIENT_ID, **sections)


@app.route("/create-order", methods=["POST"])
def create_order():
    try:
        r = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders",
                          headers={"Authorization": f"Bearer {paypal_token()}"},
                          json={"intent": "CAPTURE",
                                "purchase_units": [{"amount": {
                                    "currency_code": "USD",
                                    "value": PREMIUM_PRICE}}]},
                          timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        print("PAYPAL CREATE ERROR:", e)
        return jsonify({"error": "Could not create the PayPal order."}), 500


@app.route("/capture-order/<order_id>", methods=["POST"])
def capture_order(order_id):
    try:
        r = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture",
                          headers={"Authorization": f"Bearer {paypal_token()}",
                                   "Content-Type": "application/json"},
                          timeout=15)
        data = r.json()

        # Only unlock premium if PayPal confirms the right amount was paid
        paid = (data["purchase_units"][0]["payments"]["captures"][0]["amount"]
                if data.get("status") == "COMPLETED" else None)
        if paid and paid["value"] == PREMIUM_PRICE and paid["currency_code"] == "USD":
            session["premium"] = True
            session["used"] = 0
        return jsonify(data), r.status_code
    except Exception as e:
        print("PAYPAL CAPTURE ERROR:", e)
        return jsonify({"error": "Could not capture the PayPal payment."}), 500


# Testing shortcut: only active when ENABLE_RESET=1 is set in .env
if os.environ.get("ENABLE_RESET") == "1":
    @app.route("/reset")
    def reset():
        session.clear()
        return redirect("/")


if __name__ == "__main__":
    # Debug mode lets anyone run code through the error page, so keep it off by default
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")