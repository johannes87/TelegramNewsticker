import datetime
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import dateutil.parser
import httplib2
from dateutil.parser import parse as dt_parse


class GoogleCalendar:
    def __get_calendar_service(client_secret_file):
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


    def add_date_event(self, event_date, event_name):
        event_date_str = event_date.strftime('%Y-%m-%d')
    
        event_body = {
                'summary': event_name, 
                'start': { 'date': event_date_str },
                'end': { 'date': event_date_str }
        }
    
        new_event = self.service.events().insert(
                calendarId=self.calendar_id, body=event_body).execute()

        new_event['start']['human_readable'] = dt_parse(new_event['start']['date']).\
                strftime('%d.%m.%Y')
    
        return new_event


    def add_datetime_event(self, event_datetime, duration, event_name):
        event_datetime_end = event_datetime + duration

        event_datetime_start_str = event_datetime.astimezone().isoformat()
        event_datetime_end_str = event_datetime_end.astimezone().isoformat()

        event_body = {
            'summary': event_name,
            'start': { 'dateTime': event_datetime_start_str },
            'end': { 'dateTime': event_datetime_end_str }
        }

        new_event = self.service.events().insert(
                calendarId=self.calendar_id, body=event_body).execute()

        new_event['start']['human_readable'] = dt_parse(new_event['start']['dateTime']).\
                strftime('%d.%m.%Y um %H:%M')
    
        return new_event

    
    def get_events(self):
        now = datetime.datetime.utcnow()
        now -= datetime.timedelta(days=1) # ensure same-day events are shown
        now = now.isoformat() + 'Z' # 'Z' indicates UTC time
    
        eventsResult = self.service.events().list(
            calendarId=self.calendar_id, 
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
            ret_events.append({'start': event_start, 'summary': event_summary})
        
        return ret_events 


    def __init__(self, client_secret_file, calendar_id):
        self.service = GoogleCalendar.__get_calendar_service(client_secret_file)
        self.calendar_id = calendar_id
