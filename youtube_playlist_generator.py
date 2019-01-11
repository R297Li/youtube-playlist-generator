import bs4
import requests
import youtube_api
import datetime
import sys
from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime


# Print function for main tasks
def printHeader(message):
    print ("-----------------------------------------")
    print (message)
    print ("-----------------------------------------")


# Print function for items
def printItem(message):
    print ("- - - - - - - - - - - - - - - - - - - - -")
    print (message)
    print ("- - - - - - - - - - - - - - - - - - - - -")


# Main Function
def main():

    printHeader("Youtube Playlist Generator")

    # Url for music
    musicUrl = "https://www.billboard.com/charts/r-and-b-songs"
    printHeader("Web scrap songs from webpage: \n" + musicUrl)

    # Make request to musicUrl and obtain raw html
    pageRequest = requests.get(musicUrl)
    pageHtmlRaw = pageRequest.text

    # Parse raw html with BeautifulSoup and find all songs
    pageSoup = BeautifulSoup(pageHtmlRaw, "html.parser")
    musicContainers = pageSoup.find_all(
        'div', {'class': 'chart-list-item__text-wrapper'})

    # Initialize empty array to store song information
    songsToAdd = []

    # Append to songsToAdd array the song name and song artist
    printHeader("Compiling array of song items.")
    for musicContainer in musicContainers:
        songName = musicContainer.find(
            'div', {'class': 'chart-list-item__title'}).text.replace('\n', '')
        songArtist = musicContainer.find(
            'div', {'class': 'chart-list-item__artist'}).text.replace('\n', '')
        songInformation = songName + ":" + songArtist
        songsToAdd.append(songInformation)

    # Check if songs array is empty
    if len(songsToAdd) == 0:
        print ("Error getting songs from webpage:" + musicUrl)
        print ("Please try again.")
        sys.exit()

    # Authenticate to youtube API
    printHeader("Authenticate to youtube API.")
    youtubeClient = youtube_api.get_authenticated_service()

    # Initialize variables pertaining to newly desired playlist
    todayDate = str(date.today())
    todayTime = str(datetime.now().replace(second=0, microsecond=0).time())
    playlistTitle = "New Playlist, " + todayDate
    playlistDescription = "Music obtained from: " + musicUrl
    playlistPrivacyStatus = 'private'

    # Obtain current channel info
    printHeader("Obtain channel Info.")
    channels = youtube_api.getChannelMine(youtubeClient)

    if "error" in channels:
        print ("Error obtaining channel information. Please try again.")
        sys.exit()

    # Assuming only 1 youtube account signed in at the moment
    channel = channels['items'][0]
    channelId = channel['id']

    # Obtain list of currently existing playlists on account
    existingPlaylists = youtube_api.getExistingPlaylists(
        youtubeClient, channelId)

    # Check if playlist already exists; if so, change name of new playlist
    printHeader(
        "Check if a playlist with identical desired playlist title exists.")
    for playlist in existingPlaylists.get('items', []):
        if playlistTitle in playlist['snippet']['title']:
            playlistTitle = playlistTitle + " " + todayTime
            print ("Playlist with desired name currently exists. \n")
            print ("New playlist will be instead called: " + playlistTitle)

    # Create playlist
    printHeader("Creating playlist with name: " + playlistTitle)
    youtubePlaylistResponse = youtube_api.createPlaylist(
        youtubeClient, playlistTitle, playlistDescription, playlistPrivacyStatus)

    # Check if response from API was an error or not
    if "error" in youtubePlaylistResponse:
        print ("Error in creating playlist. \n" +
               youtubePlaylistResponse + "\n")
        print ("Please fix error and try again.")
        sys.exit()

    # Obtain newly created youtube playlist ID
    youtubePlaylistId = youtubePlaylistResponse['id']
    youtubePlaylistLink = "https://www.youtube.com/playlist?list=" + youtubePlaylistId
    totalSongs = len(songsToAdd)
    songsAddedSuccessfully = 0

    for song in songsToAdd:
        # Obtain search results for song
        searchResults = youtube_api.youtubeSearchResults(
            song.replace(':', ' '), youtubeClient)
        # For each item in search results, check if item title contains song title and artist's first name
        for searchResult in searchResults.get('items', []):
            songInformation = song.split(':')
            if (songInformation[0] in searchResult['snippet']['title']):
                songArtist = songInformation[1].split(' ')[0]
                if (songArtist in searchResult['snippet']['title']):
                    # Insert song into playlist
                    songInsertResponse = youtube_api.insertSongToPlaylist(
                        youtubeClient, searchResult['id']['videoId'], youtubePlaylistId)
                    # Check if response from API was an error or not
                    if "error" in songInsertResponse:
                        printItem(
                            "Song: " + searchResult['snippet']['title'] + " was unable to be added.")
                    else:
                        printItem(
                            "Song: " + searchResult['snippet']['title'] + " was successfully added.")
                        songsAddedSuccessfully += 1
                    break

    printHeader(str(songsAddedSuccessfully) + "/" + str(totalSongs) +
                " was successfully added to playlist: \n" + youtubePlaylistLink)


main()
