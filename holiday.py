#!/usr/bin/env python
# coding: utf-8

import ldap
import locale
import datetime
import json
from math import floor
from functools import wraps
from flask import (
    Flask, request, session, render_template, redirect, url_for, flash,
    jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.secret_key = 'wonderful secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2://holiday:@localhost/holiday'
db = SQLAlchemy(app)
db.init_app(app)
db.metadata.reflect(bind=db.get_engine(app))

_LDAP = ldap.open('ldap.keleos.fr')

locale.setlocale(locale.LC_ALL, 'fr_FR')


def get_ldap():
    global _LDAP
    try:
        _LDAP.search_s(
            'ou=People,dc=keleos,dc=fr',
            ldap.SCOPE_ONELEVEL, 'uid=Anna Boten')
    except:
        _LDAP = ldap.open('ldap.keleos.fr')
    return _LDAP


class Slot(db.Model):
    __tablename__ = 'slot'

    @hybrid_property
    def short_name(self):
        return self.name.split()[0]

    @hybrid_property
    def remaining(self):
        return self.parts - len(self.vacations)

    @remaining.expression
    def remaining(self):
        return self.parts - (
            db.session.query(func.count(1))
            .filter(Vacation.slot_id == Slot.slot_id)
            .correlate(Slot))


class Vacation(db.Model):
    __tablename__ = 'vacation'

    @hybrid_property
    def part_name(self):
        return u'après-midi' if self.part == 'pm' else u'matin'


Vacation.slot = relationship('Slot', backref=backref(
    'vacations', order_by=(Vacation.day.desc(), Vacation.part)))


def auth(function):
    """Wrapper checking whether the user is logged in."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get('person'):
            return function(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrapper


@app.template_filter()
def days(half_days):
    return u'%s%s jour%s' % (
        int(half_days / 2.), u',5' if half_days % 2 else u'',
        u's' if half_days > 2 else u'')


@app.template_filter()
def date(date):
    return date.strftime('%-d %B %Y').decode('utf-8')


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        if app.debug:
            session['person'] = request.form['username']
            return redirect(url_for('days'))

        username = request.form['username'].encode('utf-8')
        password = request.form['password'].encode('utf-8')

        user = get_ldap().search_s(
            'ou=People,dc=keleos,dc=fr',
            ldap.SCOPE_ONELEVEL, 'uid=%s' % username)
        try:
            get_ldap().simple_bind_s(user[0][0], password)
        except (ldap.INVALID_CREDENTIALS, IndexError):
            flash(u'L’identifiant ou le mot de passe est incorrect.', 'error')
        else:
            session['person'] = user[0][1]['cn'][0].decode('utf-8')
            return redirect(url_for('days'))
        return redirect(url_for('index'))
    return render_template('index.html.jinja2')


def get_slots():
    today = datetime.date.today()
    slots = (
        Slot.query
        .filter(Slot.person == session['person'])
        .filter(Slot.remaining > 0)
        .filter(Slot.start <= today)
        .filter((Slot.stop >= today) | (Slot.stop == None))
        .order_by(Slot.name)
        .all())
    return slots


@app.route('/add', methods=('GET', 'POST'))
@auth
def add():
    if request.method == 'POST':
        slot_id = request.form['slot']
        day = request.form['day']
        parts = request.form.getlist('parts')
        for part in parts:
            db.session.add(Vacation(day=day, part=part, slot_id=slot_id))
        db.session.commit()
        return redirect(url_for('days'))

    return render_template('add.html.jinja2', slots=get_slots())


@app.route('/range')
@auth
def range():
    return render_template('range.html.jinja2', slots=get_slots())


@app.route('/events/save', methods=('POST', ))
@auth
def event_save():
    events = json.loads(request.values.get('events'))

    for event in events:
        db.session.add(Vacation(
            day=datetime.datetime.strptime(event['day'], "%Y-%m-%dT%H:%M:%SZ"),
            part=event['type'],
            slot_id=int(event['slot'])))
    db.session.commit()

    return 'OK'


@app.route('/events/from/<start>/to/<end>')
@auth
def events(start, end):
    start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    vacations = (Vacation.query
                 .join(Slot)
                 .filter(Slot.person == session['person'])
                 .filter(Vacation.day >= start)
                 .filter(Vacation.day < end)
                 .all())
    vac_by_day = {}
    for vacation in vacations:
        vac_by_day.setdefault(vacation.day, [])
        vac_by_day[vacation.day].append(vacation)

    events = []
    for day, vacations in vac_by_day.items():
        vacation = vacations[0]
        label = ''

        if len(vacations) < 2:
            if vacation.part == "am":
                label = u' (Matin)'
            else:
                label = u' (Après-midi)'

        events.append({
            'start': str(day),
            'title': vacation.slot.name + label,
            'className': ['already_taken'],
            'allDay': True,
        })
    return jsonify({'events': events})


@app.route('/delete/<vacation_id>', methods=('POST',))
@auth
def delete(vacation_id):
    vacation = (
        Vacation.query
        .join(Slot)
        .filter(Slot.person == session['person'])
        .filter(Vacation.vacation_id == vacation_id)
        .first())
    db.session.delete(vacation)
    db.session.commit()
    return redirect(url_for('days'))


@app.route('/days')
@auth
def days():
    today = datetime.date.today()
    slots = (
        Slot.query
        .filter(Slot.remaining > 0)
        .filter(Slot.person == session.get('person'))
        .filter(Slot.start <= today)
        .order_by(Slot.start.desc())
        .all())
    return render_template('days.html.jinja2', slots=slots, today=today)


@app.route('/month')
@app.route('/month-<int:month>-<int:year>')
@auth
def month(month=None, year=None):
    today = datetime.date.today()
    if month is None:
        month = today.month
    if year is None:
        year = today.year
    month, year = ((month - 1) % 12 + 1), year + int(floor((month - 1) / 12.))
    title = datetime.date(year, month, 1).strftime('%B %Y').decode('utf-8')
    vacations = (
        Vacation.query
        .filter(extract('month', Vacation.day) == month)
        .filter(extract('year', Vacation.day) == year)
        .order_by(Vacation.slot_id, Vacation.day, Vacation.part)
        .all())
    return render_template(
        'month.html.jinja2', title=title, month=month, year=year,
        vacations=vacations)


@app.route('/calendar.ics')
def calendar():
    vacations = Vacation.query.all()
    return render_template('calendar.ics.jinja2', vacations=vacations)


@app.route('/disconnect')
@auth
def disconnect():
    del session['person']
    flash(u'Vous êtes déconnecté(e)', 'info')
    return redirect(url_for('days'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8282)
