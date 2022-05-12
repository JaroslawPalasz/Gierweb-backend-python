import traceback
from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response
import json
from flask.wrappers import Response
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
from flask_cors import CORS

#initialize
app = Flask(__name__)


#if dev or production
ENV = 'dev'

app.config['SECRET_KEY'] = 'aaaaah321'
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:halo123@localhost/postgres'

else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dzqabwqmjprnsp:58e6218ed78cd8116fe8f817f8ad6b1c23fe161f94fcb5c7283850b6f291ef36@ec2-176-34-168-83.eu-west-1.compute.amazonaws.com:5432/d93n0bv865ftpf'

app.config['SQLALCHEMY_BINDS'] = {
    'gamestagsfromsteam':      r'sqlite:///C:\Users\palas\gierweb\dbs\gamestagsfromsteam.db'
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
dataBase = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

############ association tables
recommendations = dataBase.Table('recommendations',
    dataBase.Column('gameId', dataBase.Integer, dataBase.ForeignKey('game.id'), primary_key=True),
    dataBase.Column('recommendedGamesId', dataBase.Integer, dataBase.ForeignKey('recommendedgames.id'),
    primary_key=True)
)

taggedGames = dataBase.Table('taggedgames',
    dataBase.Column('gameId', dataBase.Integer, dataBase.ForeignKey('game.id'), primary_key=True),
    dataBase.Column('tagId', dataBase.Integer, dataBase.ForeignKey('tag.id'), primary_key=True)
)
taggedGamesLocal = dataBase.Table('taggedgameslocal',
    dataBase.Column('gamelocalId', dataBase.Integer, dataBase.ForeignKey('gamelocal.id'), primary_key=True),
    dataBase.Column('taglocalId', dataBase.Integer, dataBase.ForeignKey('taglocal.id'), primary_key=True),
    info={'bind_key': 'gamestagsfromsteam'}
)

wishlistedGames = dataBase.Table('wishlistedgames',
    dataBase.Column('gameId', dataBase.Integer, dataBase.ForeignKey('game.id'), primary_key=True),
    dataBase.Column('wishlistId', dataBase.Integer, dataBase.ForeignKey('wishlist.id'), primary_key=True)
)

friendsfriends = dataBase.Table('friendsfriends',
    dataBase.Column('userId', dataBase.Integer, dataBase.ForeignKey('user.id'), primary_key=True),
    dataBase.Column('friendListId', dataBase.Integer, dataBase.ForeignKey('friends.id'), primary_key=True)
)

############ models

#################################################
#       gamestagsfromsteam local database       #
#################################################
############ GAME ############
class GameTaglocal(dataBase.Model):
    __tablename__ = 'gametaglocal'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    gameId = dataBase.Column(dataBase.Integer, nullable=False)
    tagId = dataBase.Column(dataBase.Integer, nullable=False)

    #initializer - all fields except id
    def __init__(self, gameId, tagId):
        self.gameId = gameId
        self.tagId = tagId
        

class GameTaglocalSchema(ma.Schema):
    class Meta:
        model = GameTaglocal
        fields = ('id', 'gameId', 'tagId')

gametaglocal_schema = GameTaglocalSchema()
gamestaglocal_schema = GameTaglocalSchema(many=True)


############ GAME ############
class Gamelocal(dataBase.Model):
    __tablename__ = 'gamelocal'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(200), nullable=False, unique=True)
    publisher = dataBase.Column(dataBase.String(200), nullable=False, unique=False)
    description = dataBase.Column(dataBase.String(9000), nullable=True)
    descriptionShort = dataBase.Column(dataBase.String(3000), nullable=True)
    imagesLink = dataBase.Column(dataBase.String(1000), nullable=True)
    headerImage = dataBase.Column(dataBase.String(1000), nullable=True)
    backgroundImage = dataBase.Column(dataBase.String(1000), nullable=True)
    videoLink = dataBase.Column(dataBase.String(1000), nullable=True)
    steamReviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    reviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    releasedOn = dataBase.Column(dataBase.String(200), nullable=True, default=None)
    comingSoon = dataBase.Column(dataBase.Boolean, nullable=False)
    # game > featuredGames (m-1) featured games parent

    #relations
    # ??? game <> tag (m-m) game can have many tags, tags can belong to many games | tag.games
    taggedGames = dataBase.relationship('Taglocal', secondary=taggedGamesLocal, 
    backref=dataBase.backref('taggedgameslocal', lazy=True))

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

class GamelocalSchema(ma.Schema):
    class Meta:
        model = Gamelocal
        fields = ('id', 'name', 'publisher', 'description', 'descriptionShort', 'imagesLink', 
        'headerImage', 'backgroundImage', 'videoLink', 'steamReviewScore', 'reviewScore',
        'releasedOn', 'comingSoon')

gamelocal_schema = GamelocalSchema()
gameslocal_schema = GamelocalSchema(many=True)


# ############ TAG ############
class Taglocal(dataBase.Model):
    __tablename__ = 'taglocal'
    __bind_key__ = 'gamestagsfromsteam'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(100))

    #relations

    def __init__(self, name):
        self.name = name

class TaglocalSchema(ma.Schema):
    class Meta:
        model = Taglocal
        fields = ('id', 'name')

taglocal_schema = TaglocalSchema()
tagslocal_schema = TaglocalSchema(many=True)


#################################################
#           gierweb heroku database             #
#################################################

############ STEAMCONNECTION ############
class SteamConnection(dataBase.Model):
    __tablename__ = 'steamconnection'
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

############ USER ############
class User(dataBase.Model):
    __tablename__ = 'user'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    public_id = dataBase.Column(dataBase.String(100), unique=True)
    email = dataBase.Column(dataBase.String(100), unique=True)
    passwordHash = dataBase.Column(dataBase.String(100), nullable=False)
    firstName = dataBase.Column(dataBase.String(100), nullable=False)
    lastName = dataBase.Column(dataBase.String(100), nullable=False)
    profilePic = dataBase.Column(dataBase.String(200), nullable=True)
    dateCreated = dataBase.Column(dataBase.DateTime, nullable=False, default=datetime.utcnow)

    #relations
    # user - roles (1-1)
    role = dataBase.relationship('Roles', backref='user', uselist=False)
    # user - friends (1-1)
    friendList = dataBase.relationship('Friends', backref='user', uselist=False)
    # user - wishlist (1-1)
    wishlist = dataBase.relationship('Wishlist', backref='user', uselist=False)
    # user - recommendedGames (1-1)
    recommendedGames = dataBase.relationship('RecommendedGames', backref='user', uselist=False)
    # user < news (1-m)
    news = dataBase.relationship('News', backref='user', lazy=True)
    # user < comment (1-m)
    comments = dataBase.relationship('Comment', backref='user', lazy=True)
    # user < review (1-m)
    reviews = dataBase.relationship('Review', backref='user', lazy=True)

    # user < reviewLikes (1-m)
    reviewLikes = dataBase.relationship('ReviewLikes', backref='user', lazy=True)
    # user < commentLikes (1-m)
    commentLikes = dataBase.relationship('CommentLikes', backref='user', lazy=True)
    # user < gameLikes (1-m)
    gameLikes = dataBase.relationship('GameLikes', backref='user', lazy=True)

    # user <> friendsList (m-m)
    friendListFriends = dataBase.relationship('Friends', secondary=friendsfriends, 
    backref=dataBase.backref('friendsfriends', lazy=True))

    def __init__(self, public_id, email, passwordHash, firstName, lastName, profilePic, dateCreated):
        self.public_id = public_id
        self.email = email
        self.passwordHash = passwordHash
        self.firstName = firstName
        self.lastName = lastName
        self.profilePic = profilePic
        self.dateCreated = dateCreated


class UserSchema(ma.Schema):
    class Meta:
        model = User
        fields = ('public_id', 'email', 'passwordHash', 'firstName', 
        'lastName', 'profilePic', 'dateCreated')

#initialize Schema, multiple Schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)

############ GAME ############
class Game(dataBase.Model):
    __tablename__ = 'game'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(200), nullable=False, unique=True)
    publisher = dataBase.Column(dataBase.String(200), nullable=False, unique=False)
    description = dataBase.Column(dataBase.String(9000), nullable=True)
    descriptionShort = dataBase.Column(dataBase.String(3000), nullable=True)
    imagesLink = dataBase.Column(dataBase.String(1000), nullable=True)
    headerImage = dataBase.Column(dataBase.String(1000), nullable=True)
    backgroundImage = dataBase.Column(dataBase.String(1000), nullable=True)
    videoLink = dataBase.Column(dataBase.String(1000), nullable=True)
    steamReviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    reviewScore = dataBase.Column(dataBase.Integer, nullable=True)
    releasedOn = dataBase.Column(dataBase.String(200), nullable=True, default=None)
    comingSoon = dataBase.Column(dataBase.Boolean, nullable=False)
    # game > featuredGames (m-1) featured games parent
    FeaturedGamesId = dataBase.Column(dataBase.Integer, 
    dataBase.ForeignKey('featuredgames.id'), nullable = True)

    #relations
    # game - gameLikes (1-1)
    # comment < commentLikes (1-m)
    gameLikes = dataBase.relationship('GameLikes', backref='game', lazy=True)
    # game < review (1-m) review can only have 1 game, game can have many reviews, game parent
    reviews = dataBase.relationship('Review', backref='game')
    # game < comment (1-m) game parent
    comments = dataBase.relationship('Comment', backref='game', lazy=True)
    # game <> recommendedGames (m-m) | recommendedgames.recommendations
    recommendedGames = dataBase.relationship('RecommendedGames', secondary=recommendations, 
    backref=dataBase.backref('recommendations', lazy=True))
    # ??? game <> tag (m-m) game can have many tags, tags can belong to many games | tag.games
    taggedGames = dataBase.relationship('Tag', secondary=taggedGames, 
    backref=dataBase.backref('taggedgames', lazy=True))
    # game <> wishlist (m-m) | wishlist.games
    wishlistedGames = dataBase.relationship('Wishlist', secondary=wishlistedGames, 
    backref=dataBase.backref('wishlistedgames', lazy=True))

    #initializer - all fields except id
    def __init__(self, name, publisher, description, descriptionShort,
    imagesLink, headerImage, backgroundImage, videoLink, steamReviewScore, 
    reviewScore, releasedOn, comingSoon, FeaturedGamesId):
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
        self.FeaturedGamesId = FeaturedGamesId

class GameSchema(ma.Schema):
    class Meta:
        model = Game
        fields = ('id', 'name', 'publisher', 'description', 'descriptionShort',
        'imagesLink', 'headerImage', 'backgroundImage', 'videoLink',
        'steamReviewScore', 'reviewScore', 'releasedOn', 'comingSoon',
        'FeaturedGamesId')

game_schema = GameSchema()
games_schema = GameSchema(many=True)


############ REVIEW ############
class Review(dataBase.Model):
    __tablename__ = 'review'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), nullable=False)
    gameId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('game.id'), nullable=False)
    text = dataBase.Column(dataBase.String(9000), nullable=True)
    posted = dataBase.Column(dataBase.DateTime, nullable=False, default=datetime.utcnow)
    isRecommended = dataBase.Column(dataBase.String(100), nullable=False)
    like = dataBase.Column(dataBase.Integer, nullable=True)
    dislike = dataBase.Column(dataBase.Integer, nullable=True)

    #relations
    # review - reviewLikes (1-1)
    # review < reviewLikes (1-m)
    reviewLikes = dataBase.relationship('ReviewLikes', backref='review', lazy=True)

    def __init__(self, userId, gameId, text, posted, isRecommended, like, 
    dislike):
        self.userId = userId
        self.gameId = gameId
        self.text = text
        self.posted = posted
        self.isRecommended = isRecommended
        self.like = like
        self.dislike = dislike

class ReviewSchema(ma.Schema):
    class Meta:
        model = Review
        fields = ('id', 'userId', 'gameId', 'text', 
        'posted', 'isRecommended', 'like', 'dislike')

review_schema = ReviewSchema()
reviews_schema = ReviewSchema(many=True)


############ COMMENT ############
class Comment(dataBase.Model):
    __tablename__ = 'comment'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), nullable=False)
    gameId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('game.id'), nullable=False)
    imageLink = dataBase.Column(dataBase.String(600), nullable=True)
    text = dataBase.Column(dataBase.String(3000), nullable=True)
    posted = dataBase.Column(dataBase.DateTime, nullable=False, default=datetime.utcnow)
    like = dataBase.Column(dataBase.Integer, nullable=True)
    dislike = dataBase.Column(dataBase.Integer, nullable=True)

    #relations
    # comment - commentLikes (1-1)
    # comment < commentLikes (1-m)
    commentLikes = dataBase.relationship('CommentLikes', backref='comment', lazy=True)

    def __init__(self, userId, gameId, imageLink, text, posted, like, dislike):
        self.userId = userId
        self.gameId = gameId
        self.imageLink = imageLink
        self.text = text
        self.posted = posted
        self.like = like
        self.dislike = dislike

class CommentSchema(ma.Schema):
    class Meta:
        model = Comment
        fields = ('id', 'userId', 'gameId', 'imageLink', 
        'text', 'posted', 'like', 'dislike')

review_schema = CommentSchema()
reviews_schema = CommentSchema(many=True)


############ NEWS ############
class News(dataBase.Model):
    __tablename__ = 'news'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), nullable=False)
    imageLink = dataBase.Column(dataBase.String(1000), nullable=True)
    text = dataBase.Column(dataBase.String(9000), nullable=True)
    posted = dataBase.Column(dataBase.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, userId, imageLink, text, posted):
        self.userId = userId
        self.imageLink = imageLink
        self.text = text
        self.posted = posted
        
class NewsSchema(ma.Schema):
    class Meta:
        model = News
        fields = ('id', 'userId', 'imageLink', 'text', 'posted')

news_schema = NewsSchema()
news_many_schema = NewsSchema(many=True)


############ TAG ############
class Tag(dataBase.Model):
    __tablename__ = 'tag'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    name = dataBase.Column(dataBase.String(200), unique=True)


    def __init__(self, name):
        self.name = name

class TagSchema(ma.Schema):
    class Meta:
        model = Tag
        fields = ('id', 'name')

tag_schema = TagSchema()
tags_schema = TagSchema(many=True)


############ WISHLIST ############
class Wishlist(dataBase.Model):
    __tablename__ = 'wishlist'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), unique=True)
    visible = dataBase.Column(dataBase.Integer, nullable=False)

    def __init__(self, userId, visible):
        self.userId = userId
        self.visible = visible

class WishlistSchema(ma.Schema):
    class Meta:
        model = Wishlist
        fields = ('id', 'userId', 'visible')

wishlist_schema = WishlistSchema()
wishlists_schema = WishlistSchema(many=True)


############ FEATURED GAMES ############
class FeaturedGames(dataBase.Model):
    __tablename__ = 'featuredgames'
    id = dataBase.Column(dataBase.Integer, primary_key=True)

    #relations
    # featuredGames < game (1-m)
    games = dataBase.relationship('Game', backref='featuredgames')

    def __init__(self):
        self

class FeaturedGamesSchema(ma.Schema):
    class Meta:
        model = FeaturedGames
        fields = ('id',)

featured_games_schema = FeaturedGamesSchema()
featured_games_many_schema = FeaturedGamesSchema(many=True)


############ RECOMMENDED GAMES ############
class RecommendedGames(dataBase.Model):
    __tablename__ = 'recommendedgames'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), unique=True)

    def __init__(self, userId):
        self.userId = userId

class RecommendedGamesSchema(ma.Schema):
    class Meta:
        model = RecommendedGames
        fields = ('id', 'userId')

recommended_games_schema = RecommendedGamesSchema()
recommended_games_many_schema = RecommendedGamesSchema(many=True)


############ FRIENDS ############
class Friends(dataBase.Model):
    __tablename__ = 'friends'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    parentUserId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), unique=True)
    
    #relations
    # friends <> user (m-m) friendsList can have many users, users can belong to different friends 
    # | friends.users

    def __init__(self, parentUserId):
        self.parentUserId = parentUserId

class FriendsSchema(ma.Schema):
    class Meta:
        model = Friends
        fields = ('id', 'parentUserId')

friends_schema = FriendsSchema()
friends_many_schema = FriendsSchema(many=True)


############ REVIEW LIKES ############
class ReviewLikes(dataBase.Model):
    __tablename__ = 'reviewlikes'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    reviewId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('review.id'))
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'))
    like = dataBase.Column(dataBase.Integer, nullable=True)

    def __init__(self, reviewId, userId, like):
        self.reviewId = reviewId
        self.userId = userId
        self.like = like

class ReviewLikesSchema(ma.Schema):
    class Meta:
        model = ReviewLikes
        fields = ('id', 'reviewId', 'userId', 'like')

reviewlikes_schema = ReviewLikesSchema()
reviewlikes_many_schema = ReviewLikesSchema(many=True)


############ COMMENT LIKES ############
class CommentLikes(dataBase.Model):
    __tablename__ = 'commentlikes'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    commentId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('comment.id'))
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'))
    like = dataBase.Column(dataBase.Integer, nullable=True)

    def __init__(self, commentId, userId, like):
        self.commentId = commentId
        self.userId = userId
        self.like = like

class CommentLikesSchema(ma.Schema):
    class Meta:
        model = CommentLikes
        fields = ('id', 'commentId', 'userId', 'like')

commentlikes_schema = CommentLikesSchema()
commentlikes_many_schema = CommentLikesSchema(many=True)


############ GAME LIKES ############
class GameLikes(dataBase.Model):
    __tablename__ = 'gamelikes'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    gameId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('game.id'))
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'))
    like = dataBase.Column(dataBase.Integer, nullable=True)

    def __init__(self, gameId, userId, like):
        self.gameId = gameId
        self.userId = userId
        self.like = like

class GameLikesSchema(ma.Schema):
    class Meta:
        model = GameLikes
        fields = ('id', 'gameId', 'userId', 'like')

gamelikes_schema = GameLikesSchema()
gamelikes_many_schema = GameLikesSchema(many=True)


############ ROLES ############
class Roles(dataBase.Model):
    __tablename__ = 'roles'
    id = dataBase.Column(dataBase.Integer, primary_key=True)
    userId = dataBase.Column(dataBase.Integer, dataBase.ForeignKey('user.id'), unique=True)
    roleId = dataBase.Column(dataBase.Integer, nullable=False)

    def __init__(self, userId, roleId):
        self.userId = userId
        self.roleId = roleId

class RolesSchema(ma.Schema):
    class Meta:
        model = Roles
        fields = ('id', 'userId', 'roleId')

roles_schema = RolesSchema()
roles_many_schema = RolesSchema(many=True)
#################################################

############ JWT TOKENS
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = str.replace(str(token), 'Bearer ', '')
            pprint(token)
        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], 
            algorithms="HS256")
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            traceback.print_exc()
            return jsonify({'message': 'token is invalid'})

        pprint('all good')
        return f(current_user, *args, **kwargs)
    return decorator
#################################################


#################################################
#                   ENDPOINTS                   #
#################################################

############ USER ####################################
# Register user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data['email']
    firstName = data['firstName']
    lastName = data['lastName']
    dateCreated=datetime.now().strftime("%Y-%m-%d")

    user = User.query.filter_by(email=email).first()
    if(user):
        return Response("{'message':'User with that email already exists'}", 
            status=500, mimetype='application/json')

    hashed_password = generate_password_hash(data['passwordHash'], method='sha256')
    id=str(uuid.uuid4())

    new_user = User(public_id=id, email=email, passwordHash=hashed_password, firstName=firstName, 
    lastName=lastName, profilePic=None, dateCreated=dateCreated)
    dataBase.session.add(new_user)
    dataBase.session.commit()

    user = User.query.filter_by(email=email).first()
    create_wishlist(user.id)
    create_roles(user.id)
    create_recommendedgames(user.id)
    return user_schema.jsonify(new_user)    

# login user
@app.route('/login', methods=['GET', 'POST'])  
def login(): 

    auth = request.get_json()


    if not auth or not auth['email'] or not auth['password']:  
         return Response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})    

    user = User.query.filter_by(email=auth['email']).first()

    if not user:
        return Response('Could not verify2', 401, 
        {'WWW-Authenticate' : 'Basic realm="Login required!"'}) 
       

    if check_password_hash(user.passwordHash, auth['password']):  
        token = jwt.encode(
            {'public_id': user.public_id, 'exp' : datetime.utcnow() + 
            timedelta(hours=24)}, 
        app.config['SECRET_KEY'], algorithm="HS256")
        pprint(token)
       
        return jsonify({'public_id' : user.public_id, 
        'email': user.email, 'firstName': user.firstName, 
        'lastName': user.lastName, 'profilePic': user.profilePic, 
        'dateCreated': user.dateCreated, 'token' : token,}) 

    return Response('could not verify',  401, {'WWW.Authentication': 'Basic realm: "login required"'})


@app.route('/logout', methods=['POST'])
def logout():
    response = make_response({'Message' : 'Logged out'})
    response.set_cookie('token', '', expires=0)
    return response

# Get all users
@app.route('/user', methods=['GET'])
def get_users():
    all_users = User.query.all()
    result = users_schema.dump(all_users)

    for index, value in enumerate(result):
        result[index]['userIdString'] = result[index]['public_id']
        result[index].pop('userId', None)
    return jsonify(result)

# Get current user
@app.route('/user/current', methods=['GET'])
@token_required
def get_current_user(current_user):
    user = User.query.filter_by(public_id=current_user.public_id).first()
    result = user_schema.dump(user)
    return jsonify(result)

# Get specific user
@app.route('/user/<public_id>', methods=['GET'])
def get_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    result = user_schema.dump(user)
    return jsonify(result)

# Get specific user unsafe
@app.route('/user/unsf/<id>', methods=['GET'])
def get_user_unsafe(id):
    user = User.query.filter_by(id=id).first()
    result = user_schema.dump(user)
    return jsonify(result)

# Update specific user
@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def update_user(current_user, public_id):

    user = User.query.filter_by(public_id=public_id).first()

    same_id = 0
    if(current_user.public_id == user.public_id):
        same_id = 1
    if((current_user.role.roleId < 2) and(same_id == 0)):
        return Response("{'message':'No permission to edit other users'}", 
            status=500, mimetype='application/json')

    data = request.get_json()
    user.email = data['email']
    hashed_password = generate_password_hash(data['passwordHash'], method='sha256')
    user.passwordHash = hashed_password
    user.firstName = data['firstName']
    user.lastName = data['lastName']
    user.profilePic = data['profilePic']

    dataBase.session.commit()

    result = user_schema.dump(user)
    return jsonify(result)

# Delete specific user
@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):

    user = User.query.filter_by(public_id=public_id).first()
    
    same_id = 0
    # user/editor and other user
    if(current_user.role.roleId < 2 and public_id != current_user.public_id):
        return Response("{'message':'No permission to delete users'}", 
            status=500, mimetype='application/json')
    # admin and himself
    if(current_user.role.roleId == 2 and public_id == current_user.public_id):
        return Response("{'message':'No permission to delete itself as admin'}", 
            status=500, mimetype='application/json')
    # admin and others, user/edit and itself

    delete_wishlist(current_user, user.wishlist.id)
    delete_roles(user.role.id)
    delete_recommendedgames(user.recommendedGames.id)
    clear_news(user.id)
    clear_gamelikes_user(user.id)
    
    if(same_id == 1):
        pprint('logging out')

    dataBase.session.delete(user)

    dataBase.session.commit()
    return user_schema.jsonify(user)


############ ON STARTUP: GAME (m), TAG (m), FEATUREDGAMES (1)
############ GAME ####################################

# Get games
@app.route('/game', methods=['GET'])
def get_games():
    all_games = Game.query.all()
    result = games_schema.dump(all_games)
    return jsonify(result)

# Get game
@app.route('/game/<id>', methods=['GET'])
def get_game(id):
    game = Game.query.get(id)
    result = game_schema.dump(game)
    return jsonify(result)

# Delete specific game - ONLY AS ADMIN
@app.route('/game/<id>', methods=['DELETE'])
@token_required
def delete_game(current_user, id):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to delete games'}", 
            status=500, mimetype='application/json')
    game = Game.query.get(id)
    
    clear_gamelikes_game(game.id)
    dataBase.session.delete(game)
    dataBase.session.commit()
    return user_schema.jsonify(game)


############ TAG ####################################

# Get all tags
@app.route('/tag', methods=['GET'])
def get_all_tags():
    all_tags = Tag.query.all()
    result = tags_schema.dump(all_tags)
    return jsonify(result)

# Get tag
@app.route('/tag/<id>', methods=['GET'])
def get_tag(id):
    tag = Tag.query.get(id)
    result = tag_schema.dump(tag)
    return jsonify(result)

# Get all tags of game
@app.route('/tag/game/<id>', methods=['GET'])
def get_all_tags_game(id):
    game = Game.query.get(id)
    tags = Tag.query.filter(Tag.taggedgames.any(id=game.id)).all()
    result = tags_schema.dump(tags)
    return jsonify(result)


# Delete tag
# ONLY AS ADMIN
@app.route('/tag/<id>', methods=['DELETE'])
@token_required
def delete_tag(current_user, id):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to delete tags'}", 
            status=500, mimetype='application/json')
    tag = Tag.query.get(id)
    tag.taggedgames = []
    dataBase.session.delete(tag)
    dataBase.session.commit()
    return tag_schema.jsonify(tag)

# modify tag name 
# ONLY AS ADMIN
@app.route('/tag/<id>', methods=['PUT'])
@token_required
def modify_tag(current_user, id):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to modify tag'}", 
            status=500, mimetype='application/json')
    tag = Tag.query.get(id)
    data = request.get_json()
    tag.name = data[0]['name']
    dataBase.session.commit()
    return tag_schema.jsonify(tag)


############ FEATUREDGAMES ####################################
# Create featuredgames object
# ONLY AS ADMIN
# ONLY ONE FEATUREDGAMES OBJ
@app.route('/featuredgames', methods=['POST'])
@token_required
def create_featuredgames(current_user):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to create featuredgames object'}", 
            status=500, mimetype='application/json')
    ftGames = None
    try:
        ftGames = FeaturedGames.query.one()
        if(ftGames is None):
            new_featuredgames = FeaturedGames()
            dataBase.session.add(new_featuredgames)
            dataBase.session.commit()
        else:
            return Response(
                "{'message':'There can only be one existing FeaturedGames object'}", 
                status=500, mimetype='application/json')
    except:
        new_featuredgames = FeaturedGames()
        dataBase.session.add(new_featuredgames)
        dataBase.session.commit()
    return featured_games_schema.jsonify(new_featuredgames)

# Get one featuredgames object
@app.route('/featuredgames', methods=['GET'])
def get_one_featuredgames():
    try:
        ftGames = FeaturedGames.query.one()
    except:
        return Response("{'message':'No featuredgames object'}", 
        status=500, mimetype='application/json')
    ftGames = FeaturedGames.query.one()
    result = featured_games_schema.dump(ftGames)
    return jsonify(result)

# Get games from featuredgames list
@app.route('/featuredgames/games', methods=['GET'])
def get_games_featuredgames():
    try:
        ftGames = FeaturedGames.query.one()
    except:
        return Response("{'message':'No featuredgames object'}", 
        status=500, mimetype='application/json')
    
    result = games_schema.dump(ftGames.games)
    return jsonify(result)

# Get featuredgames object by its id
@app.route('/featuredgames/<id>', methods=['GET'])
def get_featuredgames(id):
    featuredgames = FeaturedGames.query.get(id)
    result = featured_games_schema.dump(featuredgames)
    return jsonify(result)

# Update featuredgames (add games)
# ONLY AS EDITOR
# Request sent as {"id"} of game
@app.route('/featuredgames/games/<id>', methods=['PUT'])
@token_required
def update_featuredgames(current_user, id):
    if(current_user.role.roleId != 1):
        return Response("{'message':'No permission to edit featuredgames list'}", 
            status=500, mimetype='application/json')
    featuredgames = FeaturedGames.query.one()
    data = request.get_json()
    
    try:
        game_id = data['id']
    except KeyError:
        return Response("{'message':'No id field in request data'}", 
        status=500, mimetype='application/json')
    else:
        pprint('data has id field')
        game = Game.query.filter_by(id=game_id).first()
        if(game is not None):
            if(game.FeaturedGamesId == featuredgames.id):
                return Response("{'message':'Game is already on the featuredgames list'}", 
                status=500, mimetype='application/json')
            else:
                featuredgames.games.append(game)
                pprint("good game id: " + str(game.id) + " and game added to featured games")
        else:
            # TODO: if any number of data is invalid, returning error response
            return Response("{'message':'No game with specified id field'}", 
            status=500, mimetype='application/json')
    
    dataBase.session.commit()
    result = featured_games_schema.dump(featuredgames)
   
    return jsonify(result)

# Delete featuredgames list
# ONLY AS ADMIN
@app.route('/featuredgames/<id>', methods=['DELETE'])
@token_required
def delete_featuredgames(current_user, id):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to delete featuredgames object'}", 
            status=500, mimetype='application/json')
    featured_games = FeaturedGames.query.get(id)

    dataBase.session.delete(featured_games)
    dataBase.session.commit()

    return featured_games_schema.jsonify(featured_games)

# Delete games from featuredgames list
# ONLY AS EDITOR
# Request sent as {"id"} of game
@app.route('/featuredgames/games/<id>', methods=['DELETE'])
@token_required
def delete_featuredgames_game(current_user, id):
    if(current_user.role.roleId != 1):
        return Response("{'message':'No permission to edit featuredgames list'}", 
            status=500, mimetype='application/json')
    featured_games = FeaturedGames.query.one()

    data = request.get_json()
    try:
        game_id = data['id']
    except KeyError:
        return Response("{'message':'No id field in request data'}", 
        status=500, mimetype='application/json')
    else:
        pprint('data has id field')
        game = Game.query.filter_by(id=game_id).first()
        if(game is not None):
            if(game.FeaturedGamesId == featured_games.id):
                featured_games.games.remove(game)
                pprint("good game id: " + str(game.id) + " and game deleted from featured games")
            else:
                return Response("{'message':'Game is not on the featuredgames list'}", 
                status=500, mimetype='application/json')
        else:
            return Response("{'message':'No game with specified id field'}", 
            status=500, mimetype='application/json')
    dataBase.session.commit()

    return featured_games_schema.jsonify(featured_games)



############ ON USER CREATION: USER, ROLES (1), WISHLIST (1), RECOMMENDEDGAMES (1), FRIENDS (1)
############ ROLES ####################################
# Create roles
# ONLY WHEN CREATING NEW USER
# @app.route('/user/<id>/roles', methods=['POST'])
def create_roles(id):
    # TODO: check if user exists
    user = User.query.get(id)
    roles = Roles(userId=None, roleId=0)
    user.role = roles
    dataBase.session.add(roles)
    dataBase.session.commit()
    return roles_schema.jsonify(roles)

# Get all roles
@app.route('/roles', methods=['GET'])
def get_all_roles():
    all_roles = Roles.query.all()
    result = roles_many_schema.dump(all_roles)
    for index, value in enumerate(result):
        user = User.query.get(result[index]['userId'])
        result[index]['userIdString'] = user.public_id
        result[index].pop('userId', None)
    return jsonify(result)

# Get role of user
@app.route('/roles/user/<public_id>', methods=['GET'])
def get_user_roles(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    roles = user.role
    result = roles_schema.dump(roles)
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)

# Get role
@app.route('/roles/<id>', methods=['GET'])
def get_roles(id):
    roles = Roles.query.get(id)
    result = roles_schema.dump(roles)
    user = User.query.filter_by(id=result.userId).first()
    return jsonify({'id': result.id,
    'roleId': result.roleId,
    'userIdString': user.public_id})

# modify role of user, can't change own role
# ONLY AS ADMIN
# # Request sent as [{"int"}] of roleId
@app.route('/user/<public_id>/roles', methods=['PUT'])
@token_required
def update_roles(current_user, public_id):
    if(current_user.role.roleId < 2):
        return Response("{'message':'No permission to modify roles'}", 
            status=500, mimetype='application/json')
    user = User.query.filter_by(public_id=public_id).first()
    if(current_user.public_id == user.public_id):
        return Response("{'message':'Can't change own role'}", 
            status=500, mimetype='application/json')
    data = request.get_json()
    roleId = data[0]['roleId']
    if(roleId != 0 or roleId != 1 or roleId != 2):
        return Response("{'message':'Invalid role id'}", 
            status=500, mimetype='application/json')
    roles = user.role
    user.role.roleId = roleId
    dataBase.session.commit()

    result = roles_schema.dump(roles)
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)
    return roles_schema.jsonify(roles)

# Delete role
# ONLY WHILE DELETING USER
# @app.route('/roles/<id>', methods=['DELETE'])
def delete_roles(id):
    roles = Roles.query.get(id)
    user = User.query.filter_by(id=roles.userId).first()
    dataBase.session.delete(roles)
    dataBase.session.commit()


    result = roles_schema.dump(roles)
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)


############ WISHLIST ####################################
# Create wishlist
# ONLY WHEN CREATING NEW USER
# @app.route('/user/<id>/wishlist', methods=['POST'])
def create_wishlist(id):
    user = User.query.get(id)
    wishlist = Wishlist(userId=None, visible=0)
    user.wishlist = wishlist
    dataBase.session.add(wishlist)
    dataBase.session.commit()
    return user_schema.jsonify(wishlist)

# Add games to wishlist
# Request sent as {"id"} of game
@app.route('/user/<public_id>/wishlist', methods=['PUT'])
@token_required
def update_wishlist(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if ((not user) or (current_user.public_id != user.public_id)):
        return Response("{'message':'No user or trying to change wishlist of other user'}", 
            status=500, mimetype='application/json')
    wishlist = user.wishlist
    data = request.get_json()
    try:
        game_id = data['id']
    except KeyError:
        return Response("{'message':'No id field in request data'}", 
        status=500, mimetype='application/json')
    else:
        game = Game.query.filter_by(id=game_id).first()
        if(game is not None):
            for wishlistedGame in wishlist.wishlistedgames:
                if(game.id == wishlistedGame.id):
                    return Response("{'message':'Game is already on user's wishlist'}", 
                    status=500, mimetype='application/json')
            wishlist.wishlistedgames.append(game)
            pprint("good game id: " + str(game.id) + " and game added to wishlist of user " + 
            str(user.id))
        else:
            # TODO: if any number of data is invalid, returning error response
            return Response("{'message':'No game with specified id field'}", 
            status=500, mimetype='application/json')
    dataBase.session.commit()
    return jsonify(data)

# Change wishlist to visible/not
# Request sent as {"visible"}
@app.route('/user/<public_id>/wishlist/visible', methods=['PUT'])
@token_required
def visible_wishlist(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if ((not user) or (current_user.public_id != user.public_id)):
        return Response("{'message':'No user or trying to change wishlist of other user'}", 
            status=500, mimetype='application/json')
    wishlist = user.wishlist
    data = request.get_json()
    try:
        visible = data['visible']
    except KeyError:
        return Response("{'message':'No id field in request data'}", 
        status=500, mimetype='application/json')
    else:
        # change wishlist
        wishlist.visible = visible
        dataBase.session.commit()
    return jsonify(data)

# Get all wishlist
@app.route('/wishlist', methods=['GET'])
def get_all_wishlist():
    all_wishlists = Wishlist.query.all()
    result = wishlists_schema.dump(all_wishlists)
    return jsonify(result)

# Get wishlist
@app.route('/wishlist/<id>', methods=['GET'])
def get_wishlist(id):
    wishlist = Wishlist.query.get(id)
    for game in wishlist.wishlistedgames:
        pprint(game)
    result = wishlist_schema.dump(wishlist)
    return jsonify(result)

# Get wishlist from user ID
@app.route('/wishlist/user/<public_id>', methods=['GET'])
@token_required
def get_wishlist_user(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    wishlist = user.wishlist
    result = wishlist_schema.dump(wishlist)

    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)

# Get all games from user wishlist
@app.route('/user/<public_id>/wishlist', methods=['GET'])
@token_required
def get_all_games_wishlist(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if(user.wishlist.visible == False):
        if(current_user.public_id != user.public_id):
            return Response("{'message':'logged user can only see his wishlist'}", 
                status=500, mimetype='application/json')
    wishlist = user.wishlist
    pprint(Game.query.filter(Game.wishlistedGames.any(id=wishlist.id)).all())
    games = Game.query.filter(Game.wishlistedGames.any(id=wishlist.id)).all()
    result = games_schema.dump(games)
    return jsonify(result)

# Delete wishlist
# ONLY WHILE DELETING USER
# @app.route('/wishlist/<id>', methods=['DELETE'])
# @token_required
def delete_wishlist(current_user, id):
    # TODO: delete all games from user wishlist, should be done already
    wishlist = Wishlist.query.get(id)
    wishlist.wishlistedgames = []
    dataBase.session.delete(wishlist)
    dataBase.session.commit()
    return wishlist_schema.jsonify(wishlist)

# remove games from wishlist by user id
# ONLY OWNER OF WISHLIST
# Request sent as [{"id"}, {"id"}] of different games
@app.route('/user/<public_id>/wishlist', methods=['DELETE'])
@token_required
def delete_wishlist_games(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if(current_user.public_id != user.public_id):
        return Response("{'message':'only logged user can delete games from his wishlist'}", 
            status=500, mimetype='application/json')
    wishlist = user.wishlist
    data = request.get_json()
    try:
        game_id = data['id']
    except KeyError:
        return Response("{'message':'No id field in request data'}", 
        status=500, mimetype='application/json')
    else:
        game = Game.query.filter_by(id=game_id).first()
        if(game is not None):
            # TODO: checking if game is already on user's wishlist
            finish = 0
            for wishlistedGame in wishlist.wishlistedgames:
                if(game.id == wishlistedGame.id):
                    finish = 1
                    user.wishlist.wishlistedgames.remove(game)
                    pprint("good game id: " + str(game.id) + 
                    " and game removed from wishlist of user " + 
                    str(user.id))
                    break
                else:
                    finish = 0
            if(finish == 0):
                return Response("{'message':'No game on specified wishlist'}", 
                status=500, mimetype='application/json')
        else:
            return Response("{'message':'No game with specified id field'}", 
            status=500, mimetype='application/json')
        
    dataBase.session.commit()
    return jsonify(data)



############ RECOMMENDEDGAMES ####################################
# Create recommendedgames
# ONLY WHEN CREATING USER
# @app.route('/user/<id>/recommendedgames', methods=['POST'])
def create_recommendedgames(id):
    user = User.query.get(id)
    recommendedgames = RecommendedGames(userId=None)
    user.recommendedGames = recommendedgames
    dataBase.session.add(recommendedgames)
    dataBase.session.commit()
    return recommended_games_schema.jsonify(recommendedgames)

# Get all recommendedgames
@app.route('/recommendedgames', methods=['GET'])
def get_all_recommendedgames():
    all_recommendedgames = RecommendedGames.query.all()
    result = recommended_games_many_schema.dump(all_recommendedgames)
    return jsonify(result)

# Get recommendedgames
@app.route('/recommendedgames/<id>', methods=['GET'])
def get_recommendedgames(id):
    recommendedgames = RecommendedGames.query.get(id)
    for game in recommendedgames.recommendations:
        pprint(game)
    result = recommended_games_schema.dump(recommendedgames)
    return jsonify(result)

# Get all games from user recommendations
@app.route('/user/<public_id>/recommendedgames', methods=['GET'])
@token_required
def get_all_games_recommended(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if(current_user.public_id != user.public_id):
        return Response("{'message':'logged user can only see his recommendations'}", 
            status=500, mimetype='application/json')
    recommendedgames = user.recommendedGames
    pprint(Game.query.filter(Game.recommendedGames.any(id=recommendedgames.id)).all())
    games = Game.query.filter(Game.recommendedGames.any(id=recommendedgames.id)).all()
    result = games_schema.dump(games)
    return jsonify(result)

# Add games to recommendedgames by user public_id
# Request sent as [{"id"}, {"id"}] of different games
@app.route('/user/<public_id>/recommendedgames', methods=['PUT'])
@token_required
def update_recommendedgames(current_user, public_id):
    user = User.query.get(public_id)
    recommendedgames = user.recommendedGames
    data = request.get_json()
    for index, value in enumerate(data):
        try:
            game_id = data[index]['id']
        except KeyError:
            return Response("{'message':'No id field in request data'}", 
            status=500, mimetype='application/json')
        else:
            game = Game.query.filter_by(id=game_id).first()
            if(game is not None):
                for recommendedGame in recommendedgames.recommendations:
                    if(game.id == recommendedGame.id):
                        return Response("{'message':'Game is already on user's recommendation list'}", 
                        status=500, mimetype='application/json')
                recommendedgames.recommendations.append(game)
                pprint("good game id: " + str(game.id) + " and game added to recommendations of user " + 
                str(user.id))
            else:
                return Response("{'message':'No game with specified id field'}", 
                status=500, mimetype='application/json')
    dataBase.session.commit()
    return jsonify(data)


# remove games from recommendations by user id
# Request sent as [{"id"}, {"id"}] of different games
@app.route('/user/<id>/recommendedgames', methods=['DELETE'])
def delete_recommendedgames_games(id):
    user = User.query.get(id)
    recommendedgames = user.recommendedGames
    data = request.get_json()
    for index, value in enumerate(data):
        try:
            game_id = data[index]['id']
        except KeyError:
            return Response("{'message':'No id field in request data'}", 
            status=500, mimetype='application/json')
        else:
            game = Game.query.filter_by(id=game_id).first()
            if(game is not None):
                finish = 0
                for recommendedGame in recommendedgames.recommendations:
                    if(game.id == recommendedGame.id):
                        finish = 1
                        user.recommendedGames.recommendations.remove(game)
                        pprint("good game id: " + str(game.id) + 
                        " and game removed from recommendedgames of user " + 
                        str(user.id))
                        break
                    else:
                        finish = 0
                if(finish == 0):
                    return Response("{'message':'No game on specified recommendedgames'}", 
                    status=500, mimetype='application/json')
            else:
                return Response("{'message':'No game with specified id field'}", 
                status=500, mimetype='application/json')
    dataBase.session.commit()
    return jsonify(data)

# Delete recommendedgames
# ONLY while deleting user
# @app.route('/recommendedgames/<id>', methods=['DELETE'])
def delete_recommendedgames(id):
    recommendedgames = RecommendedGames.query.get(id)
    recommendedgames.recommendations = []
    dataBase.session.delete(recommendedgames)
    dataBase.session.commit()
    return wishlist_schema.jsonify(recommendedgames)



############ USER ACTIONS (m)
############ COMMENT ####################################

############ REVIEW ####################################

############ NEWS ####################################
# Create news
# ONLY AS EDITOR
@app.route('/user/news', methods=['POST'])
@token_required
def create_news(current_user):
    if((current_user.role.roleId == 0) or (current_user.role.roleId == 2)):
        return Response("{'message':'No permission to add news'}", 
            status=500, mimetype='application/json')
    
    user = User.query.filter_by(public_id=current_user.public_id).first()
    data = request.get_json()
    imageLink = data['imageLink']
    text = data['text']
    posted = datetime.now().strftime("%Y-%m-%d %H:%M")
    news = News(userId=None, imageLink=imageLink, text=text, posted=posted)
    user.news.append(news)
    dataBase.session.add(news)
    dataBase.session.commit()

    result = news_schema.dump(news)
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)

# Get all news
@app.route('/news', methods=['GET'])
def get_all_news():
    all_news = News.query.all()
    result = news_many_schema.dump(all_news)

    for index, value in enumerate(result):
        user = User.query.get(result[index]['userId'])
        result[index]['userIdString'] = user.public_id
        # result[index].pop('userId', None)
    return jsonify(result)

# Get news by its id
@app.route('/news/<id>', methods=['GET'])
def get_news(id):
    news = News.query.get(id)
    
    result = news_schema.dump(news)
    user = User.query.filter_by(id=result.userId).first()

    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)

# Get all news posted by user
@app.route('/user/<public_id>/news', methods=['GET'])
def get_news_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    news = user.news
    result = news_many_schema.dump(news)

    for index, value in enumerate(result):
        result[index]['userIdString'] = user.public_id
        result[index].pop('userId', None)
    return jsonify(result)

# edit news by news id
# ONLY AS EDITOR
@app.route('/news/<id>', methods=['PUT'])
@token_required
def edit_news(current_user, id):
    if(current_user.role.roleId != 1):
        return Response("{'message':'No permission to edit news'}", 
            status=500, mimetype='application/json')
    news = News.query.get(id)
    data = request.get_json()
    imageLink = data['imageLink']
    text = data['text']
    news.imageLink = imageLink
    news.text = text
    dataBase.session.commit()
    result = news_schema.dump(news)

    user = User.query.filter_by(id=news.userId).first()
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)
    
# Delete news (and delete it from news list of user)
# ONLY AS EDITOR/ADMIN
@app.route('/news/<id>', methods=['DELETE'])
@token_required
def delete_news(current_user, id):
    if(current_user.role.roleId == 0):
        return Response("{'message':'No permission to delete news'}", 
            status=500, mimetype='application/json')
    news = News.query.get(id)
    user = User.query.filter_by(id=news.userId).first()
    user.news.remove(news)
    dataBase.session.delete(news)
    dataBase.session.commit()

    result = news_schema.dump(news)
    result.pop('userId', None)
    result['userIdString'] = user.public_id
    return jsonify(result)

# clear news from news list
# ONLY WHEN DELETING USER
# @app.route('/user/<id>/news', methods=['DELETE'])
def clear_news(id):
    user = User.query.get(id)
    for newsObj in user.news:
        dataBase.session.delete(newsObj)
    user.news = []
    dataBase.session.commit()
    return news_many_schema.jsonify(user.news)


############ COMMENTLIKES ####################################



############ GAMELIKES ############
# Create game like - data consists of like and game id
# ONLY AS USER
@app.route('/user/<public_id>/gamelike', methods=['POST'])
@token_required
def create_gamelike(current_user, public_id):
    # Creating game like and adding it to list of user and game
    user = User.query.filter_by(public_id=public_id).first()
    same_id = 0
    if(current_user.public_id == user.public_id):
        same_id = 1
    if(same_id == 0):
        return Response("{'message':'No permission to like/dislike as another user'}", 
            status=500, mimetype='application/json')

    data = request.get_json()
    gameId = data['gameId']
    like = data['like']

    if((like != 0) or (like != 1)):
        return Response("{'message':'Like value must be 0/1'}", 
            status=500, mimetype='application/json')

    game = Game.query.get(gameId)
    for userGameLike in user.gameLikes:
        if (userGameLike.gameId == game.id):
            return Response("{'message':'Game has been already liked or disliked by user'}", 
            status=500, mimetype='application/json')
    gamelike = GameLikes(gameId, user.id, like)
    user.gameLikes.append(gamelike)
    game.gameLikes.append(gamelike)

    dataBase.session.add(gamelike)
    dataBase.session.commit()

    return gamelikes_schema.jsonify(gamelike)

# Edit game like
# ONLY AS USER (who liked it)
@app.route('/user/<public_id>/gamelike', methods=['PUT'])
@token_required
def edit_gamelike(current_user, public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if(current_user.public_id != user.public_id):
        return Response("{'message':'No permission to like/dislike as another user'}", 
            status=500, mimetype='application/json')

    data = request.get_json()
    gameLikeId = data['gameLikeId']
    like = data['like']
    if((like != 0) or (like != 1)):
        return Response("{'message':'Like value must be 0/1'}", 
            status=500, mimetype='application/json')

    gamelike = GameLikes.query.get(gameLikeId)
    if (gamelike is None):
        return Response("{'message':'No gamelike of this id'}", 
            status=500, mimetype='application/json')
    if(gamelike.like == like):
        delete_gamelike(gamelike.id)
    else:
        gamelike.like = like
    dataBase.session.commit()
    return gamelikes_schema.jsonify(gamelike)

# Get gamelikes
@app.route('/gamelike', methods=['GET'])
def get_gamelikes():
    all_gamelikes = GameLikes.query.all()
    result = gamelikes_many_schema.dump(all_gamelikes)
    return jsonify(result)

# Get gamelike
@app.route('/gamelike/<id>', methods=['GET'])
def get_gamelike(id):
    gamelike = GameLikes.query.get(id)
    result = gamelikes_schema.dump(gamelike)
    return jsonify(result)

# Get all gamelikes of given game
@app.route('/gamelike/game/<id>', methods=['GET'])
def get_gamelikes_game(id):
    game = Game.query.get(id)
    result = gamelikes_many_schema.dump(game.gameLikes)
    return jsonify(result)

# Get all gamelikes of given user
@app.route('/gamelike/user/<id>', methods=['GET'])
def get_gamelikes_user(id):
    user = User.query.get(id)
    result = gamelikes_many_schema.dump(user.gameLikes)
    return jsonify(result)

# Delete specific gamelike
@app.route('/gamelike/<id>', methods=['DELETE'])
@token_required
def delete_gamelike(current_user, id):
    user = User.query.filter_by(current_user.public_id).first()
    
    gamelike = GameLikes.query.get(id)
    if(gamelike.userId != user.id):
        return Response("{'message':'No permission to like/dislike as another user'}", 
            status=500, mimetype='application/json')
    
    user = User.query.get(gamelike.userId)
    game = Game.query.get(gamelike.gameId)
    user.gameLikes.remove(gamelike)
    game.gameLikes.remove(gamelike)

    dataBase.session.delete(gamelike)
    dataBase.session.commit()
    return gamelikes_schema.jsonify(gamelike)

# clear gamelikes from gamelikes list by user id
# ONLY WHEN DELETING USER
# @app.route('/gamelike/user/<id>', methods=['DELETE'])
def clear_gamelikes_user(id):
    user = User.query.get(id)
    for gamelike in user.gameLikes:
        game = Game.query.get(gamelike.gameId)
        if(game is not None):
            game.gameLikes.remove(gamelike)
        dataBase.session.delete(gamelike)
    user.gameLikes = []
    dataBase.session.commit()
    return gamelikes_many_schema.jsonify(user.gameLikes)

# clear gamelikes from gamelikes list
# ONLY WHEN DELETING GAME
# @app.route('/gamelike/game/<id>', methods=['DELETE'])
def clear_gamelikes_game(id):
    game = Game.query.get(id)
    for gamelike in game.gameLikes:
        user = User.query.get(gamelike.userId)
        if(user is not None):
            user.gameLikes.remove(gamelike)
        dataBase.session.delete(gamelike)
    game.gameLikes = []
    dataBase.session.commit()
    return gamelikes_many_schema.jsonify(game.gameLikes)



############ REVIEWLIKES ####################################



############ FRIENDS ####################################




@app.route('/steamgamestags/all', methods=['GET'])
@token_required
def test_multiple_dbs(current_user):
    if(current_user.role.roleId != 2):
        return Response("{'message':'No permission'}", 
            status=500, mimetype='application/json')
    gamesLocal = dataBase.session.execute(
        "SELECT * FROM game", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    tagsLocal = dataBase.session.execute(
        "SELECT * FROM tag", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    tagsGamesRelationLocal = dataBase.session.execute(
        "SELECT * FROM taggedgames", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    
    games_result = gameslocal_schema.dump(gamesLocal)
    tags_result = tagslocal_schema.dump(tagsLocal)
    tags_game_result = gamestaglocal_schema.dump(tagsGamesRelationLocal)
    dataBase.session.close()
    
    length = 0
    
    # Creating game
    for index, value in enumerate(games_result):
        name = games_result[index]['name']
        publisher = games_result[index]['publisher']
        description = games_result[index]['description']
        if(len(description) > 9000):
            size = len(description)
            cut = size - 9000
            description = description[:size - cut - 1]
        descriptionShort = games_result[index]['descriptionShort']
        imagesLink = games_result[index]['imagesLink']
        headerImage = games_result[index]['headerImage']
        backgroundImage = games_result[index]['backgroundImage']
        videoLink = games_result[index]['videoLink']
        steamReviewScore = games_result[index]['steamReviewScore']
        reviewScore = games_result[index]['reviewScore']
        releasedOn = games_result[index]['releasedOn']
        comingSoon = games_result[index]['comingSoon']
        new_game = Game(name=name, publisher=publisher,
        description=description, descriptionShort=descriptionShort,
        imagesLink=imagesLink, headerImage=headerImage,
        backgroundImage=backgroundImage, videoLink=videoLink,
        steamReviewScore=steamReviewScore, reviewScore=reviewScore,
        releasedOn=releasedOn, comingSoon=comingSoon,
        FeaturedGamesId=None)
        
        dataBase.session.add(new_game)
        dataBase.session.commit()

        length = length + 1
    pprint('games from gamestagsfromsteam.db: ' + str(length))
    all_games = Game.query.all()
    pprint('games moved to DB: ' + str(len(all_games)))
    length = 0
    # Creating tags
    for index, value in enumerate(tags_result):
        new_tag = Tag(tags_result[index]['name'])
        dataBase.session.add(new_tag)
        dataBase.session.commit()

        length = length + 1
    pprint('tags from gamestagsfromsteam.db: ' + str(length))
    all_tags = Tag.query.all()
    pprint('tags moved to DB: ' + str(len(all_tags)))
    length = 0

    # Connecting games to tags
    for index, value in enumerate(tags_game_result):
        tagFromId = Tag.query.filter_by(
            id=tags_game_result[index]['tagId']).first()
        gameFromId = Game.query.filter_by(
            id=tags_game_result[index]['gameId']).first()

        tagFromId.taggedgames.append(gameFromId)
        dataBase.session.commit()
        length = length + 1
    pprint('taggedgames from gamestagsfromsteam.db: ' + str(length))
    

    games2 = dataBase.session.execute(
        "SELECT * FROM game", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )
    tagsGamesRelation2 = dataBase.session.execute(
        "SELECT * FROM taggedgames", 
    bind=dataBase.get_engine(app, 'gamestagsfromsteam')
    )

    games2_result = games_schema.dump(games2)

    length = 0
    for index, value in enumerate(games2_result):
        length = length + 1
    pprint('games from gamestagsfromsteam.db: ' + str(length))
    length = 0
    for index, value in enumerate(tagsGamesRelation2):
        length = length + 1
    pprint('taggedgames from gamestagsfromsteam.db: ' + str(length))

    return jsonify(all_games)
#################################################



def main(*args, **kwargs):
    #reloading server
    # dataBase.create_all()
    # run server
    app.run()


if __name__ == '__main__':
    main()