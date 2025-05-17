import random as rd
import pandas as pd

from flask import Flask, request, jsonify, make_response

headers =  {"Content-Type":"application/json"}

app = Flask(__name__)
# port is 5000

###########
## Fonctions de I/O système

def logRonde(name, teamtype, ronde, score):
    # pandas stuff
    pass

###########
## Fonctions de l'API

# This code trusts the user and well-formed character of the requests, even if it performs some basic checks at times.

@app.get("/")
def website_root():
    resp = make_response("""<p>BELOTE</p><p><a href="/register">CONNEXION</a></p><p><a href="/submit">RENTRER RONDE</a></p><p><a href="/unregister">DÉCONNEXION</a></p>""")
    return resp, 200

@app.get("/submit")
def submitcode_get():
    resp = make_response("""<form action="submit" method="post" enctype=multipart/form-data>
    <p>Ronde :
    <select id="round" name="round">
        <option value=0 disabled selected>Choisissez un numéro de ronde...</option>
        <option value=1>1</option>
        <option value=2>2</option>
        <option value=3>3</option>
        <option value=4>4</option>
        <option value=5>5</option>
        <option value=6>6</option>
        <option value=7>7</option>
        <option value=8>8</option>
        <option value=9>9</option>
        <option value=10>10</option>
        <option value=11>11</option>
        <option value=12>12</option>
        <option value=13>13</option>
        <option value=14>14</option>
        <option value=15>15</option>
        <option value=16>16</option>
        <option value=17>17</option>
        <option value=18>18</option>
        <option value=19>19</option>
        <option value=20>20</option>
	</select></p>
    <p>Score (négatif si défaite) : <input id="score" name="score" type="number min="-1000" max="1000"/></p>
    <p><input type="submit" value="Submit"></p>
</form>""")
    return resp, 200

@app.post("/submit")
def submitcode_post():
    name = request.cookies.get("belote_user_id")
    teamtype = request.cookies.get("belote_user_team_type")
    if name == None or teamtype == None:
        resp = make_response("Non identifié auprès serveur - soumission de score ignorée.")
        return resp, 401
    try:
        ronde = int(request.form.get("round"))
        score = int(request.form.get("score"))
        assert 1 <= ronde and ronde <= 20
    except Exception:
        resp = make_response("Format de ronde invalide - soumission de score ignorée.")
        return resp, 400
    # file operation using pandas
    logRonde(name, teamtype, ronde, score)
    resp = make_response("Ronde correctement enregistrée.")
    return resp, 201

@app.get("/register")
def register_get():
    resp = make_response("""<form action="register" method="post" enctype=multipart/form-data>
    <p>Nom : <input id="name" name="name" type="text"/></p>
    <p>Type d'équipe : <input type="radio" name="teamtype" value="NS" id="NS" required/> NS <input type="radio" name="teamtype" value="EO" id="EO"/> EO</p>
    <input type="submit" value="Envoyer">
</form>""")
    return resp, 200

@app.post("/register")
def register_post():
    # build according cookie
    # add cookie to jar
    name = request.form.get("name")
    teamtype = request.form.get("teamtype")
    if name == None or teamtype == None:
        # invalid form post
        resp = make_response("Enregistrement invalide.")
        return resp, 400
    cookie1 = request.cookies.get("belote_user_id")
    cookie2 = request.cookies.get("belote_user_team_type")
    resp = make_response(f"Enregistré en temps que {str(name)} ({str(teamtype)}) !")
    if cookie1 == None or cookie2 == None: # case when only one of them is set is ill-defined and will not be considered apart
        resp.set_cookie("belote_user_id", name)
        resp.set_cookie("belote_user_team_type", teamtype)
        return resp, 201
    else:
        # user already exists
        resp = make_response(f"Déjà enregistré en temps que {str(cookie1)} ({str(cookie2)}) !")
        return resp, 403

@app.get("/unregister")
def unregister():
    cookie = request.cookies.get("belote_user_id")
    if cookie != None:
        resp = make_response("Déconnecté.")
        resp.delete_cookie("belote_user_id")
        resp.delete_cookie("belote_user_team_type")
        return resp, 201
    else:
        # user doesn't exist
        resp = make_response("Vous n'êtes pas connecté au serveur !")
        return resp, 403