#!/usr/bin/env python3
# coding: utf-8

import datetime
import locale
import httplib2
import json
from math import floor
from functools import wraps
from flask import (
    Flask, request, session, render_template, redirect, url_for, jsonify)
from flask_sqlalchemy import SQLAlchemy
from oauth2client.client import OAuth2WebServerFlow
from sqlalchemy import func, extract
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.config.from_envvar('HOLIDAY_SETTINGS')
db = SQLAlchemy(app)
db.init_app(app)
db.metadata.reflect(bind=db.get_engine(app))

locale.setlocale(locale.LC_ALL, 'fr_FR')


FLOW = OAuth2WebServerFlow(
    client_id=app.config['OAUTH_CLIENT_ID'],
    client_secret=app.config['OAUTH_CLIENT_SECRET'],
    redirect_uri=app.config['OAUTH_REDIRECT'],
    scope='profile', user_agent='holiday/1.0')


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
        if session.get('person') or app.config['TESTING']:
            return function(*args, **kwargs)
        else:
            authorize_url = FLOW.step1_get_authorize_url()
            return redirect(authorize_url)
    return wrapper


@app.route('/oauth2callback')
def oauth2callback():
    code = request.args.get('code')
    if code:
        credentials = FLOW.step2_exchange(code)
        http = credentials.authorize(httplib2.Http())
        _, content = http.request(
            'https://www.googleapis.com/plus/v1/people/me')
        data = json.loads(content.decode('utf-8'))
        if 'name' in data:
            session['person'] = '%s %s' % (
                data['name']['givenName'], data['name']['familyName'])
        return redirect(url_for('days'))
    else:
        print(request.form.get('error'))
        return redirect(url_for('index'))


@app.template_filter()
def days(half_days):
    return u'%s%s jour%s' % (
        int(half_days / 2.), u',5' if half_days % 2 else u'',
        u's' if half_days > 2 else u'')


@app.template_filter()
def date(date):
    return date.strftime('%-d %B %Y')


@app.route('/', methods=('GET', 'POST'))
def index():
    return redirect(url_for('days'))


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
        day = datetime.datetime.strptime(request.form['day'], "%Y-%m-%d")
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
        .filter(Slot.person == session.get('person'))
        .filter(Slot.start <= today)
        .order_by(Slot.start.desc())
        .all())
    return render_template('days.html.jinja2', slots=slots, today=today)


@app.route('/month')
@app.route('/month-<int:month>-<int:year>')
def month(month=None, year=None):
    today = datetime.date.today()
    if month is None:
        month = today.month
    if year is None:
        year = today.year
    month, year = ((month - 1) % 12 + 1), year + int(floor((month - 1) / 12.))
    title = datetime.date(year, month, 1).strftime('%B %Y')
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8282)
