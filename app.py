from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return '''
        <h1>Spotify Artist Recommendation</h1>
        <a href="/login">Login with Spotify</a>
    '''

@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope='user-library-read user-top-read'
    )
    
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope='user-library-read user-top-read'
    )
    
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    
    return redirect('/get_data')

@app.route('/get_data')
def get_data():
    if 'token_info' not in session:
        return redirect('/login')
    
    token_info = session['token_info']
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # Get user's top artists
    top_artists = sp.current_user_top_artists(limit=20, time_range='medium_term')
    
    # For now, just display the artist names
    artist_names = [artist['name'] for artist in top_artists['items']]
    return '<br>'.join(artist_names)

if __name__ == '__main__':
    app.run(debug=True) 