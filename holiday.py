#!/usr/bin/env python

import ldap
from functools import wraps
from flask import Flask, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'wonderful secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rtt:@localhost/rtt'
db = SQLAlchemy(app)

LDAP = ldap.open('ldap.keleos.fr')


def auth(function):
    """Wrapper checking whether the user is logged in."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get('user'):
            return function(*args, **kwargs)
        else:
            return redirect(url_for('connect'))
    return wrapper


@app.route('/')
def index():
    return render_template('index.html.jinja2')


@app.route('/connect/', methods=('GET', 'POST'))
def connect():
    return render_template('connect.html.jinja2')


if __name__ == '__main__':
    app.run()
