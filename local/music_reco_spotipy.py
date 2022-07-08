import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

client_ID='e55d8a1dee8e497892a124b579605f36'
client_SECRET='88d3689f90d446578f5d1b073ede510b'   
redirect_url='http://localhost:8888/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_ID, client_secret= client_SECRET, redirect_uri=redirect_url))

def song_features(sp, track_id, track_name):
    audio_features = sp.audio_features(track_id)
    feature_dict = {
        'name' : track_name,
        'uri' : audio_features[0]['uri'],
        'danceability': audio_features[0]['danceability'],
        'energy' : audio_features[0]['energy'],
        'valence' : audio_features[0]['valence'],
        'liveness' : audio_features[0]['liveness']
    }
    return feature_dict

def get_playlist_features(sp, username='vijthepandaturtle', playlist_id='3fwP4Mfq9BZGEg5OuxTTds'):
    results = sp.user_playlist_tracks(username, playlist_id=playlist_id)
    feature_list = []
    for idx, item in enumerate(results['items']):
        track_name = item['track']['name']
        track_id = item['track']['id']
        feature_list.append(song_features(sp, track_id, track_name))
    return feature_list

def group_songs_category(sp, feature_list):
    #write conditional logic to set values to choose songs for particular moods
    stressful_songs = []
    happy_songs = []
    calm_songs = []
    for feature in feature_list:
        if 0.4 < feature['energy'] < 0.6:
            stressful_songs.append((feature['name'], 'https://open.spotify.com/track/{}'.format(feature['uri'].split(':')[-1])))
        elif feature['energy'] > 0.6:
            happy_songs.append((feature['name'], 'https://open.spotify.com/track/{}'.format(feature['uri'].split(':')[-1])))
        elif 0.3 < feature['energy'] < 0.4:
            calm_songs.append((feature['name'], 'https://open.spotify.com/track/{}'.format(feature['uri'].split(':')[-1])))
    return stressful_songs, happy_songs, calm_songs
        
def choose_song(sp, prediction):
    feature_list = get_playlist_features(sp)
    stressful_songs, happy_songs, calm_songs = group_songs_category(sp, feature_list)
    if prediction=="STRESSED" and stressful_songs:
        return random.sample(stressful_songs, 1)
    elif prediction=="CALM" and calm_songs:
        return random.sample(calm_songs, 1)
    elif prediction=="GOOD-MOOD" and happy_songs:
        return random.sample(happy_songs, 1)

