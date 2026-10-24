# AI Research Gap Finder

An AI research assistant that takes a topic and returns research gaps, thesis topic ideas, future trends, and research questions. Users get **3 free researches** and can upgrade to **10 researches** with a one-time **$5 PayPal payment** (PayPal sandbox).

Built for the **Build What's Next with PayPal and AI** hackathon.

## Features

- Enter any research topic and get four sections of ideas: research gaps, thesis topics, future trends, and research questions
- Free tier with 3 researches, with a live usage counter
- Premium upgrade (10 researches) paid through PayPal Checkout
- Payment is verified on the server (status and amount) before premium unlocks

## How it uses AI and PayPal

**AI: Google Gemini** (via the `google-genai` Python SDK). The app sends the user's topic with a structured prompt, and Gemini returns the four sections. The server parses them into separate cards.

**PayPal: Orders v2 API and the PayPal JavaScript SDK (sandbox).**
1. The PayPal button on the page calls `/create-order`, where the server creates a $5.00 USD order.
2. The user approves the payment in the PayPal popup.
3. The page calls `/capture-order/<id>`, where the server captures the payment, checks that it completed for exactly $5.00 USD, and only then unlocks premium.

Credentials stay on the server, and all payments use the PayPal **sandbox** (no real money).

## Tech stack

Python, Flask, Google Gemini API, PayPal REST API and JS SDK, HTML/CSS

## Setup

You need Python 3.10 or newer.

### 1. Clone the repo
```
git clone https://github.com/rohachishti07/ai-research-gap-finder
cd ai-research-gap-finder
```

### 2. Create a virtual environment and install packages

Windows (Command Prompt):
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Mac/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 3. Get your keys

**Gemini API key (free):** go to https://aistudio.google.com, click **Get API key**, and create a key. The free tier has a daily request limit, so if you see an "AI service is busy" message, wait a while or set a different model in `GEMINI_MODEL`.

**PayPal sandbox credentials (free):**
1. Log in at https://developer.paypal.com and open **Apps & Credentials** with the **Sandbox** toggle selected.
2. Click **Create App** and copy the **Client ID** and **Secret**.
3. Go to **Testing Tools > Sandbox Accounts** and note the **Personal (buyer)** account's email and password. You will use it to pay.

### 4. Create a `.env` file

Copy `.env.example` to `.env` and fill it in:

```
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-3.5-flash
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_SECRET=your_sandbox_secret
FLASK_SECRET_KEY=any_long_random_text
```

- No quotes and no spaces around `=`.
- `GEMINI_MODEL` is optional. Set it to any model name currently available in Google AI Studio.
- `FLASK_SECRET_KEY` can be any long random string.

### 5. Run the app

```
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## How to test

1. Enter a topic (for example, "Mathematics and Artificial Intelligence") and click **Generate Ideas**. Four cards of results appear and the counter shows `1 / 3`.
2. Use up the 3 free researches. The 4th attempt shows a limit message.
3. Click the PayPal button and log in with the **sandbox Personal (buyer)** account from step 3 (not your real PayPal account).
4. Approve the payment. The page reloads showing `0 / 10 (Premium)`, and you can run more researches.

## Limitations and future work

- Usage and premium status are stored in a browser session cookie, so clearing cookies resets them. A production version would use user accounts and a database to record payments.
- Payments run in the PayPal sandbox only.
- Free-tier Gemini keys have a daily request limit.

Planned improvements: saved research history, PDF export, and user accounts.

## License

MIT License. See the `LICENSE` file.