import functools
import telegram
import datetime
import re

from google_calendar import GoogleCalendar


def setup(updater, calendar):
    commands = [
            LsCommand(calendar, ['ls', 'list']),
            AddCommand(calendar, ['add'])
            ]

    for cmd in commands:
        for cmd_name in cmd.names:
            updater.dispatcher.add_handler(telegram.ext.CommandHandler(cmd_name, cmd.handle))


class Command:
    def __init__(self, calendar, names):
        self.calendar = calendar
        self.names = names
    
    @staticmethod
    def get_args(text):
        return text.partition(' ')[2]

    def handle(self, bot, update):
        pass


class LsCommand(Command):
    def __init__(self, calendar, names):
        super().__init__(calendar, names)


    def handle(self, bot, update, **kwargs):
        events = self.calendar.get_events()
        message = ""
        events_by_day = {}

        for event in events:
            day = event['start'].strftime('%Y%m%d')
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        output = self._format_output(events_by_day)

        bot.sendMessage(update.message.chat_id,
                text=output,
                parse_mode=telegram.ParseMode.MARKDOWN)


    def _format_output(self, events_by_day):
        output = ""

        for day in events_by_day:
            first_event = events_by_day[day][0]

            if first_event['start'].year != datetime.datetime.now().year:
                day_str = first_event['start'].strftime('%d.%m.%Y')
            else:
                day_str = first_event['start'].strftime('%d.%m')

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


class AddCommand(Command):
    def __init__(self, calendar, names):
        super().__init__(calendar, names)


    def handle(self, bot, update):
        args = Command.get_args(update.message.text)
        (event_datetime, remaining_args) = AddCommand._parse_datetime_future(args) 
    
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
            new_event = self.calendar.add_date_event(event_datetime, event_name)
        else:
            new_event = self.calendar.add_datetime_event(
                event_datetime, datetime.timedelta(hours=2), event_name)
    
        bot.sendMessage(update.message.chat_id, 
                text='Event "{0}" am {1} hinzugefügt'.format(
                    new_event['summary'], new_event['start']))


    @staticmethod
    def _parse_datetime_future(args):
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



