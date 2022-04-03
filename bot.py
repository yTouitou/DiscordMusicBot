import os
import re
import secrets
from datetime import datetime
from pyexpat.errors import messages
import discord
from azureLink import SelectingInDB, TopStreams, UpdateEnhancedRatings, RetrievesSongsRatings
from djSettings import DJSettings
from secret import Secrets

from spotipyAPI import FindSimilarUsersToWidenRecommandations, GetSpotifyRecommandations, SongNameToID, UpdateRatingsLocally

secrets = Secrets()

default_intents = discord.Intents.default()
default_intents.members = True

client = discord.Client()
settings = DJSettings()




@client.event
async def on_ready():
    print("Le bot est prêt...")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Filou help"))

@client.event
async def on_message(message):

    # Case if that's a message from Hydra
    if (message.author.id == 547905866255433758):
        if (message.embeds[0].to_dict()['title'] == 'Now playing'):

            if (settings.currentlyPlaying):
                settings.StoppedListening()

            print('Hydra just started playing : ' + message.embeds[0].to_dict()['description'])

            messages = await message.channel.history(limit=2).flatten()
            print(str(messages[1].author.name) + ' a demandé ce titre')

            settings.StartListening()

            stream = {}
            stream['songName'] = message.embeds[0].to_dict()['description']
            stream['streamDatetime'] = message.created_at
            #print(type(message.created_at), "-->", str(message.created_at))
            stream['UserID'] = messages[1].author.id
            if (stream['UserID'] == 547905866255433758):
                stream['UserID'] = settings.upcomingSongs[0][1]
                settings.NextSong()
            stream['djMode'] = settings.djMode
            if 'songName' in settings.currentStream:
                stream['lastSongName'] = settings.currentStream['songName']
            # We'll be able to retrieve how many time the song's been played thanks to :
            # Asking Hydra .songinfo --> checking the embed message content --> getting time played --> then changing song
            settings.currentStream = stream
            print(stream)
        
        elif (message.embeds[0].to_dict()['title'].startswith("Track queued - Position")):
            messages = await message.channel.history(limit=2).flatten()
            settings.AddUpcoming(message.embeds[0].to_dict()['description'], messages[1].author.id)
            print(settings.upcomingSongs)


    # Case if that's a message from anyone other than Hydra or the bot itself
    elif (message.author.id != 940272096230133821):

        if (message.content.startswith(".")):
            if (message.content == ".pause"):
                if (settings.currentlyPlaying):
                    settings.PauseListening()
            elif (message.content == ".stop"):
                settings.ClearQueue()
                if (settings.currentlyPlaying):
                    settings.StoppedListening()
            elif (message.content == ".skip"):
                if (settings.currentlyPlaying):
                    settings.StoppedListening()
            elif (message.content == ".resume"):
                if (settings.currentlyPlaying == False):
                    settings.StartListening()
            elif (message.content.startswith(".remove")):
                settings.RemoveIndexSong(message.content[-1])

        elif (re.search(r"filou", message.content, flags = re.IGNORECASE)):

            songIntent = re.findall(r"play.*", message.content, flags = re.IGNORECASE)
            print(songIntent)
            rankingDemand = re.findall(r"top\s\d+", message.content, flags = re.IGNORECASE)

            if (len(songIntent) != 0):
                await message.channel.send(f'I can\'t play music unfortunately, only you can trigger Hydra.\nWrite the following command : ')
                embed = discord.Embed(title=f'.play {songIntent[0][5:]}')
                await message.channel.send(embed=embed)


            elif (re.search(r"help", message.content, flags = re.IGNORECASE)):
                embed = discord.Embed(title="Music Chatbot Help",
                url="https://hydra.bot/",
                description="I am Filou, your music assistant. \n\nTo make me work, you need to invite the Music Bot named Hydra in the server. \nHydra Bot : https://hydra.bot/ \nHydra Commands : https://hydra.bot/commands?category=everyone \n\nI've been build to guide you through your streaming experience. \nHere are my possibilities :\n.\n")
                #Chatbot possibilities with embed message
                embed.add_field(name='Top Streams', value='Ask me your own or global Discord\'s Top Streamings.\nYou can choose the number of top streaming displayed and the time interval.\n--> Ex: "Filou (my) top 12 from last 3 weeks"', inline=False)
                embed.add_field(name='Recommendations', value='Ask me recommendations/suggestions.\nYou can choose the number of recommandations.\n--> Ex: Filou 5 recommendations\n-\nTo maximize my recommendation system, activate me when you start streaming songs.\n--> Ex: Filou activation', inline=False)
                await message.channel.send(embed=embed)

            
            elif (re.search(r"activat(e|ion)", message.content, flags = re.IGNORECASE)):
                await message.channel.send('I am activating all my senses to make the best recommandations!')
                UpdateEnhancedRatings(message.author.id)
                await message.channel.send('Best recommandations are ready!')


            elif (re.search(r"(recommend(ation)?s?)|(suggest(ion)?s?)", message.content, flags = re.IGNORECASE)):
                nbRecommandations = re.findall(r"\d+", message.content, flags = re.IGNORECASE)
                if (len(nbRecommandations) == 0):
                    print("I've been asked for suggestions (default : 10 recommandations)")
                    nbRecommandations.append(10)
                else:
                    if (int(nbRecommandations[0]) < 1):
                        nbRecommandations[0] = 1
                    print(f"I've been asked for {nbRecommandations[0]} suggestions")
                nbRecommandations = int(nbRecommandations[0])
                
                ratingList = RetrievesSongsRatings(nbRecommandations * 10, message.author.id)
                ratingList.sort(key=lambda x: x[1], reverse=True)
                print("\n\nUser first rating list : ", ratingList)

                lastSongDescription = ''
                if 'songName' in settings.currentStream:
                    lastSongDescription = 'based on ' + settings.currentStream['songName']
                    lastSongID = SongNameToID(settings.currentStream['songName'])
                    othersRatings = FindSimilarUsersToWidenRecommandations(5, ratingList, message.author.id)
                    print("\n\nOther users not normalized rating list : ", othersRatings)
                    #Ratings normalization between user and other users ratings
                    for rating in othersRatings:
                        rating[1] *= (ratingList[0][1] / othersRatings[0][1])
                    print("\n\nOther users normalized rating list : ", othersRatings)
                    # Prevents from duplicates
                    previousRatingListSongs = [elem[0] for elem in ratingList]
                    for othersRating in othersRatings:
                        if (othersRating[0] not in previousRatingListSongs):
                            ratingList.append(othersRating)

                    #Rating maximum impact to prevent from suggesting most played songs always
                    ratingMaxImpact = 0.44
                    for elem in ratingList:
                        if (elem[1] > ratingMaxImpact):
                            elem[1] = ratingMaxImpact
                    print("\n\nConcatenated users normalized rating list : ", ratingList, f'\n(Rating Max. Value -> {ratingMaxImpact})')

                    ratingList = UpdateRatingsLocally(20, ratingList, lastSongID, message.author.id)

                ratingList.sort(key=lambda x: x[1], reverse=True)
                print("\n\nFinal rating list : ", ratingList)
                ratingList = ratingList[0:nbRecommandations]

                recommandationsReply = f'Here are my {nbRecommandations} recommandations {lastSongDescription} :'
                for i, rating in enumerate(ratingList):
                    recoLine = ''

                    query = f"""SELECT name FROM songs WHERE ID = '{rating[0]}';"""
                    recoName = SelectingInDB(query)[:-1][0][0]

                    recoLine = f"{i+1}. {recoName} - "

                    #Get song's artists to display them next to the song
                    query = f"""SELECT artists.name
                                FROM songs_artists, artists
                                WHERE songs_artists.artistID = artists.ID
                                    AND songs_artists.songID = '{rating[0]}';"""
                    artistList = SelectingInDB(query)[:-1]
                    #print(artistList)
                    for artist in artistList:
                        recoLine += artist[0] + ', '
                    recoLine = recoLine[:-2]
                    print(recoLine)
                    recommandationsReply += f'\n{recoLine}'
                
                await message.channel.send(recommandationsReply)



                                        


            elif (len(rankingDemand) != 0):

                chatbotReply = 'Here is '
                rankingLength = re.findall(r"\d+", rankingDemand[0])[0]
                #print(f"I've been asked for a top {rankingLength}")

                userRanking = ''
                if (re.search(r"my", message.content, flags = re.IGNORECASE)):
                    userRanking = message.author.id
                    chatbotReply += f"{message.author.name}'s "
                else:
                    chatbotReply += 'the Discord '
                chatbotReply += f'top {rankingLength} from last '

                rankingTime = re.findall(r"last\s(\d+\s)?(hour|day|week|month|year)", message.content, flags = re.IGNORECASE)
                #print(rankingTime)
                if (len(rankingTime) != 0):
                    rankingTime = rankingTime[0]
                    if (re.search(r'\d+', rankingTime[0])):
                        rankingTime = (rankingTime[0][:-1], rankingTime[1])
                        chatbotReply += rankingTime[0] + ' ' + rankingTime[1]
                        if (int(rankingTime[0]) > 1):
                            chatbotReply += 's'
                    else:
                        rankingTime = ('1', rankingTime[1])
                        chatbotReply += rankingTime[1]
                else:
                    rankingTime = ('1', 'week')
                    chatbotReply += rankingTime[1]

                chatbotReply += " :\n"

                #Top 10 retrieval to be added after chatbot reply
                #print(rankingTime)
                topStreams = TopStreams(rankingLength, (rankingTime[1], -int(rankingTime[0])), userRanking)
                #print('topStreams : ', topStreams)

                if (len(topStreams) != 0):
                    for i, topStream in enumerate(topStreams):
                        streamDescription = f"{i+1}. {topStream[1]} - "
                        #Get song's artists to display them next to the song
                        query = f"""SELECT artists.name
                                    FROM songs_artists, artists
                                    WHERE songs_artists.artistID = artists.ID
                                        AND songs_artists.songID = '{topStream[0]}';"""
                        artistList = SelectingInDB(query)[:-1]
                        #print(artistList)
                        for artist in artistList:
                            streamDescription += artist[0] + ', '
                        streamDescription = streamDescription[:-2]
                        streamDescription += f' / {topStream[2]} stream'
                        if (topStream[2] > 1):
                            streamDescription += 's'
                        print(streamDescription)
                        chatbotReply += f'\n{streamDescription}'
                else:
                    chatbotDuration = re.findall(r'last.*:', chatbotReply)[0]
                    chatbotReply = f"You haven't stream any song during the {chatbotDuration[:-2]}."

                await message.channel.send(chatbotReply)
                #Still need to define if user wants it about platform or himself and regarding time !


            else:
                await message.channel.send('Filou, your music chatbot. Call me with the word "help" to get more informations.')
    

    # Case if that's the bot itself message


#Can now retrieve objects IDs in discord thanks to dev mode
@client.event
async def on_member_join(member):
    general_channel = client.get_channel(940271833905786903)
    await general_channel.send(content = f'Bienvenue sur le serveur {member.display.name} !')


client.run(secrets.DiscordTOKEN)



