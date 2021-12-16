from bson import ObjectId
from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
from functools import wraps
import pymongo
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from flask_pymongo import PyMongo
import uuid

app = Flask(__name__)
#genero la secret key
app.secret_key = uuid.uuid4().hex

from datetime import timedelta
app.permanent_session_lifetime = timedelta(minutes=30)

# Database locale
client = pymongo.MongoClient('localhost', 27017)
db = client.login


#Database su cloud
#app.config['MONGO_URI'] = 'mongodb+srv://RafMosca:RafMoscaDB@cluster0.tt9vd.mongodb.net/login?retryWrites=true&w=majority'
#mongo = PyMongo(app)
#db = mongo.db

# FUNZIONE CHE CONTROLLA SE SI E' LOGGATI
def login_required(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      return redirect('/log/')

  return wrap

# Routes
from user import routes

@app.route('/')
def home():
  return render_template('dashboard.html')

@app.route('/dashboard/')
def dashboard():
  return render_template('dashboard.html')

@app.route('/log/')
def log():
  return render_template('log.html')

@app.route('/raccolta/')
def raccolta():
    return render_template('raccolta.html')

@app.route('/utente/')
@login_required
def utente():
    return render_template('page_account.html')

@app.route('/foodbox/')
@login_required
def cibo():
    count = 0
    foodd = db.foodbox.find()
    for foodbox in foodd:
        if foodbox['utente'] != session['user']['email'] and foodbox['quantita']!=0:
            count += 1
    if count == 0:
        flash('Non esistono box da prenotare!')
        return render_template('cibo.html')
    else:
        foodb = db.foodbox.find()
        return render_template('cibo.html', foodb=foodb)


@app.route('/creabox/')
@login_required
def creabox():
    return render_template('creabox.html')

@app.route('/mybox/')
@login_required
def mybox():
    count = 0
    ordinazione = db.ordinazioni.find()
    for ordi in ordinazione:
        if ordi['utente'] == session['user']['email']:
            count = count +1

    if count == 0:
        flash('Non hai nessuna box prenotata, corri ad ordinarne una!')
        return render_template(('mybox.html'))
    else:
        ordinazione = db.ordinazioni.find()
        return render_template('mybox.html', ordinazione=ordinazione)



@app.route('/myboxcaricati/')
@login_required
def myboxcaricati():
    count = 0
    foodd = db.foodbox.find()
    for foodbox in foodd:
        if foodbox['utente'] == session['user']['email']:
            count = count + 1

    if count == 0:
        flash('Non hai caricato nessuna box, corri ad crearne una!')
        return render_template(('myboxcaricati.html'))
    else:
        foodb = list(db.foodbox.find())
        ordi = list(db.ordinazioni.find())
        return render_template('myboxcaricati.html', foodb=foodb, ordi=ordi)




#FUNZIONE CHE MODIFICA LA PASSWORD
@app.route('/modificapass/<utente>', methods=['GET', 'POST'])
def modificapass(utente):
    utentee = db.users.find_one({'email': utente})
    passw = utentee['password']
    if pbkdf2_sha256.verify(request.form.get('password'), passw):
        newpassword = request.form.get('newpassword')
        newpassword = pbkdf2_sha256.encrypt(newpassword)
        db.users.update_one({"email": utente}, {"$set": {"password": newpassword}})
        flash('Password cambiata correttamente!')
        return render_template('page_account.html')
    else:
        flash('Password errata!')
        return render_template('page_account.html')

#FUNZIONE CHE DATO UN RIFIUTO IN INPUT RESTITUISCE DOVE SMALTIRLO
@app.route('/ricerca', methods=['POST'])
def ricerca():
    rifiuto = request.form.get('rifiuto')
    if db.raccolta.find_one({'rifiuto': rifiuto}):
        trovato = db.raccolta.find_one({'rifiuto': rifiuto})
        dove = trovato['dove']
        return render_template('raccolta.html', dove=dove)
    else:
        flash('Rifiuto non trovato!')
        return render_template('raccolta.html')

#FUNZIONE PER ORDINARE UNA FOODBOX
@app.route('/ordina/<oid>,<utente>', methods=('POST',))
def ordina(oid, utente):
    box = db.foodbox.find_one({'_id': ObjectId(oid)})
    quanti = box['quantita']
    nome = box['nome']
    negozio = box['negozio']
    indirizzo = box['indirizzo']
    utentebox = box['utente']
    contenuto = box['contenuto']

    db.foodbox.update_one({"_id": ObjectId(oid)}, {"$set": {"quantita": quanti-1}})
    db.ordinazioni.insert_one({'utente' : utente, 'box_number': ObjectId(oid), 'tipo' : nome, 'negozio':negozio, 'indirizzo': indirizzo, 'utente_box': utentebox, 'contenuto':contenuto})

    return redirect('/foodbox/')

#FUNZIONE PER ELIMINARE UNA FOODBOX E LE RELATIVE ORDINAZIONE
@app.route('/elimina/<oid>', methods=('POST',))
def elimina(oid):
    db.foodbox.delete_one({"_id": ObjectId(oid)})
    db.ordinazioni.delete_many({"box_number": ObjectId(oid)})
    return redirect('/myboxcaricati/')

#FUNZIONE PER CREARE UNA FOODBOX
@app.route('/create/<utente>', methods=['GET', 'POST'])
def create(utente):
    nome = request.form.get('nome')
    contenuto = request.form.get('contenuto')
    tipo = request.form.get('tipo')
    quantita = request.form.get('quantita')
    negozio = request.form.get('negozio')
    indirizzo = request.form.get('indirizzo')
    db.foodbox.insert_one({'utente': utente, 'nome': nome, 'contenuto': contenuto, 'tipo': tipo, 'quantita': int(quantita), 'negozio': negozio, 'indirizzo': indirizzo})
    return render_template('creabox.html')

#FUNZIONE PER ELIMINARE UN ORDINAZIONE
@app.route('/eliminaordi/<oid>', methods=('POST',))
def eliminaordi(oid):
    ordi = db.ordinazioni.find_one({'_id': ObjectId(oid)})
    idbox = ordi['box_number']
    box = db.foodbox.find_one({'_id': ObjectId(idbox)})
    utente = ordi['utente_box']
    tipo = ordi ['tipo']
    contenuto = ordi ['contenuto']
    negozio = ordi['negozio']
    indirizzo = ordi['indirizzo']
    if db.foodbox.find_one({'_id': ObjectId(idbox)}):
        quanti = box['quantita']
        db.foodbox.update_one({"_id": ObjectId(idbox)}, {"$set": {"quantita": quanti + 1}})
        db.ordinazioni.delete_one({"_id": ObjectId(oid)})
    else:
        db.foodbox.insert_one(
            {'utente': utente, 'tipo': tipo, 'contenuto': contenuto, 'quantita': int(1), 'negozio': negozio,
             'indirizzo': indirizzo})
        db.ordinazioni.delete_one({"_id": ObjectId(oid)})
    return redirect('/mybox/')

#FUNZIONE PER ELIMINARE L'ORDINAZIONE UNA VOLTA RITIRATO IL FOODBOX
@app.route('/boxritirato/<oid>', methods=('POST',))
def boxritirato(oid):
    db.ordinazioni.delete_one({"_id": ObjectId(oid)})
    return redirect('/mybox/')

#FUNZIONA PER EFFETTUARE RICERCA IN BASE AL TIPO DI BOX
@app.route('/myboxricerca/<utente>',  methods=['POST'])
def myboxricerca(utente):
    count = 0
    tipo = request.form.get('tipo')
    foodd = db.foodbox.find({'tipo': tipo})
    for foodbox in foodd:
        if foodbox['utente'] != utente:
            count += 1
    if tipo == "TUTTE":
        count += 1

    if count == 0:
        flash('Non esistono box del tipo selezionato!')
        return render_template('cibo.html')

    if db.foodbox.find_one({"tipo": tipo}):
        print ("Trovato!")
    else:
        if tipo != "TUTTE":
            flash('Non esistono box del tipo selezionato!')

    if tipo == "TUTTE":
        foodb = db.foodbox.find()
        return render_template('cibo.html', foodb=foodb)

    if db.foodbox.find({'tipo': tipo}):
        foodb = db.foodbox.find({'tipo': tipo})
        return render_template('cibo.html', foodb=foodb)


    return render_template('cibo.html')
