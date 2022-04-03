def ratingOPS():

    OPS = {
        # Default rating
        'default' : 0.3,

        # Rating songs thanks to previous user's similar streams
        'sameSong' : 0.1,
        'artistRelative' : 0.1,
        'genreRelative' : 0.1,

        # Rating songs thanks to Discord Latest Top Streams
        'top10Discord3d' : 0.1,
        'top10Discord2w' : 0.05,

        # Rating songs thanks to the previous stream
        'spotifyRelative' : 0.15,
        '1yearInterval' : 0.15,
        'sameChain' : 0.05,
        'sameGenre' : 0.25,
        'sameArtist' : 0.2,

        # Downgrade ratings if same song's been played recently
        'playedRecently' : 0.6,

        # Rating for first or multiple streams
        'firstKeep' : 0.82,
        'firstAdd' : 0.11,
        'multipleKeep' : 0.85,
        'multipleAdd' : 0.07
    }

    return OPS

def AddInRemainingPotential(rating, percentage):
    return rating + (1 - rating) * percentage