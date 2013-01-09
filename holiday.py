#!/usr/bin/env python
# coding: utf-8

import ldap
from datetime import date
from functools import wraps
from flask import (
    Flask, request, session, render_template, redirect, url_for, flash)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.secret_key = 'wonderful secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2://holiday:@localhost/holiday'
db = SQLAlchemy(app)
db.init_app(app)
db.metadata.reflect(bind=db.get_engine(app))

LDAP = ldap.open('ldap.keleos.fr')


class Slot(db.Model):
    __tablename__ = 'slot'

    @hybrid_property
    def days(self):
        return self.parts / 2.

    @hybrid_property
    def remaining_days(self):
        return self.days - sum(
            db.session.query(Vacation.part)
            .filter(Vacation.slot_id == self.slot_id)
            .all())


class Vacation(db.Model):
    __tablename__ = 'vacation'


def auth(function):
    """Wrapper checking whether the user is logged in."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get('person'):
            return function(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrapper


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        username = request.form['username'].encode('utf-8')
        password = request.form['password'].encode('utf-8')
        user = LDAP.search_s(
            'ou=People,dc=keleos,dc=fr',
            ldap.SCOPE_ONELEVEL, 'uid=%s' % username)
        try:
            LDAP.simple_bind_s(user[0][0], password)
        except (ldap.INVALID_CREDENTIALS, IndexError):
            flash(u'L’identifiant ou le mot de passe est incorrect.', 'error')
        else:
            session['person'] = user[0][1]['cn'][0].decode('utf-8')
        return redirect(url_for('index'))

    return render_template('index.html.jinja2')


@app.route('/add/', methods=('GET', 'POST'))
@auth
def add():
    if request.method == 'POST':
        slot_id = request.form['slot']
        day = request.form['day']
        parts = request.form.getlist('parts')
        for part in parts:
            db.session.add(Vacation(day=day, part=part, slot_id=slot_id))
        db.session.commit()
        return redirect(url_for('index'))

    today = date.today()
    slots = (
        Slot.query
        .filter(Slot.person == session.get('person'))
        .filter(Slot.remaining_days > 0)
        .filter(Slot.start <= today)
        .filter((Slot.stop >= today) | (Slot.stop == None))
        .order_by(Slot.name)
        .all())
    return render_template('add.html.jinja2', slots=slots)


@app.route('/days/')
@auth
def days():
    today = date.today()
    slots = (
        Slot.query
        .filter(Slot.person == session.get('person'))
        .filter(Slot.start <= today)
        .order_by(Slot.start.desc())
        .all())
    return render_template('days.html.jinja2', slots=slots)


@app.route('/disconnect/')
@auth
def disconnect():
    del session['person']
    flash(u'Vous êtes déconnecté(e)', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8282)
