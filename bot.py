#!/usr/bin/env python3

import telegram.ext
import datetime
import configparser
import os
import sys
import logging
import re

from google_calendar import GoogleCalendar

# TODO: beschraenken auf grashuepfer news gruppe / liste von user_ids
# idee: beschraenken auf alle nutzer in der "Grashuepfer News" Gruppe

calendar = None
config = None

def get_cmd_arguments(text):
    return text.partition(' ')[2]


def parse_datetime_future(args):
    datetime_matchers = [
        {
            'pattern': r'(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+)\s+(\d+):(\d+)(.*)',
            'formats': ['%d %m %Y %H %M', '%d %m %y %H %M'],
            'is_datetime': True
        },
        {
            'pattern': r'(\d+)\s*\.\s*(\d+)\.?\s*(\d+):(\d+)(.*)',
            'formats': ['%d %m %H %M'],
            'is_datetime': True
        },
        {
            'pattern': r'(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+)(.*)',
            'formats': ['%d %m %Y', '%d %m %y'],
            'is_datetime': False
        },
        {
            'pattern': r'(\d+)\s*\.\s*(\d+)\.?(.*)',
            'formats': ['%d %m'],
            'is_datetime': False
        }
    ]

    dt = None
    remaining_args = None

    for matcher in datetime_matchers:
        formats = matcher['formats']
        pattern = matcher['pattern']
        is_datetime = matcher['is_datetime']

        m = re.match(pattern, args)
        if m:
            print("matched; args={0} pattern={1}".format(args, pattern))
            for fmt in formats:
                try:
                    n_datetime_groups = len(fmt.split(' '))
                    datetime_str = " ".join(m.groups()[0:n_datetime_groups])
                    dt = datetime.datetime.strptime(datetime_str, fmt)
                    if not is_datetime:
                        dt = dt.date()

                    remaining_args = m.group(n_datetime_groups + 1)

                    break

                except ValueError:
                    continue 

            break

    if dt is None:
        return (None, args)

    if dt.year == 1900:  # use current/next year when no year is given
        dt = dt.replace(year=datetime.datetime.now().year)

        # ensure date is not in the past
        if type(dt) is datetime.date and dt < datetime.datetime.now().date():
            dt = datetime.date(dt.year + 1, dt.month, dt.day)
        elif type(dt) is datetime.datetime and dt.date() < datetime.datetime.now().date():
            dt = datetime.datetime(dt.year + 1, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    return (dt, remaining_args)


def cmd_add(bot, update):
    args = get_cmd_arguments(update.message.text)
    (event_datetime, remaining_args) = parse_datetime_future(args) 

    if event_datetime is None:
        bot.sendMessage(update.message.chat_id,
                text="Datum unverständlich :(")
        return

    event_name = remaining_args.strip()

    if event_name == '':
        bot.sendMessage(update.message.chat_id,
                text='Das Event braucht noch einen Namen')
        return
    
    if type(event_datetime) is datetime.date:
        new_event = calendar.add_date_event(event_datetime, event_name)
    else:
        new_event = calendar.add_datetime_event(event_datetime, 1, event_name)

    bot.sendMessage(update.message.chat_id, 
            text='Event "{0}" am {1} hinzugefügt'.format(
                new_event['summary'], new_event['start']['date']))


def cmd_ls(bot, update):
    events = calendar.get_events()
    message = ""
    events_by_day = {}

    for event in events:
        day = event['start'].strftime('%Y%m%d')
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    output = format_ls_output(events_by_day)

    bot.sendMessage(update.message.chat_id, 
            text=output, 
            parse_mode=telegram.ParseMode.MARKDOWN)


def format_ls_output(events_by_day):
    output = ""

    for day in events_by_day:
        day_str = events_by_day[day][0]['start'].strftime('%d.%m')
        output += "*{0}*\n".format(day_str)

        for event in events_by_day[day]:
            has_time = type(event['start']) is datetime.datetime
            if has_time:
                time_str = event['start'].strftime('%H:%M')
                output += "- _{0}_ {1}\n".format(time_str, event['name'])
            else:
                output += "- {0}\n".format(event['name'])

        output += "\n"

    return output


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


