import unittest
import datetime
from unittest.mock import create_autospec, MagicMock

import google_calendar
from commands import AddCommand, LsCommand


class TestAccessControl(unittest.TestCase):
    def test_access_control(self):
        calendar = create_autospec(google_calendar.GoogleCalendar)
        allowed_id = 1234;

        ls_command = LsCommand(calendar, ['ls'], [allowed_id])
        update = MagicMock()
        update.message.chat.id = 31337
        bot = MagicMock()
        ret = ls_command.handle(bot, update)
        self.assertFalse(ret)
        bot.sendMessage.assert_not_called()

        update = MagicMock()
        update.message.chat.id = allowed_id
        bot = MagicMock()
        ret = ls_command.handle(bot, update)
        self.assertTrue(ret)
        bot.sendMessage.assert_called()

        ls_command_any_allowed = LsCommand(calendar, ['ls'], [])
        update = MagicMock()
        update.message.chat.id = 912389781
        bot = MagicMock()
        ret = ls_command_any_allowed.handle(bot, update)
        self.assertTrue(ret)
        bot.sendMessage.assert_called()
        

class TestParseDatetimeFuture(unittest.TestCase):
    def assert_datetime_equals(self, args, day, month, year, hour, minute, remaining_args):
        (dt, rem) = AddCommand._parse_datetime_future(args)
        self.assertEqual(dt.year, year)
        self.assertEqual(dt.month, month)
        self.assertEqual(dt.day, day)
        self.assertEqual(dt.hour, hour)
        self.assertEqual(dt.minute, minute)
        self.assertEqual(rem, remaining_args)

    def assert_date_equals(self, args, day, month, year, remaining_args):
        (dt, rem) = AddCommand._parse_datetime_future(args)
        self.assertEqual(dt.year, year)
        self.assertEqual(dt.month, month)
        self.assertEqual(dt.day, day)
        self.assertEqual(rem, remaining_args)

    def test_datetime_with_year(self):
        self.assert_datetime_equals("15. 10.83 13:00 foo", 15, 10, 1983, 13, 0, ' foo')
        self.assert_datetime_equals("15. 10.   83 13:0", 15, 10, 1983, 13, 0, '')
        self.assert_datetime_equals("15.10.83 13:0", 15, 10, 1983, 13, 0, '')
        self.assert_datetime_equals("15.10.1983 13:0", 15, 10, 1983, 13, 0, '')

    def test_date_with_year(self):
        self.assert_date_equals("15. 3. 2014", 15, 3, 2014, "")
        self.assert_date_equals("15. 3. 14", 15, 3, 2014, "")
        self.assert_date_equals("15. 3. 14  ", 15, 3, 2014, "  ")

    def test_no_year_given(self):
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        tomorrow = now + datetime.timedelta(days=1)

        yesterday_day_month_str = yesterday.strftime('%d. %m')
        self.assert_date_equals(yesterday_day_month_str,
                yesterday.day, yesterday.month, now.year + 1, '')
        
        now_day_month_str = now.strftime('%d. %m.')
        self.assert_date_equals(now_day_month_str,
                now.day, now.month, now.year, '')

        tomorrow_day_month_str = tomorrow.strftime('%d. %m. ')
        self.assert_date_equals(tomorrow_day_month_str,
                tomorrow.day, tomorrow.month, tomorrow.year, ' ')


        yesterday_dmHM_str = yesterday.strftime('%d. %m. %H:%M')
        now_dmHM_str = now.strftime('%d. %m %H:%M')
        tomorrow_dmHM_str = tomorrow.strftime('%d.%m.  %H:%M')


        self.assert_datetime_equals(yesterday_dmHM_str,
                yesterday.day, yesterday.month, now.year + 1, yesterday.hour, yesterday.minute, '')

        self.assert_datetime_equals(now_dmHM_str,
                now.day, now.month, now.year, now.hour, now.minute, '')

        self.assert_datetime_equals(tomorrow_dmHM_str,
                tomorrow.day, tomorrow.month, tomorrow.year, tomorrow.hour, tomorrow.minute, '')
