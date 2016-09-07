#!/usr/bin/env python3

import telegram.ext
import datetime
import configparser
import os
import sys
import logging

from google_calendar import GoogleCalendar

# TODO: beschraenken auf grashuepfer news gruppe / liste von user_ids
# idee: beschraenken auf alle nutzer in der "Grashuepfer News" Gruppe

calendar = None
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
    
    return dt.date()


def cmd_add(bot, update):
    args = get_cmd_arguments(update.message.text)
    date_str, sep, event_name = args.partition(' ')
    event_date = parse_date_future(date_str)

    if event_date is None:
        bot.sendMessage(update.message.chat_id,
                text="Wie bitte?! Ich konnte das Datum nicht verstehen. Verwende bitte keine Leerzeichen in der Datumsangabe")
        return
    
    new_event = calendar.add_date_event(event_date, event_name)

    bot.sendMessage(update.message.chat_id, 
            text='Event "{0}" am {1} hinzugefügt'.format(
                new_event['summary'], new_event['start']['date']))


def cmd_ls(bot, update):
    events = calendar.get_events()
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

    updater.start_polling()
    updater.idle()


def main():
    global config
    config = read_config('config.ini')
    
    global calendar
    calendar = GoogleCalendar(config['CalendarClientSecretFile'], config['CalendarID'])
    
    setup_logging()
    setup_telegram()


if __name__ == '__main__':
    main()


