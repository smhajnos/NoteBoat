# -*- coding: utf-8 -*-
"""
Created on Thu May 26 12:22:48 2022

@author: Sam Hajnos
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import sqlite3

SUCCESS = 0
ARTIST_NOT_FOUND = 1
ALREADY_SUBSCRIBED = 2
OTHER_ERROR = 3


class SpotifyHandler():
    def __init__(self):
        print("Logging in to Spotify", end="...")
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        print("Done.")
        print("Connecting to Data Warehouse", end="...")
        self.dataWarehouse = sqlite3.connect("datawarehouse.db")
        print("Done.")
        self.cursor = self.dataWarehouse.cursor()
        
    def commit(self):
        self.dataWarehouse.commit()
        #push database to backup location?
        
    def clearPending(self):
        cur = self.cursor
        cur.execute("DELETE FROM pending_notifications")
        self.commit()
        
    def check(self): 
        print("Getting subbed artitsts")
        artists = self.getSubbedArtists()
        cur = self.cursor
        for artist in artists:
            #print("Checking artist {}".format(artist))
            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE artist = ?", (artist,))
            #print("Getting artist name")
            artist_name = self.getArtistName(artist)
            #print("Getting albums")
            results = self.spotify.artist_albums(artist)
            #print("Found albums")
            albums = results["items"]
            while results["next"]:
                results = self.spotify.next(results)
                albums.extend(results["items"])
            if albums:  
                for album in albums:
                    if album["album_type"] != "compilation":
                        uri = album["uri"]
                        cur.execute("SELECT COUNT(*) FROM albums WHERE album=:uri", {"uri":uri})
                        count = cur.fetchone()
                        if count[0] == 0:
                            print("New album found: {}".format(album["name"]))
                            url = album["external_urls"]["spotify"]
                            for u in cur.execute("SELECT user FROM subscriptions WHERE artist=:artist",{"artist":artist}):
                                user = u[0]
                            album_name = album["name"]
                            artist_string = self.getArtistsString(album)
                            self.insertPending(user, artist_name, artist_string, uri, album_name, url)
        self.commit()
        print("Done checking")
    def getArtistsString(self, album_data):
        artists = []
        for artist in album_data["artists"]:
            artists.append(artist["name"])            
        str_out = "; ".join(artists)
        return str_out
    
    def getArtistName(self, artist):
        res = self.spotify.artists([artist])
        return res["artists"][0]["name"]
    
    def insertPending(self, user,artist_name, artist_string, album_uri, album_name,url):
        cur = self.cursor
        cur.execute("SELECT COUNT(*) FROM pending_notifications WHERE user=:user AND artist_name=:artist AND artist_string=:artist_string AND album_name=:album_name AND album=:album AND url=:url", {"user":user,"artist":artist_name,"artist_string":artist_string,"album":album_uri,"album_name":album_name,"url":url})        
        res = cur.fetchone()
        if res[0] == 0:
            cur.execute("INSERT INTO pending_notifications (user, artist_name, artist_string, album_name, album, url) VALUES (:user, :artist, :artist_string, :album_name, :album, :url)", {"user":user,"artist":artist_name,"artist_string":artist_string,"album":album_uri,"album_name":album_name,"url":url})        
            self.commit()
        
    def getNextPending(self):
        cur = self.cursor
        cur.execute("SELECT ID, user, artist_name, artist_string, album, album_name, url FROM pending_notifications ORDER BY artist_name ASC, album_name ASC, user ASC")
        res1 = cur.fetchone()
        res2 = {"ID":res1[0], "user":res1[1], "artist_name":res1[2],"artist_string":res1[3],"album":res1[4], "album_name":res1[5], "url":res1[6]}
        return res2
    
    def pendingCount(self):
        cur = self.cursor
        cur.execute("SELECT COUNT(*) FROM pending_notifications")
        res = cur.fetchone()
        return res[0]
    
    def unpend(self, ID, album_uri):
        cur = self.cursor
        cur.execute("DELETE FROM pending_notifications WHERE ID = ?",(ID,))
        self.addAlbum(album_uri=album_uri)
        self.commit()
        
    def getSubbedArtists(self, user=None):
        cur = self.cursor
        artists = []
        if user:
            for row in cur.execute("SELECT DISTINCT artist FROM subscriptions WHERE user = ?",(str(user),)):
                artists.append(row[0])
        else:
            for row in cur.execute("SELECT DISTINCT artist FROM subscriptions"):
                artists.append(row[0])
        return artists
        
    def searchForArtist(self, artist_name):
        print("Searching for artist")
        results = self.spotify.search(q="artist:" + artist_name, type="artist", limit=1)
        items = results["artists"]["items"]
        if len(items) > 0:
            print("Artist found")
            artist = items[0]
            try:
                res = {"name":artist["name"], "image":artist["images"][0]["url"],"uri":artist["uri"]}
            except:
                res = {"name":artist["name"], "image":"","uri":artist["uri"]}
        else:
            print("Artist not found")
            res = {"name":None,"image":"","uri":""}
        return res
    
    def addSubscription(self, user, artist):
        print("Adding subscription")
        cur = self.cursor
        cur.execute("SELECT COUNT(*) FROM subscriptions WHERE artist = ?", (artist,))
        res = cur.fetchone()
        if res[0] == 0:
            self.newArtist(artist)
        cur.execute("SELECT COUNT(*) FROM subscriptions WHERE user = ? AND artist = ?", (str(user), artist))
        res = cur.fetchone()
        if res[0] > 1:
            print("More than one subscription found")
            cur.execute("DELETE FROM subscriptions WHERE user = ? AND artist = ?", (str(user), artist))
            cur.execute("INSERT INTO subscriptions (user, artist) VALUES (?, ?)", (str(user), artist))
            self.commit()
            return ALREADY_SUBSCRIBED
        if res[0] == 1:
            print("Already subscribed")
            return ALREADY_SUBSCRIBED
        if res[0] == 0:
            print("Subscribing")
            cur.execute("INSERT INTO subscriptions (user, artist) VALUES (?, ?)", (str(user), artist))
            self.commit()
            #status_code = self.newArtist(artist)
            return SUCCESS
        
        
    def newArtist(self, artist):
        results = self.spotify.artist_albums(artist)
        albums = results["items"]
        if results["next"]:
            while results["next"]:
                results = self.spotify.next(results)
                albums.extend(results["items"])
            for album in albums:
                self.addAlbum(album_data=album)
            return SUCCESS
        else:
            return ARTIST_NOT_FOUND
        
    
    def addAlbum(self, album_data=None, album_uri=None):
        cur = self.cursor
        album = album_data
        if album:
            if album["album_type"] != "compilation":
                cur.execute("SELECT COUNT(*) FROM albums WHERE album=?", (album["uri"],))
                res = cur.fetchone()
                if res[0] == 0:
                    cur.execute("INSERT INTO albums (album) VALUES (?)", (album["uri"],))
                    print("Inserted album {}".format(album["name"]))
                else:
                    print("Album {} is already in the list".format(album["name"]))
            self.commit()
        elif album_uri:
            cur.execute("SELECT COUNT(*) FROM albums WHERE album=?", (album_uri,))
            res = cur.fetchone()
            if res[0] == 0:
                cur.execute("INSERT INTO albums (album) VALUES (?)", (album_uri,))
                print("Inserted album {}".format(album_uri))
            else:
                print("Album {} is already in the list".format(album_uri))
            self.commit()
        
    def removeSubscription(self, user, artist):
        cur = self.cursor
        cur.execute("DELETE FROM subscriptions WHERE user = ? AND artist = ?", (str(user), artist))
        self.commit()   
        return SUCCESS         
        
    
    def subscribe(self, user, artist_name):
        status_code = OTHER_ERROR
        res = self.searchForArtist(artist_name)
        if res["name"]:
            uri = res["uri"]
            status_code = self.addSubscription(user, uri)
        else:
            status_code = ARTIST_NOT_FOUND
        return (status_code, res)
        
    def unsubscribe(self, user, artist_name):
        status_code = OTHER_ERROR
        res = self.searchForArtist(artist_name)
        if res["name"]:
            uri = res["uri"]
            status_code = self.removeSubscription(user, uri)
        else:
            status_code = ARTIST_NOT_FOUND
        return (status_code, res)
    
    def getSubscriptions(self, user):
        cur = self.cursor
        res = []
        for row in cur.execute("SELECT artist FROM subscriptions WHERE user=?", (str(user), )):
            res.append(self.getArtistName(row[0]))
        return res