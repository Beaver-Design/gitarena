from flask import Flask, session, url_for, redirect, flash
from flask import render_template_string
import sys
import os

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG')

git_authorize = r'https://github.com/login/oauth/authorize'
git_access_token = r'https://github.com/login/oauth/access_token'

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def index():
    if session.get('user_id', False):
        t = '<p>Hello! {{ session["user_id"] }}</p>'\
            '<a href="{{ url_for("logout") }}">Logout</a>'
        for key in session:
            t = t + '<p>%s: %s</p>'%(key, session[key])
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)

@app.route('/login')
def login():
    if session.get('user_id', False):
        return '%s, you are already logged in!!!'%session['user_id']
    else:
        git_url = git_authorize + '?' + 'client_id='+GITHUB_CLIENT_ID + '&redirect_uri=' + url_for('authorized')
        return redirect(git_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/user')
def user():
    return session['user_id']

@app.route('/github-callback')
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)
    user.github_access_token = access_token
    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)

if __name__ == '__main__':
    app.run(debug=True)