const express = require('express');
const SpotifyWebApi = require('spotify-web-api-node');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
const port = 3000;

// Session middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

const spotifyApi = new SpotifyWebApi({
    clientId: process.env.SPOTIFY_CLIENT_ID,
    clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
    redirectUri: process.env.REDIRECT_URI
});

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/public/index.html');
});

app.get('/login', (req, res) => {
    const scopes = [
        'user-library-read',
        'user-top-read',
        'user-read-recently-played',
        'user-read-playback-state',
        'user-read-currently-playing',
        'playlist-read-private',
        'user-read-private'
    ];
    const authorizeURL = spotifyApi.createAuthorizeURL(scopes);
    res.redirect(authorizeURL);
});

app.get('/callback', async (req, res) => {
    const { code } = req.query;
    try {
        const data = await spotifyApi.authorizationCodeGrant(code);
        spotifyApi.setAccessToken(data.body['access_token']);
        spotifyApi.setRefreshToken(data.body['refresh_token']);
        
        // After successful login, collect and save data
        await collectAndSaveData();
        
        // Redirect to a success page
        res.send('Data collected successfully! You can close this window.');
        
    } catch (error) {
        console.error('Error getting tokens:', error);
        res.redirect('/#/error/invalid token');
    }
});

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function collectAndSaveData() {
    try {
        console.log('Starting data collection...');
        
        // Get all user's playlists and library data in one go
        const [
            userProfile,
            playlists,
            recentlyPlayed,
            savedTracks
        ] = await Promise.all([
            spotifyApi.getMe(),
            spotifyApi.getUserPlaylists({ limit: 50 }),
            spotifyApi.getMyRecentlyPlayedTracks({ limit: 50 }),
            spotifyApi.getMySavedTracks({ limit: 50 })
        ]);

        // Get user's top items for all time ranges in parallel
        const timeRanges = ['short_term', 'medium_term', 'long_term'];
        const topItemsPromises = timeRanges.flatMap(range => [
            spotifyApi.getMyTopArtists({ limit: 50, time_range: range }),
            spotifyApi.getMyTopTracks({ limit: 50, time_range: range })
        ]);

        const topItemsResults = await Promise.all(topItemsPromises);

        // Process all the data
        const artistData = {};
        const artistStats = new Map();

        // Process playlists to get artist frequencies
        playlists.body.items.forEach(playlist => {
            if (playlist.tracks) {
                const trackCount = playlist.tracks.total;
                playlist.tracks.items?.forEach(item => {
                    if (item?.track?.artists) {
                        item.track.artists.forEach(artist => {
                            if (!artistStats.has(artist.id)) {
                                artistStats.set(artist.id, {
                                    name: artist.name,
                                    playlistAppearances: 0,
                                    trackCount: 0,
                                    recentPlays: 0,
                                    savedTracks: 0,
                                    totalDuration: 0
                                });
                            }
                            artistStats.get(artist.id).playlistAppearances++;
                        });
                    }
                });
            }
        });

        // Process recently played tracks
        recentlyPlayed.body.items.forEach(item => {
            item.track.artists.forEach(artist => {
                if (!artistStats.has(artist.id)) {
                    artistStats.set(artist.id, {
                        name: artist.name,
                        playlistAppearances: 0,
                        trackCount: 0,
                        recentPlays: 0,
                        savedTracks: 0,
                        totalDuration: 0
                    });
                }
                const stats = artistStats.get(artist.id);
                stats.recentPlays++;
                stats.totalDuration += item.track.duration_ms;
            });
        });

        // Process saved tracks
        savedTracks.body.items.forEach(item => {
            item.track.artists.forEach(artist => {
                if (!artistStats.has(artist.id)) {
                    artistStats.set(artist.id, {
                        name: artist.name,
                        playlistAppearances: 0,
                        trackCount: 0,
                        recentPlays: 0,
                        savedTracks: 0,
                        totalDuration: 0
                    });
                }
                artistStats.get(artist.id).savedTracks++;
            });
        });

        // Process top items for each time range
        timeRanges.forEach((range, index) => {
            const artistsResponse = topItemsResults[index * 2];
            const tracksResponse = topItemsResults[index * 2 + 1];

            const artists = artistsResponse.body.items.map(artist => ({
                id: artist.id,
                name: artist.name,
                popularity: artist.popularity,
                followers: artist.followers.total,
                genres: artist.genres,
                spotify_url: artist.external_urls.spotify,
                images: artist.images,
                statistics: {
                    playlist_appearances: artistStats.get(artist.id)?.playlistAppearances || 0,
                    recent_plays: artistStats.get(artist.id)?.recentPlays || 0,
                    saved_tracks: artistStats.get(artist.id)?.savedTracks || 0,
                    total_listening_time: artistStats.get(artist.id)?.totalDuration || 0,
                    appears_in_top_tracks: tracksResponse.body.items.filter(track => 
                        track.artists.some(a => a.id === artist.id)
                    ).length
                }
            }));

            artistData[range] = {
                artists: artists,
                metadata: {
                    total_artists: artists.length,
                    collection_date: new Date().toISOString(),
                    most_common_genres: getMostCommonGenres(artists)
                }
            };
        });

        // Save the data
        const filePath = path.join(__dirname, 'data', 'data_spotify.json');
        const dataDir = path.join(__dirname, 'data');
        
        if (!fs.existsSync(dataDir)){
            fs.mkdirSync(dataDir);
        }

        fs.writeFileSync(
            filePath,
            JSON.stringify(artistData, null, 2)
        );

        console.log('\nData collection completed successfully!');
        console.log(`Data saved to: ${filePath}`);

    } catch (error) {
        console.error('Fatal error during data collection:', error);
        throw error;
    }
}

// Helper function to get most common genres
function getMostCommonGenres(artists) {
    const genreCounts = {};
    artists.forEach(artist => {
        artist.genres.forEach(genre => {
            genreCounts[genre] = (genreCounts[genre] || 0) + 1;
        });
    });
    
    return Object.entries(genreCounts)
        .sort(([,a], [,b]) => b - a)
        .reduce((obj, [key, value]) => ({
            ...obj,
            [key]: value
        }), {});
}

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
}); 