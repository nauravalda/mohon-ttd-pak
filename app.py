from flask import Flask, request, render_template, session, redirect, url_for, send_file, flash

import base64
import sqlite3
from hashlib import sha3_256 as sha3
from collections import OrderedDict
from xhtml2pdf import pisa
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from pypdf import PdfReader

import cipher.rc4 as rc4
import cipher.rsa as rsa

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./tmp/"
app.config['SECRET_KEY'] = 's3cr3t_k3y_Th4t_1s_very_l0ng_and_c0mpl3x'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}

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
    conn.commit()
    conn.close()
    return rows

def get_matakuliah(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM mata_kuliah")
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows
    
def get_all_data(conn):
    cur = conn.cursor()
    cur.execute("SELECT mahasiswa.nim as nim, mahasiswa.nama as nama, mata_kuliah.kode as kode_mk, mata_kuliah.nama as nama_mk, mata_kuliah.sks as sks, nilai.nilai as nilai FROM nilai JOIN mahasiswa ON nilai.nim = mahasiswa.nim JOIN mata_kuliah ON nilai.kode = mata_kuliah.kode;")
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

def get_all_data_by_nim(conn, nim):
    cur = conn.cursor()
    cur.execute("SELECT mahasiswa.nim as nim, mahasiswa.nama as nama, mata_kuliah.kode as kode_mk, mata_kuliah.nama as nama_mk, mata_kuliah.sks as sks, nilai.nilai as nilai FROM nilai JOIN mahasiswa ON nilai.nim = mahasiswa.nim JOIN mata_kuliah ON nilai.kode = mata_kuliah.kode WHERE mahasiswa.nim = ?;", (nim,))
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

def get_nama_by_nim(conn, nim):
    cur = conn.cursor()
    cur.execute("SELECT nama FROM mahasiswa WHERE nim = ?", (nim,))
    rows = cur.fetchall()
    nama = rows[0][0]
    conn.commit()
    conn.close()
    return nama

def get_nama_mk_sks_by_kode(conn, kode):
    cur = conn.cursor()
    cur.execute("SELECT nama, sks FROM mata_kuliah WHERE kode = ?", (kode,))
    rows = cur.fetchall()
    nama = rows[0][0]
    sks = rows[0][1]
    conn.commit()
    conn.close()
    return (nama, sks)

def get_transcript_by_nim(conn, nim):
    cur = conn.cursor()
    cur.execute("SELECT * FROM nilai WHERE nim = ?", (nim,))
    rows = cur.fetchall()
    nim = rows[0][0]
    public_key = rows[0][1]
    ttd = rows[0][2]
    rc4_key = rows[0][3]
    conn.commit()
    conn.close()
    return (nim, public_key, ttd, rc4_key)

    

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

            nama = get_nama_by_nim(create_connection('database/data_akademik.db'), nim_nilai)
            (nama_mk, sks) = get_nama_mk_sks_by_kode(create_connection('database/data_akademik.db'), kode_nilai)

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
            
            conn = create_connection('database/data_akademik.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO nilai (nim, kode, nilai) VALUES (?, ?, ?)", (nim_nilai, kode_nilai, nilai))
            
            conn.commit()
            conn.close()
            session['data_akademik'][nim_nilai]['ttd'] = ''
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
            aes_key = bytearray(rc4_key,'utf-8')
            # generate aes-256 key
            len0 = len(aes_key)
            for i in range(16):
                if i >= len0:
                    aes_key.append(aes_key[i % len0])
            aes_key = aes_key[:16]
            session['aes_key'] = bytes(aes_key)

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
        data = get_all_data(create_connection('database/data_akademik.db'))
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

@app.route('/sign', methods=['POST'])
def sign():
    nim = request.form['nim']
    if nim in session['data_akademik']:
        signed_data = str(nim) + str(session['data_akademik'][nim]['nama'])
        for data in session['data_akademik'][nim]['records']:
            signed_data = signed_data + str(data['kode_mk']) + str(data['nama_mk']) + str(data['sks']) + str(data['nilai'])
        signed_data = signed_data + str(session['data_akademik'][nim]['ipk'])
        # Get encypted hash
        signature_array = rsa.encrypt(
            session['private_key'],
            str(base64.b64encode(sha3(signed_data.encode()).hexdigest().encode('utf-8')).decode('utf-8'))
        )
        # Convert signature to base64 string
        signature = ""
        for _ in range(len(signature_array)):
            if _ > 0:
                signature = signature + ','
            signature = signature + str(signature_array[_])
        
        session['data_akademik'][nim]['ttd'] = base64.b64encode(signature.encode()).decode()
        session['data_akademik'][nim]['public_key'] = session['public_key']
        session.modified = True
        database = create_connection('database/data_akademik.db')  
        cur = database.cursor()
        cur.execute("INSERT INTO transkrip (nim, public_key) VALUES (?, ?) ON CONFLICT(nim) DO UPDATE SET public_key = excluded.public_key", (nim, str(session['public_key'])))

        database.commit()
        database.close()


    return redirect(url_for('showdata'))



@app.route('/verify', methods=['POST'])
def verify():
    # if theres a file

    if 'file' in request.files:
        try:
            file = request.files['file']
            pdf = PdfReader(file)
            raw = pdf.pages[0].extract_text()
            data = raw.split('\n')
            nim = ""
            name = ""
            records = []
            ipk = ""
            ttd = ""
            
            for i in range(len(data)):
                if data[i].startswith(" "):
                    data[i] = data[i][1:]

            for i in range(len(data)):

                if data[i].find("NIM:") != -1:
                    nim = data[i].split(": ")[1]
                elif data[i].find("Nama:") != -1:
                    name = data[i].split(": ")[1]
                elif data[i].find("Nilai") != -1:
                    i = i + 1
                    while not data[i].find("Total jumlah SKS") != -1:
                        i = i + 1
                        records.append({
                            'kode_mk': data[i],
                            'nama_mk': data[i+1],
                            'sks': int(data[i+2]),
                            'nilai': data[i+3]
                        })
                    
                        i = i + 4
                elif data[i].find("IPK:") != -1:
                    ipk = float(data[i].split(": ")[1])
                elif data[i].startswith("--Begin signature"):
                    i = i + 1
                    while not data[i].startswith("--End signature"):
                        ttd = ttd + data[i]
                        i = i + 1
                    ttd = ttd.replace(" ", "")
                    break

            database = create_connection('database/data_akademik.db')
            cur = database.cursor()
            cur.execute("SELECT * FROM transkrip WHERE nim = ?", (nim,))
            rows = cur.fetchall()
            database.commit()
            database.close()
            if len(rows) == 0:
                flash(f'{file.filename}', 'danger')
                return redirect(url_for('transcript_dec'))
            public_key = rows[0][1]
            public_key = tuple(map(int, public_key[1:-1].split(',')))
            print(public_key)

            
            # Get data hash
            signed_data = str(nim) + str(name)
            for record in records:
                signed_data = signed_data + str(record['kode_mk']) + str(record['nama_mk']) + str(record['sks']) + str(record['nilai'])
            signed_data = signed_data + str(ipk)
            nim_hash = sha3(signed_data.encode()).hexdigest()

            # Get decrypted signature
            signature = base64.b64decode(ttd.encode()).decode('utf-8')
            signature_array = [int(_) for _ in signature.split(',')]
            dec_hash = rsa.decrypt(public_key,signature_array).decode('utf-8')
            print(dec_hash)
            
            if dec_hash == nim_hash:
                flash(f'{file.filename}', 'success')
                return redirect(url_for('transcript_dec'))
            else:
                flash(f'{file.filename}', 'danger')
                return redirect(url_for('transcript_dec'))
        except:
            flash(f'{file.filename}', 'danger')
            return redirect(url_for('transcript_dec'))

    if 'nim' in request.form and 'ttd' in request.form:
        try:
            nim = request.form['nim']
            if nim in session['data_akademik']:
                # Get data hash
                signed_data = str(nim) + str(session['data_akademik'][nim]['nama'])
                for data in session['data_akademik'][nim]['records']:
                    signed_data = signed_data + str(data['kode_mk']) + str(data['nama_mk']) + str(data['sks']) + str(data['nilai'])
                signed_data = signed_data + str(session['data_akademik'][nim]['ipk'])
                nim_hash = sha3(signed_data.encode()).hexdigest()

                # Get decrypted signature
                signature = base64.b64decode(request.form['ttd'].encode()).decode('utf-8')
                signature_array = [int(_) for _ in signature.split(',')]
                dec_hash = rsa.decrypt(session['public_key'],signature_array).decode('utf-8')

                if dec_hash == nim_hash:
                    flash(f'{nim}', 'success')
                    print("Verified")
                    return redirect(url_for('showdata'))
                else:
                    flash(f'{nim}', 'danger')
                    print("Not Verified")
                    return redirect(url_for('showdata'))
        except:
            flash(f'{nim}', 'danger')
            return redirect(url_for('showdata'))
    return redirect(url_for('showdata'))


        
        


@app.route('/transcript', methods=['POST'])
def transcript():

    # Generate transcript HTML
    nim = request.form['nim']
    if nim in session['data_akademik']:
        data = session['data_akademik'][nim]
        data['sks'] = 0
        data['nim'] = nim
        for rec in data['records']:
            data['sks'] = data['sks'] + rec['sks']
        for i in range(len(data['records'])):
            data['records'][i]['no'] = i + 1
        data['ttd'] = '\n'.join(data['ttd'][i:i+40] for i in range(0, len(data['ttd']), 40))
    html = render_template('transcript.html', data=data)

    # Convert HTML to PDF
    pisa_res = False
    fname = "tmp/file.tmp"
    with open(fname,"wb") as f:
        pisa_res = pisa.CreatePDF(html, f)

    # Encrypt PDF
    fname_enc = "tmp/file_enc.tmp"
    cipher = AES.new(session['aes_key'],AES.MODE_ECB)
    with open(fname_enc,"wb") as f_enc:
        with open(fname,"rb") as f:
            ct = cipher.encrypt(pad(f.read(), AES.block_size))
            f_enc.write(ct)
    session['data_akademik'][nim]['aes_key'] = session['aes_key']
    session.modified = True

    # How to decrypt
    # with open("tmp/dec.pdf","wb") as f_dec:
    #     with open(fname_enc,"rb") as f:
    #         ct = unpad(cipher.decrypt(f.read()),AES.block_size)
    #         f_dec.write(ct)

    database = create_connection('database/data_akademik.db')  
    cur = database.cursor()
    cur.execute("INSERT INTO transkrip (nim, public_key) VALUES (?, ?) ON CONFLICT(nim) DO UPDATE SET public_key = excluded.public_key", (nim, str(session['public_key'])))
    database.commit()
    database.close()    
    # Send PDF
    if not pisa_res.err:
        return send_file(fname_enc, as_attachment=True, download_name=(str(nim)+".pdf"))
    return redirect(url_for('showdata'))

@app.route('/decrypt', methods=['GET', 'POST'])
def transcript_dec():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('showdata'))
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('showdata'))
        if file and allowed_file(file.filename):
            cipher = AES.new(session['aes_key'],AES.MODE_ECB)
            file_dec = unpad(cipher.decrypt(file.stream.read()),AES.block_size)
            with open("tmp/decrypted.pdf", "wb") as f:
                f.write(file_dec)
            file.close()
            
            return send_file("tmp/decrypted.pdf", as_attachment=True, download_name=(str(file.filename.split(".")[0])+"-decrypted.pdf"))
    filename = session.get('last_file', None)
    return render_template('upload.html', filename=filename)


if __name__ == '__main__':
    app.run(debug=True)