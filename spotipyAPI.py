import json
import time
from datetime import date
import re
import requests
import base64

from azureLink import InsertSongsDataInDB, RetrievesSongsRatings, TuplesListToListsList, UpdateEnhancedRatings
from azureLink import InsertingInDB
from azureLink import SelectingInDB
from azureLink import CrossDataBetweenSongsAndUsers
from ratingOperators import AddInRemainingPotential, ratingOPS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from secret import Secrets

secrets = Secrets()

client_id = secrets.spotifyClientID
client_secret = secrets.spotifyClientSecret

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id,
                                                           client_secret=client_secret))

'''
trackURI = 'spotify:track:0n9iqBDje39F71sJxCzKLl'
results = sp.search(q='Taki Taki', limit=1)
for idx, track in enumerate(results['tracks']['items']):
    print(idx, track.keys())
    print([artist['name'] for artist in track['artists']])
    print(track['duration_ms'] / 1000)
    print(track['name'])
    print(track['id'])
    print(track['popularity'])
    print(track['uri'])
    trackURI = track['uri']

trackFeatures = sp.audio_features(trackURI)
print("Track Features : ")
for key,value in trackFeatures[0].items():
    print(f'{key} : {value}')
'''


def SongNameToID(songName):
    results = sp.search(q=songName, limit=1)
    #print(results['tracks']['items'][0]['id'])
    return results['tracks']['items'][0]['id']

def SongNameToURI(songName):
    results = sp.search(q=songName, limit=1)
    #print(results['tracks']['items'][0]['uri'])
    return results['tracks']['items'][0]['uri']

#print(results.keys())

#Data retrieval (in JSON) from Million Playlists by Spotify
def retrieveFromJSON():
    with open('mpd.slice.0-999.json', 'r') as f:
        data = json.load(f)

    playlists = data['playlists']
    trackURIS = []
    n = 0
    playlistsLimit = 52     #Supposed to last around 1h
    print(f'Number of playlists added to the Database : {playlistsLimit}')

    for playlistInfo in playlists:
        if (n == playlistsLimit):
            break

        for track in playlistInfo['tracks']:
            trackURIS.append(track['track_uri'])

        n = n + 1
    
    '''
    print('\nFirst Playlist content : ')
    for uri in trackURIS:
        print(uri)
    '''
    return trackURIS

#retrieveFromJSON()


def trackURIPipeline(trackURI):
    results = sp.track(trackURI)
    songSpecs = {}
    songSpecs['id'] = results['id']
    songSpecs['name'] = results['name']
    songSpecs['duration_ms'] = results['duration_ms']
    songSpecs['release_date'] = results['album']['release_date']
    songSpecs['release_date_precision'] = results['album']['release_date_precision']
    songSpecs['artists'] = []
    for artist in results['artists']:
        artistSpecs = {'id' : artist['id'], 'name' : artist['name'], 'genres' : sp.artist(artist['uri'])['genres']}
        songSpecs['artists'].append(artistSpecs)
    
    #print(songSpecs)
    return songSpecs

def SongSpecsToDB(trackURIList):
    #Ensures object given to azureLink.py function is a list of specifications
    if (isinstance(trackURIList, list) == False):
        trackURIList = [trackURIList]

    songSpecsList = []
    for i in range(len(trackURIList)):
        songSpecsList.append(trackURIPipeline(trackURIList[i])) 

    InsertSongsDataInDB(songSpecsList)

#SongSpecsToDB(retrieveFromJSON())


def DateTimeSQLFormat(anyDatetime):
    withoutMS = re.split(r'\..*', str(anyDatetime))[0]
    return withoutMS.replace('-', '')


def UserStreamDB(stream, djMode):
    
    userExists = False
    resultQuery = SelectingInDB(f"""SELECT ID FROM users WHERE ID = '{stream['UserID']}';""")[0]
    if (resultQuery != None):
        userExists = True

    # Done if this user doesn't exist yet
    if (userExists == False):
        query = f'''INSERT INTO users VALUES ('{stream['UserID']}')'''
        InsertingInDB(query)
        #CrossDataBetweenSongsAndUsers(newUserID=stream['UserID'])


    songID = SongNameToID(stream['songName'])
    songExists = False
    resultQuery = SelectingInDB(f"""SELECT ID FROM songs WHERE ID = '{songID}';""")[0]
    if (resultQuery != None):
        songExists = True

    # Inserts song in DB if doesn't exist
    SongSpecsToDB([SongNameToURI(stream['songName'])])

    #Enfin ajouter le stream qui possède ses références dans la DB (song IDs)
    lastSongColumn = ""
    lastSongValue = ""
    if 'lastSongName' in stream:
        lastSongColumn = "lastSongID, "
        lastSongValue = "\'" + SongNameToID(str(stream['lastSongName'])) + "\', "
    
    # Calculates relative listening duration
    listening_duration = stream['listening_ms']
    song_duration = SelectingInDB(f'''SELECT duration FROM songs WHERE ID='{songID}';''')[0][0]
    relative_listening_duration = round(listening_duration/song_duration, 2)
    if (relative_listening_duration > 1):
        relative_listening_duration = 1.00

    # Inserts the user's stream in streams table
    query = f'''INSERT INTO streams (userID, songID, streamDatetime, relativeListeningTime, {lastSongColumn}djMode) VALUES ('{stream['UserID']}', '{songID}', '{DateTimeSQLFormat(stream['streamDatetime'])}', {relative_listening_duration}, {lastSongValue}'{djMode}');'''
    InsertingInDB(query)

    # if song doesn't exist create a record for each user with the song with 0.3 ratings
    if (songExists == False):
        #CrossDataBetweenSongsAndUsers(newSongID=songID)
        True
    
    query = f'''INSERT INTO songs_users VALUES ('{songID}', '{stream['UserID']}', {ratingOPS()['default']}, {ratingOPS()['default']});'''
    InsertingInDB(query)

    # Get user's ratings regarding song he's just been playing
    query = f'''SELECT rating, enhancedRating FROM songs_users WHERE userID = '{stream['UserID']}' AND songID = '{songID}';'''
    ratings = SelectingInDB(query)[0]
    currentRating = ratings[0]
    currentEnhancedRating = ratings[1]

    # Updates rating regarding listening time
    if (currentRating == 0.3):
        newRating = float(currentRating) * ratingOPS()['firstKeep'] + relative_listening_duration * ratingOPS()['firstAdd']
        query = f'''UPDATE songs_users SET rating = {newRating}, enhancedRating = {float(currentEnhancedRating) + newRating - float(currentRating)} WHERE userID = '{stream['UserID']}' AND songID = '{songID}';'''
        InsertingInDB(query)
    else:
        newRating = float(currentRating) * ratingOPS()['multipleKeep'] + relative_listening_duration * ratingOPS()['multipleAdd']
        query = f'''UPDATE songs_users SET rating = {newRating}, enhancedRating = {float(currentEnhancedRating) + newRating - float(currentRating)} WHERE userID = '{stream['UserID']}' AND songID = '{songID}';'''
        InsertingInDB(query)
    print('Stream successfully inserted')
    


def GetSpotifyRecommandations(trackID, nbRecommandations, clientID, clientSecret):
    # Step 1 - Authorization 
    url = "https://accounts.spotify.com/api/token"
    headers = {}
    data = {}

    # Encode as Base64
    message = f"{clientID}:{clientSecret}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')

    headers['Authorization'] = f"Basic {base64Message}"
    data['grant_type'] = "client_credentials"

    r = requests.post(url, headers=headers, data=data)

    token = r.json()['access_token']
    
    headers = {
        "Accept" : "application/json",
        "Content-Type" : "application/json",
        "Authorization" : "Bearer " + token
    }

    r = requests.get(f"https://api.spotify.com/v1/recommendations?limit={nbRecommandations}&market=FR&seed_tracks={trackID}", headers=headers)
    data = r.json()

    idList = []
    for track in data['tracks']:
        idList.append(track['uri'][-22:])

    return idList
    


# Makes an update of ratings after retrieval
def UpdateRatingsLocally(nbSpRecommandations, songsRating, lastSongID, userID, clientID=client_id, clientSecret=client_secret):

    # Upgrades song rating if spotify recommands it regarding last song streamed
    spotifyRcs = GetSpotifyRecommandations(lastSongID, nbSpRecommandations, clientID, clientSecret)
    for rating in songsRating:
        if (rating[0] in spotifyRcs):
            rating[1] = AddInRemainingPotential(rating[1], ratingOPS()['spotifyRelative'])
    
    
    # Upgrades song rating if the song has been released within a 1-year interval regarding last song played
    releaseDate = None
    try:
        releaseDate = SelectingInDB(f"""SELECT albumReleaseDate FROM songs WHERE ID = '{lastSongID}';""")[:-1][0][0]
    except:
        SongSpecsToDB([f'spotify:track:{lastSongID}'])
        releaseDate = SelectingInDB(f"""SELECT albumReleaseDate FROM songs WHERE ID = '{lastSongID}';""")[:-1][0][0]
    #print('releaseDate :', releaseDate)
    for rating in songsRating:
        query = f"""SELECT DATEDIFF(day, albumReleaseDate, '{releaseDate}') as Interval
                    FROM songs 
                    WHERE id = '{rating[0]}';"""
        dayInterval = SelectingInDB(query)[:-1]
        if (len(dayInterval) != 0):
            dayInterval = dayInterval[0][0]
            if (abs(dayInterval) < 365):
                rating[1] += ratingOPS()['1yearInterval']


    # Upgrades song rating if same chain as before
    query = f"""SELECT songID
                FROM streams
                WHERE lastSongID = '{lastSongID}';"""
    chainIDs = SelectingInDB(query)[:-1]
    for i in range(len(chainIDs)):
        chainIDs[i] = chainIDs[i][0]
    for rating in songsRating:
        if (rating[0] in chainIDs):
            rating[1] = AddInRemainingPotential(rating[1], ratingOPS()['sameChain'])


    # Upgrades song rating if last song was the same genre
    query = f"""SELECT DISTINCT streams.songID
            FROM streams 
                INNER JOIN songs ON streams.songID = songs.ID 
                INNER JOIN songs_artists ON songs.ID = songs_artists.songID
                INNER JOIN artists_genres ON songs_artists.artistID = artists_genres.artistID
            WHERE streams.userID = '406121355025711104'
                AND artists_genres.genreName IN (SELECT genreName 
                                                FROM songs_artists 
                                                    INNER JOIN artists_genres ON songs_artists.artistID = artists_genres.artistID
                                                WHERE songs_artists.songID = '2x7MyWybabEz6Y6wvHuwGE');"""
    sameGenreList = SelectingInDB(query)[:-1]
    for i in range(len(sameGenreList)):
        sameGenreList[i] = sameGenreList[i][0]
    for rating in songsRating:
        if (rating[0] in sameGenreList):
            rating[1] = AddInRemainingPotential(rating[1], ratingOPS()['sameGenre'])


    # Upgrades song rating if last song was made by the same artist
    query = f"""SELECT streams.songID
            FROM streams 
                INNER JOIN songs ON streams.songID = songs.ID 
                INNER JOIN songs_artists ON songs.ID = songs_artists.songID
            WHERE streams.userID = '{userID}'
                AND songs_artists.artistID IN (SELECT artistID FROM songs_artists WHERE songID = '{lastSongID}');"""
    sameArtistList = SelectingInDB(query)[:-1]
    for i in range(len(sameArtistList)):
        sameArtistList[i] = sameArtistList[i][0]
    for rating in songsRating:
        if (rating[0] in sameArtistList):
            rating[1] = AddInRemainingPotential(rating[1], ratingOPS()['sameArtist'])


    # Downgrades song rating if it's been played just before
    for rating in songsRating:
        query = f"""SELECT DATEDIFF(minute, MAX(streamDatetime), GETDATE()) as Interval
                    FROM streams 
                    WHERE songid = '{rating[0]}';"""
        minuteInterval = SelectingInDB(query)[:-1]
        #print('minuteInterval : ', minuteInterval, 'on following song :', rating[0])
        if (minuteInterval[0][0] != None):
            minuteInterval = minuteInterval[0][0]
            if (minuteInterval < 60):
                rating[1] -= ratingOPS()['playedRecently'] - minuteInterval/100
        

    return songsRating


def FindSimilarUsersToWidenRecommandations(nbOtherUsers, songsRating, userID):
    # Stores user's best songs for less calculation time
    userRecommandedSongs = [elem[0] for elem in songsRating]

    # Retrieves randomly a defined number of other users
    query = f"""SELECT TOP {nbOtherUsers} ID FROM users
                WHERE ID != '{userID}'
                ORDER BY RAND();"""
    usersSelected = SelectingInDB(query)[:-1]
    #print('usersSelected tuples :', usersSelected)

    usersSelected = TuplesListToListsList(usersSelected)
    #print('usersSelected lists :', usersSelected)

    # Get other users favorite songs
    usersRatings = {}
    for user in usersSelected:
        usersRatings[user[0]] = RetrievesSongsRatings(len(songsRating), user[0])
    #print('usersRatings :', usersRatings)

    # Calculates for each other user, same  number of preferred songs and their rating similarity
    similarityArray = []
    for user, ratingList in usersRatings.items():
        distances = []
        
        # Calculates distance
        for rating in ratingList:
            if (rating[0] in userRecommandedSongs):
                distances = [abs(elem[1]-rating[1]) for elem in songsRating if rating[0] == elem[0]]
        
        print('distances :', distances)

        # Stores [average(distance), number of same favorite songs, userID]
        similarity = None
        if (len(distances) > 0):
            similarity = [sum(distances)/len(distances), len(distances), user]
        else:
            similarity = [1, 0, user]
        similarityArray.append(similarity)
    
    #print('similarityArray :', similarityArray)

    # Finds user with the minimum average distance between rates
    similarityArray.sort(key=lambda x: x[0])
    lessDistanceUser = similarityArray[0][2]

    # Finds user with the minimum average distance between rates 
    # having at least 70% of same songs regarding the user having the most similar songs streamed
    similarityArray.sort(key=lambda x: x[1], reverse=True)
    songsSimilarUsers = [elem for elem in similarityArray if (elem[1]/similarityArray[0][1]) >= 0.7]
    songsSimilarUsers.sort(key=lambda x: x[0])
    mostSongsSimilarUser = songsSimilarUsers[0][2]

    # We finally get those two user's ratings regarding last song played
    lessDistanceUserRatings = usersRatings[lessDistanceUser]
    lessDistanceUserRatings.sort(key=lambda x: x[1], reverse=True)
    # We defined the second user ratings as None if both users kept are the same
    mostSongsSimilarUserRatings = None
    if (lessDistanceUser != mostSongsSimilarUser):
        mostSongsSimilarUserRatings = usersRatings[mostSongsSimilarUser]
        mostSongsSimilarUserRatings.sort(key=lambda x: x[1], reverse=True)
        # Normalisation between first and second similar ratings
        for rating in mostSongsSimilarUserRatings:
            rating[1] *= (lessDistanceUserRatings[0][1] / mostSongsSimilarUserRatings[0][1])

    #print('Ratings retained :', lessDistanceUserRatings, mostSongsSimilarUserRatings)

    ratingsFromOthers = lessDistanceUserRatings
    if (mostSongsSimilarUserRatings != None):
        ratingsFromOthers = ratingsFromOthers + mostSongsSimilarUserRatings

    #print('ratingsFromOthers :', ratingsFromOthers)
    ratingsFromOthers.sort(key=lambda x: x[1], reverse=True)
    
    return ratingsFromOthers


    


        
    
#FindSimilarUsersToWidenRecommandations()

'''
ratingList = RetrievesSongsRatings(6, '406121355025711104')
print(ratingList)

#Testing with lastSong = Alejandro by Lady Gaga, user being myself
songsRating = UpdateRatingsLocally(20, ratingList, '4lwavw59UjXUPJZtKNdFYp', '406121355025711104')
print(songsRating)
'''




