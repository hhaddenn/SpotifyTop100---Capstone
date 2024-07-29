import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth

billboard_url = "https://www.billboard.com/charts/hot-100"

# Load environment variables from .env file
load_dotenv()

# Get the Spotify credentials from the environment variables
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Get the date from the user
year = input("Which year do you want to travel to?\n")
month = input("Which month do you want to travel to?\n")
day = input("Which day do you want to travel to?\n")
if len(month) == 1:
    month = f"0{month}"
if len(day) == 1:
    day = f"0{day}"
date = f"/{year}-{month}-{day}"

# Request the page
response = requests.get(f"{billboard_url}{date}")
response.raise_for_status()
billboard_page = response.text
soup = BeautifulSoup(billboard_page, "html.parser")

# Get the song names and artists
chart_items = soup.find_all("li", class_="o-chart-results-list__item")
songs_and_artists = []

for item in chart_items:
    song = item.find("h3", class_="c-title")
    artist = item.find("span", class_="c-label")
    if song and artist:
        song_name = song.get_text(strip=True)
        artist_name = artist.get_text(strip=True)

        # Remove featured artists and other conjunctions
        for keyword in ["Featuring", "featuring", "Feat.", "feat.", "With", "with", "&", "And", "and", "X", "x", "Vs", "vs", "Vs.", "vs."]:
            if keyword in artist_name:
                artist_name = artist_name.split(keyword)[0].strip()
                break

        songs_and_artists.append((song_name, artist_name))

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope="playlist-modify-private",
                                               show_dialog=True))

# Function to search for a song on Spotify
def search_spotify_song(song_name, artist_name):
    query = f"track:{song_name} artist:{artist_name}"
    result = sp.search(q=query, type="track", limit=1)
    if result['tracks']['items']:
        return result['tracks']['items'][0]['uri']
    # Try searching by song name only if artist search fails
    query = f"track:{song_name}"
    result = sp.search(q=query, type="track", limit=1)
    if result['tracks']['items']:
        return result['tracks']['items'][0]['uri']
    return None

# Search for the songs on Spotify
song_uris = []
for song, artist in songs_and_artists:
    uri = search_spotify_song(song, artist)
    if uri:
        song_uris.append(uri)
    else:
        print(f"{song} by {artist} doesn't exist in Spotify. Skipped.")

# Create a new playlist
playlist_name = f"{date[1:]} Billboard 100"
playlist = sp.user_playlist_create(user=sp.me()['id'], name=playlist_name, public=False)

# Add the songs to the playlist
sp.playlist_add_items(playlist['id'], song_uris)
print(f"Playlist {playlist_name} created successfully.")