import os
import json
import csv
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time

def load_genres_from_json(filename='data/genres/all_spotify_genres.json'):
    """
    Load genres from the JSON file
    Returns:
        list: List of genre names
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('genres', [])
    except Exception as e:
        print(f"Error loading genres from JSON: {str(e)}")
        return []

def validate_spotify_genres(genres):
    """
    Validate genres against Spotify API by searching for tracks in each genre
    Returns:
        list: List of valid genre names
    """
    # Load environment variables
    load_dotenv()
    
    try:
        # Set up authentication with client credentials
        auth_manager = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        validated_genres = []
        total = len(genres)
        
        print(f"\nValidating {total} genres...")
        
        for i, genre in enumerate(genres, 1):
            try:
                # Search for tracks in the genre
                results = sp.search(q=f'genre:"{genre}"', type='track', limit=1)
                
                # If we get any results, consider the genre valid
                if results['tracks']['items']:
                    validated_genres.append(genre)
                    print(f"[{i}/{total}] Found valid genre: {genre}")
                else:
                    print(f"[{i}/{total}] Invalid genre: {genre}")
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error validating genre '{genre}': {str(e)}")
                continue
        
        return validated_genres
        
    except Exception as e:
        print(f"Error validating genres with Spotify API: {str(e)}")
        return []

def save_genres_to_csv(genres, filename='data/genres/spotify_genres.csv'):
    """
    Save the validated genres to a CSV file
    Args:
        genres (list): List of valid genre names
        filename (str): Path to save the CSV file
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['genre'])  # Header
            for genre in sorted(genres):  # Sort genres alphabetically
                writer.writerow([genre])
        return True
    except Exception as e:
        print(f"Error saving genres to CSV: {str(e)}")
        return False

if __name__ == '__main__':
    print("Loading genres from JSON file...")
    all_genres = load_genres_from_json()
    
    if all_genres:
        print(f"Found {len(all_genres)} genres in JSON file")
        valid_genres = validate_spotify_genres(all_genres)
        
        if valid_genres:
            print(f"\nFound {len(valid_genres)} valid Spotify genres")
            if save_genres_to_csv(valid_genres):
                print("Valid genres saved to data/genres/spotify_genres.csv")
                print("\nExample valid genres (first 10):")
                print(", ".join(sorted(valid_genres)[:10]))
            else:
                print("Error saving genres to CSV file")
        else:
            print("No valid genres found or error occurred during validation")
    else:
        print("No genres were loaded from JSON file") 