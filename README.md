# Discord Music Chatbot and Recommandation System
Discord Python Bot combined with Microsoft Azure SQL for music recommendations.
Author : Yves Touitou

<br/>

## Chatbot set up procedure
Make sure you own all required packages/libraries to launch the project thanks to requirements.txt : "pip install -r requirements.txt"

Join the Discord Music Bot server with the following link : "https://discord.gg/K6JHaVez"

Start the bot with "python bot.py" in your Python terminal.

You can now discuss with Filou, the music chatbot.

## Chatbot possibilities
Filou (the chatbot), listens to the songs you listen with the Hydra Bot.
Every stream, song, artist, genre is recorded in the Azure SQL Database.
Thanks to all this data stored, you can ask Filou :
- Top Streams of the Discord platform/your own streams within your selected time range
- Song recommendations which can adapt to the previous songs played

### Hydra
Hydra plays music from Spotify, Deezer or SoundCloud in your voice channel, here are the commands :
https://hydra.bot/commands?category=everyone

## Project Outcome
The azure SQL database is the free version so the server is located in East US. This slows down all queries making the recommendation system very slow. It's working at the moment with few users and not many songs streamed but as data grows, it could take more than a music duration to offer recommandations to the user.

Yet, the recommendation system is stronger with many people using it because each time a user plays songs, it adds them to the database.

A possibility to fill the songs table in the database is to upload songs from "Spotify Million Playlists". It's a dataset gathering a million playlists created between 2010 and 2018 but my free version of azure SQL isn't able to receive that amount of data.

You can find the whole weighting system for user's recommendations in "ratingOperators.py". They can be changed to try to find the best balance to make the best songs prediction.
To know if the predictions are nicely done regarding last song played, we can lean on the "song radio" feature from Spotify which gives 49 songs considering your music habits and the song's characteristics.

