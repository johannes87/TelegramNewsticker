#!/usr/bin/python3

import telegram.ext
import caldav
import datetime
import configparser
import os
import sys
import httplib2
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import logging
import dateutil.parser


# TODO: beschraenken auf grashuepfer news gruppe / liste von user_ids

calendar_service = None
config = None

def get_cmd_arguments(text):
    return text.partition(' ')[2]


def parse_date_future(date_str):
    date_str = date_str.strip('.')

    formats_to_try = [
            '%d.%m.%Y',
            '%d.%m.%y',
            '%d.%m'
            ]

    dt = None

    for fmt in formats_to_try:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue

    if dt is None:
        return

    if dt.year == 1900:  # use current/next year when no year is given
        dt = dt.replace(year=datetime.datetime.now().year)

        if dt.date() < datetime.datetime.now().date():
            dt = datetime.datetime(dt.year + 1, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    
    return dt


def calendar_add(event_datetime, event_name):
    event_date_str = event_datetime.strftime('%Y-%m-%d')

    event_body = {
            'summary': event_name, 
            'start': { 'date': event_date_str },
            'end': { 'date': event_date_str }
            }

    new_event = calendar_service.events().insert(
            calendarId=config['CalendarID'], body=event_body).execute()

    return new_event


def calendar_get_events():
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    eventsResult = calendar_service.events().list(
        calendarId=config['CalendarID'], 
        timeMin=now,
        orderBy='startTime',
        singleEvents=True,
        ).execute()
    events = eventsResult.get('items', [])
    
    ret_events = []

    for event in events:
        event_summary = event['summary']

        if 'dateTime' in event['start']:
            event_start = dateutil.parser.parse(event['start']['dateTime'])
        else:
            event_start = dateutil.parser.parse(event['start']['date']).date()

        ret_events.append({'start': event_start, 'name': event_summary})
    
    return ret_events 


def calendar_remove(event_id):
    pass


def cmd_add(bot, update):
    args = get_cmd_arguments(update.message.text)
    date_str, sep, event_name = args.partition(' ')
    event_datetime = parse_date_future(date_str)

    if event_datetime is None:
        bot.sendMessage(update.message.chat_id,
                text="Wie bitte?! Ich konnte das Datum nicht verstehen. Verwende bitte keine Leerzeichen in der Datumsangabe")
        return
    
    new_event = calendar_add(event_datetime, event_name)

    bot.sendMessage(update.message.chat_id, 
            text='Event "{0}" am {1} hinzugefügt'.format(
                new_event['summary'], new_event['start']['date']))


def cmd_ls(bot, update):
    events = calendar_get_events()
    message = ""
    
    for event in events:
        if type(event['start']) is datetime.date:
            datetime_str = event['start'].strftime('%d.%m.%Y')
        else:
            datetime_str = event['start'].strftime('%d.%m.%Y %H:%M')

        message += "*{0}*: {1}\n\n".format(datetime_str, event['name'])

    bot.sendMessage(update.message.chat_id, 
            text=message, 
            parse_mode=telegram.ParseMode.MARKDOWN)


def cmd_rm(bot, update):
    # XXX idee: /del 14.9 stupferich => das loeschen was am meisten matcht, und nur wenn eindeutig
    args = get_cmd_arguments(update.message.text)
    


def get_calendar_service(client_secret_file):
    def get_credentials():
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        
        SCOPES = "https://www.googleapis.com/auth/calendar"
        APPLICATION_NAME = "Google-Calendar-API Client"

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'calendar-grashuepfer.json')

        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None
        
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


def read_config(config_file):
    required_keys = [
            'TelegramAccessToken',
            'CalendarClientSecretFile',
            'CalendarID'
            ]

    if not os.path.isfile(config_file):
        print('error: {0} not found'.format(config_file))
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(config_file)

    for key in required_keys:
        if key not in config['DEFAULT']:
            print('error: key {0} does not exist in {1}'.format(key, config_file))
            sys.exit(1)

    return config['DEFAULT']

def setup_logging():
    logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.ERROR)

def setup_telegram():
    updater = telegram.ext.Updater(config['TelegramAccessToken'])

    updater.dispatcher.add_handler(telegram.ext.CommandHandler('add', cmd_add))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('ls', cmd_ls))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('list', cmd_ls))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('rm', cmd_rm))

    updater.start_polling()
    updater.idle()


def main():
    global config
    config = read_config('config.ini')
    
    global calendar_service
    calendar_service = get_calendar_service(config['CalendarClientSecretFile'])
    
    setup_logging()
    setup_telegram()


if __name__ == '__main__':
    main()


