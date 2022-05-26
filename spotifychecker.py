# -*- coding: utf-8 -*-
"""
Created on Thu May 26 12:22:48 2022

@author: Sam Hajnos
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


artists_uris = ["spotify:artist:1294QqYm1VuxxjRiL9M0h9", "spotify:artist:5sWHDYs0csV6RS48xBl0tH"]
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

for artist in arists_uris:
    results = spotify.artist_albums(artist)
    albums = results['items']
    while results['next']:
        results = spotify.next(results)
        albums.extend(results['items'])
    
    
results = spotify.artist_albums(birdy_uri)
albums = results['items']
while results['next']:
    results = spotify.next(results)
    albums.extend(results['items'])

for album in albums:
    print(album['name'])