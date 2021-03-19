# -*- coding: utf-8 -*-
"""
Created on Thu May 21 22:25:36 2020

@author: Shane Melton
"""

import os
import sys
import requests
import ConfigParser
import datetime
import time
from time import sleep
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Loads configuration file
def load_config(filename='config'):
  config = ConfigParser.RawConfigParser()
  this_dir = os.path.abspath(os.path.dirname(__file__))
  config.read(this_dir + '/' + filename)
  if config.has_section('SprinklerConfig'):
      return {name:val for (name, val) in config.items('SprinklerConfig')}
  else:
      print ('Unable to read file %s with section SprinklerConfig' % filename)
      print ('Make sure a file named config lies in the directory %s' % this_dir)
      raise Exception('Unable to find config file')

#Method to find the rainfall based on local time and an offset.
#the offset is in place to check the rainfall yesterday or up to
#5 days previously. The API is from OpenWeatherMap.org

def rainfall(config, offset,a,b):
    api_key = config['api_key']
    #base URL for API
    base_url = "http://api.openweathermap.org/data/2.5/onecall/timemachine?"
    #lattitude
    lat = config['lat']
    #logitude
    lon = config['lon']
    #date and time in unix
    dt = str(int(time.time()-offset))
    #complet URL
    complete_url = base_url + "lat=" + lat + "&lon=" + lon + "&dt=" + dt + "&appid=" + api_key
    response1 = requests.get(complete_url)
    #This part of the code takes the data from openweatherapp and parses out the rainfall info
    w = response1.json()     
    if "hourly" in w:
        r = w['hourly']
        rain_total = 0
        for i in r[a:b]:
            for j in i:
                if j == 'rain':
                    h = i['rain']
                    rain = h['1h']
                    rain_total += rain
    else:
        r = "No hourly report yet."
        rain_total = 0
    return rain_total, r

def forecast(config):
    #This part of the code deals with the forecast part of the openweatherapp data
    api_key = config['api_key']
    #base URL for API
    base_url = "http://api.openweathermap.org/data/2.5/onecall?"
    #lattitude
    lat = config['lat']
    #logitude
    lon = config['lon']
    #complet URL
    complete_url = base_url + "lat=" + lat + "&lon=" + lon + "&exclude=minutely,daily" + "&appid=" + api_key
    response1 = requests.get(complete_url) 
    w = response1.json()     
    if "hourly" in w:
        r = w['hourly']
        rain_forecast_12h = 0
        for i in r[:12]:
            for j in i:
                if j == 'rain':
                    h = i['rain']
                    rain = h['1h']
                    rain_forecast_12h += rain
    else:
        rain_forecast_12h = 0
    return rain_forecast_12h

# Returns current time in format yyyy-mm-dd HH:MM:SS
def now():
  return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Runs sprinkler
def run_sprinkler(config):
  pin = int(config['gpio_starter'])
  led = int(config['gpio_led1'])
  runtime = float(config['runtime_min'])
  with open(config['log_file'],'a') as log_file:
    try:
      GPIO.setup((pin, led), GPIO.OUT)
      log_file.write('Starting sprinkler ' + str(datetime.datetime.now()) + '\n')
      GPIO.output((pin,led), GPIO.HIGH)
      sleep(runtime * 60) 
      log_file.write('Stopping sprinkler ' + str(datetime.datetime.now()) + '\n')
      GPIO.output((pin,led), GPIO.LOW)
    except Exception as ex:
      log_file.write('An error has occurred:\n' + str((datetime.datetime.now(), ex.message)))  
      GPIO.output((pin,led), GPIO.LOW)

# Main method
#   1.  Reads config file
#   2.  Checks past 24 hours of rainfall and forecasted 12 hours rainfall
#   3.  Runs sprinkler if rainfall falls below threshold
def main(): 
  # Load configuration file  
  config = load_config()
  time = datetime.datetime.now()
    
  with open(config['log_file'],'a') as log_file:
    # Get past 12 hour precip and forcasted 12 hour precip
    # The time.hour == # is the time you want it to check the weather
    if time.hour == 6:
        rainfall_t = rainfall(config,0,1,11)[0] + rainfall(config,43200,22,24)[0]
        forecast_t = forecast(config)
    if time.hour == 18:
        rainfall_t = rainfall(config,0,11,22)[0]
        forecast_t = forecast(config)
    else:
        rainfall_t = 0
    if rainfall_t is None:
      log_file.write('%s: Error getting rainfall amount, setting to 0.0 mm\n ' + now())
      rainfall_t = 0.0
    else:
      log_file.write('%s: Previous 12h Rainfall: %f mm\n' % (now(), rainfall_t))
      log_file.write('%s: Forecast 12h Rainfall: %f mm\n' % (now(), forecast_t))
    
  # If this is less than RAIN_THRESHOLD_IN run sprinkler
  if rainfall_t <= float(config['rain_threshold_mm']) and forecast_t <= float(config['forecast_threshold_mm']):
    run_sprinkler(config)

# Test API access
def test_api():
  config = load_config()
  rainfall_t, r = rainfall(config,0)
  if rainfall_t is None:
    print ("Unable to access API")
    print ("Request info: ")
    print (r.text)
    return
  
  total = rainfall(load_config(),0,1,15)[0] + rainfall(load_config(),86400,14,24)[0]
  forecast_ = forecast(config)
  if total is None:
    print ("API works but unable to get history.  Did you sign up for the right plan?")
    return
  print ("API seems to be working with past 24 hour rainfall = " + str(total) + " mm")
  print ("Forecast 24h rainfall = " + str(forecast_))
    
# Runs without checking rainfall
def force_run():
  config = load_config()
  run_sprinkler(config)
  
# Sets all GPIO pins to GPIO.LOW.  Should be run when the 
# raspberry pi starts.
def init():
    config = load_config()
    pin = int(config['gpio_starter'])
    led = int(config['gpio_led1'])
    GPIO.setup((pin, led), GPIO.OUT)
    GPIO.output((pin,led), GPIO.LOW)      
    
if __name__ == "__main__":
  if len(sys.argv) == 1:
    # Standard mode
    main()
  elif len(sys.argv) == 2 and sys.argv[1] == 'test':
    # Tests connection to API
    # Make sure you run as root or this won't work
    test_api()
  elif len(sys.argv) == 2 and sys.argv[1] == 'force':
    # Runs sprinkler regardless of rainfall
    force_run()
  elif len(sys.argv) == 2 and sys.argv[1] == 'init':
    # Sets pin and led GPIOs to GPIO.LOW
    init()
  else:
    print ("Unknown inputs", sys.argv)
        
        
    
    
    
    
