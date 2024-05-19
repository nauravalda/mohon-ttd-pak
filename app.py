from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import os
import base64
import sqlite3
from collections import OrderedDict

import cipher.rc4 as rc4
import cipher.rsa as rsa

app = Flask(__name__)
app.config['SECRET_KEY'] = 's3cr3t_k3y_Th4t_1s_very_l0ng_and_c0mpl3x'



def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn

def get_mahasiswa(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM mahasiswa")
    rows = cur.fetchall()
    return rows

def get_matakuliah(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM mata_kuliah")
    rows = cur.fetchall()
    return rows
    
def get_all_data(conn):
    cur = conn.cursor()
    cur.execute("SELECT mahasiswa.nim as nim, mahasiswa.nama as nama, mata_kuliah.kode as kode_mk, mata_kuliah.nama as nama_mk, mata_kuliah.sks as sks, nilai.nilai as nilai FROM nilai JOIN mahasiswa ON nilai.nim = mahasiswa.nim JOIN mata_kuliah ON nilai.kode = mata_kuliah.kode;")
    rows = cur.fetchall()
    return rows
def get_all_data_by_nim(conn, nim):
    cur = conn.cursor()
    cur.execute("SELECT mahasiswa.nim as nim, mahasiswa.nama as nama, mata_kuliah.kode as kode_mk, mata_kuliah.nama as nama_mk, mata_kuliah.sks as sks, nilai.nilai as nilai FROM nilai JOIN mahasiswa ON nilai.nim = mahasiswa.nim JOIN mata_kuliah ON nilai.kode = mata_kuliah.kode WHERE mahasiswa.nim = ?;", (nim,))
    rows = cur.fetchall()
    return rows

def get_nama_by_nim(conn, nim):
    cur = conn.cursor()
    cur.execute("SELECT nama FROM mahasiswa WHERE nim = ?", (nim,))
    rows = cur.fetchall()
    nama = rows[0][0]
    return nama

def get_nama_mk_sks_by_kode(conn, kode):
    cur = conn.cursor()
    cur.execute("SELECT nama, sks FROM mata_kuliah WHERE kode = ?", (kode,))
    rows = cur.fetchall()
    nama = rows[0][0]
    sks = rows[0][1]
    return (nama, sks)

    

def hitung_ipk(records):
    total_sks = 0
    total_points = 0
    nilai_dict = {'A': 4.0, 'AB': 3.5, 'B': 3.0, 'BC': 2.5, 'C': 2.0, 'D': 1.0, 'E': 0.0}
    
    for record in records:
        sks = record['sks']
        nilai = record['nilai']
        if nilai in nilai_dict:
            total_points += nilai_dict[nilai] * sks
            total_sks += sks

    if total_sks == 0:
        return 0.0
    
    return total_points / total_sks

def encrypt (data_akademik):
    for nim in data_akademik:
        for record in data_akademik[nim]['records']:
            record['nim'] = base64.b64encode(rc4.rc4(bytearray(record['nim'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
            record['nama'] = base64.b64encode(rc4.rc4(bytearray(record['nama'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
            record['kode_mk'] = base64.b64encode(rc4.rc4(bytearray(record['kode_mk'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
            record['nama_mk'] = base64.b64encode(rc4.rc4(bytearray(record['nama_mk'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
            record['sks'] = base64.b64encode(rc4.rc4(bytearray(str(record['sks']), 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
            record['nilai'] = base64.b64encode(rc4.rc4(bytearray(record['nilai'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
        data_akademik[nim]['nama'] = base64.b64encode(rc4.rc4(bytearray(data_akademik[nim]['nama'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
        data_akademik[nim]['ipk'] = base64.b64encode(rc4.rc4(bytearray(str(data_akademik[nim]['ipk']), 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
        data_akademik[nim]['ttd'] = base64.b64encode(rc4.rc4(bytearray(data_akademik[nim]['ttd'], 'utf-8'), bytes(session['rc4_key'], 'utf-8'))).decode('utf-8')
    return data_akademik

def decrypt (data_akademik):
    for nim in data_akademik:
        for record in data_akademik[nim]['records']:
            record['nim'] = rc4.rc4(base64.b64decode(record['nim']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
            record['nama'] = rc4.rc4(base64.b64decode(record['nama']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
            record['kode_mk'] = rc4.rc4(base64.b64decode(record['kode_mk']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
            record['nama_mk'] = rc4.rc4(base64.b64decode(record['nama_mk']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
            record['sks'] = int(rc4.rc4(base64.b64decode(record['sks']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8'))
            record['nilai'] = rc4.rc4(base64.b64decode(record['nilai']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
        data_akademik[nim]['nama'] = rc4.rc4(base64.b64decode(data_akademik[nim]['nama']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
        data_akademik[nim]['ipk'] = float(rc4.rc4(base64.b64decode(data_akademik[nim]['ipk']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8'))
        data_akademik[nim]['ttd'] = rc4.rc4(base64.b64decode(data_akademik[nim]['ttd']), bytes(session['rc4_key'], 'utf-8')).decode('utf-8')
    return data_akademik

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inputdata', methods=['GET', 'POST'])
def inputdata():
    if request.method == 'POST':
        if 'nim' in request.form and 'nama' in request.form:
            nim = request.form['nim']
            nama = request.form['nama']
            conn = create_connection('database/data_akademik.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO mahasiswa (nim, nama) VALUES (?, ?)", (nim, nama))
            conn.commit()
            conn.close()
        elif 'kode' in request.form and 'nama' in request.form and 'sks' in request.form:
            kode = request.form['kode']
            nama = request.form['nama']
            sks = request.form['sks']
            conn = create_connection('database/data_akademik.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO mata_kuliah (kode, nama, sks) VALUES (?, ?, ?)", (kode, nama, sks))
            conn.commit()
            conn.close()
        elif 'nim_nilai' in request.form and 'kode_nilai' in request.form and 'nilai' in request.form:
            nim_nilai = request.form['nim_nilai']
            kode_nilai = request.form['kode_nilai']
            nilai = request.form['nilai']
            conn = create_connection('database/data_akademik.db')
            cur = conn.cursor()
            # cur.execute("INSERT INTO nilai (nim, kode, nilai) VALUES (?, ?, ?)", (nim_nilai, kode_nilai, nilai))
            nama = get_nama_by_nim(conn, nim_nilai)
            (nama_mk, sks) = get_nama_mk_sks_by_kode(conn, kode_nilai)

            if session['encrypted'] == True:
                session['data_akademik'] = decrypt(session['data_akademik'])

            if nim_nilai not in session['data_akademik']:
                session['data_akademik'][nim_nilai] = {
                    'nama': nama,
                    'records': [],
                    'ipk': 0,
                    'ttd': '',
                }

            session['data_akademik'][nim_nilai]['records'].append({
                'nim': nim_nilai,
                'nama': nama,
                'kode_mk': kode_nilai,
                'nama_mk': nama_mk,
                'sks': sks,
                'nilai': nilai,
            })

            session['data_akademik'][nim_nilai]['ipk'] = hitung_ipk(session['data_akademik'][nim_nilai]['records'])
            if session['encrypted'] == True:
                session['data_akademik'] = encrypt(session['data_akademik'])
            conn.commit()
            conn.close()
            session.modified = True
        return render_template('inputdata.html', mahasiswa=get_mahasiswa(create_connection('database/data_akademik.db')), mata_kuliah=get_matakuliah(create_connection('database/data_akademik.db')), data=session['data_akademik'])
    mahasiswa = get_mahasiswa(create_connection('database/data_akademik.db'))
    mata_kuliah = get_matakuliah(create_connection('database/data_akademik.db'))
    return render_template('inputdata.html', mahasiswa=mahasiswa, mata_kuliah=mata_kuliah)

@app.route('/generatekey', methods=['GET', 'POST'])
def generatekey():
    if 'public_key' not in session:
        session['public_key'] = None
    if 'private_key' not in session:
        session['private_key'] = None
    if 'rc4_key' not in session:
        session['rc4_key'] = None
    if request.method == 'POST':
        if 'rc4_key' in request.form:
            rc4_key = request.form['rc4_key']
            session['rc4_key'] = rc4_key
            return render_template('generatekey.html', rc4_key=session['rc4_key'], public_key=session['public_key'], private_key=session['private_key'])
        else :
            (public_key, private_key) = rsa.generate_key_pair()
            session['public_key'] = public_key
            session['private_key'] = private_key

            return render_template('generatekey.html', public_key=session['public_key'], private_key=session['private_key'])
    return render_template('generatekey.html', public_key=session['public_key'], private_key=session['private_key'], rc4_key=session['rc4_key'])

@app.route('/showdata', methods=['GET', 'POST'])
def showdata():
    if request.method == 'POST':
        if session['rc4_key'] is not None:
            if session['encrypted'] == False:
                session['data_akademik'] = encrypt(session['data_akademik'])
                session['encrypted'] = True
            else:
                session['data_akademik'] = decrypt(session['data_akademik'])
                session['encrypted'] = False

            return render_template('showdata.html', data_per_nim=session['data_akademik'], encrypted=session['encrypted'])
    if 'data_akademik' not in session or session['data_akademik'] == {}:
        conn = create_connection('database/data_akademik.db')
        data = get_all_data(conn)
        data_per_nim = OrderedDict()  # Menggunakan OrderedDict untuk menyimpan urutan
        for row in data:
            nim = row[0]
            if nim not in data_per_nim:
                data_per_nim[nim] = {
                    'nama': row[1],
                    'records': [],
                    'ipk': 0.0,
                    'ttd': ''  # Placeholder untuk tanda tangan digital
                }
            data_per_nim[nim]['records'].append({
                'nim': row[0],
                'nama': row[1],
                'kode_mk': row[2],  
                'nama_mk': row[3],
                'sks': row[4],
                'nilai': row[5]            
            })
        # Hitung IPK untuk setiap NIM
        for nim in data_per_nim:
            data_per_nim[nim]['ipk'] = hitung_ipk(data_per_nim[nim]['records'])
        session['data_akademik'] = data_per_nim
    if 'encrypted' not in session:
            session['encrypted'] = False
    return render_template('showdata.html', data_per_nim=session['data_akademik'], encrypted=session['encrypted'])

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        nim = request.form['nim']
        data_akademik = session['data_akademik']
        if nim in data_akademik:
            data_akademik[nim]['ttd'] = 'anjayyyyyyttd'
            session['data_akademik'] = data_akademik


    return redirect(url_for('showdata'))



# @app.route('/verify<nim>', methods=['GET', 'POST'])

if __name__ == '__main__':
    app.run(debug=True)