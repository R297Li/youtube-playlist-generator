import os

import google.oauth2.credentials
import webbrowser

import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
from six.moves import input

# The CLIENT_SECRETS_FILE variable specifies the name and location of a file
# that contains the OAuth 2.0 information for this application, including its
# client_id and client_secret.
CLIENT_SECRETS_FILE = "./resources/src/secret/client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Messages to display in terminal for authenication
authUrlMessage = 'Please visit this URL to authorize this Playlist Generator: \n \n{url}'
authCodeMessage = '\nEnter the authorization code: '


# Method to authenticate to youtube API
def get_authenticated_service():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    authUrl, _ = flow.authorization_url(prompt='consent')
    print (authUrlMessage.format(url=authUrl))
    webbrowser.open_new_tab(authUrl)
    authCode = input(authCodeMessage)
    flow.fetch_token(code=authCode)
    authCredentials = flow.credentials
    return build(API_SERVICE_NAME, API_VERSION, credentials=authCredentials)


# Method to print response
def print_response(response):
    print(response)


# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
    resource = {}
    for p in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = p.split('.')
        ref = resource
        for pa in range(0, len(prop_array)):
            is_array = False
            key = prop_array[pa]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key)-2:]
                is_array = True

            if pa == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[p]:
                    if is_array:
                        ref[key] = properties[p].split(',')
                    else:
                        ref[key] = properties[p]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource


# Method to remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value

    return good_kwargs


# Method to communicate to youtube API and obtain channel info
def channels_list_mine(client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.channels().list(
        **kwargs
    ).execute()

    return response


# Method to communicate to youtube API to search for desired item
def search_list_by_keyword(client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.search().list(
        **kwargs
    ).execute()

    return response


# Method to communicate to youtube API to create playlist
def playlist_create(client, properties, **kwargs):
    resource = build_resource(properties)
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlists().insert(
        body=resource,
        **kwargs
    ).execute()

    return response


# Method to communicate to youtube API to obtain all existing playlists
def playlists_list_by_channel_id(client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlists().list(
        **kwargs
    ).execute()

    return response


# Method to communicate to youtube API with item to insert to playlist
def playlist_items_insert(client, properties, **kwargs):
    resource = build_resource(properties)
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlistItems().insert(
        body=resource,
        **kwargs
    ).execute()

    return response


# Method to obtain channel info
def getChannelMine(client):
    response = channels_list_mine(client,
                                  part='snippet,contentDetails,statistics',
                                  mine=True)

    return response


# Method to obtain youtube search results
def youtubeSearchResults(songInformation, client):
    maxSearchResults = 25
    youtubeResults = search_list_by_keyword(
        client, part='snippet', maxResults=maxSearchResults, q=songInformation, type='')
    return youtubeResults


# Method to create new playlist
def createPlaylist(client, title, description, privacyStatus):
    playlistProperties = {'snippet.title': title,
                          'snippet.description': description,
                          'snippet.tags[]': '',
                          'snippet.defaultLanguage': '',
                          'status.privacyStatus': privacyStatus}
    response = playlist_create(client, playlistProperties,
                               part='snippet,status',
                               onBehalfOfContentOwner='')

    return response


# Method to obtain all existing playlists
def getExistingPlaylists(client, channelId):
    response = playlists_list_by_channel_id(client,
                                            part='snippet,contentDetails',
                                            channelId=channelId,
                                            maxResults=25)

    return response


# Method to insert song to playlist
def insertSongToPlaylist(client, videoId, playlistId):
    songProperties = {'snippet.playlistId': playlistId,
                      'snippet.resourceId.kind': 'youtube#video',
                      'snippet.resourceId.videoId': videoId,
                      'snippet.position': ''}

    response = playlist_items_insert(client, songProperties,
                                     part='snippet', onBehalfOfContentOwner='')

    return response
