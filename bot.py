#!/usr/bin/python3

import telegram.ext
import caldav
from datetime import datetime
import configparser
import os
import sys
import httplib2
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import logging


# TODO: beschraenken auf grashuepfer news gruppe / liste von user_ids

calendar_service = None
config = None

def get_cmd_arguments(text):
    return text.partition(' ')[2]

def parse_datetime(datetime_str):
    datetime_str = datetime_str.strip('.')

    formats_to_try = [
            #'%d.%m.%Y %H:%M',
            #'%d.%m.%y %H:%M',
            '%d.%m.%Y',
            '%d.%m.%y',
            #'%d.%m %H:%M',
            '%d.%m'
            ]

    dt = None

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            break
        except ValueError:
            continue
    
    # TODO "25.8" => 25.8.2017 
    if dt.year == 1900:  # use current year when no year is given
        dt = datetime(datetime.now().year, dt.month, dt.day, 
                dt.hour, dt.minute, dt.second)
    
    return dt


def calendar_add(event_datetime, event_name):
    pass


def calendar_list_events():
    # TODO: bug reporten: wenn laufzeitfehler entstehen (z.b. nicht-existenter
    # methodenaufruf), wird keine exception/warning auf der konsole ausgegeben

    # eventsResult = calendar_service.events().list(
    #     calendarId=config['CalendarID'], timeMin=now, 
    #     orderBy='startTime').execute()
    # events = eventsResult.get('items', [])

    print("asdf")

    # for event in events:
    #     print(event)


def calendar_remove(event_id):
    pass


def cmd_add(bot, update):
    args = get_cmd_arguments(update.message.text)
    datetime_str, sep, event_name = args.partition(' ')
    event_datetime = parse_datetime(datetime_str)
    
    calendar_add(event_datetime, event_name)

    bot.sendMessage(update.message.chat_id, 
            text='date: {0}, event: {1}'.format(event_datetime, event_name))


def cmd_ls(bot, update):
    calendar_list_events()


def cmd_rm(bot, update):
    try:
        event_nr = int(get_cmd_arguments(update.message.text))
    except ValueError:
        print("/rm: argument '{0}' invalid".format(get_cmd_arguments(update.message.text)))
        return

    print("event_nr =", event_nr)


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

def main():
    global config
    config = read_config('config.ini')
    
    global calendar_service
    calendar_service = get_calendar_service(config['CalendarClientSecretFile'])
def setup_logging():
    logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.ERROR)

    updater = telegram.ext.Updater(config['TelegramAccessToken'])
    
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('add', cmd_add))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('ls', cmd_ls))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler('rm', cmd_rm))
    updater.start_polling()

    updater.idle()


    setup_logging()
if __name__ == '__main__':
    main()


