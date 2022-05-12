# This script is used for getting games from Steam API, only once, 
# and serializing and preparing them so that they can be added
# to separate local database according to given model.
# It is also used for testing connections to multiple databases.

import re
from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response
import json
from flask.wrappers import Request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask_marshmallow import Marshmallow
from flask.templating import render_template
from datetime import datetime, timedelta
import os
from pprint import pp, pprint

from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
from functools import wraps
import sqlite3
import requests
from random import randrange
import string
import time
from bs4 import BeautifulSoup
import traceback

from sqlalchemy import select

#initialize
app = Flask(__name__)

ENV = 'dev'

app.config['SECRET_KEY'] = 'aaaaah321'
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:\Users\palas\gierweb\dbs\gamestagsfromsteam.db'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dzqabwqmjprnsp:58e6218ed78cd8116fe8f817f8ad6b1c23fe161f94fcb5c7283850b6f291ef36@ec2-176-34-168-83.eu-west-1.compute.amazonaws.com:5432/d93n0bv865ftpf'

app.config['SQLALCHEMY_BINDS'] = {
    'localhost':        'postgresql://postgres:halo123@localhost/postgres',
    'herokubackend':        'postgresql://dzqabwqmjprnsp:58e6218ed78cd8116fe8f817f8ad6b1c23fe161f94fcb5c7283850b6f291ef36@ec2-176-34-168-83.eu-west-1.compute.amazonaws.com:5432/d93n0bv865ftpf'
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
dataBase = SQLAlchemy(app)
ma = Marshmallow(app)

############ association tables
taggedGames = dataBase.Table('taggedgames',
    dataBase.Column('gameId', dataBase.Integer, dataBase.ForeignKey('game.id'), primary_key=True),
    dataBase.Column('tagId', dataBase.Integer, dataBase.ForeignKey('tag.id'), primary_key=True),
    info={'bind_key': 'gamestagsfromsteam'}
)
taggedGames2 = dataBase.Table('taggedgames2',
    dataBase.Column('game2Id', dataBase.Integer, dataBase.ForeignKey('game2.id'), primary_key=True),
    dataBase.Column('tag2Id', dataBase.Integer, dataBase.ForeignKey('tag2.id'), primary_key=True),
    info={'bind_key': 'testing'}
)


############ models

#################################################
#       gamestagsfromsteam local database       #
#################################################

############ STEAMCONNECTION ############
class SteamConnection(dataBase.Model):
    __tablename__ = 'steamconnection'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    addedGamesOn = dataBase.Column(dataBase.DateTime, nullable=False, default=datetime.utcnow)
    gamesNumber = dataBase.Column(dataBase.Integer, nullable=False)
    tagsNumber = dataBase.Column(dataBase.Integer, nullable=False)

    def __init__(self, addedGamesOn, gamesNumber, tagsNumber):
        self.addedGamesOn = addedGamesOn
        self.gamesNumber = gamesNumber
        self.tagsNumber = tagsNumber

class SteamConnectionSchema(ma.Schema):
    class Meta:
        model = SteamConnection
        fields = ('id', 'addedGamesOn', 'gamesNumber', 'tagsNumber')

connection_schema = SteamConnectionSchema()

############ GAME ############
class Game(dataBase.Model):
    __tablename__ = 'game'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(200), nullable=False, unique=True)
    publisher = dataBase.Column(dataBase.String(200), nullable=False, unique=False)
    description = dataBase.Column(dataBase.String(200), nullable=True)
    descriptionShort = dataBase.Column(dataBase.String(200), nullable=True)
    imagesLink = dataBase.Column(dataBase.String(100), nullable=True)
    headerImage = dataBase.Column(dataBase.String(100), nullable=True)
    backgroundImage = dataBase.Column(dataBase.String(100), nullable=True)
    videoLink = dataBase.Column(dataBase.String(100), nullable=True)
    steamReviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    reviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    releasedOn = dataBase.Column(dataBase.String(200), nullable=True, default=None)
    comingSoon = dataBase.Column(dataBase.Boolean, nullable=False)
    # game > featuredGames (m-1) featured games parent
    #relations
    # ??? game <> tag (m-m) game can have many tags, tags can belong to many games | tag.games
    taggedGames = dataBase.relationship('Tag', secondary=taggedGames, 
    backref=dataBase.backref('taggedgames', lazy=True))

    def __init__(self, name, publisher, description, descriptionShort, imagesLink, headerImage, 
    backgroundImage, videoLink, steamReviewScore, reviewScore, releasedOn, comingSoon):
        self.name = name
        self.publisher = publisher
        self.description = description
        self.descriptionShort = descriptionShort
        self.imagesLink = imagesLink
        self.headerImage = headerImage
        self.backgroundImage = backgroundImage
        self.videoLink = videoLink
        self.steamReviewScore = steamReviewScore
        self.reviewScore = reviewScore
        self.releasedOn = releasedOn
        self.comingSoon = comingSoon

class GameSchema(ma.Schema):
    class Meta:
        model = Game
        fields = ('id', 'name', 'publisher', 'description', 'descriptionShort', 'imagesLink', 
        'headerImage', 'backgroundImage', 'videoLink', 'steamReviewScore', 'reviewScore',
        'releasedOn', 'comingSoon')

game_schema = GameSchema()
games_schema = GameSchema(many=True)


############ TAG ############
class Tag(dataBase.Model):
    __tablename__ = 'tag'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    # TODO: tag name unique just like user email
    name = dataBase.Column(dataBase.String(100))

    def __init__(self, name):
        self.name = name

class TagSchema(ma.Schema):
    class Meta:
        model = Tag
        fields = ('id', 'name')

tag_schema = TagSchema()
tags_schema = TagSchema(many=True)
#################################################


#################################################
#           testing local database              #
#################################################

############ GAME ############
class Game2(dataBase.Model):
    __tablename__ = 'game2'
    __bind_key__ = 'testing'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(200), nullable=False, unique=True)
    publisher = dataBase.Column(dataBase.String(200), nullable=False, unique=False)
    description = dataBase.Column(dataBase.String(200), nullable=True)
    descriptionShort = dataBase.Column(dataBase.String(200), nullable=True)
    imagesLink = dataBase.Column(dataBase.String(100), nullable=True)
    headerImage = dataBase.Column(dataBase.String(100), nullable=True)
    backgroundImage = dataBase.Column(dataBase.String(100), nullable=True)
    videoLink = dataBase.Column(dataBase.String(100), nullable=True)
    steamReviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    reviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    releasedOn = dataBase.Column(dataBase.String(200), nullable=True, default=None)
    comingSoon = dataBase.Column(dataBase.Boolean, nullable=False)
    # game > featuredGames (m-1) featured games parent
    #relations
    # ??? game <> tag (m-m) game can have many tags, tags can belong to many games | tag.games
    taggedGames = dataBase.relationship('Tag2', secondary=taggedGames2, 
    backref=dataBase.backref('taggedgames2', lazy=True))

    def __init__(self, name, publisher, description, descriptionShort, imagesLink, headerImage, 
    backgroundImage, videoLink, steamReviewScore, reviewScore, releasedOn, comingSoon):
        self.name = name
        self.publisher = publisher
        self.description = description
        self.descriptionShort = descriptionShort
        self.imagesLink = imagesLink
        self.headerImage = headerImage
        self.backgroundImage = backgroundImage
        self.videoLink = videoLink
        self.steamReviewScore = steamReviewScore
        self.reviewScore = reviewScore
        self.releasedOn = releasedOn
        self.comingSoon = comingSoon

class Game2Schema(ma.Schema):
    class Meta:
        model = Game2
        fields = ('id', 'name', 'publisher', 'description', 'descriptionShort', 'imagesLink', 
        'headerImage', 'backgroundImage', 'videoLink', 'steamReviewScore', 'reviewScore',
        'releasedOn', 'comingSoon')

game2_schema = Game2Schema()
games2_schema = Game2Schema(many=True)


############ TAG ############
class Tag2(dataBase.Model):
    __tablename__ = 'tag2'
    __bind_key__ = 'testing'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(100))

    def __init__(self, name):
        self.name = name

class Tag2Schema(ma.Schema):
    class Meta:
        model = Tag2
        fields = ('id', 'name')

tag2_schema = Tag2Schema()
tags2_schema = Tag2Schema(many=True)
#################################################


############ functions used for data (games) preparation
# and for moving data to local database

def create_tags2(name, id):
    try:
        reqGame = requests.get('https://store.steampowered.com/app/' + id)
        soup = BeautifulSoup(reqGame.content, 'html.parser')
        soupd = soup.find_all('a', class_="app_tag")
        len0 = 0
        allTags = ""
        if(not soupd):
            pprint('fail getting tags for game ' + id)
        else:
            for tagSoup in soupd:
                len0 = len0 + 1
                tagName = tagSoup.get_text()
                tagNameStr = str(tagName)
                tagNameStr = tagNameStr.strip()

                tagDB = Tag.query.filter_by(name=tagNameStr).first()
                if (tagDB is None):
                    new_tag = Tag(name=tagNameStr)
                    dataBase.session.add(new_tag)
                    dataBase.session.commit()
                
                game = Game.query.filter_by(name=name).first()
                tagDB = Tag.query.filter_by(name=tagNameStr).first()

                gameTagged = False
                for taggedGame in tagDB.taggedgames:
                    if(game.id == taggedGame.id):
                        gameTagged = True
                        break
                        # game is already tagged

                if(gameTagged == False):
                    tagDB.taggedgames.append(game)

                allTags = allTags + " " + tagNameStr + " "
            print('tags for game ' + id)
            pprint(allTags)
            pprint("\n")
    except:
        pprint('fail getting tags for game ' + str(name) + " " + str(id))
        print('Waiting')
        traceback.print_exc()
        time.sleep(360)

    dataBase.session.commit()
    return

def create_game2(data, id):
    name = data['name']
    publisher = ""
    developer = ""
    description = ""
    descriptionShort = ""
    headerImage = ""
    backgroundImage = ""
    try:
        if((len(data['publishers'])) == 1 and (data['publishers'][0] == '')):
            for index, value in enumerate(data['developers']):
                publisher = publisher + value + ", "
            # publisher = developer
        else:
            for index, value in enumerate(data['publishers']):
                publisher = publisher + value + ", "
    except KeyError:
        pprint('No publisher or developer')
    
    description = data['about_the_game']
    descriptionShort = data['short_description']
    RE2 = re.compile(u'(<(?s)(.*?)>)', re.UNICODE)
    description.strip(u'\u200b')
    description = RE2.sub('', description)
    descriptionShort.strip(u'\u200b')
    descriptionShort = RE2.sub('', descriptionShort)
    
    headerImage = data['header_image']
    backgroundImage = data['background']

    # images and videos
    imagesLink = ""
    imagesLinkFull = ""
    videoLink = ""
    videoLinkFull =""

    releasedOn = data['release_date']['date']
    comingSoon = data['release_date']['coming_soon']

    #screenshots
    try:
        if(data['screenshots'] is None):
            imagesLink=""
            imagesLinkFull=""
        else:
            for index, value in enumerate(data['screenshots']):
                #path_thumbnail+path_full path_thumbnail+path_full
                imagesLink = imagesLink + data['screenshots'][index]['path_thumbnail']
                imagesLink = imagesLink + "+" + data['screenshots'][index]['path_full'] + " "
                imagesLinkFull = imagesLink
                if(index == 3):
                    break
        # videos
        if(data['movies'] is None):
            videoLink=""
            videoLinkFull=""
        else:
            for index, value in enumerate(data['movies']):
                #webm480+webmmax webm480+webmmax
                videoLink = videoLink + data['movies'][index]['webm']['480']
                videoLink = videoLink + "+" + data['movies'][index]['webm']['max'] + " "
                videoLinkFull = videoLink
                if(index == 3):
                    break
    except KeyError:
        videoLink=""
        videoLinkFull=""

    # reviews
    steamReviewScore=0
    reviewScore=0
    req0 = requests.get('https://store.steampowered.com/appreviews/' + id + '?json=1&language=all')
    data0 = req0.json()
    
    if((data0['success'] == True) and (comingSoon is False) and 
    (data0['query_summary']['total_reviews'] > 0)):
        steamReviewScore = int((float(data0['query_summary']['total_positive']) / 
        float((data0['query_summary']['total_reviews']))) * 100)
    else:
        steamReviewScore = -1
    
    new_game = Game(name=name, publisher=publisher, description=description, 
    descriptionShort=descriptionShort, imagesLink=imagesLinkFull, headerImage=headerImage, 
    backgroundImage=backgroundImage, videoLink=videoLinkFull, steamReviewScore=steamReviewScore, 
    reviewScore=reviewScore, releasedOn=releasedOn, comingSoon=comingSoon)

    dataBase.session.add(new_game)
    dataBase.session.commit()

    # tags
    create_tags2(name, id)

    return game_schema.jsonify(new_game)  

def sort_game_date(steamDate):
    # steamDate = "1 Aug, 2012"
    steamDate = steamDate.replace(',', '')
    listt = steamDate.split()

    # day
    if(len(listt[0]) == 1):
        # add zero
        listt[0] = '0' + listt[0]

    # month
    #Dec
    if(listt[1] == 'Dec'):
        listt[1] = '12'
    #Nov
    elif(listt[1] == 'Nov'):
        listt[1] = '11'
    #Oct
    elif(listt[1] == 'Oct'):
        listt[1] = '10'
    #Sep
    elif(listt[1] == 'Sep'):
        listt[1] = '09'
    #Aug
    elif(listt[1] == 'Aug'):
        listt[1] = '08'
    #Jul
    elif(listt[1] == 'Jul'):
        listt[1] = '07'
    #Jun
    elif(listt[1] == 'Jun'):
        listt[1] = '06'
    #May
    elif(listt[1] == 'May'):
        listt[1] = '05'
    #Apr
    elif(listt[1] == 'Apr'):
        listt[1] = '04'
    #Mar
    elif(listt[1] == 'Mar'):
        listt[1] = '03'
    #Feb
    elif(listt[1] == 'Feb'):
        listt[1] = '02'
    #Jan
    elif(listt[1] == 'Jan'):
        listt[1] = '01'

    date = datetime.now().strftime("%Y-%m-%d")

    # year-month-day
    stringToDateTime = listt[2] + '-' + listt[1] + '-' + listt[0]
    dtobj = datetime.fromisoformat(stringToDateTime)

    return dtobj

@app.route('/testing/gamelength', methods=['GET'])
def test_length():
    games = dataBase.session.execute(
        "SELECT * FROM game", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    games_result = games_schema.dump(games)
    for index, value in enumerate(games_result):
        if(games_result[index]['name'] == "Mad Zombie"):
            description = games_result[index]['description']
            if(len(description) > 10000):
                size = len(description)
                cut = size - 10000
                description = description[:size - cut - 1]
            pprint(len(description))

    return jsonify(games_result)

@app.route('/testing/steamgamestags', methods=['GET'])
def test_multiple_dbs():

    #### BELOW WORKS, beware of SQLALCHEMY versions (using 1.3.24 downgrade)
    games = dataBase.session.execute(
        "SELECT * FROM game", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    tags = dataBase.session.execute(
        "SELECT * FROM tag", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    tagsGamesRelation = dataBase.session.execute(
        "SELECT * FROM taggedgames", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    
    games_result = games_schema.dump(games)
    tags_result = tags_schema.dump(tags)
    
    length = 0
    
    # Creating game
    for index, value in enumerate(games_result):
        sessionTesting = dataBase.create_scoped_session(
            options={'bind': dataBase.get_engine(app, 'testing')}
        )
        new_game = Game2(games_result[index]['name'], games_result[index]['publisher'],
        games_result[index]['description'], games_result[index]['descriptionShort'],
        games_result[index]['imagesLink'], games_result[index]['headerImage'],
        games_result[index]['backgroundImage'], games_result[index]['videoLink'],
        games_result[index]['steamReviewScore'], games_result[index]['reviewScore'],
        games_result[index]['releasedOn'], games_result[index]['comingSoon'])
        
        sessionTesting.add(new_game)
        sessionTesting.commit()
        length = length + 1
    pprint('games from gamestagsfromsteam.db: ' + str(length))
    all_games = Game2.query.all()
    pprint('games moved to testing.db: ' + str(len(all_games)))
    length = 0
    # Creating tags
    for index, value in enumerate(tags_result):
        sessionTesting = dataBase.create_scoped_session(
            options={'bind': dataBase.get_engine(app, 'testing')}
        )
        new_tag = Tag2(tags_result[index]['name'])
        sessionTesting.add(new_tag)
        sessionTesting.commit()
        length = length + 1
    pprint('tags from gamestagsfromsteam.db: ' + str(length))
    all_tags = Tag2.query.all()
    pprint('tags moved to testing.db: ' + str(len(all_tags)))
    length = 0
    # Connecting games to tags
    for index, value in enumerate(tagsGamesRelation):
        sessionTesting = dataBase.create_scoped_session(
            options={'bind': dataBase.get_engine(app, 'testing')}
        )
        tagFromId = sessionTesting.query(Tag2).filter_by(id=value[1]).first()
        gameFromId = sessionTesting.query(Game2).filter_by(id=value[0]).first()
        # tagDB.taggedgames.append(game)
        tagFromId.taggedgames2.append(gameFromId)
        sessionTesting.commit()
        length = length + 1
    pprint('taggedgames from gamestagsfromsteam.db: ' + str(length))
    

    games2 = dataBase.session.execute(
        "SELECT * FROM game2", 
    bind=dataBase.get_engine(app, 'testing')
    )
    tagsGamesRelation2 = dataBase.session.execute(
        "SELECT * FROM taggedgames2", 
    bind=dataBase.get_engine(app, 'testing')
    )

    games2_result = games_schema.dump(games2)

    length = 0
    for index, value in enumerate(games2_result):
        length = length + 1
    pprint('games2 from testing.db: ' + str(length))
    length = 0
    for index, value in enumerate(tagsGamesRelation2):
        length = length + 1
    pprint('taggedgames2 from testing.db: ' + str(length))

    result = games_schema.dump(games)
    return jsonify(result)

@app.route('/steam/steamgamestags', methods=['GET'])
def prepare_steam_games():
    addedGamesOn = datetime.now()
    req = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/?')
    data = json.loads(req.content)
    data = data['applist']['apps']
    temp = ""
    badGame1 = "Artwork"
    badGame2 = "Anime"
    badGame3 = "Hentai"
    badGame4 = "DLC"
    badGame5 = "Romance"
    badGame6 = "Schoolgirl"
    badGame7 = "Demo"
    badGame8 = "Artbook"
    badGame9 = "Soundtrack"
    badGame10 = "VR"
    badGame11 = "Wallpapers"
    badGame12 = "OST"
    badGame13 = "Extra"
    badGame14 = "Playtest"

    length = 0
    for index, value in enumerate(data):
        length = length + 1
    pprint('length before cuts: ' + str(length))

    # Cutting ugly games
    length = 0
    for index, value in enumerate(data):
        temp = str(data[index]['name'])
        if ((badGame1 in temp) or (badGame2 in temp) or (badGame3 in temp) or (badGame4 in temp)
        or (badGame5 in temp) or (badGame6 in temp) or (badGame7 in temp) or (badGame8 in temp)
        or (badGame9 in temp) or (badGame10 in temp) or (badGame11 in temp) or (badGame12 in temp)
        or (badGame13 in temp) or (badGame14 in temp) or (temp == "")):
            data.remove(value)
        length = length + 1
    pprint('length after first cuts: ' + str(length))

    # Cutting ugly non-Ascii names
    RE = re.compile(u'[⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]', re.UNICODE)
    ok = 1
    for index, value in enumerate(data):
        temp = str(data[index]['name'])
        if(not re.findall(RE, temp)):
            ok
        else:
            data.remove(value)

    # Cutting games randomly (down to around 5k games)
    del data[::2]
    del data[::2]
    del data[::2]
    del data[::3]
    length = 0
    for index, value in enumerate(data):
        length = length + 1
    pprint('length after :2 :2 :2 :3 cuts: ' + str(length))

    # # Getting all games (7k+ requests)
    fails = 0
    notGamesLeft = 0
    game_id = 0
    url = 'http://store.steampowered.com/api/appdetails?appids=' + str(game_id)
    i = 0
    while i < len(data):
        game_id = str(data[i]['appid'])
        try:
            print('now on index ' + str(i) + ' and game_id ' + str(game_id))
            url = 'http://store.steampowered.com/api/appdetails?appids=' + str(game_id)
            reqGame = requests.get(url)
            dataGame = reqGame.json()
            try:
                gamefromDBName = dataGame[game_id]['data']['name']
                gamefromDB = Game.query.filter_by(name=gamefromDBName).first()
            except KeyError:
                fails = fails + 1
                pprint('fail: ' + url)
                data.remove(data[i])
                i = i - 1
            else:
                if((dataGame[game_id]['success'] == True) and (not gamefromDB)):
                    if(dataGame[game_id]['data']['type'] == "game"):
                        create_game2(dataGame[game_id]['data'], game_id)
                    else:
                        notGamesLeft = notGamesLeft + 1
                        pprint('not a game: ' + game_id)
                        data.remove(data[i])
                        i = i - 1
                else:
                    fails = fails + 1
                    pprint('fail: ' + url)
                    data.remove(data[i])
                    i = i - 1
        except TypeError:
            pprint('Waiting for a game: ' + str(game_id))
            time.sleep(360)
            i = i
        else:
            i = i + 1

    pprint('fails: ' + str(fails))
    pprint('notGamesLeft: ' + str(notGamesLeft))

    length = 0
    for index, value in enumerate(data):
        length = length + 1
    pprint('length after adding to DB ' + str(length))

    addedGamesOn
    all_games = Game.query.all()
    all_tags = Tag.query.all()
    new_steam_connection = SteamConnection(addedGamesOn, len(all_games), len(all_tags))
    dataBase.session.add(new_steam_connection)
    dataBase.session.commit()
    
    pprint('Finished getting games from steam api')

    return jsonify(data)
#################################################

def main(*args, **kwargs):
    app.run()


if __name__ == '__main__':
    main()