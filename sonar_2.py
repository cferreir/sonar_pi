#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# Enhanced by Carlos Ferreira Oct 26 2018
# License: GPL 2.0 
import os
from gps import *
from time import *
import time
import threading
import requests
import json

#Libraries
import RPi.GPIO as GPIO
 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 24
GPIO_ECHO = 23
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

gpsd = None #seting the global variable
# distance = None

# os.system('clear') #clear the terminal (optional)

distance = 0

class SONARPoller(threading.Thread):
  global distance
  
  def __init__(self):
    threading.Thread.__init__(self)
    
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    while sonarth.running:  
       # set Trigger to HIGH
      GPIO.output(GPIO_TRIGGER, True)
 
      # set Trigger after 0.01ms to LOW
      time.sleep(0.00001)
      GPIO.output(GPIO_TRIGGER, False)
 
      StartTime = time.time()
      StopTime = time.time()
 
      # save StartTime
      while GPIO.input(GPIO_ECHO) == 0:
          StartTime = time.time()
 
      # save time of arrival
      while GPIO.input(GPIO_ECHO) == 1:
          StopTime = time.time()
 
      # time difference between start and arrival
      TimeElapsed = StopTime - StartTime
      # multiply with the sonic speed (34300 cm/s)
      # and divide by 2, because there and back
      distance = (TimeElapsed * 34300) / 2
      time.sleep(60)
      
  def join(self):
      return distance
 

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer

if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  sonarth = SONARPoller() # create sonar thread
  global distance
  
  try:
    gpsp.start() # start it up
    sonarth.start() # check distance

    while gpsd.fix.latitude == 0:
       time.sleep(10)
  
    ltlg = str(gpsd.fix.latitude)+','+str(gpsd.fix.longitude)

    payload = {'latlng': ltlg, 'key': 'AIzaSyCFAu81ebNZ36Bi557-SFKg19wMQ848EcU'}
   
    print "Latitude and Longitude: " + ltlg
 
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=payload)

# For successful API call, response code will be 200 (OK)
    if(r.ok):

        # Loading the response data into a dict variable
        # json.loads takes in only binary or string variables so using content to fetch binary content
        # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
        jData = json.loads(r.content)

        print("The response contains {0} properties".format(len(jData)))
        print("\n")
        # for key in jData:
        #    print key + " : " + jData[key]
        print(jData['results'][0]['formatted_address']) 
        # print "JSON Output: " + json.dumps(jData)
        # print "END JSON ****************************************************"
    else:
        # If response code is not ok (200), print the resulting http error code with description
        r.raise_for_status()
        print "END OF ERROR *******************"

# Request a Street View photo

    payload = {'size': '400x400', 'location': ltlg, 'fov': '90', 'pitch': '10', 'key': 'AIzaSyCFAu81ebNZ36Bi557-SFKg19wMQ848EcU'}
   
    r = requests.get('https://maps.googleapis.com/maps/api/streetview/metadata', params=payload)

# For successful API call, response code will be 200 (OK)
    if(r.ok):

        # Loading the response data into a dict variable
        # json.loads takes in only binary or string variables so using content to fetch binary content
        # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
        jData = json.loads(r.content)

        print("The response contains {0} properties".format(len(jData)))
        print("\n")
        # for key in jData:
        #    print key + " : " + jData[key]
        # print(jData['results'][0]['formatted_address']) 
        print "JSON Output: " + json.dumps(jData)
        print "END JSON ****************************************************"
    else:
        # If response code is not ok (200), print the resulting http error code with description
        r.raise_for_status()
        print "END OF ERROR *******************"

    while True:
      #It may take a second or two to get good data
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc

      # os.system('clear')
      print ("Measured Distance = %.1f cm" % distance)
      print
      print ' GPS reading'
      print '----------------------------------------'
      print 'latitude    ' , gpsd.fix.latitude
      print 'longitude   ' , gpsd.fix.longitude
      print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
      print 'altitude (m)' , gpsd.fix.altitude
      print 'eps         ' , gpsd.fix.eps
      print 'epx         ' , gpsd.fix.epx
      print 'epv         ' , gpsd.fix.epv
      print 'ept         ' , gpsd.fix.ept
      print 'speed (m/s) ' , gpsd.fix.speed
      print 'climb       ' , gpsd.fix.climb
      print 'track       ' , gpsd.fix.track
      print 'mode        ' , gpsd.fix.mode
      print
      # print 'sats        ' , gpsd.satellites

      time.sleep(5) #set to whatever

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    gpsp.running = False
    sonarth.running = False
    gpsp.join() # wait for the thread to finish what it's doing
    sonarth.join()
    GPIO.cleanup()
  print "Done.\nExiting."

 
