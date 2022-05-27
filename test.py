# -*- coding: utf-8 -*-
"""
Created on Thu May 26 13:08:42 2022

@author: sam
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotifychecker

sh = spotifychecker.SpotifyHandler()
def test1():
    birdy_uri = 'spotify:artist:5sWHDYs0csV6RS48xBl0tH'
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    
    results = spotify.artist_albums(birdy_uri, album_type='album')
    albums = results['items']
    while results['next']:
        results = spotify.next(results)
        albums.extend(results['items'])
    
    for album in albums:
        print(album)
        
def test2():
    sh.check()
    print(sh.pendingCount())
    while sh.pendingCount() > 0:
        res = sh.getNextPending()
        print("Hey {user}, new album from {artist_name}, {album_name}. Check it out here: {url}".format(**res))
        sh.unpend(res["ID"],res["album"])
        print(sh.pendingCount())

    
def test3():
    res = sh.spotify.artists(["spotify:artist:5sWHDYs0csV6RS48xBl0tH"])

    print(res["artists"][0]["name"])
    
def test4():
    res = sh.searchForArtist("Grandson")
    print(res)
    sh.addSubscription("145372956304867328", res["uri"])
    
def test5():
    sh.newArtist("spotify:artist:5sWHDYs0csV6RS48xBl0tH")