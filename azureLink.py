from datetime import datetime
import pyodbc
import time
import requests
from ratingOperators import ratingOPS
from secret import Secrets
server = 'mysqlservermusic.database.windows.net'
database = 'musicBotDB'
username = 'LetMeBurn'
driver= '{ODBC Driver 18 for SQL Server}'
secrets = Secrets()

###############################################
## Queries test :

def SelectTest():
    with pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:mysqlservermusic.database.windows.net;PORT=1433;DATABASE=musicBotDB;UID=' + secrets.azureUID + ';PWD=' + secrets.azurePwD + 'ulay') as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM test;")
            row = cursor.fetchone()
            while row:
                print(row)
                row = cursor.fetchone()

def InsertTest():
    with pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:mysqlservermusic.database.windows.net;PORT=1433;DATABASE=musicBotDB;UID=LetMeBurn;PWD=Fr3nchenculay') as conn:
        with conn.cursor() as cursor:
            songName = 'Toxic'
            releaseDate = '20171117 21:14:47'
            try:
                cursor.execute(f"""INSERT INTO test VALUES('{songName}', '{releaseDate}');""")
            except:
                True


#############################################
### Basic queries with SQLquery as parameter

def SelectingInDB(SQLquery):
    with pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:mysqlservermusic.database.windows.net;PORT=1433;DATABASE=musicBotDB;UID=LetMeBurn;PWD=Fr3nchenculay') as conn:
        with conn.cursor() as cursor:
            rows = []
            cursor.execute(SQLquery)
            row = cursor.fetchone()
            rows.append(row)
            while row:
                #print(row)
                row = cursor.fetchone()
                rows.append(row)
            return rows

# Can be executed for sql updates as well
def InsertingInDB(SQLquery):
    with pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:mysqlservermusic.database.windows.net;PORT=1433;DATABASE=musicBotDB;UID=LetMeBurn;PWD=Fr3nchenculay') as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(SQLquery)
            except:
                True


#############################################
## Special queries

def InsertSongsDataInDB(songSpecsList):
    with pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:mysqlservermusic.database.windows.net;PORT=1433;DATABASE=musicBotDB;UID=LetMeBurn;PWD=Fr3nchenculay') as conn:
        with conn.cursor() as cursor:
            nSong = 0
            print("The dataset to be uploaded is made of", len(songSpecsList), "songs.")
            for songSpecs in songSpecsList:
                start = time.time()

                # Song insertion
                try:
                    songSpecs['name'].replace("\'", "\'\'")
                    cursor.execute(f'''INSERT INTO songs VALUES('{songSpecs['id']}', '{songSpecs['name']}', '{songSpecs['duration_ms']}', '{songSpecs['release_date']}');''')
                except:
                    True

                # Artist and genres insertion
                for artist in songSpecs['artists']:
                    try:
                        cursor.execute(f'''INSERT INTO artists VALUES('{artist['id']}', '{artist['name']}');''')
                    except:
                        True

                    for genre in artist['genres']:
                        try:
                            cursor.execute(f'''INSERT INTO genres VALUES('{genre}')''')
                        except:
                            True
                        try:
                            cursor.execute(f'''INSERT INTO artists_genres VALUES('{artist['id']}', '{genre}');''')
                        except:
                            True

                    try:
                        cursor.execute(f'''INSERT INTO songs_artists VALUES('{songSpecs['id']}', '{artist['id']}');''')
                    except:
                        True
                
                end = time.time()
                print(f'{round(end - start, 2)} seconds needed for Song #{nSong}')

                nSong = nSong + 1


def CrossDataBetweenSongsAndUsers(newSongID = None, newUserID = None):
    if (newSongID != None):
        userIDs = SelectingInDB("""SELECT ID FROM users""")[:-1]
        for i in range(len(userIDs)):
            userIDs[i] = userIDs[i][0]

        for userID in userIDs:
            query = f'''INSERT INTO songs_users VALUES ('{newSongID}', '{userID}', {ratingOPS()['default']}, {ratingOPS()['default']});'''
            print(query)
            InsertingInDB(query)

    else:
        songIDs = SelectingInDB("""SELECT ID FROM songs""")[:-1]
        for i in range(len(songIDs)):
            songIDs[i] = songIDs[i][0]

        for songID in songIDs:
            query = f'''INSERT INTO songs_users VALUES ('{songID}', '{newUserID}', {ratingOPS()['default']}, {ratingOPS()['default']});'''
            print(query)
            InsertingInDB(query)


# Make top X retrievals function of X and (my or platform)
# param : pastTime is like : ('day', -7)
def TopStreams(nbSongs, pastTime, userID = ''):

    if (userID != ''):
        userID = f"""AND streams.userID = '{userID}'"""

    query = f"""SELECT TOP {nbSongs} songs.ID, songs.name, count(*) FROM songs, streams
                WHERE songs.ID = streams.songID
                    {userID}
                    AND streams.streamDatetime BETWEEN DATEADD({pastTime[0]},{pastTime[1]},GETDATE()) AND GETDATE()
                GROUP BY songs.ID, songs.name
                ORDER BY count(*) DESC;
                """
    
    return SelectingInDB(query)[:-1]




# Makes an update of ratings before retrieval
def UpdateEnhancedRatings(userID):

    # Resets all enhanced ratings to ratings for user
    query = f"""UPDATE songs_users
                SET enhancedRating = rating
                WHERE userID = '{userID}';"""
    InsertingInDB(query)

    
    # Upgrades enhanced rating for songs being in the top 10 Bot within 3 days
    query = f"""UPDATE songs_users 
                SET enhancedRating = enhancedRating + (1 - enhancedRating) * {ratingOPS()['top10Discord3d']}
                WHERE songID IN (SELECT TOP 10 songs.ID FROM songs, streams
                                WHERE songs.ID = streams.songID
                                    AND streams.streamDatetime BETWEEN DATEADD(day,-3,GETDATE()) AND GETDATE()
                                GROUP BY songs.ID, songs.name
                                ORDER BY count(*) DESC)
                    AND userID = '{userID}';"""
    InsertingInDB(query)


    # Upgrades enhanced rating for songs being in the top 10 Bot within 2 weeks
    query = f"""UPDATE songs_users 
                SET enhancedRating = enhancedRating + (1 - enhancedRating) * {ratingOPS()['top10Discord2w']}
                WHERE songID IN (SELECT TOP 10 songs.ID FROM songs, streams
                                WHERE songs.ID = streams.songID
                                    AND streams.streamDatetime BETWEEN DATEADD(week,-2,GETDATE()) AND GETDATE()
                                GROUP BY songs.ID, songs.name
                                ORDER BY count(*) DESC)
                    AND userID = '{userID}';"""
    InsertingInDB(query)
    


    # Upgrades enhanced rating regarding how many times the artist has been streamed by user
    query = f"""SELECT songs_users.songID, SUM(artists_streams.nbStreams) as TotalStreams
                FROM songs_users
                    INNER JOIN songs_artists ON songs_users.songID = songs_artists.songID
                    INNER JOIN (SELECT artistRedundancy.artistID, artistRedundancy.nbStreams
                                FROM (SELECT artists.id as artistID, count(*) as nbStreams
                                    FROM streams
                                        INNER JOIN songs ON streams.songID = songs.ID
                                        INNER JOIN songs_artists ON songs.ID = songs_artists.songID
                                        INNER JOIN artists ON songs_artists.artistID = artists.ID
                                    WHERE streams.userID = '{userID}'
                                    GROUP BY artists.id) as artistRedundancy) as artists_streams ON songs_artists.artistID = artists_streams.artistID
                WHERE songs_users.userID = '{userID}'
                GROUP BY songs_users.songID"""
    artistsHabitsTuples = SelectingInDB(query)[:-1]
    # From tuples to lists to make it modifiable
    artistsHabits = []
    for elem in artistsHabitsTuples:
        artistHabit = []
        for insideElem in elem:
            artistHabit.append(insideElem)
        artistsHabits.append(artistHabit)
    
    # If higher than max percentage, equals to max percentage
    for elem in artistsHabits:
        elem[1] = round(float(elem[1])/400, 2)             # 250 can be modified
        if elem[1] > ratingOPS()['artistRelative']:
            elem[1] = ratingOPS()['artistRelative']

    #print(artistsHabits)
    
    multipleQuery = ''
    for elem in artistsHabits:
        query = f"""UPDATE songs_users
                    SET enhancedRating = enhancedRating + {elem[1]}
                    WHERE songID = '{elem[0]}';"""
        multipleQuery += query
    InsertingInDB(multipleQuery)

#UpdateEnhancedRatings('406121355025711104')


def TuplesListToListsList(tuplesList):
    songsRating = []
    for elem in tuplesList:
        songRating = []
        for insideElem in elem:
            songRating.append(insideElem)
        songsRating.append(songRating)
    return songsRating
    

# Retrieves songs regarding ratings
def RetrievesSongsRatings(nbRecommandations, userID):
    
    #Supposed to be bigger to adjust with post-retrieval rating changes
    nbRetrieved = nbRecommandations

    query = f"""SELECT TOP {nbRecommandations} songs_users.songID, songs_users.enhancedRating, songs.name
                FROM songs_users INNER JOIN songs ON songs_users.songID = songs.ID
                WHERE songs_users.userID = '{userID}'
                ORDER BY songs_users.enhancedRating DESC;"""

    currentSelectionTuples = SelectingInDB(query)[:-1]

    # Transforms ratingList from list of tuples to list of lists to make the values modifiable
    songsRating = TuplesListToListsList(currentSelectionTuples)
    ### We can now use : ### songsRating ###

    for rating in songsRating:
        # Conversion from decimal.Decimal to float
        rating[1] = float(rating[1])

    return songsRating


