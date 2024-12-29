import os
import csv
import time
import pandas as pd
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def load_genres(filename='data/genres/spotify_genres.csv'):
    """
    Load validated genres from CSV file
    Returns:
        list: List of genre names
    """
    try:
        df = pd.read_csv(filename)
        return df['genre'].tolist()
    except Exception as e:
        print(f"Error loading genres from CSV: {str(e)}")
        return []

def get_top_artists_by_genre(sp, genre, limit=100):
    """
    Get top artists for a specific genre
    Args:
        sp: Spotify client
        genre: Genre name
        limit: Number of artists to fetch (max 100)
    Returns:
        list: List of dictionaries containing artist information
    """
    artists = []
    offset = 0
    
    while len(artists) < limit:
        try:
            # Search for artists of the specific genre
            results = sp.search(
                q=f'genre:"{genre}"',
                type='artist',
                limit=min(50, limit - len(artists)),  # Spotify API limit is 50 per request
                offset=offset
            )
            
            if not results['artists']['items']:
                break
                
            # Extract relevant artist information
            for artist in results['artists']['items']:
                artist_info = {
                    'artist_id': artist['id'],
                    'artist_name': artist['name'],
                    'genre': genre,
                    'popularity': artist['popularity'],
                    'followers': artist['followers']['total'],
                    'genres': ','.join(artist['genres']),
                    'spotify_url': artist['external_urls']['spotify']
                }
                artists.append(artist_info)
            
            offset += len(results['artists']['items'])
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching artists for genre '{genre}': {str(e)}")
            break
    
    # Sort by popularity and return top 'limit' artists
    return sorted(artists, key=lambda x: x['popularity'], reverse=True)[:limit]

def save_artists_to_csv(artists_data, filename='data/artists_by_genre.csv'):
    """
    Save artists data to CSV file
    Args:
        artists_data: List of dictionaries containing artist information
        filename: Output CSV file path
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(artists_data)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        print(f"Error saving artists to CSV: {str(e)}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Spotify client
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error initializing Spotify client: {str(e)}")
        return
    
    # Load genres
    print("Loading genres from CSV...")
    genres = load_genres()
    
    if not genres:
        print("No genres loaded. Please check the input file.")
        return
    
    print(f"Found {len(genres)} genres")
    
    # Collect artists for each genre
    all_artists = []
    total_genres = len(genres)
    
    for i, genre in enumerate(genres, 1):
        print(f"\nProcessing genre {i}/{total_genres}: {genre}")
        artists = get_top_artists_by_genre(sp, genre)
        print(f"Found {len(artists)} artists for genre '{genre}'")
        all_artists.extend(artists)
    
    # Save results
    if all_artists:
        print(f"\nTotal artists collected: {len(all_artists)}")
        if save_artists_to_csv(all_artists):
            print("Artists data saved to data/artists_by_genre.csv")
        else:
            print("Error saving artists data")
    else:
        print("No artists data collected")

if __name__ == '__main__':
    main() 