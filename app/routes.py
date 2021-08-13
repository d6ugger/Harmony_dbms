from flask import Flask, render_template, flash, redirect, url_for, request, json
from app import app, mysql

#Global Variables
countMatch=-1
artistName=''
userData = []
userRow=[]
searchArtist=''
dic={}
userLogged=()


#Main page which leads to login 
@app.route('/')
def main():
    global dic
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM users')
    user=cur.fetchall()
    for i in user:
        dic[i] = False
    return redirect(url_for("login"))



#Login Page 
@app.route('/Login', methods  =['POST','GET'])
def login():
    global dic
    global userLogged
    if request.method == 'POST' and 'email' in request.form and 'passwd' in request.form:
        email=request.form['email']
        passwd=request.form['passwd']
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM users where email=%s and passwd=%s', (email, passwd))
        user=cur.fetchone()
        userLogged=user
        dic[user]=True
        print(dic[user])
        if(dic[user]==True):
            return redirect(url_for("homePage"))
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


#Register Page
@app.route('/Register', methods=['POST','GET'])
def register():
    email=""
    name=""
    if request.method == 'POST':
        if 'uname' in request.form and 'uname'.lower()!='admin' and 'passwd' in request.form and 'email' in request.form and 'gender' in request.form and 'dob' in request.form:
            name=request.form['uname']
            passwd=request.form['passwd']
            email=request.form['email']
            gender=request.form['gender']
            dob=request.form['dob']
            cur=mysql.connection.cursor()
            print(email)
            cur.execute('SELECT * FROM users WHERE email=%s',(email,))
            if cur.fetchone():
                return render_template('reg.html')
            print(email)
            cur.execute('SELECT COUNT(*) FROM users')
            cur.execute('INSERT INTO users(user_id, Name, email, passwd, gender, dob) VALUES (%s, %s, %s, %s, %s, %s)', (int(cur.fetchone()[0])+1,name, email, passwd, gender, dob))
            mysql.connection.commit()
            return redirect(url_for("main"))
        else:
            return render_template('reg.html')
    else:
        return render_template('reg.html')


#HomePage all Pages lead to this
@app.route('/HomePage', methods=['POST','GET'])
def homePage():
    global dic
    global userLogged
    print("HOMEPAGE")
    if( userLogged not in dic or dic[userLogged] is False):
        return redirect(url_for("login"))
    else:
        return render_template('homePage.html', uname=userLogged[1])



@app.route('/Profile', methods=['POST','GET'])
def profile():
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))
        else:
            return render_template('profilePage.html', info=userLogged)
    if(request.method=='POST' and 'passwd' in request.form):
        userLogged[1]!='admin'
        cur=mysql.connection.cursor()
        userLogged[3]=request.form['passwd']
        cur.execute('UPDATE users SET passwd=%s WHERE user_id=%s',(request.form['passwd'], userLogged[0]))
        mysql.connection.commit()
        return render_template('profilePage.html', info=userLogged)



@app.route('/meet')
def artistPick():
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))
    curr=mysql.connection.cursor()

    #Finding Users with the same interest
    sql_select_query = """select * from fav_artists f where f.user_id = %s"""
    curr.execute(sql_select_query, (userLogged[0],))
    data=curr.fetchall()
    list_of_artists=[]
    for i in data:
        list_of_artists.append(i[1])
    print(list_of_artists)

    if len(list_of_artists)==0:
        curr.execute(" select * from artists")
        data=curr.fetchall()
    elif len(list_of_artists)==1:
        curr.execute("select * from artists  where artist_id = %s ", (list_of_artists[0],))
        data = curr.fetchall()
    else:
        list_of_artists=tuple(list_of_artists)
        print(list_of_artists)
        curr.execute("select * from artists  where artist_id in %s order by artist_id", (list_of_artists, ))
        data = curr.fetchall()

    return render_template("artist.html", info=data)



@app.route('/match', methods=['GET', 'POST'])
def match():
    global countMatch
    global userData
    global userRow
    global artistName
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))

    if request.method == 'POST':
        artistName = request.form.get('comp_select')

        # Find Artist Details
        curr=mysql.connection.cursor()
        sql_select_query = """select * from artists a where a.name = %s"""
        curr.execute(sql_select_query, (artistName,))
        data = curr.fetchall()
    
        #Finding Users with the same interest
        sql_select_query = """select * from fav_artists f where f.artist_id = %s"""
        curr.execute(sql_select_query, (data[0][0],))
        data=curr.fetchall()
        list_of_user=[]
        for i in data:
            list_of_user.append(i[0])
        print(list_of_user)

        # Find Matching User Id's
        sql_select_query = """ select * from users u where u.user_id in %s"""
        curr.execute(sql_select_query, (list_of_user, ))
        data=curr.fetchall()
        userData=data
        countMatch=-1

    countMatch+=1
    if countMatch==len(userData):
        countMatch=0  
    if userData[countMatch][0]==userLogged[0]:
        countMatch+=1
    if countMatch==len(userData):
        countMatch=0
    userRow=userData[countMatch]
    print(countMatch)

    return render_template("meet.html", info=userRow)




@app.route('/connect', methods=['GET', 'POST'])
def connect():
    global artistName
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))

    userId = request.form.get('userid')
    userName = request.form.get('userName')
    userEmail=''

    # Find Artist Details
    curr=mysql.connection.cursor()
    sql_select_query = """select * from artists a where a.name = %s"""
    curr.execute(sql_select_query, (artistName,))
    data = curr.fetchone()

    #Adding to User connections
    curr.execute('select * from users where user_id = %s', (userId,))
    dat=curr.fetchone()
    userEmail=dat[2]
    curr.execute('select * from connections c where c.u_id1 = %s', (userLogged[0],  ))
    dat = curr.fetchall()
    print(userId)
    print(userLogged[0])
    print(data[0])
    flag=0
    for i in dat:
        if i[1]==userId:
            flag=1
    if flag==0:        
        curr.execute('INSERT INTO connections(u_id1, u_id2, co_artist) VALUES (%s, %s, %s)', (userLogged[0], userId, data[0]))
        mysql.connection.commit()
        userName='You have connected with '+userName
    else:
        userName='You have already been connected with '+userName
    passingdata=[userName, userEmail]
    return render_template('connected.html', info=passingdata)



@app.route("/fav_sugg", methods=["POST", "GET"])
def suggestion() :
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))

    user_id = userLogged[0]
    cur = mysql.connection.cursor() 
    cur.execute("select * from songs where genre in (select distinct genre from songs where artist_name in ( select distinct artist_name from albums where artist_id in ( select artist_id from fav_artists where user_id=\""+str(user_id)+"\"))) order by rand() limit 4;")
    result = cur.fetchall()

    return render_template("fav_sugg_display.html", result=result)



@app.route('/artist', methods={'GET', 'POST'})
def artistSearch():
    global searchArtist
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))

	# Store the name of artist
    if request.method == 'POST':
        details = request.form
        searchArtist = details['name']
        return redirect('artistResult')

    return render_template('search.html')   


@app.route('/artistResult', methods={'GET', 'POST'})
def artistResult():
    global userLogged
    global searchArtist
    user = userLogged[0]
    name = searchArtist
    global dic
    if( userLogged not in dic or dic[userLogged] is False):
        return redirect(url_for("login"))

    #Getting the artist searched
    cur = mysql.connection.cursor()
    print(searchArtist)
    sql_query = """select * from albums a where a.album_name = %s """
    sql = """select * from artists a where a.name = %s """
    resultValue = cur.execute(sql_query, (name,))
    if resultValue > 0:
        userDetails = cur.fetchall()
    else:
        return 'Invalid Artist'
    cur.execute(sql, (name,))
    artis = cur.fetchone()
    artistID = artis[0]
    temp=''

    #Adding to favourite albums
    if request.method == 'POST':
        albumID = request.form
        id = albumID['numb']
        cur = mysql.connection.cursor()
        cur.execute(" select * from fav_albums where user_id = %s", (user,))
        data = cur.fetchall()
        cur.execute(" select * from fav_artists where user_id = %s", (user,))
        dataArtist = cur.fetchall()
        flag=0
        z=0
        for i in data:
            if i[1] == id:
                flag=1
        for i in dataArtist:
            if i[1] == artistID:
                z=1
        if( flag == 0):
            temp='Album Added To Favourites'
            cur.execute("INSERT INTO fav_albums(user_id, album_id) VALUES(%s, %s)",(user, id))
            if z==0:
                cur.execute("INSERT INTO fav_artists(user_id, artist_id) VALUES(%s, %s)",(user, artistID))
            mysql.connection.commit()
        else:
            temp='Album was already in Favourites'
        cur.close()
    info=[userDetails, artis, temp]
    return render_template('result.html',info = info)

#Function to be an artist
@app.route('/artistAdd', methods={'GET', 'POST'})
def artistAdd():
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))

    cur=mysql.connection.cursor()
    email=""
    name=""
    if request.method == 'POST':
        if 'uname' in request.form and 'passwd' in request.form and 'email' in request.form:
            name=request.form['uname']
            passwd=request.form['passwd']
            email=request.form['email']
            print(email)
            cur.execute('SELECT * FROM artists WHERE name= %s',(name,))
            if cur.fetchone():
                return render_template('addSong.html', info = 0)
            cur.execute('SELECT COUNT(*) FROM artists')
            cur.execute('INSERT INTO artists(artist_id, name, email, passwd, dob, signed, gender, followers ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (int(cur.fetchone()[0])+1,name, email, passwd, userLogged[4], 0, userLogged[5], 0 ))
            mysql.connection.commit()
            print(email)
            return render_template('addSong.html', info = 1)
        else:
            return render_template('addArtist.html', info =1)
    else:
        return render_template('addArtist.html', info =1)


#Function to add songs
@app.route('/songAdd', methods={'GET', 'POST'})
def songAdd():
    global dic
    global userLogged
    if(request.method=='GET'):
        if( userLogged not in dic or dic[userLogged] is False):
            return redirect(url_for("login"))
    
    print("HERE")
    if request.method == 'POST':
        if 'uname' in request.form and 'artist_name' in request.form and 'album_name' in request.form and 'genre' in request.form and 'lang' in request.form and 'dor' in request.form:
            name=request.form['uname']
            artist_name=request.form['artist_name']
            label_name=''
            if 'label_name' in request.form:
                label_name=request.form['label_name']
            album_name=request.form['album_name']
            dor=request.form['dor']
            genre=request.form['genre']
            lang=request.form['lang']
            passwd = request.form['passwd']
            cur=mysql.connection.cursor()
            print(artist_name)
            print("HERE2")
            cur.execute('select * from artists where name = %s and passwd = %s ', (artist_name, passwd))
            dat=cur.fetchall()
            if len(dat)==0:
                print("HERE3")
                return render_template('addSong.html', info = 2)
            print("HERE4")
            cur.execute('SELECT COUNT(*) FROM songs')
            cur.execute('INSERT INTO songs(song_id, name, artist_name, label_name, album_name, release_date, views, genre, language) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (int(cur.fetchone()[0])+1,name, artist_name, label_name, album_name, dor, 0, genre, lang))
            mysql.connection.commit()
            
            return render_template('songAdded.html', name=name)
        else:
            print("HERE5")
            return render_template('addSong.html')
    else:
        print("HERE6")
        return render_template('addSong.html')
