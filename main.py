from flask import Flask, request, make_response, jsonify
import pandas as pd
import logging
import os
import datetime
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import datastore


def webhook(request):

    # get request body
    req = request.get_json(force=True)
    # Printing the request body to check what information is retrieved
    # You can see this by going to the cloud function logs
    logging.info('Request: ' + str(req))

    # extract the name of the detected intent
    detect_intent = req["queryResult"]["intent"]["displayName"]
    logging.info('Intent Detected: ' + str(detect_intent))

    res = ''

    # Map intents to functions that do fulfillment
    if detect_intent == 'order_coffee - no':
        res = order_coffee(req)
    if detect_intent == 'Default Welcome Intent':
        res = welcome(req)
    if detect_intent == 'make_appointment_yes':
        res = make_appointment(req)
    if detect_intent == 'log_status':
        res = log_status(req)
    if detect_intent == 'get_status':
        res = lookup_status(req)
    if detect_intent == 'detect_language':
        res = detect_language(req)
    if detect_intent == 'invite_to_meeting':
        res = invite_to_meeting(req)

    # You can create arbitrary functions here mapped to your intent

    # returning the result from the function of the matched intent
    return make_response(jsonify({'fulfillmentText': res}))


def order_coffee(req):
    logging.info(req['queryResult']['parameters'])
    logging.info(req['queryResult']['outputContexts'])

    #dictionary for parameters extracted form context
    params = {}

    # because the parameters are in a context, we have to work a bit to get them
    for context in req['queryResult']['outputContexts']:
        logging.info('context-' + str(context))
        parameter_dict = dict(context['parameters'])
        logging.info('context-dict-' + str(parameter_dict))
        for key, val in context['parameters'].items():
                params[key] = val

    logging.info(str(params))

    # extract date, time from datetimes
    date = params['date'].split('T')[0]
    time = params['time'].split('T')[1].split('-')[0]

    #extract Other parameter
    temp = params['coffee-temp']
    size = params['coffee-size']
    coffee = params['coffee']
    # call function that will check for collisions and create entry
    response = createCalenderEvent(date, time, coffee, size, temp)

    return response


def invite_to_meeting(req):
    logging.info(req['queryResult']['parameters'])
    logging.info(req['queryResult']['outputContexts'])

    #dictionary for parameters extracted form context
    params = {}

    # because the parameters are in a context, we have to work a bit to get them
    for context in req['queryResult']['outputContexts']:
        logging.info('context-' + str(context))
        parameter_dict = dict(context['parameters'])
        logging.info('context-dict-' + str(parameter_dict))
        for key, val in context['parameters'].items():
                params[key] = val

    logging.info(str(params))

    # extract date, time from datetimes
    date = params['date'].split('T')[0]
    time = params['time'].split('T')[1].split('-')[0]

    #extract Other parameter
    temp = params['coffee-temp']
    size = params['coffee-size']
    coffee = params['coffee']
    email_invitation = params['email']
    # call function that will check for collisions and create entry
    response = createCalenderEvent(
        date, time, coffee, size, temp, email_invitation)

    return response


def welcome(req):
    # Check what the parameters are
    logging.info(req['queryResult']['parameters'])

    return 'welcome intent'


def createCalenderEvent(date, time, bev="drink", size="", temp="", email_invitation="", userid=0):

    # modify to your calender id
    calenderID = 'c_5qvevtf8jvjaskog3mgkkjf7po@group.calendar.google.com'
    # modify to your s-a key file (in Cloud Function source folder)
    key_file_name = 'key.json'

    # you can change this scope to allow read only access etc
    scope = 'https://www.googleapis.com/auth/calendar'

    # authentication
    my_credentials = ServiceAccountCredentials.from_json_keyfile_name(
        key_file_name, scopes=scope)

    logging.info("created credentials in createCalenderEvent")

    service = build('calendar', 'v3', credentials=my_credentials)

    # process datetime strings passed from dialogflow
    starthour = time.split(':')[0]
    startmins = time.split(':')[1]
    endhour = str(int(starthour) + 1)
    starttime = str(date)+'T' + starthour + ':' + startmins + \
        ':00-04:00'  # tail is time zone
    endtime = str(date)+'T' + endhour + ':' + startmins + ':00-04:00'

    #check if there is already an appointment at that date/time
    events_result = service.events().list(
        calendarId=calenderID, timeMin=starttime, timeMax=endtime).execute()
    logging.info(events_result)

    events = events_result.get('items', [])
    if not events:
        logging.info('No overlapping events found')
    else:
        logging.info('Overlapping event found')
        return 'That time slot is unfortunately not available'
    return email_invitation
    # create new event
    if (email_invitation):
        event = {
            'summary': 'Appointment user ' + str(userid),
            'location': 'Somewhere',
            'description': 'Have a nice ' + size + ' ' + temp + ' ' + bev,
            'start': {
                'dateTime': starttime,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': endtime,
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': email_invitation},
            ]
        }
    else:
        event = {
            'summary': 'Appointment user ' + str(userid),
            'location': 'Somewhere',
            'description': 'Have a nice ' + size + ' ' + temp + ' ' + bev,
            'start': {
                'dateTime': starttime,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': endtime,
                'timeZone': 'America/New_York',
            }
        }
    logging.info(event)

    # insert event in calender
    event = service.events().insert(calendarId=calenderID, body=event).execute()

    response = 'You\'re all set for {} at {}'.format(date, time)

    return response


def make_appointment(req):
    logging.info(req['queryResult']['parameters'])
    logging.info(req['queryResult']['outputContexts'])

    #dictionary for parameters extracted form context
    params = {}

    # because the parameters are in a context, we have to work a bit to get them
    for context in req['queryResult']['outputContexts']:
        logging.info('context-' + str(context))
        parameter_dict = dict(context['parameters'])
        logging.info('context-dict-' + str(parameter_dict))
        for key, val in context['parameters'].items():
                params[key] = val

    logging.info(str(params))

    # extract date, time from datetimes
    date = params['date'].split('T')[0]
    time = params['time'].split('T')[1].split('-')[0]

    # call function that will check for collisions and create entry
    response = createCalenderEvent(date, time)

    return response


def log_status(req):
    logging.info(req['queryResult']['parameters'])
    params = dict(req['queryResult']['parameters'])

    userid = params["userid"]
    status = params["status"]

    datastore_client = datastore.Client()
    # kind used for illustration purposes
    kind = 'demo-status'
    # the Cloud Datastore key for the new entity
    taskKey = datastore_client.key(kind)

    # prepare the new entity
    task = datastore.Entity(key=taskKey)
    task['userid'] = int(userid)
    task['status'] = status
    task['timestamp'] = datetime.datetime.now()

    # save the entity
    datastore_client.put(task)

    return 'Your status has been recorded. Have a good day!'


def lookup_status(req):
    response = ''

    # extract user id
    userid = int(req['queryResult']['parameters']['userid'])

    # kind we are using for illustration
    kind = 'demo-status'

    # create client and query
    datastore_client = datastore.Client()
    query = datastore_client.query(kind=kind)
    query.add_filter('userid', '=', userid)

    # execute query
    results = list(query.fetch())

    if len(results) > 0:

        logging.info('query:' + str(results))

        # grab data from first element in results
        # you should probably be more clever here
        status = results[0]['status']
        timezoneoffset = datetime.timedelta(hours=-4)
        timestamp = results[0]['timestamp']
        easterntime = timestamp + timezoneoffset

        response = 'Status at {}: {}'.format(
            easterntime.strftime('%H:%M on %d %B %Y'), status)
    else:
        response = 'Mmm...we don\'t have any records for that user.'

    return response


def detect_language(req):
    # get language parameter passed from dialogflow
    language = req['queryResult']['parameters']['language']

    return 'From webhook: I hear ' + language + ' is hard to learn!'
