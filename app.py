from bson import ObjectId
from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
from functools import wraps
import pymongo
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from flask_pymongo import PyMongo

app = Flask(__name__)
app.secret_key = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'

# Database locale
client = pymongo.MongoClient('localhost', 27017)
db = client.login


#Database su cloud
#app.config['MONGO_URI'] = 'mongodb+srv://RafMosca:RafMoscaDB@cluster0.tt9vd.mongodb.net/login?retryWrites=true&w=majority'
#mongo = PyMongo(app)
#db = mongo.db

# Decorators
def login_required(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      return redirect('/')
  
  return wrap

# Routes
from user import routes

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/dashboard/')
@login_required
def dashboard():
  return render_template('dashboard.html')


@app.route('/raccolta/')
@login_required
def raccolta():
    return render_template('raccolta.html')

@app.route('/utente/')
@login_required
def utente():
    return render_template('page_account.html')

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

@app.route('/foodbox/')
@login_required
def cibo():
    foodb = db.foodbox.find()
    return render_template('cibo.html', foodb=foodb)


@app.route('/add', methods=['POST'])
def add_todo():
    rifiuto = request.form.get('new-todo')
    if db.raccolta.find_one({'rifiuto': rifiuto}):
        trovato = db.raccolta.find_one({'rifiuto': rifiuto})
        dove = trovato['dove']
        return render_template('raccolta.html', dove=dove)
    else:
        flash('Rifiuto non trovato!')
        return render_template('raccolta.html')

@app.route('/ordina/<oid>,<utente>', methods=('POST',))
def ordina(oid, utente):
    box = db.foodbox.find_one({'_id': ObjectId(oid)})
    quanti = box['quantita']
    tipo = box['tipo']
    negozio = box['negozio']
    indirizzo = box['indirizzo']
    utentebox = box['utente']
    contenuto = box['contenuto']

    db.foodbox.update_one({"_id": ObjectId(oid)}, {"$set": {"quantita": quanti-1}})
    db.ordinazioni.insert_one({'utente' : utente, 'box_number': ObjectId(oid), 'tipo' : tipo, 'negozio':negozio, 'indirizzo': indirizzo, 'utente_box': utentebox, 'contenuto':contenuto})

    return redirect('/foodbox/')

@app.route('/elimina/<oid>', methods=('POST',))
def elimina(oid):
    db.foodbox.delete_one({"_id": ObjectId(oid)})
    db.ordinazioni.delete_many({"box_number": ObjectId(oid)})
    return redirect('/myboxcaricati/')




@app.route('/creabox/')
@login_required
def creabox():
    return render_template('creabox.html')

@app.route('/create/<utente>', methods=['GET', 'POST'])
def create(utente):
    tipo = request.form.get('tipo')
    contenuto = request.form.get('contenuto')
    quantita = request.form.get('quantita')
    negozio = request.form.get('negozio')
    indirizzo = request.form.get('indirizzo')
    db.foodbox.insert_one({'utente': utente, 'tipo': tipo, 'contenuto': contenuto, 'quantita': int(quantita), 'negozio': negozio, 'indirizzo': indirizzo})
    return render_template('creabox.html')



@app.route('/mybox/')
@login_required
def mybox():
    ordinazione = db.ordinazioni.find()
    return render_template('mybox.html', ordinazione=ordinazione)

@app.route('/myboxcaricati/')
@login_required
def myboxcaricati():
    foodb = list(db.foodbox.find())
    ordi = list(db.ordinazioni.find())
    return render_template('myboxcaricati.html', foodb=foodb, ordi=ordi)

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

@app.route('/boxritirato/<oid>', methods=('POST',))
def boxritirato(oid):
    db.ordinazioni.delete_one({"_id": ObjectId(oid)})
    return redirect('/mybox/')