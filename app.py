from flask import Flask, render_template, redirect, request, session, url_for
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
    name = db.Column(db.String(80), nullable=False)
    uri = db.Column(db.String(120), unique=True, nullable=False)
    access_token=db.Column(db.String(120), nullable=False)

    tracks = db.relationship('Track', backref='user', lazy=True)

    def __repr__(self):
        return f"User( {self.name}, {self.uri} )"

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    artist = db.Column(db.String(40), nullable=False)
    img_url = db.Column(db.String(40), nullable=False)
    uri = db.Column(db.String(40), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Track( {self.title}, {self.artist}, {self.uri} )"


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
SCOPE = "playlist-modify-public playlist-modify-private user-modify-playback-state user-read-playback-state user-read-currently-playing user-library-modify"
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

    name = profile_data['display_name']
    uri = profile_data['uri']
    a_t = access_token

    user = User(name=name, uri=uri, access_token=a_t)

    if User.query.filter_by(name = name).first() != None and User.query.filter_by(name = name).first().name == name:
        print('User is already created')
    else:
        db.session.add(user)
        db.session.commit()
        print(f'{name} is added to the database')
    
    # redirecting to the home page
    return redirect('/home')

@app.route("/home")
def home():
    profile_data = session['profile_data']
    return render_template("home.html", pd=profile_data)

@app.route("/profile/<id>")
def profile(id):
    print(id)
    profile_data = session['profile_data']
    user = User.query.filter_by(uri = id).first()
    tracks = []
    if user != None:
        tracks = user.tracks

    if (id == profile_data['uri']):
        return render_template("profile.html", pd=profile_data, tr=tracks)
    else:
        return redirect(url_for('rec', id=id))

@app.route("/rec/<id>")
def rec(id):
    user = User.query.filter_by(uri = id).first()
    print(user)
    if user != None:
        return render_template("rec.html", name = user.name, id=id)
    
    else:
        return render_template("error.html")

@app.route("/results/<id>", methods=["GET", "POST"])
def results(id):

    if request.method == "POST":
        access_token = session['access_token']
        auth_header = {"Authorization": "Bearer {}".format(access_token)}
        track = request.form["recommendation"]
        query = track.replace(" ", "%20") + "&type=track"
        search_url = "https://api.spotify.com/v1/search?q=" + query
        search_response = requests.get(search_url, headers=auth_header)
        search_result = json.loads(search_response.text)

    
    return render_template("results.html", sr=search_result, id=id)

@app.route("/add_song/<uri>/<id>")
def add_song(uri,id):
    print(id)

    access_token = session['access_token']
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    track_url = "https://api.spotify.com/v1/tracks/" + uri[14:]
    search_response = requests.get(track_url, headers=auth_header)
    search_result = json.loads(search_response.text)

    title = search_result['name']
    artist = search_result['artists'][0]['name']
    img_url = search_result['album']['images'][1]['url']
    uri = uri[14:]

    print(title, artist, img_url, uri)




    rec_user = User.query.filter_by(uri = id).first()
    print(rec_user.id)

    track = Track(title=title, artist=artist, img_url=img_url, uri=uri, user_id=rec_user.id)

    db.session.add(track)
    db.session.commit()

    print(rec_user.tracks)


    return redirect(url_for('rec',id=id))

@app.route("/like/<uri>/<id>")
def like(uri,id):
    print(id)
    print(uri)

    access_token = session['access_token']
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    like_url = "https://api.spotify.com/v1/me/tracks?ids=" + uri
    put_like = requests.put(like_url, headers=auth_header)
    print(put_like.text)

    track = Track.query.filter_by(uri=uri).first()
    print(track)
    db.session.delete(track)
    db.session.commit()
    
    print("Song is added")


    return redirect(url_for('profile', id=id))


if __name__ == "__main__":
    app.run(debug=True) 