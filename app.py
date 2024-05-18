from flask import Flask, request, jsonify, render_template


import cipher.rc4 as rc4
import cipher.rsa as rsa

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inputdata')
def inputdata():
    return render_template('inputdata.html')

@app.route('/generatekey')
def generatekey():
    return render_template('generatekey.html')

@app.route('/showdata')
def showdata():
    return render_template('showdata.html')



if __name__ == '__main__':
    app.run(debug=True)