import requests
import time
import json
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = str(os.environ["CHAT_ID"])

PAIR = "MXBTC"
CHECK_INTERVAL = 30

STATE_FILE = "state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "mode": None,
            "reference": 0,
            "percent": 1.5,
            "offset": None
        }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

def get_price():
    r = requests.get(
        "https://api.mexc.com/api/v3/ticker/price",
        params={"symbol": PAIR}
    )
    return float(r.json()["price"])

def get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    if offset:
        r = requests.get(url, params={"offset": offset})
    else:
        r = requests.get(url)

    return r.json()["result"]

send("🤖 MX/BTC signal bot spuštěn")

while True:
    try:
        updates = get_updates(state["offset"])

        for u in updates:

            state["offset"] = u["update_id"] + 1

            if "message" not in u:
                continue

            text = u["message"]["text"].strip()

            if text == "/mx":
                state["mode"] = "MX"
                state["reference"] = get_price()

                send(
                    f"✅ Držíš MX\n"
                    f"Referenční kurz:\n"
                    f"{state['reference']}"
                )

            elif text == "/btc":
                state["mode"] = "BTC"
                state["reference"] = get_price()

                send(
                    f"✅ Držíš BTC\n"
                    f"Referenční kurz:\n"
                    f"{state['reference']}"
                )

            elif text == "/status":

                current = get_price()

                if state["reference"] != 0:
                    diff = (
                        (current - state["reference"])
                        / state["reference"]
                    ) * 100
                else:
                    diff = 0

                send(
                    f"Stav: {state['mode']}\n"
                    f"Reference: {state['reference']}\n"
                    f"Aktuálně: {current}\n"
                    f"Změna: {diff:.2f}%\n"
                    f"Limit: {state['percent']}%"
                )

            elif text.startswith("/percent"):

                try:
                    p = float(text.split()[1])
                    state["percent"] = p
                    send(f"✅ Nastaveno {p}%")
                except:
                    send(
                        "Použití:\n"
                        "/percent 1.5"
                    )

            elif text == "/help":

                send(
                    "/mx\n"
                    "/btc\n"
                    "/status\n"
                    "/percent X"
                )

            save_state(state)

        if state["mode"]:

            current = get_price()

            diff = (
                (current - state["reference"])
                / state["reference"]
            ) * 100

            limit = state["percent"]

            if state["mode"] == "MX" and diff >= limit:

                send(
                    f"📈 MX posílil o "
                    f"{diff:.2f}%\n\n"
                    f"Doporučení:\n"
                    f"MX ➜ BTC"
                )

                state["reference"] = current
                save_state(state)

            elif state["mode"] == "BTC" and diff <= -limit:

                send(
                    f"📉 BTC posílil o "
                    f"{abs(diff):.2f}%\n\n"
                    f"Doporučení:\n"
                    f"BTC ➜ MX"
                )

                state["reference"] = current
                save_state(state)

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(e)
        time.sleep(60)
