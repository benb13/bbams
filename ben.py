#! /usr/bin/python2
#######################################################
# File: 	ben.py
# Author:  	Benjamin Bordonaro
# Copyright:    copyright 2011-2013   
# Source:       http://www.benjaminbordonaro.com
# Version:	13.07.22
# License:	GNU GPL v2
#
# New Features 13.07.02+
# - Added the ability to retrieve other weather results such as humidity
# - Added the ability to save other weather results to data.dat
# - Fixed code with msgLine and htmlLine
# - Cleaned up code and enhanced the ability to set msgLine and htmlLine
# - Moved Aquarium/Wine Temperature to htmlline5
#
# Features:
# - Integration of PogoPlug ArchLinuxARM, Arduino Uno and 
#   Temperature Sensors
# - Email and Text Alerts for High and Low Temperatures
# - Bidirectional communication between PogoPlug Linux server 
#   and Arduino
# - Web access from Apple iPhone and iPad
# - Data Logging and Analysis using RRDTool
# - Webcam support
# - Email Support (POP and SMTP)
# - FTP Support
# - Weather Support (upgraded to xml.dom)
# - Integration with Philips hue LED Zigbee Lightbulb system
# - Data file for most recent information
# - Reporting Module
# - Custom Configuration Options
#
# Code Credits:
# - Weather upgrade to use xml.dom
#   Matthew Petroff (http://www.mpetroff.net/)
#######################################################
# Import Libaries
import datetime                         # datetime library
import time				# for sleep function
import serial				# pyserial
from smtplib import SMTP		# email/smtp
import ftplib				# ftp (file transfer)
import poplib				# pop email access
import time				# date time
import rrdtool				# rrdtool
import platform				# platform info
import urllib2				# http url library
import json				# json library
import ConfigParser			# to read ini file
from email.MIMEText import MIMEText     # email format
from xml.dom import minidom             # XML Library
import codecs				# Codec Library
from phue import Bridge			# Philips hue Library
#######################################################
# Read in configuration file using Config Parser
aConfig = ConfigParser.RawConfigParser()
aConfig.read('/srv/arduino/settings.cfg')
#aConfig.get('prd', 'config')
#######################################################
#Program Name - used for messages, alerts, etc.
myPN = aConfig.get('prd', 'appname')
myVer = aConfig.get('prd', 'appversion')
myAppVer = aConfig.get('prd', 'appversion')
myAppLabel = aConfig.get('prd', 'applabel')
myAppServer = aConfig.get('prd', 'appserver')
#######################################################
# App Configuation
#######################################################
# 12.03.08 moved configuration to settings.cfg
#Alerts level for Temperature
alertHighTemp = aConfig.getfloat('prd', 'alerthightemp')
alertLowTemp = aConfig.getfloat('prd', 'alertlowtemp')

# Web Camera (Enable = 1, Disable = 0)
myWebcamera = aConfig.getint('prd', 'webcamera')

# Arduino (Enable = 1, Disable = 0)
myArduinoIn = aConfig.getint('prd', 'arduinoin')
myArduinoOut = aConfig.getint('prd', 'arduinoout')
mySerial = aConfig.getint('prd', 'serial')
myTempSensor = aConfig.getint('prd', 'tempsensor')

# Debugging (Enable = 1, Disable = 0
myDebug = aConfig.getint('prd', 'debug')

# Email Checking (Enable = 1, Disable = 0)
myEmail = aConfig.getint('prd', 'email')

# FTP (Enable = 1, Disable = 0)
myFTP = aConfig.getint('prd', 'ftp')

# Internet IP Checking (Enable = 1, Disable = 0)
myIP = aConfig.getint('prd', 'ip')
myIPPort = aConfig.get('prd', 'hostipport')

# Write Message File (Enable = 1, Disable = 0)
myMsg = aConfig.getint('prd', 'messages')

# Retrieve Weather from Google (Enable = 1, Disable = 0)
myWeather = aConfig.getint('prd', 'weather')
myWeatherLon = aConfig.get('prd', 'weatherlon')
myWeatherLat = aConfig.get('prd', 'weatherlat')
myWeatherCity = aConfig.get('prd', 'weathercity')
myWeatherState = aConfig.get('prd', 'weatherstate')
myWeatherAPI = aConfig.get('prd', 'weatherapi')

# Build and save report (Enable = 1, Disable = 0)
# Text Alerts (Enable = 1, Disable = 0)
myReport = aConfig.getint('prd', 'reports')
myTxtAlerts = aConfig.getint('prd', 'txtalerts')
myAlertsAll = aConfig.getint('prd', 'alertsall')

# Time to Send Report via Email
myReportTime = aConfig.get('prd', 'reporttime')

# Philips hue Configuration
myHueIP = aConfig.get('prd', 'hueip')
myHueEnable = aConfig.getint('prd', 'hueenable')

#######################################################
# Variables
logdata1 = ""
msg1 = ""
myReportBody = ""
myReportBreak = "-------------------------------------------"
#######################################################
# serial port of Arduino on ArchLinux ARM server
# Usually it is /dev/ttyACM0
if mySerial == 1:
   ser = serial.Serial('/dev/ttyACM0', 9600)

#######################################################
#Functions
#######################################################
def ams_lcd_format(lcdline):
    retline = lcdline[:20]
    retline = retline.ljust(20)    
    return retline

def ams_email_check():
    mprt = 110
    mbox = poplib.POP3_SSL(aConfig.get('prd', 'emailpopsrvr1'))
    mbox.getwelcome()
    mbox.user(aConfig.get('prd', 'emailuser1'))
    mbox.pass_(aConfig.get('prd', 'emailpass1'))
    mstat = mbox.stat()
    print(mstat)
    messageCount = len(mbox.list()[1])
    print(str(messageCount) + " Email Message(s)")
    rvalue = str(messageCount)
    for mList in range(messageCount):
      eSub = ""
      eFrom = ""
      for msgl in mbox.retr(mList+1)[1]:
        if msgl.startswith("Subject"):
           #print msgl
           eSub = msgl[8:].strip()
        if msgl.startswith("From"):
           #print msgl
           eFrom = msgl.strip()
      if eFrom.find(eusr2) > -1:
        rvalue = eSub
      else:
        rvalue = "No Message"
    mbox.quit()
    return rvalue

def ams_ftp_upload(ftpsdir1, file1):
    # Using Config File settings.cfg
    ftpuser1 = aConfig.get('prd', 'ftpuser1')
    ftppass1 = aConfig.get('prd', 'ftppass1')
    ftpsite1 = aConfig.get('prd', 'ftpsite1')
    #ftpsourcedir1 = aConfig.get('prd', 'ftpsourcedir1')
    ftpdestdir1 = aConfig.get('prd', 'ftpdestdir1')
    try:
       connftp = ftplib.FTP(ftpsite1)
       connftp.login(ftpuser1,ftppass1)
       connftp.cwd(ftpdestdir1)
       fhandle1 = open(ftpsdir1 + file1, "rb")
       connftp.storbinary('STOR ' + file1, fhandle1)
       fhandle1.close()
       connftp.quit()
    except:
       print("FTP Error")

def ams_email_alert(subject, message, sendto):
    # Using Config File settings.cfg
    msg = MIMEText(message)
    # msg['Subject'] = myPN + " " + subject
    msg['Subject'] = subject
    msg['From'] = aConfig.get('prd', 'emailuser2')
    msg['To'] = aConfig.get('prd', 'emailuser2')
    smtpObj = SMTP(aConfig.get('prd', 'emailsmtpsrvr2'),587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.ehlo()
    smtpObj.login(aConfig.get('prd', 'emailuser2'), aConfig.get('prd', 'emailpass2'))
    try:
       if len(sendto) > 1:
          smtpObj.sendmail(aConfig.get('prd', 'emailuser2'), sendto, msg.as_string())
       else:
          smtpObj.sendmail(aConfig.get('prd', 'emailuser2'), aConfig.get('prd', 'emailuser2'), msg.as_string())
    finally:         
       smtpObj.close()

def ams_write_to_log(file1, rw, line_to_write):
    if rw == "a":
     datafile1=open(file1,'a')
    if rw == "w":
     datafile1=open(file1,'w')
    datafile1.write(line_to_write + "\n")
    datafile1.close()

def ams_write_html_file(file_to_write, line_to_write):
    html_header = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
       <meta http-equiv="content-type" content="text/html; charset=utf-8" />
       <meta name="viewport" content="width=device-width, user-scalable=no" />
       <title>Arduino Monitor</title>
       <link rel ="stylesheet" href = "/iPhoneIntegration.css" />
    </head>
    <body>
    """
    html_footer = "<br><h2>Last Updated: " + tdnow + "</h2>\n</body></html>"
    html_all = html_header + line_to_write + html_footer
    ams_write_to_log(file_to_write,'w',html_all)

def ams_getWeather2():
    # Fetch data (change lat and lon to desired location)
    try:
       weather_xml = urllib2.urlopen('http://graphical.weather.gov/xml/SOAP_server/ndfdSOAPclientByDay.php?whichClient=NDFDgenByDay&lat=' + myWeatherLat + '&lon=' + myWeatherLon + '&format=24+hourly&numDays=4&Unit=e').read()
    except:
       return "Error: weather"
    dom = minidom.parseString(weather_xml)
    # Parse temperatures
    xml_temperatures = dom.getElementsByTagName('temperature')
    highs = [None]*4
    lows = [None]*4
    for item in xml_temperatures:
      if item.getAttribute('type') == 'maximum':
        values = item.getElementsByTagName('value')
        for i in range(len(values)):
            highs[i] = int(values[i].firstChild.nodeValue)
      if item.getAttribute('type') == 'minimum':
        values = item.getElementsByTagName('value')
        for i in range(len(values)):
            lows[i] = int(values[i].firstChild.nodeValue)

    # Parse icons
    xml_icons = dom.getElementsByTagName('icon-link')
    icons = [None]*4
    for i in range(len(xml_icons)):
      icons[i] = xml_icons[i].firstChild.nodeValue.split('/')[-1].split('.')[0].rstrip('0123456789')

    # Parse dates
    xml_day_one = dom.getElementsByTagName('start-valid-time')[0].firstChild.nodeValue[0:10]
    day_one = datetime.datetime.strptime(xml_day_one, '%Y-%m-%d')

    # Print some info for debugging
    if myDebug == 1:
      print("xml_day_one: " + str(xml_day_one))
      print("day_one:     " + str(day_one))
      print("High:        " + str(highs[0]))
      print("Low:         " + str(lows[0]))

    tdnow3 = time.strftime('%a', (time.localtime(time.time())))
    #weather = myWeatherCity + "|High: " + str(highs[0]) + "F  Low: " + str(lows[0]) + "F"
    weather = "High: " + str(highs[0]) + "F  Low: " + str(lows[0]) + "F"
    # if there was an error getting the condition, the city is invalid
    if weather == "<?xml version=":
        return "Invalid city"

    #return the weather condition
    return weather

def ams_getWeather3(rWType):
    # Fetch data from wunderground.com
    try:
       f = urllib2.urlopen('http://api.wunderground.com/api/' + myWeatherAPI + '/geolookup/conditions/q/' + myWeatherState + '/' + myWeatherCity + '.json')
    except:
       return "Error: weather"
    json_string = f.read()
    # write the weather to a file for future use
    ams_write_to_log('/srv/arduino/weather.dat','w',json_string)
    parsed_json = json.loads(json_string)
    location = parsed_json['location']['city']
    temp_f = str(parsed_json['current_observation']['temp_f']) + "F"
    datasave.set('data','weather-temp-f',str(temp_f)) 

    weather_current = parsed_json['current_observation']['weather']
    datasave.set('data','weather-current',str(weather_current)) 

    weather_humidity = str(parsed_json['current_observation']['relative_humidity'])
    weather_humidity = weather_humidity.replace("%"," Percent")
    datasave.set('data','weather-humidity',str(weather_humidity)) 

    weather_feelslike = str(parsed_json['current_observation']['feelslike_f']) + "F"
    datasave.set('data','weather-feelslike-f',str(weather_feelslike)) 

    #v2013.07.18 - Save additional weather data
    weather_wind = str(parsed_json['current_observation']['wind_string'])
    datasave.set('data','weather-wind',str(weather_wind)) 

    f.close()
    #weather = "High: " + str(highs[0]) + "F  Low: " + str(lows[0]) + "F"
    if rWType == "temperature":
       weather = str(temp_f) + "F " + str(weather_current) 
       print "Current weather is %s %s" % (str(temp_f), str(weather_current))
    if rWType == "humidity":
       weather = str(weather_humidity) 
    if rWType == "feelslike":
       weather = "Feels like " + str(weather_feelslike)

    return weather

def buildReport(rHeading, rText):
    myB = rHeading + "\n" + rText + "\n" + myReportBreak + "\n"
    return myB 

def ams_sethuecolor(rBulbNumber, rColor, rBlink):
    # Usage ams_sethuecolor(1,"blue",0)
    # Colors Supported: off, white, red, green, purple, pink, blue, yellow
    b = Bridge(myHueIP)
    lights = b.get_light_objects('id')
    # Moved off setting above light turn on so that the bulb does not
    # flicker if it is off and another off command comes across
    if rColor == "off":
        lights[rBulbNumber].on = False
    else:
        if (lights[rBulbNumber].on == False):
           lights[rBulbNumber].on = True
    if rColor == "white":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 14922
        lights[rBulbNumber].saturation = 144
        lights[rBulbNumber].xy = [0.4595, 0.4105]
    if rColor == "white50":
        lights[rBulbNumber].brightness = 125
        lights[rBulbNumber].hue = 14922
        lights[rBulbNumber].saturation = 144
        lights[rBulbNumber].xy = [0.4595, 0.4105]
    if rColor == "red":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 49746
        lights[rBulbNumber].saturation = 235
        lights[rBulbNumber].xy = [0.6449, 0.0329]
    if rColor == "purple":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 46033
        lights[rBulbNumber].saturation = 228
        lights[rBulbNumber].xy = [0.2336, 0.1129]
    if rColor == "pink":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 47793
        lights[rBulbNumber].saturation = 211
        lights[rBulbNumber].xy = [0.3627, 0.1807]
    if rColor == "yellow":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 19886
        lights[rBulbNumber].saturation = 254
        lights[rBulbNumber].xy = [0.4304, 0.5023]
    if rColor == "blue":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 47108
        lights[rBulbNumber].saturation = 254
        lights[rBulbNumber].xy = [0.167, 0.04]
    if rColor == "green":
        lights[rBulbNumber].brightness = 250
        lights[rBulbNumber].hue = 23543
        lights[rBulbNumber].saturation = 254
        lights[rBulbNumber].xy = [0.3919, 0.484]

#######################################################
# Begin main program
#######################################################
#blank msg variables
msgLine1 = ""
msgLine2 = ""
msgLine3 = ""
msgLine4 = ""
htmlLine1 = ""
htmlLine2 = ""
htmlLine3 = ""
htmlLine4 = ""
htmlLine5 = ""
htmlLine6 = ""
htmlLine7 = ""
htmlLine8 = ""
htmlLine9 = ""
htmlLine10 = ""

#Store current date and time
tdnow = time.strftime('%m-%d-%Y %H:%M:%S', (time.localtime(time.time())))
tdnowlcd = time.strftime('%m-%d-%Y %I:%M%p', (time.localtime(time.time())))
tdnow2 = time.strftime('%b %d, %Y %I:%M%p', (time.localtime(time.time())))
tdreport = time.strftime('%H%M', (time.localtime(time.time())))
tdmin = time.strftime('%M', (time.localtime(time.time())))
tddow = time.strftime('%a', (time.localtime(time.time())))
tdweekday = time.strftime('%w', (time.localtime(time.time())))

htmlLine1 = "<h1>Time</h1><ul><li>" + tdnowlcd + "</ul>"

#Commented for debugging
#print("tdnow:" + tdnow)
#print("tdnow2:" + tdnow2)
#print("tdreport:" + tdreport)
#print("tdmin:" + tdmin)
#print("tddow:" + tddow)
#print("tdweekday:" + tdweekday)

if myAlertsAll == 1:
   print("Alerts On")
else:
   print("Alerts Off")

# Begin data file
datasave = ConfigParser.SafeConfigParser()
datasave.read('/srv/arduino/data.dat')
datasave.set('data','time',str(tdnowlcd))

#Moved debug info to the top so that we can seed the LCD with
#debug info if no data is present
if myDebug == 1:
    myReportBody = myReportBody + "System Information:\n"
    print("Debugging is enabled")
    print 'system   :', platform.system()
    datasave.set('data','platform-system',platform.system())
    myReportBody = myReportBody + platform.system() + " "
    print 'release  :', platform.release()
    datasave.set('data','platform-release',platform.release())
    myReportBody = myReportBody + platform.release() + "\n"
    print 'machine  :', platform.machine()
    datasave.set('data','platform-machine',platform.machine())
    myReportBody = myReportBody + platform.machine() + "\n"
    myReportBody = myReportBody + myReportBreak + "\n"

if myReport == 1:
    myReportBody = myReportBody + buildReport("Report Created:",tdnow)

timeforweather = 0

if myWeather == 1:
    # v13.03.10 Retrieve weather every 15 minutes
    if (tdmin == "00" or tdmin == "15" or tdmin == "30" or tdmin == "45"):
      print("Time to retrieve the weather")
      timeforweather = 1
      weather1 = ams_getWeather3("temperature")
      fweather1 = "Current: " + weather1.replace("|","\n")
    if myReport == 1:
      # Weather report rewritten for v2013.07.19 + Code fixes
      myWeatherReport = "Now " + str(datasave.get('data','weather-temp-f')) + " " + str(datasave.get('data','weather-current')) + "\nFeels like " + str(datasave.get('data','weather-feelslike-f')) + "\nHumidity is " + datasave.get('data','weather-humidity') + "\nWind is " + str(datasave.get('data','weather-wind'))
      myReportBody = myReportBody + buildReport("Weather Conditions:", myWeatherReport)
      if myTxtAlerts == 1:
        if tdreport == myReportTime:
           ams_email_alert("Weather",myWeatherReport,aConfig.get('prd', 'smstextuser1'))
        else:
             print("Not time to send weather text alert")
      else:
        print("Text alerts are not enabled")

# For timing reasons check email first and then 
# write it to the serial port later
if myEmail == 3:
   retEmail = ams_email_check()
   datasave.set('data','email',retEmail)

# Check Internet IP Address
if myIP == 1:
    ################################################
    # TODO: Needs to be rewritten. 
    # whatismyip is no longer a free active service
    ################################################
    pub_ip = urllib2.urlopen("http://automation.whatismyip.com/n09230945.asp").read()
    print pub_ip
    datasave.set('data','ip',pub_ip) 
    if myReport == 1:
       myReportBody = myReportBody + buildReport("My Internet IP:", pub_ip)

# Read the Arduino
if myArduinoIn == 1: 
    print("Reading data from the Arduino")
    # flush the serial input and read the data from Arduino
    ser.flushInput()
    sresult = ser.readline().strip()
    datasave.set('data','arduino-in',sresult)
    print(sresult)

# Read the temperature from the Arduino
if myTempSensor == 1: 
    # flush the serial input and read the data from Arduino
    ser.flushInput()
    sresult = ser.readline().strip()
    #############################################################
    # 12.12.31 - Added for splitting multiple tempsensor results
    tMetric1, tMetric2, tMetric3 = sresult.split("|")
    print("Temperature1: " + tMetric1)
    print("Temperature2: " + tMetric2)
    print("Temperature3: " + tMetric3)
    #############################################################
    datasave.set('data','temperature',sresult) 
    #############################################################
    # Write to RRD Round Robin Database for analytics
    #############################################################
    #ret = rrdtool.update("/srv/arduino/ttemp.rrd","N:" + sresult)
    ret = rrdtool.update("/srv/arduino/ttemp2.rrd", "N:" + tMetric1 + ":" +  tMetric2 + ":" + tMetric3)
    if ret:
       print rrdtool.error()
    #############################################################
    print("Temperature: " + sresult)
    #Alerts checking for high and low temp
    #If temp is exactly 32 degrees or less something is wrong with 
    #reading the sensor
    if myAlertsAll == 1: 
       if float(sresult) > 32.00:
          if float(sresult) < alertLowTemp:
            print("Alert: Low Temp")
            ams_email_alert("Temperature", "High Temperature: " + str(sresult),"0")
          if float(sresult) > alertHighTemp:
            print("Alert: High Temp")
            ams_email_alert("Temperature","Low Temperature: " + str(sresult),"0")
    # used for debugging
    #sresult = "00.00"
    if myReport == 1:
       myReportBody = myReportBody + buildReport(myAppLabel + " Temperature:", str(sresult) + "F")
       # TODO: Need to fix this code
       htmlLine5 = "<h1>" + myAppLabel + " Temperature</h1><ul><li><a href=\"rrdgraph.html\">" + sresult + "</a></ul>"
    if myWebcamera == 1: 
       htmlLine2 = htmlLine2 + "<h1>Camera</h1><ul><li><img width=\"260\" src=\"webcam.jpg\"></ul>"
else:       
    print("ArduinoIn is not enabled")

# Write Application Version to the footer of the report
myReportBody = myReportBody + buildReport(myPN + " Version", myVer)

if myReport == 1:
    ams_write_to_log('/srv/arduino/report.txt','w',myReportBody)
    # Email Report out at myReporTime
    if tdreport == myReportTime:
       print("Sending Report")
       ams_email_alert("System Report",myReportBody,"0")
    else:
       print("Not sending report")

#Write HTML File - index.html
if myWeather == 1:
   if tdreport == myReportTime:
     htmlLine2 = "<h1>Weather</h1><ul><li><a href=\"message.html\">" + fweather1 + "</a></ul>"

#Philips hue API integration added v2013.03.02
if myHueEnable == 1:
    #msgLine3 = ams_lcd_format("Philips hue enabled")
    htmlLine3 = "<h1>Philips hue</h1><ul><li><a href=\"hueschedule.html\">enabled</a></ul>"
    # Read file an execute hue api based on hueschedule.cfg
    huehtml = "<h1>Philips hue Schedule</h1>"
    for hline in open("/srv/arduino/benschedule.cfg","r").readlines():
      huehtml = huehtml + "<ul><li>" + hline + "</ul>"
      hAction, hDow, hBulb, hTime, hColor, hAlert = hline.split(",")
      if (hAction == "HUE" ):
        if (tdreport == hTime and hDow == "AL"):
          ams_sethuecolor(int(hBulb),hColor,hAlert)    
        if (int(tdweekday) > 0 and int(tdweekday) < 6):
          if (tdreport == hTime and hDow == "WD"):
	    ams_sethuecolor(int(hBulb),hColor,hAlert)
        if (int(tdweekday) < 1 or int(tdweekday) > 5):
          if (tdreport == hTime and hDow == "WE"):
	    ams_sethuecolor(int(hBulb),hColor,hAlert)
    ams_write_html_file('/srv/http/hueschedule.html',huehtml)

#FTP functionality added in v2012.09.11
if myFTP == 1:
    if (tdmin == "05"):
       print("FTPing images to website")
       ams_ftp_upload('/srv/http/img/','temp1h.png')
       ams_ftp_upload('/srv/http/img/','temp4h.png')
       ams_ftp_upload('/srv/http/img/','temp1d.png')
       ams_ftp_upload('/srv/http/img/','temp7d.png')
       ams_ftp_upload('/srv/http/img/','temp30d.png')
       ams_ftp_upload('/srv/http/img/','temp90d.png')

if myMsg == 1:
   msgOut = "|" + msgLine1 + "|" + msgLine2 + "|" + msgLine3 + "|" + msgLine4 + "|"
   ams_write_to_log('/srv/arduino/messages.cfg','w',msgOut)


datasave.set('data','version',"v" + str(myVer))

# New code added in v2013.07.18 to set the msgLines at the end of the script
# to any parameters in the data.dat file
msgLine1 = ams_lcd_format(datasave.get('data','time'))
msgLine2 = ams_lcd_format(datasave.get('data','weather-temp-f') + ' ' + datasave.get('data','weather-current'))
msgLine3 = ams_lcd_format('Feels like ' + datasave.get('data','weather-feelslike-f') + 'F')
msgLine4 = ams_lcd_format(datasave.get('data','version'))

# then let's save the msglines to the data.dat file for future use or debuggung
datasave.set('data','msgLine1',msgLine1)
datasave.set('data','msgLine2',msgLine2)
datasave.set('data','msgLine3',msgLine3)
datasave.set('data','msgLine4',msgLine4)

# Grab any data before we close the file
htmlLine4 = "<h1>Weather</h1><ul><li>Now " + str(datasave.get('data','weather-temp-f')) + " " + str(datasave.get('data','weather-current')) + "<br>Feels like " + str(datasave.get('data','weather-feelslike-f')) + "<br>Humidity is " + datasave.get('data','weather-humidity') + "<br>Wind is " + str(datasave.get('data','weather-wind')) + "</ul>"

htmlLine9 = "<h1>Server</h1><ul><li>"
htmlLine9 = htmlLine9 + datasave.get('data','platform-system') + "<br>"
htmlLine9 = htmlLine9 + datasave.get('data','platform-release') + "<br>"
htmlLine9 = htmlLine9 + datasave.get('data','platform-machine') + "<br>"
htmlLine9 = htmlLine9 + "</ul>"

htmlLine10 = "<h1>Version</h1><ul><li>" + datasave.get('data','version') + "</ul>"

# Write Data File and Close
datafile = open('/srv/arduino/data.dat','w')
datasave.write(datafile)
datafile.close()

# Write index.html File
ams_write_html_file('/srv/http/index.html',htmlLine1 + htmlLine2 + htmlLine3 + htmlLine4 + htmlLine5 + htmlLine6 + htmlLine7 + htmlLine8 + htmlLine9 + htmlLine10)

# If we are not checking email and the Arduino is active
# then write the msgLines to the Arduino
if myArduinoOut == 1:
    ser.flushOutput()
    ser.write("|" + ams_lcd_format(msgLine1) + "||||\r\n")
    print("|" + ams_lcd_format(msgLine1) + "||||\r\n")
    time.sleep(5)
    if (len(msgLine2) > 3): 
       ser.flushOutput()
       ser.write("|" + ams_lcd_format(msgLine1) + "|" + ams_lcd_format(msgLine2) + "|||\r\n")
       print("|" + ams_lcd_format(msgLine1) + "|" + ams_lcd_format(msgLine2) + "|||\r\n")
       time.sleep(5)
    if (len(msgLine3) > 3): 
       ser.flushOutput()
       ser.write("|" + ams_lcd_format(msgLine1) + "||" + ams_lcd_format(msgLine3) + "||\r\n")
       print("|" + ams_lcd_format(msgLine1) + "||" + ams_lcd_format(msgLine3) + "||\r\n")
       time.sleep(5)
    if (len(msgLine4) > 3): 
       ser.flushOutput()
       ser.write("|" + ams_lcd_format(msgLine1) + "|||" + ams_lcd_format(msgLine4) + "|\r\n")
       print("|" + ams_lcd_format(msgLine1) + "|||" + ams_lcd_format(msgLine4) + "|\r\n")
       time.sleep(5)
print("Script Completed.")
