#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
import time
import datetime

#for uploading photo:
#from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
app = Flask(__name__)
app.secret_key = "secret9032Key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='project_part_2_schema',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)



#Define a route to hello function
@app.route('/')
def hello(): 
    return render_template('index.html')

@app.route('/general',  methods=['GET', 'POST'])
def general():
    cursor = conn.cursor();
    if(request.method=="POST"):
        session['profiles'] = request.form.get('general')
		# Get data from submitted form
		# Query the Database
        searching = """SELECT DISTINCT * FROM album CROSS JOIN artist CROSS JOIN user CROSS JOIN song WHERE artist.fname LIKE '%%%s%%'  
        OR song.title LIKE  '%%%s%%'  OR album.albumName LIKE '%%%s%%' """ % (session['profiles'],session['profiles'],session['profiles'])
        #print(searching)
        cursor.execute(searching)
        #print('Stopped')
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        return render_template("general.html", data=data)
    else:
        cursor.close()
        return render_template('general.html', error='Search Not Found')

#Define route for login
@app.route('/login')
def login():
    return render_template('index.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    ts = time.time()
    lastlogin = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
  

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s and pwd = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    #cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        query = 'UPDATE user SET lastlogin = %s WHERE username = %s'
        cursor.execute(query, (lastlogin, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    ts = time.time()
    lastlogin = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    nickname = request.form['nickname'] 
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO user VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, fname, lname, lastlogin, nickname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = """SELECT reviewSong.username, reviewSong.songID, reviewText, reviewDate, song.title FROM friend, reviewSong, user, song 
    WHERE ((friend.user1 = %s AND friend.user2 = reviewSong.username) OR (friend.user2 = %s AND friend.user1 = reviewSong.username)) 
    AND acceptStatus = 'Accepted' AND user.username = %s AND user.lastlogin < reviewSong.reviewDate AND song.songID = reviewSong.songID UNION 
    SELECT reviewSong.username, reviewSong.songID, reviewText, reviewDate, song.title FROM follows, reviewSong, user, song WHERE (follows.follower = %s 
    AND follows.follows = reviewSong.username) AND user.username = %s AND user.lastlogin < reviewSong.reviewDate AND song.songID = reviewSong.songID"""
    cursor.execute(query, (user, user, user, user, user))
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, reviewing=data) 

@app.route('/album_feed')
def album_feed():
    user = session['username']
    cursor = conn.cursor();
    query = """SELECT reviewAlbum.username, reviewAlbum.albumID, reviewText, reviewDate, album.albumName FROM friend, reviewAlbum, user, album
    WHERE ((friend.user1 = %s AND friend.user2 = reviewAlbum.username) OR (friend.user2 = %s AND friend.user1 = reviewAlbum.username)) 
    AND acceptStatus = 'Accepted' AND user.username = %s AND user.lastlogin < reviewAlbum.reviewDate AND album.albumID = reviewAlbum.albumID UNION 
    SELECT reviewAlbum.username, reviewAlbum.albumID, reviewText, reviewDate, album.albumName FROM follows, reviewAlbum, user, album WHERE (follows.follower = %s 
    AND follows.follows = reviewAlbum.username) AND user.username = %s AND user.lastlogin < reviewAlbum.reviewDate AND album.albumID = reviewAlbum.albumID"""
    cursor.execute(query, (user, user, user, user, user))
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, reviewing=data) 

@app.route('/artist_feed')
def artist_feed():
    user = session['username']
    cursor = conn.cursor();
    query = """SELECT DISTINCT song.title, song.releaseDate, artist.fname, userFanOfArtist.artistID 
    FROM (artistPerformsSong NATURAL JOIN userFanOfArtist NATURAL JOIN artist NATURAL JOIN song) JOIN user
    WHERE song.releaseDate > user.lastlogin AND userFanOfArtist.username = %s"""
    cursor.execute(query, (user))
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, data=data) 

@app.route('/user_profile', methods=['GET', 'POST'])
def profile():
    #grabs information from the forms
    username = session['username']
    ts = time.time()
    updatedAt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    acceptStatus = request.form.get('acceptStatus')
    user1 = request.form.get('requestSentBy')
    print(user1)
    #print(acceptStatus)
    if(acceptStatus):
        cursor = conn.cursor();
        query = "UPDATE friend SET acceptStatus = '%s', updatedAt = '%s' WHERE user2 = '%s' AND requestSentBy = '%s'" % (acceptStatus, updatedAt, username, user1)
        print(query)
        cursor.execute(query)
        conn.commit()
    #cursor used to send queries
    cursor = conn.cursor()
    query = "SELECT * FROM friend WHERE acceptStatus = 'Pending' AND user2 = '%s' " % (username)
    cursor.execute(query)
    conn.commit()
    #stores the results in a variable
    data = cursor.fetchall()
    print(data)
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        return render_template('user_profile.html', friends=data)
    else:
        #returns an error message to the html page
        error = ''
        cursor.close()
        return render_template('user_profile.html', error=error)

# Create Search Function
@app.route('/search',  methods=['GET', 'POST'])
def search():
    cursor = conn.cursor();
    if(request.method=="POST"):
        session['profiles'] = request.form.get('searched')
		# Get data from submitted form
		# Query the Database
        searching = """SELECT DISTINCT * FROM album CROSS JOIN artist CROSS JOIN user CROSS JOIN song WHERE artist.fname LIKE '%%%s%%'  
        OR song.title LIKE  '%%%s%%'  OR album.albumName LIKE '%%%s%%'  OR user.username LIKE  '%%%s%%'  """ % (session['profiles'],session['profiles'],session['profiles'],session['profiles'])
        #print(searching)
        cursor.execute(searching)
        #print('Stopped')
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        return render_template("search.html", data=data)
    else:
        cursor.close()
        return render_template('search.html', error='Search Not Found')
    
@app.route('/rsearch',  methods=['GET', 'POST'])
def rsearch():
    cursor = conn.cursor();
    if(request.method=="POST"):
        session['profiles'] = request.form.get('searched')
		# Get data from submitted form
		# Query the Database
        searching = """SELECT DISTINCT * FROM reviewSong CROSS JOIN reviewAlbum WHERE reviewAlbum.reviewText LIKE '%%%s%%' 
        OR reviewSong.reviewText LIKE '%%%s%%' """ % (session['profiles'])
        cursor.execute(searching)
        #print('Stopped')
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        return render_template("search.html", data=data)
    else:
        cursor.close()
        return render_template('search.html', error='Search Not Found')
    
@app.route('/rSprofile',  methods=['GET', 'POST'])
def rSprofile():
    cursor = conn.cursor();
    songs = """SELECT DISTINCT username, songID, reviewText, reviewDate, title FROM reviewSong NATURAL JOIN song 
    WHERE reviewText LIKE  '%%%s%%' """ % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('rs_profile.html', reviewing=data)

@app.route('/rAprofile',  methods=['GET', 'POST'])
def rAprofile():
    cursor = conn.cursor();
    songs = """SELECT DISTINCT username, albumID, reviewText, reviewDate, albumName FROM reviewAlbum NATURAL JOIN album 
    WHERE reviewText LIKE  '%%%s%%' """ % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('ra_profile.html', reviewing=data)

@app.route('/song_profile', methods=['GET', 'POST'] )
def song_profile():
    #print(session['profiles'])
    cursor = conn.cursor();
    songs = """SELECT DISTINCT song.title, artistPerformsSong.artistID, songInAlbum.albumID, songGenre.genre, song.releaseDate, song.songURL,
    reviewSong.username, reviewSong.reviewText, reviewSong.reviewDate, rateSong.username, rateSong.stars, rateSong.ratingDate FROM song
    NATURAL JOIN artistPerformsSong NATURAL JOIN reviewSong NATURAL JOIN rateSong NATURAL JOIN songGenre NATURAL JOIN 
    songInAlbum WHERE song.title = '%s'""" % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('song_profile.html', reviewing=data)

@app.route('/generalsong', methods=['GET', 'POST'] )
def generalsong():
    #print(session['profiles'])
    cursor = conn.cursor();
    songs = """SELECT DISTINCT song.title, artistPerformsSong.artistID, songInAlbum.albumID, songGenre.genre, song.releaseDate, song.songURL
    FROM song NATURAL JOIN artistPerformsSong NATURAL JOIN songGenre NATURAL JOIN songInAlbum WHERE song.title = '%s'""" % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('generalsong.html', reviewing=data)

@app.route('/album_profile',  methods=['GET', 'POST'])
def album_profile():
    cursor = conn.cursor();
    albums = """SELECT DISTINCT album.albumName, album.albumID, songInAlbum.songID, reviewAlbum.username, song.title, reviewAlbum.reviewText, 
    reviewAlbum.reviewDate, rateAlbum.username, rateAlbum.stars FROM album NATURAL JOIN song NATURAL JOIN artistPerformsSong NATURAL JOIN 
    songInAlbum LEFT JOIN reviewAlbum ON reviewAlbum.albumID = album.albumID LEFT JOIN rateAlbum ON rateAlbum.albumID = album.albumID
    WHERE album.albumName = '%s';""" % (session['profiles'])
    print(albums)
    cursor.execute(albums)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('album_profile.html', reviewing=data)

@app.route('/generalalbum',  methods=['GET', 'POST'])
def generalalbum():
    cursor = conn.cursor();
    albums = """SELECT DISTINCT album.albumName, album.albumID, songInAlbum.songID, song.title 
    FROM album NATURAL JOIN song NATURAL JOIN songInAlbum 
    WHERE album.albumName = '%s';""" % (session['profiles'])
    print(albums)
    cursor.execute(albums)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('generalalbum.html', reviewing=data)

@app.route('/artist_profile',  methods=['GET', 'POST'])
def artist_profile():
    cursor = conn.cursor();
    artists = """SELECT artist.artistID, artist.fname, artist.lname, artist.artistBio, artist.artistURL, artistPerformsSong.songID, song.title
    FROM artist NATURAL JOIN artistPerformsSong NATURAL JOIN song WHERE artist.fname = '%s'""" % (session['profiles'])
    #print(artists)
    cursor.execute(artists)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('artist_profile.html', reviewing=data) 

@app.route('/generalartist',  methods=['GET', 'POST'])
def generalartist():
    cursor = conn.cursor();
    artists = """SELECT artist.artistID, artist.fname, artist.lname, artist.artistBio, artist.artistURL, artistPerformsSong.songID, song.title
    FROM artist NATURAL JOIN artistPerformsSong NATURAL JOIN song WHERE artist.fname = '%s'""" % (session['profiles'])
    #print(artists)
    cursor.execute(artists)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('generalartist.html', reviewing=data) 

@app.route('/grsearch',  methods=['GET', 'POST'])
def grsearch():
    cursor = conn.cursor();
    if(request.method=="POST"):
        session['profiles'] = request.form.get('searched')
		# Get data from submitted form
		# Query the Database
        searching = """SELECT DISTINCT * FROM reviewSong CROSS JOIN reviewAlbum WHERE reviewAlbum.reviewText LIKE '%%%s%%' 
        OR reviewSong.reviewText LIKE '%%%s%%' """ % (session['profiles'])
        cursor.execute(searching)
        #print('Stopped')
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        return render_template("general.html", data=data)
    else:
        cursor.close()
        return render_template('general.html', error='Search Not Found')
    
@app.route('/grSprofile',  methods=['GET', 'POST'])
def grSprofile():
    cursor = conn.cursor();
    songs = """SELECT DISTINCT username, songID, reviewText, reviewDate, title FROM reviewSong NATURAL JOIN song 
    WHERE reviewText LIKE  '%%%s%%' """ % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('grs_profile.html', reviewing=data)

@app.route('/grAprofile',  methods=['GET', 'POST'])
def grAprofile():
    cursor = conn.cursor();
    songs = """SELECT DISTINCT username, albumID, reviewText, reviewDate, albumName FROM reviewAlbum NATURAL JOIN album 
    WHERE reviewText LIKE  '%%%s%%' """ % (session['profiles'])
    print(songs)
    cursor.execute(songs)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('gra_profile.html', reviewing=data)


@app.route('/fans',  methods=['POST'])
def fans():
    #grabs information from the forms
    username = session['username']
    fans = request.form['fans']
    cursor = conn.cursor()
    query = """SELECT artistID FROM userFanOfArtist WHERE EXISTS (SELECT user.username FROM user 
    WHERE userFanOfArtist.username = user.username AND userFanOfArtist.username = %s AND userFanOfArtist.artistID = %s) """
    cursor.execute(query, (username, fans))
    conn.commit()
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    if data is None:
        cursor = conn.cursor()
        query = """INSERT INTO userFanOfArtist VALUES('%s', '%s')""" % (username, fans)
        cursor.execute(query)
        conn.commit()
        cursor.close()
        return render_template('artist_profile.html', reviewing=data)
    else:
        cursor.close()
        return redirect('/artist_profile')

@app.route('/fatear_profile',  methods=['GET', 'POST'])
def fatear_profile():
    cursor = conn.cursor();
    fatears = """SELECT DISTINCT user.fname, user.lname, user.username, user.nickname, user.lastlogin, userFanOfArtist.artistID
    FROM user NATURAL JOIN userFanOfArtist WHERE user.username = '%s'""" % (session['profiles'])
    cursor.execute(fatears)
    conn.commit()
    data = cursor.fetchall()
    cursor.close()
    return render_template('fatear.html', reviewing=data)

@app.route('/following',  methods=['POST'])
def following():
    #grabs information from the forms
    username = session['username']
    following = request.form['following']
    #print(following)
    ts = time.time()
    createdAt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    query = """SELECT follows FROM follows WHERE EXISTS (SELECT username FROM user WHERE follows.follower = user.username AND 
    (follows.follower = %s AND follows.follows = %s)) """
    cursor.execute(query, (username, following))
    conn.commit()
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    if data is None:
        cursor = conn.cursor()
        query = "INSERT INTO follows (follower, follows, createdAt) VALUES('%s', '%s', '%s')" % (username, following, createdAt)
        cursor.execute(query)
        conn.commit()
        cursor.close()
        return render_template('fatear.html', reviewing=data, success="You Are Following")
    else:
        cursor.close()
        return redirect('/fatear_profile') 
    
@app.route('/friendship',  methods=['POST'])
def friendship():
    #grabs information from the forms
    username = session['username']
    friendship = request.form['friendship']
    print(friendship)
    ts = time.time()
    createdAt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    query = """SELECT user2 FROM friend WHERE EXISTS (SELECT username FROM user 
    WHERE friend.user2 = user.username AND friend.user1 = %s AND friend.user2 = %s) """
    cursor.execute(query, (username, friendship))
    conn.commit()
    #stores the results in a variable
    data = cursor.fetchone()
    print(data)
    #use fetchall() if you are expecting more than 1 data row
    if data is None:
        cursor = conn.cursor()
        query = """INSERT INTO friend (user1, user2, acceptStatus, requestSentBy, createdAt) 
        VALUES('%s', '%s', 'Pending', '%s', '%s')""" % (username, friendship, username, createdAt)
        cursor.execute(query)
        conn.commit()
        cursor.close()
        return redirect('/fatear_profile')
    else:
        # cursor = conn.cursor()
        # query = """INSERT INTO friend (user1, user2, acceptStatus, requestSentBy, createdAt) 
        # VALUES('%s', '%s', 'Pending', '%s', '%s')""" % (username, friendship, username, createdAt)
        # cursor.execute(query)
        # conn.commit()
        cursor.close()
        return render_template('fatear.html', reviewing=data, success="You Are Friends")

@app.route('/review_page', methods=['GET'])
def review_page():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM song')
    songIds = cursor.fetchall()
    cursor.close()
    return render_template('reviews.html', list_of_songs=songIds)
        
@app.route('/reviews', methods=['POST'])
def reviews():
    username = session['username']
    cursor = conn.cursor()
    songID = request.form.get('songID')
    reviewText = request.form.get('reviewText')
    ts = time.time()
    reviewDate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM song')
    songIds = cursor.fetchall()
    try:
        query = 'INSERT INTO reviewSong VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, songID, reviewText, reviewDate))
        conn.commit()
        cursor.close()
        return render_template('reviews.html', list_of_songs=songIds, success="Successfully added Review")
    except Exception as e:
        print(e)
        conn.commit()
        cursor.close()
        return render_template('reviews.html', list_of_songs=songIds, error="Unexpected error occured")
    #return redirect(url_for('home'))

@app.route('/reviewa_page', methods=['GET'])
def reviewa_page():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM album')
    albumIds = cursor.fetchall()
    cursor.close()
    return render_template('reviewa.html', list_of_albums=albumIds)

@app.route('/reviewa', methods=['POST'])
def reviewa():
    username = session['username']
    cursor = conn.cursor()
    albumID = request.form.get('albumID')
    reviewText = request.form.get('reviewText')
    ts = time.time()
    reviewDate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM song')
    albumIds = cursor.fetchall()
    try:
        query = 'INSERT INTO reviewAlbum VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, albumID, reviewText, reviewDate))
        conn.commit()
        cursor.close()
        return render_template('reviews.html', list_of_albums=albumIds, success="Successfully added Review")
    except Exception as e:
        print(e)
        conn.commit()
        cursor.close()
        return render_template('reviewa.html', list_of_albums=albumIds, error="Unexpected error occured")
    
@app.route('/ratea_page', methods=['GET'])
def ratea_page():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM album')
    albumIds = cursor.fetchall()
    cursor.close()
    return render_template('ratea.html', list_of_albums=albumIds)

@app.route('/ratea', methods=['POST'])
def ratea():
    username = session['username']
    cursor = conn.cursor()
    albumID = request.form.get('albumID')
    stars = request.form.get('stars')
    ts = time.time()
    reviewDate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM album')
    albumIds = cursor.fetchall()
    try:
        query = 'INSERT INTO reviewAlbum VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, albumID, stars, reviewDate))
        conn.commit()
        cursor.close()
        return render_template('ratea.html', list_of_albums=albumIds, success="Successfully added Rating")
    except Exception as e:
        print(e)
        conn.commit()
        cursor.close()
        return render_template('ratea.html', list_of_albums=albumIds, error="Unexpected error occured")
    
@app.route('/rates_page', methods=['GET'])
def rates_page():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM song')
    songIds = cursor.fetchall()
    cursor.close()
    return render_template('rates.html', list_of_songs=songIds)

@app.route('/rates', methods=['POST'])
def rates():
    username = session['username']
    cursor = conn.cursor()
    songID = request.form.get('songID')
    stars = request.form.get('stars')
    ts = time.time()
    reviewDate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM song')
    songIds = cursor.fetchall()
    try:
        query = 'INSERT INTO rateSong VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, songID, stars, reviewDate))
        conn.commit()
        cursor.close()
        return render_template('rates.html', list_of_songs=songIds, success="Successfully added Rating")
    except Exception as e:
        print(e)
        conn.commit()
        cursor.close()
        return render_template('rates.html', list_of_songs=songIds, error="Already rated")

@app.route('/ratesreviews', methods=['GET', 'POST'])
def ratesreviews(): 
    return render_template('ratesreviews.html')
  
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = '#SPRING2023!3strikes'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 7000, debug = True)
