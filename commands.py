import functools
import telegram
import datetime
import re
import dateutil.parser

from google_calendar import GoogleCalendar


def setup(updater, calendar, allowed_chat_ids):
    commands = [
            LsCommand(calendar, ['ls', 'list'], allowed_chat_ids),
            AddCommand(calendar, ['add'], allowed_chat_ids)
            ]

    for cmd in commands:
        for cmd_name in cmd.names:
            updater.dispatcher.add_handler(telegram.ext.CommandHandler(cmd_name, cmd.handle))


class Command:
    @staticmethod
    def get_args(update):
        return update.message.text.partition(' ')[2]


    @staticmethod
    def parse_datetime_str(dt_str):
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
        remaining_dt_str = None
    
        for matcher in datetime_matchers:
            formats = matcher['formats']
            pattern = matcher['pattern']
            is_datetime = matcher['is_datetime']
    
            m = re.match(pattern, dt_str)
            # print("str={0}, trying {1}".format(dt_str, pattern))
            if m:
                # print("matched, str={0}, fmt={1}, pttrn={2}".format(dt_str, formats, pattern))
                for fmt in formats:
                    try:
                        n_datetime_groups = len(fmt.split(' '))
                        datetime_str = " ".join(m.groups()[0:n_datetime_groups])
                        dt = datetime.datetime.strptime(datetime_str, fmt)
                        if not is_datetime:
                            dt = dt.date()
    
                        remaining_dt_str = m.group(n_datetime_groups + 1)
    
                        break
    
                    except ValueError:
                        continue 
    
                break

        return (dt, remaining_dt_str)

    @staticmethod
    def format_events_listing(events):
        output = ""

        events_by_day = {}

        for event in events:
            day = event['start'].strftime('%Y%m%d')
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        
        if len(events_by_day) > 0:
            for day in sorted(events_by_day):
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
                        output += "◦ {0} → {1}\n".format(time_str, event['name'])
                    else:
                        output += "◦ {0}\n".format(event['name'])

                output += "\n"
        else:
            output += "Keine anstehenden Events\n\n"

        output += "_Befehle_:\n" \
                "`/list` oder `/ls`\n" \
                "`/add 14.3.2042 Schlonz im AKK`\n" \
                "`/add 23.5. 20:00 Krümel im Z10`"

        return output


    def __init__(self, calendar, names, allowed_chat_ids):
        self.calendar = calendar
        self.names = names
        self.allowed_chat_ids = allowed_chat_ids
    

    def handle(self, bot, update):
        return self.access_allowed(update)


    def access_allowed(self, update):
        message = update.message
        chat = message.chat

        if len(self.allowed_chat_ids) == 0:
            return True
        
        if chat.id not in self.allowed_chat_ids:
            print("ACCESS CONTROL: chat_id {0} not allowed. username='{1}', first_name='{2}', last_name='{3}', text='{4}'".format(
                chat.id, chat.username, chat.first_name, chat.last_name, update.message.text))
            return False

        return True


class LsCommand(Command):
    def __init__(self, calendar, names, allowed_chat_ids):
        super().__init__(calendar, names, allowed_chat_ids)


    def handle(self, bot, update):
        if not super().handle(bot, update):
            return False

        events = self.calendar.get_events()
        output = Command.format_events_listing(events)

        bot.sendMessage(update.message.chat.id,
                text=output,
                parse_mode=telegram.ParseMode.MARKDOWN)
        
        return True

class AddCommand(Command):
    @staticmethod
    def _parse_datetime_future(args):
        (dt, remaining_args) = Command.parse_datetime_str(args) 
        
        if dt is None:
            return (None, remaining_args)

        if dt.year == 1900:  # use current/next year when no year is given
            dt = dt.replace(year=datetime.datetime.now().year)
    
            # ensure date is not in the past
            if type(dt) is datetime.date and dt < datetime.datetime.now().date():
                dt = datetime.date(dt.year + 1, dt.month, dt.day)
            elif type(dt) is datetime.datetime and dt.date() < datetime.datetime.now().date():
                dt = datetime.datetime(dt.year + 1, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    
        return (dt, remaining_args)


    def __init__(self, calendar, names, allowed_chat_ids):
        super().__init__(calendar, names, allowed_chat_ids)


    def handle(self, bot, update):
        if not super().handle(bot, update):
            return False

        args = Command.get_args(update)
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
                    new_event['summary'], new_event['start']['human_readable']))

        return True
