import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_everynoise_genres():
    """
    Scrape all music genres from Every Noise at Once website
    Returns:
        list: A list of all unique genres
    """
    url = "https://everynoise.com/everynoise1d.html"
    
    try:
        # Send GET request to the website
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all genre links - they are in <a> tags with title containing "Re-sort"
        genre_links = soup.find_all('a', title=lambda x: x and 'Re-sort' in x)
        
        # Extract genre names and clean them
        genres = []
        for link in genre_links:
            genre = link.text.strip()
            if genre:  # Only add non-empty genres
                genres.append(genre)
        
        return sorted(list(set(genres)))  # Remove duplicates and sort
        
    except requests.RequestException as e:
        print(f"Error fetching the website: {str(e)}")
        return []
    except Exception as e:
        print(f"Error parsing the website: {str(e)}")
        return []

def save_genres_to_file(genres, filename='data/all_spotify_genres.json'):
    """
    Save the list of genres to a JSON file
    Args:
        genres (list): List of genre names
        filename (str): Path to save the JSON file
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'total_genres': len(genres),
            'genres': genres,
            'source': 'Every Noise at Once (https://everynoise.com/everynoise1d.html)'
        }, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    print("Scraping genres from Every Noise at Once...")
    genres = scrape_everynoise_genres()
    
    if genres:
        print(f"\nFound {len(genres)} unique genres!")
        save_genres_to_file(genres)
        print(f"Genres saved to data/all_spotify_genres.json")
        print("\nExample genres (first 10):")
        print(", ".join(genres[:10]))
    else:
        print("No genres were found. Please check your internet connection.") 