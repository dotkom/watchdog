from icalendar import Calendar
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from tzlocal import get_localzone
from models import checkin
from config import icsLocation, DBusername, DBpassword, DBlocation, tomail, frommail, frommailpass
import urllib.request
import smtplib
import pytz

# Gets ical file and parses it to a calendar
# Example ical is used
req = urllib.request.Request(icsLocation)
response = urllib.request.urlopen(req)
data = response.read()
gcal = Calendar.from_ical(data)

# Creates empty list for future use and utc variable for timezone converting
people = []
utc = pytz.UTC

# Sets up engine for database connection
engine = create_engine('mysql+mysqlconnector://' + DBusername + ':' + DBpassword + '@' + DBlocation, echo=False)

# The date that starts generating the calendar
defineDate = datetime(2014, 9, 22, 00, 00).replace(tzinfo=get_localzone())

# Sets up the engine to get information from SQL server
conn = engine.connect()

# Generates a text-field for the e-mail report
def generateText():
    textField = "\nThese people did not check in during their watch-hours:"

    for person in people:
        textField += ("\n" + person)

    return textField

# Sends the email with the content apropriate to the reciever
def sendEmail():
    smtpserver = smtplib.SMTP("smtp.gmail.com",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(frommail, frommailpass)
    header = 'To:' + tomail + '\n' + 'From: ' + frommail + '\n' + 'Subject:Watchdog Daily Report ' + str(todate.day) + '.' + str(todate.month) + '\n'
    msg = header + generateText()
    smtpserver.sendmail(frommail, tomail, msg)
    print ('Email sent')
    smtpserver.close()

# Loops through the ical and looks for relevant events
for event in gcal.walk('vevent'):
    isFound = True

    start = event.decoded('dtstart')

    todate = datetime.now().replace(tzinfo=get_localzone())

    today = todate.weekday()

    # Compares the dates of the ical events towards the current date
    if ((start > defineDate) and (start < (defineDate + timedelta(days=7))) and (start.weekday() == today)):
        isFound = False
        name = event.get('summary')
        end = event.decoded('dtend')

        # Gets the data from the database
        s = select([checkin])
        result = conn.execute(s)

        # Loops through the sql content
        for row in result:
            tempTime = row['time'].split(':')
            tempName = row['name']
            tempWeekDay = int(tempTime[0])
            tempHours = int(tempTime[1])
            tempMinutes = int(tempTime[2])
            tempDay = int(tempTime[3])
            tempMonth = int(tempTime[4])

            tempNameList = tempName.split(' ')
            tempName = (tempNameList[0] + " " + tempNameList[(len(tempNameList) - 1)])


            # Compares checkin date to today and reports if person is found
            if (start.weekday() == tempWeekDay):
                if (((tempHours >= start.hour) and (tempHours < end.hour)) and (tempDay == todate.day) and (tempMonth == todate.month)):
                    isFound = True
                    break

        # If person isn't found; adds name to list
        if (not(isFound)):
            people.append(name)


sendEmail()

response.close()