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

#import OpenCV
import cv2
# import cv2.cv as cv
# from common import clock, draw_str
 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 24
GPIO_ECHO = 23
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

gpsd = None #seting the global variable
distance = 0 # global distance variable

os.system('clear') #clear the terminal (optional)

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

class SonarDistance(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global distance #bring it in scope
    distance = 0
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    global distance
    while sonar1.running:
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
      distance = round((TimeElapsed * 34030) / 2)
      time.sleep(1)
    GPIO.cleanup()

def get_image(ramp_frames):
    # read is the easiest way to get a full image out of a VideoCapture object.
    # Ramp the camera - these frames will be discarded and are only used to allow v4l2
    # to adjust light levels, if necessary
    for i in xrange(ramp_frames):
       temp = camera.read()
    retval, im = camera.read()
    return im
 
def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30), flags = cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:,2:] += rects[:,:2]
    return rects

def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  sonar1 = SonarDistance() # create sonar thread
 
  try:
    gpsp.start() # start it up
    sonar1.start() # start sonar
    while gpsd.fix.latitude == 0:
       time.sleep(3)
  
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
    
    old_distance = 0

    camera = cv2.VideoCapture(0)
    
    counter = 0
    old_lat = round(gpsd.fix.latitude, 4)
    old_long = round(gpsd.fix.longitude, 4)
    face_cascade = cv2.CascadeClassifier('/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml')

    while True:
      # os.system('clear')
      curr_lat = round(gpsd.fix.latitude, 4)
      curr_long = round(gpsd.fix.longitude, 4)
      if (old_distance-10 > distance) or (old_distance+10 < distance):
        image = get_image(5)
        cv2.imwrite('opencv'+str(counter)+'.png', image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        cv2.imwrite('opencv'+str(counter)+'GRAY.png', gray)
#        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        rects = detect(gray, face_cascade)
        if (rects != []):
          vis = image.copy()
          draw_rects(vis, rects, (0, 255, 0))
#        for (x,y,w,h) in faces:
#            image = cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),2)
#            roi_gray = gray[y:y+h, x:x+w]
#            roi_color = image[y:y+h, x:x+w]
          cv2.imwrite('opencv'+str(counter)+'FACE.png', vis)
        counter = counter + 1
        old_distance = distance
        old_lat = round(gpsd.fix.latitude, 4)
        old_long = round(gpsd.fix.longitude, 4)
        print 'Measured Distance = ', distance, ' cm'
        print
        print ' GPS reading'
        print '----------------------------------------'
        print 'latitude    ' , curr_lat
        print 'longitude   ' , curr_long
        print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
        print 'altitude (m)' , gpsd.fix.altitude
        print 'eps         ' , gpsd.fix.eps
        print 'epx         ' , gpsd.fix.epx
        print 'epv         ' , gpsd.fix.epv
        print 'ept         ' , gpsd.fix.ept
        print 'speed (m/s) ' , round(gpsd.fix.speed)
        print 'climb       ' , gpsd.fix.climb
        print 'track       ' , gpsd.fix.track
        print 'mode        ' , gpsd.fix.mode
        print
        # print 'sats        ' , gpsd.satellites
      else:
        print "Measured Distance is same"

      time.sleep(2) #set to whatever

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    del(camera)
    gpsp.running = False
    sonar1.running = False
    gpsp.join() # wait for the thread to finish what it's doing
  print "Done.\nExiting."

 
