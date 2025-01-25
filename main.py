'''
QuarkoFOSS - Main

This is the original Quarko code
Under the MIT license a copy is available in the LICENSE file

(some code is changed for privacy reasons.. (tokens etc))
'''

#QuarkoFOSS - Main
#Made by EletrixTime
# finished on : 24/06/2024 18:19 !
#(C) 2024 EletrixTime
from flask import Flask, render_template, flash, session, request, send_file, redirect, abort, jsonify, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, Column, String, Integer, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os
import random
import html
import time
import uuid
import datetime
from datetime import *
import requests
import sentry_sdk
import threading
from time import sleep
import sys
import mailtrap as mt
import traceback
from libs import webhooklog, hashmng, stats
from db import sessiondb, User, Post, ChatDB, Stats
import config


def delayed_exit():
    sleep(5)
    stats.stats("A admin initied a restart",{"status":"restarting"})
    os._exit(0)
    #python = sys.executable
    #os.execl(python, python, *sys.argv)

def secure_random(a,b): # securing random
    #get the timestamp and increment it
    timestamp = int(time.time() +random.randint(5,10))
    return timestamp

def print(text):
    '''Feeding the void'''
    pass
stats.stats("Quarko init...",{"status":"starting"})

mail_client = mt.MailtrapClient(token=config.MAILTRAP_TOKEN)
DISABLED_ROUTE = {}

MAINTENANCE = False
reset_pswd_tokens = {}
CDN_MAIN_URL = config.CDN_MAIN_URL
CDN_PASSWORD = config.CDN_PASSWORD
def pswd_generate_token(email):
    token_uuid = str(uuid.uuid4())
    expiration_time = datetime.utcnow() + timedelta(minutes=15)
    reset_pswd_tokens[token_uuid] = {
        "email": email,
        "expires_at": expiration_time
    }
    print(token_uuid)
    return token_uuid

def pswd_is_token_expired(token_uuid):
    token_data = reset_pswd_tokens.get(token_uuid)
    if not token_data:
        return True
    return datetime.utcnow() > token_data["expires_at"]



#True = 1, False = 0
def randomstr():
    code = "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(16))
    return code

app = Flask(__name__,template_folder="src")
app.secret_key = randomstr()
socketio = SocketIO(app)
CORS(app)

sentry_sdk.init(
    dsn=config.SENTRY_URL,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

@app.before_request
def checkmtn():
    try:
        if MAINTENANCE == True:
            if request.path.startswith("/assets") or request.path.startswith("/logout") or request.path.startswith("/faq") or request.path.startswith("/admin"):
                pass
            else:
                return "<center><h1>Quarko - MAINTENANCE</h1><p>Bonjour Quarko est en maintenance!</p><a href=https://dsc.gg/quarko>Discord</a></center>"
        else:
            if request.path.startswith("/assets") or request.path.startswith("/logout") or request.path.startswith("/faq"):
                pass
            else:
                token = session.get("token")
                if token is not None:
                    user = sessiondb.query(User).filter_by(token=token).first()        
                    if user == None:
                        session.clear()
                    else:
                        if user.ban == "1":
                            return render_template("legals/ban.html",banraison=user.ban_raison,username=user.username,accid=user.id)
                else:
                    if any(request.path.startswith(route) for route in DISABLED_ROUTE):
                        return "[DESACTIVÉ] : 403",403
                    else:
                        pass
    except Exception as e:
        pass
def check_if_admin():
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first()
        if user is not None:
            if user.staff == "1":
                return True
    return False


    
@app.route('/assets/<path:filename>')
def get_asset(filename):
    file_path = os.path.join("assets", filename)
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return send_file(file_path)
    else:
        return "404_not_found"
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/faq")
def legal_faq():
    return render_template("legals/faq.html")


@app.route('/users/<string:user_id>')
def view_user(user_id):
    if_followed = False
    if isinstance(user_id, str):
        t = sessiondb.query(User).filter_by(username=user_id).first()
    else:
        t = sessiondb.query(User).filter_by(id=user_id).first()
    main_user = sessiondb.query(User).filter_by(token=session.get("token")).first()
    if main_user is not None:
        cake = json.loads(t.who_followed)
        if main_user.id in cake["who_followed"]:
            if_followed = True

            
    if t is not None:
        post_l = sessiondb.query(Post).filter(Post.author == t.username).all()
        return render_template("profile.html",followers=t.followers,background_url=t.background_url,username=user_id,id=t.id,certified=t.certified,staff=t.staff,description=t.bio,banned=t.ban,premium=t.premium,pp_url=t.profile_url,post=post_l,if_follow=if_followed)
    else:
        banorno = False
        return render_template("profile.html",followers="404",username="Unknown_ID",ID="0000",certified="False",staff="False",description="Wrong ID :/",banned="0",if_followed=if_followed)
@app.route('/users/<string:user_id>/follow',methods=["POST"])
def follow_manager(user_id):
    print(user_id)
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first()
        userv2 = sessiondb.query(User).filter_by(id=user_id).first()
        if user is not None:
            if userv2 is not None:
                if user.id != userv2.id:
                    cake = json.loads(userv2.who_followed)
                    cake = cake["who_followed"]
                    if user.id in json.loads(userv2.who_followed)["who_followed"]:
                        cake.remove(user.id)
                        userv2.who_followed = json.dumps({"who_followed":cake})
                        userv2.followers -= 1
                        sessiondb.commit()
                        flash("Vous ne suivez plus ce compte !")
                        return redirect(f"/")
                        
                    else:
                        cake.append(user.id)
                        userv2.who_followed = json.dumps({"who_followed":cake})
                        userv2.followers += 1
                        sessiondb.commit()
                        flash("Vous suivez ce compte !")
                        return redirect(f"/")
                else:
                    flash("Vous ne pouvez pas vous suivre vous-même !")    
                    return redirect(f"/")           
        else:
            return redirect("/")
    else:
        return redirect("/")

#Authenfication/Signup/Logout

#Login :
@app.route("/login", methods=["GET", "POST"])
def auth_login():
    try:
        if request.method == "GET":
            if "logged" in session and session["logged"] == "1":
                return redirect("/")
            else:
                return render_template("auth/login.html")
        elif request.method == "POST":
            #caca = randomstr() # vous inquiètez pas je vais bien :D
            password = hashmng.hash_text(text=request.form['password'])
            email = request.form['email']
            user = sessiondb.query(User).filter_by(email=email).first()
            print(user)
            if user is None:
                flash("Le compte existe pas !")
                return render_template("auth/login.html")
            else:
                
                if password == user.password:
                    if user.ban == "1":
                        flash('Ce compte a été suspendue')
                        return redirect("../login")
                    else:
                        
                        
                        session["username"] = user.username
                        session["logged"] = "1"
                        #session["id"] == user.id
                        session["token"] = user.token
                        sessiondb.commit()
                        return redirect("/")
                else:
                    flash("Identifiant incorrect !")
                    return render_template("auth/login.html")
    except Exception as e:
        flash(f"Impossible de vous authentifier : {e}")
        return redirect("/")
    
@app.route("/logout")
def auth_logout():
    try:
        session.clear()
        flash("Déconnexion avec succès !")
        return redirect("/")
    except:
        flash("Une erreur est survenue lors de la déconnexion (êtes vous connecter ?)")
        return redirect("/")
@app.route("/register",methods=["GET", "POST"])
def auth_register():
    if request.method == "GET":return render_template("auth/register.html")
    elif request.method == "POST": #ok le postier
        username = request.form['username'];username = username.replace(" ", "");username = html.escape(username)
        username = username.lower()
        password = hashmng.hash_text(text=request.form['password'])
        email = request.form['email']
        t = sessiondb.query(User).filter_by(username=username,email=email)
        if len(username) > 25:
            flash("Pseudo trop long !")
            return redirect (url_for('auth_register'))
        if t is not None:
            caca = randomstr() # tkt'
            uploaded_file = request.files['file']

            if uploaded_file.filename != '':
                filename = uploaded_file.filename  
                files = {'file': (filename, uploaded_file.stream, uploaded_file.content_type)}
                data = {"password": CDN_PASSWORD} 
                qs = requests.post(CDN_MAIN_URL, files=files, data=data)
                qs = json.loads(qs.text)



            kk = secure_random(10000000,1000000000000)
            adduser = User(ip=request.headers.get('CF-Connecting-IP'), username=username, email=email, bio="Je suis nouveau !", password=password, id=kk, token=caca, join_date=datetime.now(), profile_url=qs["url"],show_username=username)
            session["username"] = username
            session["logged"] = "1"
            #session["id"] == kk
            session["token"] = caca     
            sessiondb.add(adduser)
            sessiondb.commit()    
            flash("Compte créé avec succèss ")  
            return redirect("/")
        else:
            flash("Pseudo déja pris !")
            return render_template("auth/register.html")
# Manage:
@app.route("/manage",methods=["POST","GET"])
def auth_manage():
        token = session["token"]
        user = sessiondb.query(User).filter_by(token=token).first()
        if user is not None:
            if request.method == 'GET':
                
                if user.devmode == "1":
                    devmode = True
                   
                else:
                    devmode = False
                return render_template("auth/manage.html",user_bio=user.bio,devmode=devmode,premium=user.premium)
            elif request.method == 'POST':
                bio = html.escape(request.form["bio"])
                user.bio = bio
               

                if request.form.get('devmode') == "on":
                    session["devmode"] = True
                    user.devmode = True
                else:
                    session["devmode"] = False
                    user.devmode = False
                
                sessiondb.commit()
                flash(request.form.get('devmode'))
                return redirect("../manage")
        else:
            flash("Veuiller vous connecter")
            return redirect("/")            

@app.route("/manage/a/delete_acc",methods=["POST"])
def auth_manage_a_delete_acc():
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first()
        if user is not None:
            if hashmng.hash_text(request.form["password"]) == user.password:
                sessiondb.delete(user)
                sessiondb.commit()
                session.clear()
                flash("😓 Ton compte a été supprimé !");return redirect("/")  
            else:
                flash("Mot de passe incorrect !");return redirect("../../../../manage")  
        else:
            flash("Non-connecter!");return redirect("../../../login")  
    else:
        flash("Non-connecter!");return redirect("../../../login")  

@app.route("/manage/a/change_pp",methods=["POST"])
def manage_a_change_pp():
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first()
        if user is not None:
            attachements = request.files['file']
            if attachements.filename != '':
                            filename = attachements.filename  # Save the original filename
                            file_path = f"data/tmp{filename}"
                            attachements.save(file_path)
                            file_size = os.stat(file_path).st_size

                            if file_size > 50 * 1024 * 1024:
                                flash("Fichier Trop Lourd !")
                                return redirect("../../../../../manage")
                            else:
                                with open(file_path, 'rb') as file:
                                    files = {'file': (filename, file.read(), attachements.content_type)}
                                    data = {"password": CDN_PASSWORD}
                                    res = requests.post(CDN_MAIN_URL, files=files, data=data)
                                    qs = json.loads(res.text)
                                    attachements_url = qs["url"]
                                    file.close()
                                    os.remove(file_path)
                                    flash("La photo de profile a été changée !")
                                    return redirect("../../../../../manage")

            else:
                flash("Une erreur est survenue inconnue");return redirect("../../../../manage")  
        else:
            flash("Merci de te connecter !");return redirect("../../../login")   
    else:
        flash("Merci de te connecter !");return redirect("../../../login")   

@app.route("/manage/a/background",methods=["POST"])
def manage_a_background():
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first()
        if user is not None:
            if user.premium == "1":
                uploaded_file = request.files['file']
                attachements = request.files['file']
                if attachements.filename != '':
                            filename = attachements.filename  # Save the original filename
                            file_path = f"data/tmp{filename}"
                            attachements.save(file_path)
                            file_size = os.stat(file_path).st_size

                            if file_size > 50 * 1024 * 1024:
                                flash("Too big file!")
                                return redirect("../../../../../manage")
                            else:
                                with open(file_path, 'rb') as file:
                                    files = {'file': (filename, file.read(), attachements.content_type)}
                                    data = {"password": CDN_PASSWORD}
                                    res = requests.post(url=CDN_MAIN_URL, files=files, data=data)
                                    qs = json.loads(res.text)
                                    user.background_url=qs["url"];sessiondb.commit()
                                    file.close()
                                    os.remove(file_path)
                        
                                    flash("Votre fond a été changé avec sucèss !");return redirect("/")
            else:
                flash("Oh il te faut Quarko Premium !");return redirect("../../../../manage")
        else:
            flash("Merci de te connecter !");return redirect("../../../login")   
    else:
        flash("Merci de te connecter !");return redirect("../../../login")   


#Admin :
@app.route("/admin/restart")
def admin_restart():
    if check_if_admin():
        #return "[DESACTIVÉ]"
        threading.Thread(target=delayed_exit).start()
        return '<meta http-equiv="refresh" content="7; URL=/" /><center> <h1>Rédemarrage en cours...</h1> <br> <p>Merci de patienter</p> <p>Vou serez redirigè sur la page d\'accueil dans quelques secondes</p> </center>'
    else:
        abort(403)
@app.route("/admin/login_as/",methods=["POST"])
def admin_login_as():
    if check_if_admin():
        user = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user is not None:
            session["token_staff"] = session["token"]
            session["username"] = user.username
            session["logged"] = "1"
            session["token"] = user.token
            
            return redirect("/")
        else:
            flash("Utilisateur non-trouvé ? (ID Valide ?)");return redirect("../../admin")
@app.route("/admin/login_as/reconnect")
def admin_login_as_reconnect():
    if session.get("token_staff") is not None:
        admin = sessiondb.query(User).filter_by(token=session.get("token_staff")).first()
        if admin is not None:
            
            session["username"] = admin.username
            session["logged"] = "1"
            session["token"] = admin.token
            session["token_staff"] = None

            return redirect("/")
        else:
            flash("Une erreur est survenue inconnue");return redirect("../../admin")
    return redirect("/")
@app.route("/admin")
def admin_dash():
        token = session["token"]
        user = sessiondb.query(User).filter_by(token=token).first()
        if user is not None:
            if user.staff == "1":
                return render_template("admin/new.html")
            else:
                flash("403 : Not authorized")
                return redirect("/")
        else:
            flash("403 : Not authorized")
            return redirect("/")

@app.route("/admin/ban",methods=["POST"])
def admin_ban():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            user2.ban = True
            user2.ban_raison = request.form["raison"]
            sessiondb.commit()
            flash("bannis !")
            #webhooklog.send_log_webhook(title="Banissement de compte",text=f"Un compte a été bannit \n > Pseudo du modérateur : {user.username}/{user.id} \n \n > Pseudo de la personne bannis : {user2.username}/{user2.id} \n > Raison de son banissement : {user2.ban_raison} \n \n \n > Action : `BAN`")
            return redirect("../../admin")
        else:
            flash("Utilisateur non-trouvé ? (ID Valide ?)");return redirect("../../admin")  
    else:
        abort(403)

@app.route("/admin/permissions/premium",methods=["POST"])
def admin_permissions_premium():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            if user2.premium == "1":
                    user2.premium = False
                    sessiondb.commit()
                    flash("Permission PREMIUM retirée")
                    return redirect("/admin")
            else:
                    user2.premium = True
                    sessiondb.commit()
                    flash("Permission PREMIUM ajouté")
                    return redirect("/admin")  
        else:
            flash("Utilisateur non-trouvé ? (ID valide ?)");return redirect("../../admin")  
    else:
        abort(403) 

@app.route("/admin/delete_account",methods=["POST"])
def admin_deleteacc():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            sessiondb.delete(user2)
            sessiondb.commit()
            flash("Le compte a bien-été supprimé avec succès !")
            return redirect("../../admin")
        else:
            flash("Utilisateur non-trouvé ? (ID Valide ?)");return redirect("../../admin")  

    else:
        abort(403)
@app.route("/admin/unban",methods=["POST"])
def admin_unban():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            user2.ban = False
            sessiondb.commit()
            flash("Utilisateur unban !")
            #webhooklog.send_log_webhook(title="Débanissement de compte",text=f"Un compte a été unban \n > Pseudo du modérateur : {user.username}/{user.id} \n \n > Pseudo de la personne bannis : {user2.username}/{user2.id} \n > Raison de son banissement : {user2.ban_raison} \n \n \n > Action : `UNBAN`")
            return redirect("../admin")
        else:
            flash("Utilisateur non-trouvé ? (ID Valide ?)");return redirect("../../admin")  
    else:
        abort(403)

    
@app.route("/admin/delete_post",methods=["POST"])
def admin_post_delete():
    if check_if_admin():
            post = sessiondb.query(Post).filter_by(id=request.form["id"]).first()
            if post is not None:
                sessiondb.delete(post)
                sessiondb.commit()
                flash("Le post a bien été supprimé !")
                return redirect("../admin")
            else:
                flash("Post non-trouvé ! (ID Valide ?)");return redirect("../../admin")  
    else:
        abort(403)


@app.route("/admin/permissions/admin",methods=["POST"])
def admin_permissions():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            if user2.staff == "1":
                    user2.staff = False
                    sessiondb.commit()
                    flash("Permission ADMIN retirée")
                    return redirect("/admin")
            else:
                    user2.staff = True
                    sessiondb.commit()
                    flash("Permission ADMIN ajouté")
                    return redirect("/admin")  
        else:
            flash("Utilisateur non-trouvé ? (ID valide ?)");return redirect("../../admin")  
    else:
        abort(403)  

@app.route("/admin/permissions/certif",methods=["POST"])
def certif_permissions():
    if check_if_admin():
        user2 = sessiondb.query(User).filter_by(id=request.form["id"]).first()
        if user2 is not None:
            if user2.certified == "1":
                user2.certified = False
                sessiondb.commit()
                flash("Certification retirée")
                return redirect("/admin")
            else:
                user2.certified = True
                sessiondb.commit()
                flash("Certification ajouté")
                return redirect("/admin")   
        else:
            flash("Utilisateur non-trouvé ? (ID valide ?)");return redirect("../../admin") 
    else: abort(403)

#===========================================================================
'''Post Routes'''
#===========================================================================

@app.route("/posts/create", methods=["GET", "POST"])
def posts_create():
    
    if session.get("logged"): 
            if request.method == "GET":
                return render_template("posts/new.html")
            elif request.method == "POST":
                token = request.form["token"]
                title = html.escape(request.form["title"])
                text = html.escape(request.form["text"])
                u = sessiondb.query(User).filter_by(token=token).first()
                if title == " ":
                    flash("Titre Invalide")
                    return redirect("../../posts/create")      
                else:          
                    if not u:
                        flash("Utilisateur introuvable")
                        return redirect("../../posts/create")
                    
                    username = u.username
                    caca2 = secure_random(1000, 10000000000000000)
                    
                    if len(title) > 50:
                        flash("Tu dépasse la limite de 50 caractère possible pour le titre !")
                        return redirect("../../posts/create")
                    
                    if u.premium == "1":
                        cace = 1000
                    else:
                        cace = 250
                        
                    if len(text) > cace:
                        flash("Oh.. tu dépasse la limites de charactère !")
                        return redirect("../../posts/create")
                    attachements = request.files['file']
                    if attachements:
                        if attachements.filename != '':
                            filename = attachements.filename  # Save the original filename
                            file_path = f"data/tmp{filename}"
                            attachements.save(file_path)
                            file_size = os.stat(file_path).st_size
                            
                            if file_size > 50 * 1024 * 1024:
                                flash("Too big file!")
                                return redirect("../../posts/create")
                            else:
                                with open(file_path, 'rb') as file:
                                    files = {'file': (filename, file.read(), attachements.content_type)}
                                    data = {"password": CDN_PASSWORD}
                                    res = requests.post(CDN_MAIN_URL, files=files, data=data)
                                    qs = json.loads(res.text)
                                    attachements_url = qs["url"]
                                    file.close()
                                    os.remove(file_path)
                        else:
                            attachements_url = "empty"
                    else:
                        attachements_url = "empty"

                    post_d = Post(author=username, id=caca2, title=title, views="0", text=text, attachements=attachements_url)
                    sessiondb.add(post_d)
                    sessiondb.commit()
                    return redirect(f"../posts/view/{caca2}")

    else:
        flash("Veuiller vous connecter !");return redirect("../../../../login") 
@app.route("/posts/delete/<string:id>")
def posts_delete(id):
    p = sessiondb.query(Post).filter_by(id=id).first()
    user = sessiondb.query(User).filter_by(token=session.get("token")).first()
    if user is not None:
        if p.author == user.username:
            if p is not None:
                sessiondb.delete(p)
                sessiondb.commit()
                flash("Le post a bien été supprimé !")
                return redirect("/")
    flash("Une Une erreur est survenue est survenue !")
    return redirect("../../../../posts/view/{}".format(id))


@app.route('/posts/view/<string:id>')
def posts_view(id):
    liked = False
    u = sessiondb.query(Post).filter_by(id=id).first()
    comments = sessiondb.query(ChatDB).filter_by(post_id=id).all()
    if u is not None:
        if session.get("token") is not None:
            user = sessiondb.query(User).filter_by(token=session.get("token")).first()
            if user is not None:   
                liked = False
                if user.id in json.loads(u.who_liked)["who_liked"]:
                    liked = True  
                else:
                    liked = False 
                u.views += 1
                sessiondb.commit()
        if u.attachements is not '' or None:
            attachements = u.attachements
        return render_template("posts/view.html",title=u.title,text=u.text,author=u.author,likes=u.likes,views=u.views,attachements_url=attachements,is_liked=liked,id=id,comments=comments)

    else:
        flash("Post Introuvable !")
        return redirect("/")
@app.route("/posts/like/<string:id>",methods=["POST"])
def posts_like(id):
    u = sessiondb.query(Post).filter_by(id=id).first()
    user = sessiondb.query(User).filter_by(token=session.get("token")).first()
    if u is not None and user is not None:
        if user.id in json.loads(u.who_liked)["who_liked"]:
            cake  = json.loads(u.who_liked)
            cake["who_liked"].remove(user.id)
            u.who_liked = json.dumps(cake)
            u.likes -= 1
            
            sessiondb.commit()
            return redirect(f"../../../posts/view/{id}")
        else:
            u.likes += 1
            cake = json.loads(u.who_liked)
            cake["who_liked"].append(user.id)
            u.who_liked = json.dumps(cake)
            sessiondb.commit()
            return redirect(f"../../../posts/view/{id}")
    else:
        flash("Post Introuvable !")
        return redirect("/")
    
@app.route("/posts/comments/<string:id_post>",methods=["POST"])
def posts_comments(id_post):
    if request.form.get("message").strip() == "":
        flash("Vous ne pouvez pas envoyer un commentaire vide !");return redirect(url_for("posts_view",id=id_post))
    if session.get("token") is not None:
        user = sessiondb.query(User).filter_by(token=session.get("token")).first();post=sessiondb.query(Post).filter_by(id=id_post).first()
        if user and post is not None:
            x = ChatDB(username=html.escape(user.username),author_id=user.id,message=html.escape(request.form.get("message")),room="com",timestamp=datetime.now(),post_id=id_post)
            sessiondb.add(x)
            sessiondb.commit()
            return redirect(url_for("posts_view",id=id_post))
        else:
            flash("Une erreur est survenue inconnue");return redirect(url_for("home"))
    else:
        return redirect(url_for("auth_login"))


@app.route("/explore")
def explore():
    
    posts = sessiondb.query(Post).all()
    return render_template("posts/explore.html", posts=posts)

#===========================================================================
'''Password_Reset'''
#===========================================================================
@app.route("/pswd/reset",methods=["GET","POST"])
def pswd_reset():

    tokenreset = request.form.get('token') 
    #print(reset_pswd.is_token_expired(tokenreset))

    if request.method == "POST":
        if tokenreset  == None or pswd_is_token_expired(tokenreset):
            try:reset_pswd_tokens.pop(tokenreset, None)
            except:
                pass
            flash("Une erreur est survenue : Invalid token")
            return redirect("/")  
        tokendata = reset_pswd_tokens.get(tokenreset)
        print(reset_pswd_tokens)
        reset_pswd_tokens.pop(tokenreset, None)  
        if tokendata is not None:
            email = tokendata["email"]
            newpassword = request.form.get("password")
            u = sessiondb.query(User).filter_by(email=email).first()
            if u is not None:
                u.password = hashmng.hash_text(newpassword)
                caca = randomstr() 
                u.token = caca;session["token"] = caca
                sessiondb.commit()
                return redirect("/")
            else:
                flash("Une erreur est survenue : Une erreur est survenue inconnue !")
                return redirect("/")               

        else:
            flash("Une erreur est survenue : Compte inexistant !")
            return redirect("/")
    elif request.method == "GET":

        return render_template("auth/pswd_reset.html")
@app.route("/very/fun")
def very_fun():
    return redirect("../../../../not/very/fun")
@app.route("/not/very/fun")
def not_very_fun():
    return redirect("https://www.youtube.com/watch?v=Gc2u6AFImn8")
@app.route("/pswd/ask_reset",methods=["GET","POST"])
def pswd_reset_ask():
    if request.method == "POST":
        u = sessiondb.query(User).filter_by(email=request.form.get("email")).first()

        if u is not None:
            d5 = pswd_generate_token(email=request.form.get("email"))
            mail = mt.Mail(sender=mt.Address(email=config.MAIL, name="[Quarko] : Changement de mot de passe"),to=[mt.Address(email=u.email)],subject="Changement de mot de passe",text=f"Bonjour, vous avez récemment demander le changement de mot-de-passe cliquer ici : https://quarko.linux-scratcher.fr/pswd/reset?token={d5} \nCe lien expire dans 15 minutes ! \n \n - Quarko Team",category="password-reset")
            try:
                mail_client.send(mail)
                flash(f"Un mail a été envoyé à : {u.email}");return redirect(url_for("pswd_reset_ask"))
            except Exception as e:
                print(e)
                flash("Une Une erreur est survenue est survenue ! merci de nous contacter sur discord !");return redirect(url_for("pswd_reset_ask"))
        else:
            flash("Compte inexistant !")
            return redirect("../login")
    elif request.method == "GET":
        return render_template("auth/pswd_reset_ask.html")

# Search Manager
@app.route("/search")
def search():
    try:
        query = request.values["query"]
    except:
        query = ""
    datd = sessiondb.query(User).filter(User.username.like(f'%{query}%'))
    return render_template("search.html", results=datd)

#handler d'Une erreur est survenue :
@app.errorhandler(500)
def internal_server_error(e):
    print(traceback.format_exc())
    err_id = secure_random(0,500000000)
    webhooklog.send_log_webhook(title="❌・Une Une erreur est survenue est survenue !",text=f"# Une Une erreur est survenue est survenue :  \n > Route : `{request.url}` \n > TraceBack :  \n```python{traceback.format_exc()}``` \n > ID de l'Une erreur est survenue `{err_id}`")
    try:
        sessiondb.rollback()
    except:
        pass
    return render_template("err/500.html",err_id=err_id)


'''PARTIE TCHAT'''
CHAT_CONNECT = {"public-1": 0}
@app.route("/chat/public")
def chat_public():
    if session.get("token") is not None:
        return render_template("chat/public.html")
    else:
        flash("Veuiller vous connecter !")
        return redirect("../../../../login")

@socketio.on('connect')
def handle_connect(data):
    join_room("public-1")# temporaire hein
    CHAT_CONNECT["public-1"] += 1
    stats.send_data({"connected_chat":CHAT_CONNECT["public-1"]})

    emit('update_connected', {'update_connected':CHAT_CONNECT["public-1"]})
@socketio.on('send_message')
def handle_send_message(data):
    u = sessiondb.query(User).filter_by(token=data.get("token")).first()
    if u is not None:
        if u.staff == "1":
            staff = "true"
        else:
            staff = "false"
        webhooklog.send_log_webhook(title="💬 Tchat Publique - Message",text=f"> Message : `{data.get('message')}` \n > Pseudo de la personne qui a envoyé le message : `{u.username}` \n > Action : `SEND_MESSAGE`")
        emit('send_message', {'username': u.username, 'message': data.get("message"),'pp':u.profile_url,'admin':staff}, room=data.get("room"))
@socketio.on('disconnect')
def handle_disconnect():
    CHAT_CONNECT["public-1"] -= 1
    stats.send_data({"connected_chat":CHAT_CONNECT["public-1"]})
    emit('update_connected', {'update_connected':CHAT_CONNECT["public-1"]}) #temporaire
#dashboard.bind(app)

#@app.route("/panelv2")
#def panelv2():
#    return render_template("/admin/new.html")
''''Mobile App'''''

@app.route("/mobile/check_login")
def mobile_check_login():
    if session.get("token") is not None:
        return redirect(url_for("home"))
    else:
        return redirect(url_for("auth_login"))
'''API'''
OAUTH2_TOKEN_LIST= {}
@app.route("/api/oauth2/token",methods=["GET"])
def api_oauth2_token():
    TOKEN  = request.values.get("TOKEN")
    if TOKEN in OAUTH2_TOKEN_LIST:
        user_id = OAUTH2_TOKEN_LIST[TOKEN]
        user = sessiondb.query(User).filter_by(id=user_id).first()
        if user is not None:
            return jsonify({"status":"done","email":user.email,"username":user.username,"id":user.id,"join_date":user.join_date,"staff":user.staff}),200
    
    return jsonify({"status":"error","message":"unknow"}),400
@app.route("/api/oauth2/login",methods=["POST","GET"])
def api_oauth2_login():
    if session.get("token") is not None:
        if request.args.get("app_name") and request.args.get("redirect_url"):
            if "quarko" in request.args.get("app_name").lower():
                return redirect("/")
            else:
                TOKEN = randomstr()
                user = sessiondb.query(User).filter_by(token=session.get("token")).first()
                OAUTH2_TOKEN_LIST.update({TOKEN:user.id})
                return render_template("auth/oauth2_login.html",app_name=request.args.get("app_name"),redirect_url=request.args.get("redirect_url"),TOKEN=TOKEN)
    return redirect(url_for("auth_login"))

@app.route("/api/posts/read/<string:id>",methods=["GET"])
def api_posts_read(id):
    post = sessiondb.query(Post).filter_by(id=id).first()
    if post is not None:   
        return jsonify({"status":"ok","title":post.title,"text":post.text,"author":post.author,"likes":post.likes,"views":post.views,"attachements":post.attachements}),200
    return jsonify({"status":"error","message":"invalid_id?"}),400

@app.route("/api/posts/new",methods=["POST"])
def api_pposts_new():
    if request.json["token"] is not None:
        user = sessiondb.query(User).filter_by(token=request.json["token"]).first()
        if user is not None:
            if request.json["title"] and request.json["text"]:
                post = Post(author=user.username,id=secure_random(10000000,1000000000000),title=request.json["title"],views="0",text=request.json["text"],attachements="empty")
                sessiondb.add(post)
                sessiondb.commit()
                return jsonify({"status":"ok","id":post.id}),200
    return jsonify({"status":"error","message":"invalid_token_or_not_valid_data"}),400

@app.route("/api/posts/delete",methods=["DELETE"])
def api_posts_delete():
    if request.json["token"] is not None:
        user = sessiondb.query(User).filter_by(token=request.json["token"]).first()
        if user is not None:
            if request.json["id"] is not None:
                post = sessiondb.query(Post).filter_by(id=request.json["id"]).first()
                if post is not None:
                    if post.author == user.username:
                        sessiondb.delete(post)
                        sessiondb.commit()
                        return jsonify({"status":"ok"}),200
                    else:
                        return jsonify({"status":"error","message":"not_author"}),403
    return jsonify({"status":"error","message":"invalid_token_or_not_valid_data"}),400


@app.route("/api/posts/comments/new",methods=["POST"])
def api_posts_comments_new():
    if request.json["token"] is not None:
        user = sessiondb.query(User).filter_by(token=request.json["token"]).first()
        if user is not None:
            if request.json["id"] is not None:
                post = sessiondb.query(Post).filter_by(id=request.json["id"]).first()
                if post is not None:
                    if request.json["message"] is not None:
                        chat = ChatDB(username=user.username,author_id=user.id,message=request.json["message"],room="com",timestamp=datetime.now(),post_id=request.json["id_post"])
                        sessiondb.add(chat)
                        sessiondb.commit()
                        return jsonify({"status":"done"}),200

    return jsonify({"status":"error","message":"invalid_token_or_not_valid_data"}),400

@app.route("/api/me")
def api_me():
    if request.json["token"] is not None:
        user = sessiondb.query(User).filter_by(token=request.json["token"]).first()
        if user is not None:
            return jsonify({"status":"done","username":user.username,"id":user.id,"certified":user.certified,"staff":user.staff,"premium":user.premium,"bio":user.bio,"background_url":user.background_url,"followers":user.followers}),200
    return jsonify({"status":"error","message":"invalid_token_or_not_valid_data"}),400

@app.route("/api/get_token")
def api_get_token():
    if session.get("token") is not None:
        return jsonify({"status":"ok","token":session.get("token")}),200
    return redirect("/")
if __name__ == '__main__':
    print("Done ! (serv web start)")
    stats.stats("Quarko Started",{"status":"Started"})
    # check if a user exist
    try:
        x = sessiondb.query(User).filter_by(staff='1').first()
        if x is None:
            PASSWORD = randomstr()
            sessiondb.add(User(username="Admin",email="admin@admin.admin",password=hashmng.hash_text(PASSWORD),bio="Debug user",staff=True,token=randomstr()))
            sessiondb.commit()
            print("[QuarkFOSS] : Admin user created !")
            print("USERNAME : admin@admin.admin")
            print("PASSWORD : ",PASSWORD)
    except Exception as e:
        print(e)
        pass
    socketio.run(app, port=80,host="0.0.0.0")
