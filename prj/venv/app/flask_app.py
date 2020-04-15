from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask import request

import html_content_extractor

app = Flask(__name__, template_folder='templates')
socketio = SocketIO( app )

@app.route('/')
def index():
    return render_template("mturk_requester.html")

@app.route('/register_request', methods=['POST'])
def register_request():
    print("registering request...")

    print("description: " + request.form['descr'])
    print("time: " + request.form['hours'] + "hrs")

    #update request description/query
    html_content_extractor.update_request(request.form['descr'])




    return render_template("mturk_request_complete.html")

@app.route('/register_response', methods=['POST'])
def register_response():
    print("registering response...")

    print("url: " + request.form['url_response'])
    print("summary: " + request.form['summary'])

    return render_template("mturk_response_complete.html")

if __name__ == "__main__":
    socketio.run(app, debug = True)