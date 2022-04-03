DROP TABLE IF EXISTS artists_genres;
DROP TABLE IF EXISTS songs_artists;
DROP TABLE IF EXISTS songs_users;
DROP TABLE IF EXISTS streams;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS users;

CREATE TABLE songs
(
	ID VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    duration INT NOT NULL,
    albumReleaseDate DATE
);

CREATE TABLE users
(
	ID VARCHAR(50) PRIMARY KEY
);

CREATE TABLE streams 
(
	userID VARCHAR(50),
    songID VARCHAR(50),
    streamDatetime DATETIME,
    relativeListeningTime DECIMAL(3,2) NOT NULL,
    lastSongID VARCHAR(50),
    djMode VARCHAR(50) NOT NULL,
    PRIMARY KEY(userID, songID, streamDatetime),
    FOREIGN KEY (songID) REFERENCES songs(ID),
    FOREIGN KEY (userID) REFERENCES users(ID),
    FOREIGN KEY (lastSongID) REFERENCES songs(ID)
);

CREATE TABLE artists
(
	ID VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE genres
(
	name VARCHAR(50) PRIMARY KEY
);

CREATE TABLE songs_users
(
	songID VARCHAR(50),
    userID VARCHAR(50),
    rating DECIMAL(3,2),
    enhancedRating DECIMAL(3,2),
    PRIMARY KEY(songID, userID),
    FOREIGN KEY (songID) REFERENCES songs(ID),
    FOREIGN KEY (userID) REFERENCES users(ID)
);

CREATE TABLE songs_artists
(
	songID VARCHAR(50),
    artistID VARCHAR(50),
    PRIMARY KEY(songID, artistID),
    FOREIGN KEY (songID) REFERENCES songs(ID),
    FOREIGN KEY (artistID) REFERENCES artists(ID)
);

CREATE TABLE artists_genres
(
	artistID VARCHAR(50),
    genreName VARCHAR(50),
    PRIMARY KEY(artistID, genreName),
    FOREIGN KEY (artistID) REFERENCES artists(ID),
    FOREIGN KEY (genreName) REFERENCES genres(name)
);

-- To show tables :
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';

-- To describe tables :
--    exec sp_columns MyTable