#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  seazerbot.py
#  
#  Copyright 2020 jacks <jacks@DESKTOP-MINUT5T>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#####  REFERENCES  #####
###                  ###
#    Ahmad Bilesanmi
#  https://bilesanmiahmad.medium.com/how-to-login-with-twitter-api-using-python-6c9a0f7165c5
#
#    Miguel Garcia
#  https://realpython.com/twitter-bot-python-tweepy/
#
#    Adam Oudad
#  https://medium.com/@adam.oudad/stream-tweets-with-tweepy-in-python-99e85b6df468
#
#    Vik Paruchuri
#  https://www.dataquest.io/blog/streaming-data-python/
#
#    Sanket Gupta
#  https://towardsdatascience.com/a-guide-to-unicode-utf-8-and-strings-in-python-757a232db95c
###                  ###
########################

from requests_oauthlib import OAuth1Session
from io import TextIOWrapper
import os
import json
import tweepy
import base64
import hashlib
import random
import time
import datetime

#user data for twitter
from InitCreds import *
oauth_token        = str(oauth_token)
oauth_token_secret = str(oauth_token_secret)
userID             = int(userID)
API_key            = str(API_key)
API_key_secret     = str(API_key_secret)
userID             = int(userID)
screen_name        = str(screen_name)
        
#initialize random number generator
random.seed()

#this be where the songs are stored
folderName = (r'{}\songs'.format(os.path.dirname(__file__)))
listOfSongs = []

#global variable to check if tweet has been added to queue already
tweetIDList = []
#global variable, sets max length of song quote
tweetLimit = 280

# Authenticate to Twitter
auth = tweepy.OAuthHandler(API_key, API_key_secret)
auth.set_access_token(oauth_token, oauth_token_secret)

# Create API object
api = tweepy.API(auth, wait_on_rate_limit=True,
    wait_on_rate_limit_notify=True)

# ==================================================================== #
# ==================================================================== #
# ==================================================================== #

##THE ACTUAL BEGINNING OF THE BOT##

#-------------------------INITIALIZE-------------------------#

#Initialization of the list of songs available
#params: str songsFolder
#return: arr: str songs
def initSongs(folder = folderName):
    songs = os.listdir(folder)
    for i in range(len(songs)):
        songs[i] = songs[i].replace('.txt', '')
    print(songs)
    return songs

#-------------------------STREAMING-------------------------#

#Class of objects generated by stream, rules in on_status
class MyStreamListener(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        self.me = api.me()

    def on_status(self, status):
        #ignore retweets
        if status.retweeted:
            return
        #ignore self
        if status.user.id == userID:
            return
        #like tweet if mentioned
        api.create_favorite(status.id)
        #add tweet to queue
        tweetText = status.text
        tweetName = status.user.screen_name
        tweetID = status.id_str
        try:
            addToQueue(tweetText, tweetName, tweetID)
        except IOError as err:
            print(err)
        
        print(status.text)
        #send body of tweet to be turned into the title and simpled
        # ~ simpleTitle = simplify(tweet.text)
        # ~ addToQueue(simpleTitle, tweet.user.name)
        # ~ api.create_favorite(tweet.id)

    def on_error(self, status):
        print('Error detected')
        if status_code == 420:
            #diconnects stream
            return False

#Tweepy API stream, listens for terms defined in stream.filter        
def seazerListen():
    tweets_listener = MyStreamListener(api)
    stream = tweepy.Stream(api.auth, tweets_listener)
    stream.filter(track=['@' + screen_name, '#' + screen_name])

#Adds simpled title and username to queue, separated by line.
#params: str title, str name
def addToQueue(title, name, tweetID):
    #check if tweet has already been added
    if not (tweetID in tweetIDList):
        #add new tweet ID and remove old if necessary
        tweetIDList.append(tweetID)
        if len(tweetIDList) > 1:
            del tweetIDList[0]
        #add simple title and uname to text file "userQueue.txt"
        while True:
            try:
                userQueue = open(r'{}\userQueue.txt'.format(os.path.dirname(__file__)), 'a', encoding = 'utf8')
                break
            except IOError:
                print('addToQueue file open already.')
                # ~ #retry
        title.replace('\n', '')
        # ~ userQueue = open(r'{}\{}.txt'.format(os.path.dirname(__file__), 'userQueue'), 'a')
        userQueue.write('{}\n{}\n'.format(title, name))
        print('+++++ {} to userQueue +++++'.format([title, name]))
        userQueue.close()

#-------------------------SENDING-------------------------#

#Sends a tweet from queue
#params: arr: str songs
#return:
def tweetSong(songs):
    random.seed()
    apologize = False
    apologizeUser = ''
    
    #tweet lyrics from title in top of queue
    #userRequest is [title, requester]
    userRequest = pullQueue(songs)
    logRequest = userRequest
    songBody = str(pullSong(userRequest[0]))
    
    #change songBody if pullSong fails, also say sorry
    if songBody == 'randomize':
        apologizeUser = userRequest[1]
        userRequest = pullRandom(songs)
        songBody = str(pullSong(userRequest[0]))
        apologize = True
    altSongBody = songBody
    
    #returns [title, author]
    songData = pullSongData(userRequest[0])
    #returns str
    songBody = tweetCompose(songBody, songData[0])
    
    #send tweet
    api.update_status(songBody)
    print('Sent tweet.')
    print()
    time.sleep(3)
    
    #pulls the ID of the most recent status from SeazerBot
    tweetID = newestStatus()
    
    #send reply, checks if the reply was split
    reply = replyCompose(altSongBody, songData[0], userRequest[1], songData[1])
    
    if reply[1] == '':
        api.update_status(reply[0], in_reply_to_status_id = tweetID)
    else:
        api.update_status(reply[0], in_reply_to_status_id = tweetID)
        sleep(3)
        tweetID = newestStatus()
        api.update_status(reply[1], in_reply_to_status_id = tweetID)
    
    #could not fulfill request, sorry    
    if apologize == True:
        sorryID = newestStatus()
        
        apology = "I'm sorry, @{}, but I failed to meet your request.".format(apologizeUser)
        api.update_status(apology, in_reply_to_status_id = sorryID)
    
    print('Successfully replied.')
    print()
    return logRequest
    
#Pulls request from top of "userQueue.txt" and removes from queue
#params: arr: str songs
#return: array: str simple, str username
def pullQueue(songs):
    #open the queue and read into memory "lines"
    while True:
        try:
            userQueue = open(r'{}\userQueue.txt'.format(os.path.dirname(__file__)), 'r', encoding = 'utf8')
            break
        except IOError:
            print('pullQueue read file open already')
            #retry
    # ~ userQueue = open(r'{}\{}.txt'.format(os.path.dirname(__file__), 'userQueue'), 'r')
    lines = userQueue.readlines()
    userQueue.close()
    #check if queue is empty, if so then return random song
    if len(lines) < 2:
        userQueue = open(r'{}\userQueue.txt'.format(os.path.dirname(__file__)), 'w', encoding = 'utf8')
        userQueue.close()
        return pullRandom(songs)
    else:
        title = lines[0]
        userRequest = lines[1]
        #to remove the top entries we have to rewrite the whole file l m a o
        userQueue = open(r'{}\userQueue.txt'.format(os.path.dirname(__file__)), 'w', encoding = 'utf8')
        #rewrites file, excluding first two lines
        for line in lines[2:]:
            userQueue.write(line)
        userQueue.close()
        simpleTitle = simplify(title)
        
        #find closest match in file list
        simpleTitle = findMatch(simpleTitle, songs)
        if simpleTitle == 'no match':
            return pullQueue
    
    return [simpleTitle, userRequest]
    
#In case of empty queue, pulls a random song from
#D:\jacks\Documents\seazer\songs
#params: arr: str songs
#return: arr: str simple, str SeazerBot
def pullRandom(songs):
    r = random.randint(0, len(songs) - 1)
    randomSong = songs[r]
    #return just the file name
    return [randomSong, screen_name]

#Pulls lines from song
#params: int simpleTitle
#return: str lyrics
def pullSong(simpleTitle):
    print(simpleTitle)
    #just in case.........
    simpleTitle = simpleTitle.replace('.txt', '')
    #how many lines from the song to tweet
    numLines = 3
    jukebox = open(r'{}\{}.txt'.format(folderName, simpleTitle), 'r', encoding = 'utf8')
    #find how many lines are in the song
    lines = jukebox.readlines()
    jukebox.close()
    if len(lines) == 0:
        return("Oops! Someone cracked this world's shell!")
    else:
        justRandomizeIt = 0
        while True:
            #take a few lines from the song
            #select which line to start from, ensuring there is no overflow
            selectLine = random.randint(0, len(lines) - numLines + 1)
            #pull lyrics and include line breaks
            lyrics = ''
            for i in range(2, numLines + 2):
                #hey i have a -1 because this checks the end of the range
                if i == numLines + 2 - 1:
                    endLine = lines[selectLine + i]
                    endLine = endLine.replace('\n', '')
                    lyrics = '{}{}'.format(lyrics, endLine)
                elif i == 2:
                    lyrics = '{}{}'.format(lyrics, lines[selectLine + i])
                else:
                    lyrics = '{}{}'.format(lyrics, lines[selectLine + i])
            
            if justRandomizeIt == 5:
                return 'randomize'
            #check if tweet is okay, else we loop again
            if len(lines[0]) + len(lyrics) + len('"\n\n"\n  -  ') < 280:
                break
            else:
                with open(r'{}\seazerlog.txt'.format(os.path.dirname(__file__)), 'a', encoding='utf-8') as r:
                    r.write('ERROR, TOO LONG:\nThese are the lines:\n{}\n'.format(lyrics))
                
                justRandomizeIt = justRandomizeIt + 1
                
    return lyrics

#Pulls title and translator from song
#params: str simpleTitle
#return: arr: str title, str translator
def pullSongData(simpleTitle):
    jukebox = open(r'{}\{}.txt'.format(folderName, simpleTitle), 'r', encoding = 'utf8')
    songData = str
    lines = jukebox.readlines()
    jukebox.close()
    title = lines[0]
    translator = lines[1]
    songData = ['{}\n'.format(title), '{}\n'.format(translator)]
    return songData
    
#Composes string into tweet for publishing
#params: str tweet, str title, str author
#return: str lyrics
def tweetCompose(tweet, title):
    tweet = tweet.split('\n')
    
    lyrics = ''
    lentweet = len(tweet)
    for i in range(lentweet):
        #end line
        if i == lentweet - 1:
            endLine = tweet[i]
            endLine = endLine.replace('\n', '')
            lyrics = '{} {}'.format(lyrics, endLine)
        #middle lines
        elif 0 < i < lentweet - 1:
            lyrics = '{} {}\n'.format(lyrics, tweet[i])
        #start line
        else:
            lyrics = '{}{}\n'.format(lyrics, tweet[i])
    lyrics = lyrics.replace('\n', '\n\n')    
    lyrics = ('"{}"\n  -  {}'.format(fontify(lyrics), title))
    return lyrics

#Composes reply and breaks if necessary
#params: str body, str title, str requester
#return: arr: str reply, str nextReply
def replyCompose(body, title, requester, author):
    reply = '{}{}Requested by @{}\n\nAlt text:\n{}'.format(title, author, requester, body)
    if len(reply) > 280:
        reply = '{}Requested by @{}'.format(title, requester)
        nextReply = 'Alt text:\n{}'.format(body)
    else:
        nextReply = ''
    return [reply, nextReply]

#Pulls the ID of the most recent status from SeazerBot
#params:
#return: str tweetID
def newestStatus():
    tweetID = api.user_timeline(user_id = userID, count = 1)
    tweetID = str(tweetID)
    start = tweetID.find('\'id\': ')
    end = tweetID.find(', \'id_str\': ')
    tweetID = (tweetID[(start + 6):end])
    return tweetID   

#Compares request text to available files, returns closest match.
#params: str simpleTitle, arr: str songs
#return: str match
def findMatch(simpleTitle, songs):
    #Makes array of sequential strings
    #params: str someString
    #return: arr: str sets
    def getSets(someString):
        sets = []
        holder = ''

        for i in range(len(someString)):
            holder = ''
            for j in range(i, len(someString)):
                holder = holder + someString[j]
                if not holder in sets:
                    sets.append(holder)
        return sets
    
    #check if there is an exact match
    if simpleTitle in songs:
        return simpleTitle
    #check for the nearest match
    else:
        winner = ''
        winScore = 0
        #get all sequential strings inside simpleTitle
        titleSets = getSets(simpleTitle)
        for piece in songs:
            score = 0
            #get all sequential strings inside piece
            #every matching set between simpleTitle and piece
            #adds to score
            for t in titleSets:
                if t in piece:
                    score = score + 1
            #if piece has a higher score, record it
            if score > winScore:
                winner = piece
                winScore = score
                #if max score possible: return that piece
                if winScore == len(titleSets):
                    return winner
        #in case of an empty string perhaps, return for handling
        if winner == '':
            winner = 'no match'
        #return piece with highest score
        return winner

#Changes the font to be fancy.
#params: str body
#return: str body
def fontify(body):
    uniChars = '𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙'
    asciiChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for c in range(len(asciiChars)):
        body = body.replace(asciiChars[c], uniChars[c])
    return body

#Simplifies song title to quickly pull from list of songs
#params: str title
#return: str simpleTitle
def simplify(title):
    asciiChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # ~ badChars = '!?@#*- \n'
    # ~ for c in badChars:
        # ~ title = title.replace(c, '')
        # ~ title = title.lower()
        # ~ title = title.replace('seazerbot', '')
        # ~ title = title.replace(' ','')
        # ~ title = title.replace('\n', '')
    title = title.lower()
    title = title.replace('seazerbot', '')
    for c in title:
        if c not in asciiChars:
            title = title.replace(c, '')
    if title == '':
        title = 'somethingjapanese'
    return title