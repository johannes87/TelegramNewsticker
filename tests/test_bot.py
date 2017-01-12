import unittest
import bot
import datetime

class TestParseDatetimeFuture(unittest.TestCase):
	def assert_datetime_equals(self, args, day, month, year, hour, minute, remaining_args):
		(dt, rem) = bot.parse_datetime_future(args)
		self.assertEqual(dt.year, year)
		self.assertEqual(dt.month, month)
		self.assertEqual(dt.day, day)	
		self.assertEqual(dt.hour, hour)
		self.assertEqual(dt.minute, minute)
		self.assertEqual(rem, remaining_args)

	def assert_date_equals(self, args, day, month, year, remaining_args):
		(dt, rem) = bot.parse_datetime_future(args)
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
		self.assert_date_equals("15. 3. 14   ", 15, 3, 2014, "   ")

	def test_no_year_given(self):
		now = datetime.datetime.now()
		yesterday = now - datetime.timedelta(days=1)
		tomorrow = now + datetime.timedelta(days=1)

		yesterday_day_month_str = yesterday.strftime('%d. %m')
		now_day_month_str = now.strftime('%d. %m.')
		tomorrow_day_month_str = tomorrow.strftime('%d. %m. ')

		self.assert_date_equals(yesterday_day_month_str, 
			yesterday.day, yesterday.month, now.year + 1, '')

		self.assert_date_equals(now_day_month_str,
			now.day, now.month, now.year, '')

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



			

