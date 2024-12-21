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
    const scopes = ['user-library-read', 'user-top-read'];
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

async function collectAndSaveData() {
    try {
        // Get user's top artists for different time ranges
        const timeRanges = ['short_term', 'medium_term', 'long_term'];
        const artistData = {};

        for (const range of timeRanges) {
            const data = await spotifyApi.getMyTopArtists({ 
                limit: 50, 
                time_range: range 
            });
            // Log the first artist from each time range
            console.log(`First artist from ${range}:`, 
                JSON.stringify(data.body.items[0], null, 2)
            );
            artistData[range] = data.body.items;
        }

        // Create a timestamp for the filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filePath = path.join(__dirname, 'data', `spotify_data_${timestamp}.json`);

        // Save the data
        fs.writeFileSync(
            filePath,
            JSON.stringify(artistData, null, 2)
        );

        console.log(`Data saved to ${filePath}`);

    } catch (error) {
        console.error('Error collecting data:', error);
        throw error;
    }
}

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
}); 