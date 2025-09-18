import random as rd
import pandas as pd
import math

from flask import Flask, request, jsonify, make_response

headers =  {"Content-Type":"application/json"}

nbNS = 4

###########
## Fonctions de I/O système

# Define column names
if nbNS == 4:
    column_names=["#Ronde", "NS1", "NS2", "NS3", "NS4", "EO1", "EO2", "EO3", "EO4"]
else:
    column_names=["#Ronde", "NS1", "NS2", "NS3", "NS4", "NS5", "EO1", "EO2", "EO3", "EO4", "EO5"]

extracols_donnes = ["Moyenne NS", "Min NS", "Min EO"]
extracols_scores = []

extrarows_donnes = ["TOTAL"]
extrarows_scores = ["TOTAL", "Rang global", "Rang camp"]

dataframe_donnes = None
dataframe_scores = None

def initDonnes():
    dataframe_donnes = pd.DataFrame(columns=column_names+extracols_donnes)
    for i in range(nbNS * 4): # 4 rounds per pair match
        dataframe_donnes.at[i, "#Ronde"] = i+1
        for j in column_names[1:]:
            dataframe_donnes.at[i, j] = None
        for j in extracols_donnes:
            dataframe_donnes.at[i, j] = None
    for i in range(len(extrarows_donnes)):
        dataframe_donnes.at[4*nbNS+i, column_names[0]] = extrarows_donnes[i]
        for j in column_names[1:]:
            dataframe_donnes.at[4*nbNS+i, j] = None
    dataframe_donnes.to_excel("donnes.xlsx")
    return dataframe_donnes

def initScores():
    dataframe_scores = pd.DataFrame(columns=column_names+extracols_scores)
    for i in range(nbNS * 4): # 4 rounds per pair match
        dataframe_scores.at[i, "#Ronde"] = i+1
        for j in column_names[1:]:
            dataframe_scores.at[i, j] = None
        for j in extracols_scores:
            dataframe_scores.at[i, j] = None
    for i in range(len(extrarows_scores)):
        dataframe_scores.at[4*nbNS+i, column_names[0]] = extrarows_scores[i]
        for j in column_names[1:]:
            dataframe_scores.at[4*nbNS+i, j] = None
    dataframe_scores.to_excel("scores.xlsx")
    return dataframe_scores

class ContradictionScoreError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def getMsg(self):
        return self.msg

class AlreadyReportedCoherentScore(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def getMsg(self):
        return self.msg

class NoScoreToRectify(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def getMsg(self):
        return self.msg

def logRonde(name, team, ronde, score):
    oppTeam = getOpponentTeam(team, ronde)
    if dataframe_donnes.at[int(ronde)-1, team] == None and dataframe_donnes.at[int(ronde)-1, oppTeam] == None:
        dataframe_donnes.at[int(ronde)-1, team] = int(score)
        dataframe_donnes.at[int(ronde)-1, oppTeam] = -int(score)
        finalizeRound(ronde)
        finalizeTeam_Rounds(team)
        dataframe_donnes.to_excel("donnes.xlsx")
    elif dataframe_donnes.at[int(ronde)-1, getOpponentTeam(team, ronde)] == -int(score):
        raise AlreadyReportedCoherentScore(f"{oppTeam} a déjà annoncé un score compatible avec le vôtre pour la ronde #{ronde}. Vous pouvez retourner au menu principal.") # "silent" error : coherent score duplication by opponent team
    else:
        oldscore = dataframe_donnes.at[int(ronde)-1, getOpponentTeam(team, ronde)]
        raise ContradictionScoreError(f"{team} a annoncé {score} points pour la ronde #{ronde} mais {oppTeam} avait déjà annoncé un score incompatible de {oldscore}")

def rectifyRonde(name, team, ronde, score):
    oppTeam = getOpponentTeam(team, ronde)
    if dataframe_donnes.at[int(ronde)-1, team] != None and dataframe_donnes.at[int(ronde)-1, oppTeam] != None:
        dataframe_donnes.at[int(ronde)-1, team] = int(score)
        dataframe_donnes.at[int(ronde)-1, oppTeam] = -int(score)
        finalizeRound(ronde)
        finalizeTeam_Rounds(team)
        dataframe_donnes.to_excel("donnes.xlsx")
    else:
        raise NoScoreToRectify(f"{team} ne peut pas rectifier son score à la ronde #{ronde} car aucun score n'avait été rentré auparavant")

def logRondeText(name, team, ronde, score):
    with open("donnes.txt", "a") as f:
        f.write(f"{name} : {team} marque {score} à la ronde {ronde}\n")

def getRecordedRounds(team):
    res = []
    for i in range(4*nbNS):
        score = dataframe_donnes.at[i, team]
        if score != None:
            res.append((i+1, score, getOpponentTeam(team, i+1)))
    return res

def checkRowCompleteness(ronde):
    for i in column_names:
        if dataframe_donnes.at[int(ronde)-1, i] == None:
            return False
    return True

def checkColCompleteness_Rounds(team):
    for i in range(4*nbNS):
        if dataframe_donnes.at[i, team] == None:
            return False
    return True

def checkColCompleteness_Scores(team):
    for i in range(4*nbNS):
        if dataframe_scores.at[i, team] == None:
            return False
    return True

def checkScoreCompleteness():
    for team in column_names[1:]:
        if not (checkColCompleteness_Rounds(team) and checkColCompleteness_Scores(team)): # round completeness SHOULD mean score completeness if updates are well started
            return False
    return True

def updateRankings():
    if checkScoreCompleteness():
        scores_all_raw = list(dataframe_scores.at[4*nbNS, team] for team in column_names[1:])
        scores_all_sorted = scores_all_raw[:]
        scores_all_sorted.sort(reverse=True)
        rankings_full = [scores_all_sorted.index(i)+1 for i in scores_all_raw]
        scores_NS_raw = list(dataframe_scores.at[4*nbNS, team] for team in column_names[1:nbNS+1])
        scores_NS_sorted = scores_NS_raw[:]
        scores_NS_sorted.sort(reverse=True)
        rankings_NS = [scores_NS_sorted.index(i)+1 for i in scores_NS_raw]
        scores_EO_raw = list(dataframe_scores.at[4*nbNS, team] for team in column_names[nbNS+1:2*nbNS+1])
        scores_EO_sorted = scores_EO_raw[:]
        scores_EO_sorted.sort(reverse=True)
        rankings_EO = [scores_EO_sorted.index(i)+1 for i in scores_EO_raw]
        rankings_separated = rankings_NS + rankings_EO
        for i in range(2*nbNS):
            dataframe_scores.at[4*nbNS+1, column_names[i+1]] = rankings_full[i]
            dataframe_scores.at[4*nbNS+2, column_names[i+1]] = rankings_separated[i]
        dataframe_scores.to_excel("scores.xlsx")

def finalizeTeam_Rounds(team):
    if checkColCompleteness_Rounds(team):
        dataframe_donnes.at[4*nbNS, team] = sum(dataframe_donnes.at[i, team] for i in range(4*nbNS))
        dataframe_donnes.to_excel("donnes.xlsx")
        finalizeTeam_Scores(team)

def finalizeTeam_Scores(team):
    if checkColCompleteness_Scores(team):
        dataframe_scores.at[4*nbNS, team] = sum(dataframe_scores.at[i, team] for i in range(4*nbNS))
        dataframe_scores.to_excel("scores.xlsx")
        updateRankings()

def finalizeRound(ronde):
    if checkRowCompleteness(ronde):
        round_avg = sum(dataframe_donnes.at[int(ronde)-1, "NS"+str(i)] for i in range(1, nbNS+1)) / nbNS
        dataframe_donnes.at[int(ronde)-1, "Moyenne NS"] = round_avg
        dataframe_donnes.at[int(ronde)-1, "Min NS"] = min(dataframe_donnes.at[int(ronde)-1, "NS"+str(i)] for i in range(1, nbNS+1)) / nbNS
        dataframe_donnes.at[int(ronde)-1, "Min EO"] = min(dataframe_donnes.at[int(ronde)-1, "EO"+str(i)] for i in range(1, nbNS+1)) / nbNS
        dataframe_donnes.to_excel("donnes.xlsx")
        for team in column_names[1:]: # compute round score for every team : the lambda is sign(score) * sqrt(abs(score - avg))
            team_score_for_round = dataframe_donnes.at[int(ronde)-1, team]
            dataframe_scores.at[int(ronde)-1, team] = (1 if team_score_for_round >= round_avg else -1) * math.sqrt(math.abs(round_avg - team_score_for_round))
        dataframe_scores.to_excel("scores.xlsx")

###########
## Fonctions de calcul de match

# 4 teams :
# 1-1 2-3 3-2 4-4
# 1-4 2-2 3-1 4-3
# 1-2 2-4 3-3 4-1
# 1-3 2-1 3-4 4-2

def getOpponentTeam(team, ronde):
    if team[:2] == "NS":
        return "EO" + str([1,3,2,4,4,2,1,3,2,4,3,1,3,1,4,2][(ronde-1)//nbNS * nbNS + int(team[2])-1])
    else:
        return "NS" + str([1,3,2,4,3,2,4,1,4,1,3,2,2,4,1,3][(ronde-1)//nbNS * nbNS + int(team[2])-1])

# TODO implem pour 5 équipes de chaque côté

""" for i in range(1, 17):
    for j in range(1,5):
        for k in ["NS", "EO"]:
            if getOpponentTeam(getOpponentTeam(k+str(j), i), i) != k + str(j):
                print(f"Mismatch at round #{i}, team {k+str(j)}")
 """

app = Flask(__name__)
# port is 5000

with app.app_context(): # things to do at run, before any request
    dataframe_donnes = initDonnes()
    dataframe_scores = initScores()
    # WARNING : restarting the server will clear the current tables !!!

###########
## Fonctions de l'API

# This code trusts the user and well-formed character of the requests, even if it performs some basic checks at times.

@app.get("/")
def website_root():
    resp = make_response("""<p><h1>BELOTE</h1></p><p><a href="/register"><h2>CONNEXION</h2></a></p><p><a href="/submit"><h2>RENTRER RONDE</h2></a></p><p><a href="/pastrounds"><h2>CONSULTER ANCIENNES RONDES</h2></a></p><p><a href="/rectification"><h2>RECTIFIER RONDE</h2></a></p><p><a href="/scores"><h2>CONSULTER CLASSEMENT</h2></a></p><p><a href="/unregister"><h2>DÉCONNEXION</h2></a></p>""")
    return resp, 200

@app.get("/submit")
def submitcode_get():
    resp = make_response("""<p><form action="submit" method="post" enctype=multipart/form-data>
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
</form></p>
<p><a href="/">RETOUR PAGE PRINCIPALE</a></p>
""")
    return resp, 200

@app.post("/submit")
def submitcode_post():
    name = request.cookies.get("belote_user_id")
    team = request.cookies.get("belote_user_team")
    if name == None or team == None:
        resp = make_response("""<p>Non identifié auprès serveur - soumission de score ignorée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 401
    try:
        ronde = int(request.form.get("round"))
        score = int(request.form.get("score"))
        assert 1 <= ronde and ronde <= 20
        assert -250 <= score and score <= 250
    except Exception:
        resp = make_response("""<p>Format de ronde invalide - soumission de score ignorée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 400
    # file operation using pandas
    logRondeText(name, team, ronde, score)
    try:
        logRonde(name, team, ronde, score)
    except AlreadyReportedCoherentScore as e:
        resp = make_response(f"""<p>{e.getMsg()}<p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 208
    except ContradictionScoreError as e:
        resp = make_response(f"""<p>ERREUR : {e.getMsg()}<p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 409
    resp = make_response("""<p>Ronde correctement enregistrée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
    return resp, 201

@app.get("/scores")
def scores_get():
    if checkScoreCompleteness():
        return make_response("""<p>Tous les scores ont été calculés et sont disponibles. C'est l'heure du grand reveal !</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>"""), 200
    else:
        return make_response("""<p>La belote n'est pas terminée pour le moment. Encore un peu de patience !</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>"""), 200

@app.get("/pastrounds")
def pastrounds_get():
    name = request.cookies.get("belote_user_id")
    team = request.cookies.get("belote_user_team")
    if name == None or team == None:
        resp = make_response("""<p>Non identifié auprès serveur - aucun historique de rondes disponible.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 401
    res = f"""<p>RONDES EXISTANTES POUR {name} (équipe {team}) :</p><table style="width:100%"><tr>
        <td>#RONDE</td>
        <td>RÉSULTAT</td>
        </tr>"""
    for (ronde, score, oppTeam) in getRecordedRounds(team):
        res += f"<tr><td>Ronde #{ronde}</td><td>{score} contre {oppTeam}</td></tr>"
    return make_response(res + """</table><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>"""), 200

@app.get("/rectification")
def rectification_get():
    resp = make_response("""<p><form action="rectification" method="post" enctype=multipart/form-data>
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
</form></p>
<p><a href="/">RETOUR PAGE PRINCIPALE</a></p>
""")
    return resp, 200

@app.post("/rectification")
def rectification_post():
    name = request.cookies.get("belote_user_id")
    team = request.cookies.get("belote_user_team")
    if name == None or team == None:
        resp = make_response("""<p>Non identifié auprès serveur - rectification de score ignorée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 401
    try:
        ronde = int(request.form.get("round"))
        score = int(request.form.get("score"))
        assert 1 <= ronde and ronde <= 20
        assert -250 <= score and score <= 250
    except Exception:
        resp = make_response("""<p>Format de ronde invalide - rectification de score ignorée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 400
    # file operation using pandas
    logRondeText(name, team, ronde, score)
    try:
        rectifyRonde(name, team, ronde, score)
    except NoScoreToRectify as e:
        return make_response(f"""<p>{e.getMsg()}"""), 405
    resp = make_response("""<p>Ronde correctement rectifiée.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
    return resp, 201

@app.get("/register")
def register_get():
    resp = make_response("""<p><form action="register" method="post" enctype=multipart/form-data>
    <p>Nom : <input id="name" name="name" type="text"/></p>
    <p>Équipe :
    <select id="team" name="team">
        <option value=0 disabled selected>Choisissez une équipe...</option>
        <option value="NS1">NS1</option>
        <option value="NS2">NS2</option>
        <option value="NS3">NS3</option>
        <option value="NS4">NS4</option>
        <option value="NS5">NS5</option>
        <option value="EO1">EO1</option>
        <option value="EO2">EO2</option>
        <option value="EO3">EO3</option>
        <option value="EO4">EO4</option>
        <option value="EO5">EO5</option>
	</select></p>
    <input type="submit" value="Envoyer">
</form></p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
    return resp, 200

@app.post("/register")
def register_post():
    # build according cookie
    # add cookie to jar
    name = request.form.get("name")
    team = request.form.get("team")
    if name == None or team == None:
        # invalid form post
        resp = make_response("""<p>Enregistrement invalide.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 400
    cookie1 = request.cookies.get("belote_user_id")
    cookie2 = request.cookies.get("belote_user_team")
    resp = make_response(f"""<p>Enregistré en temps que {str(name)} ({str(team)}) !</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
    if cookie1 == None or cookie2 == None: # case when only one of them is set is ill-defined and will not be considered apart
        resp.set_cookie("belote_user_id", name)
        resp.set_cookie("belote_user_team", team)
        return resp, 201
    else:
        # user already exists
        resp = make_response(f"""<p>Déjà enregistré en temps que {str(cookie1)} ({str(cookie2)}) !</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 403

@app.get("/unregister")
def unregister():
    cookie = request.cookies.get("belote_user_id")
    if cookie != None:
        resp = make_response("""<p>Déconnecté.</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        resp.delete_cookie("belote_user_id")
        resp.delete_cookie("belote_user_team")
        return resp, 201
    else:
        # user doesn't exist
        resp = make_response("""<p>Vous n'êtes pas connecté au serveur !</p><p><a href="/">RETOUR PAGE PRINCIPALE</a></p>""")
        return resp, 403