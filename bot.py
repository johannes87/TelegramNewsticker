#!/usr/bin/env python3

import telegram.ext
import configparser
import os
import sys
import logging

from google_calendar import GoogleCalendar
import commands

# TODO: beschraenken auf grashuepfer news gruppe / liste von user_ids
# idee: beschraenken auf alle nutzer in der "Grashuepfer News" Gruppe

config = None

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


def setup_telegram(calendar):
    updater = telegram.ext.Updater(config['TelegramAccessToken'])
    commands.setup(updater, calendar)
    updater.start_polling()
    updater.idle()


def main():
    setup_logging()

    global config
    config = read_config('config.ini')
    
    calendar = GoogleCalendar(config['CalendarClientSecretFile'], config['CalendarID'])
    setup_telegram(calendar)


if __name__ == '__main__':
    main()


