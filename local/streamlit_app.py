import streamlit as st
import time
import base64
from PIL import Image
import torch
import torch.nn as nn

#local imports
from eeg_local import streamEEGData
from model import GRUModel
from music_reco_spotipy import choose_song

import spotipy
from spotipy.oauth2 import SpotifyOAuth


client_ID='e55d8a1dee8e497892a124b579605f36'
client_SECRET='88d3689f90d446578f5d1b073ede510b'   
redirect_url='http://localhost:8888/callback'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_ID, client_secret= client_SECRET, redirect_uri=redirect_url))

#mapping labels to moods
label_dict= {0:'STRESSED', 1:'CALM', 2:'GOOD-MOOD'}
#instantiating and loading saved model for inference
model = GRUModel(2548, 3, 128, 2)   
model.load_state_dict(torch.load('model.pth'))
model.eval()

st.title("Stress Detection EEG")
prediction = None

song_name = "Recommending a song ..."
song_url = None

streambutton = st.button('Stream Data')
if streambutton:
    #Generating and collecting features from the EEG sensor
    features = streamEEGData(60)
    for feat_vector in features:
        feat_vector = feat_vector.reshape((1,1,2548))
        data_point = torch.FloatTensor(feat_vector)
        output = model(data_point)[0]
        prediction = torch.argmax(output)
        prediction = label_dict[int(prediction)]
        #print(prediction)
    print("Connection closed.")
st.header("Your current mood : {}".format(prediction))
if prediction:
    song_name, song_url = choose_song(sp, prediction)[0]
st.header("Suggested Song :")
st.write("Song Name :", song_name)
st.write("Song URL :", song_url)
