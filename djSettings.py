from datetime import datetime
from datetime import timedelta
import math
from spotipyAPI import UserStreamDB

from numpy import true_divide

class DJSettings:

    def __init__(self):
        self.djMode = 'off'
        #self.songType = 'famous'
        self.currentStream = {}
        self.upcomingSongs = []
        self.startListeningDate = None
        self.currentlyPlaying = False
        self.totalListeningTime = timedelta()
        



    def StartListening(self):
        self.startListeningDate = datetime.now()
        self.currentlyPlaying = True

    def PauseListening(self):
        self.totalListeningTime += (datetime.now() - self.startListeningDate)
        print(self.totalListeningTime)
        self.currentlyPlaying = False

    def StoppedListening(self):
        self.totalListeningTime += (datetime.now() - self.startListeningDate)
        self.currentlyPlaying = False
        self.currentStream['listening_ms'] = math.ceil(self.totalListeningTime.total_seconds()*1000)
        self.totalListeningTime = timedelta()
        UserStreamDB(self.currentStream, self.djMode)


    def AddUpcoming(self, songName, userID):
        self.upcomingSongs.append((songName, userID))

    def NextSong(self):
        del self.upcomingSongs[0]

    def RemoveIndexSong(self, index):
        del self.upcomingSongs[0]

    def ClearQueue(self):
        self.upcomingSongs = []




    ##################################################################

    ## Changing DJ Mode
    def ChangeModeToOff(self):
        self.djMode = 'off'

    def ChangeModeToAssisting(self):
        self.djMode = 'assisting'

    def ChangeModeToAutomatic(self):
        self.djMode = 'automatic'

    ## Verifying DJ Mode
    def IsModeOff(self):
        return self.djMode == 'off'

    def IsModeAssisting(self):
        return self.djMode == 'assisting'

    def IsModeAutomatic(self):
        return self.djMode == 'automatic'

    ##################################################################


    '''
    ## Changing Song Type
    def ChangeTypeToFamous(self):
        self.songType = "famous"

    def ChangeTypeToDiscover(self):
        self.songType = "discover"

    ## Verifying Song Type
    def IsTypeFamous(self):
        return self.songType == "famous"

    def IsTypeDiscover(self):
        return self.songType == "discover"
    '''