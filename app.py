from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
import requests
import json

app = Flask(__name__)
app.secret_key = 'hello'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"User( {username}, {email}"

class Recommendations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recommendation = db.Column(db.String(80))


# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-modify-playback-state user-read-playback-state user-read-currently-playing"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# Client Keys
CLIENT_ID = "2f670ff76de6412799bf623c1d9fddd6"
CLIENT_SECRET = "f7146c3df1f448169dc3ab350e67c9d6"

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}





@app.route("/")
def auth():
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens

    print(request.args)

    auth_token = request.args['code']
    print("auth_token", auth_token)
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)

    print(response_data)

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # storing personal user data
    session['profile_data'] = profile_data
    session['access_token'] = access_token

    # redirecting to the home page
    return redirect('/home')

@app.route("/home")
def home():
    print(session['profile_data'])
    print(session['access_token'])
    return render_template("home.html")

@app.route("/profile/<id>")
def profile(id):
    profile_data = session['profile_data']
    return render_template("profile.html", pd=profile_data)

@app.route("/rec/<id>")
def rec(id):
    return render_template("rec.html", rec=recommendation)

if __name__ == "__main__":
    app.run(debug=True) 