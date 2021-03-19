import requests
import datetime
import ConfigParser
import time
import os
import sys

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

def rainfall(config, offset):
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
    w = response1.json()     
    if "hourly" in w:
        r = w['hourly']
        rain_total = 0
        for i in r:
            for j in i:
                if j == 'rain':
                    h = i['rain']
                    rain = h['1h']
                    rain_total += rain
    else:
        r = "No hourly report yet."
        rain_total = 0
    return rain_total

def forecast(config,a):
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
        rain_forecast = 0
        for i in r[:a]:
            for j in i:
                if j == 'rain':
                    h = i['rain']
                    rain = h['1h']
                    rain_forecast += rain
    else:
        rain_forecast = 0
    return rain_forecast

def main():
    #init config file
    config = load_config()
    #selecting what kind of weather data you want
    while True:
        ans = raw_input('Do you want historical (H), forecast (F), or both (B)? ')
        print(ans)
        
        if str(ans) == 'H':
            #enter number of days back you want to see the weather data for.
            days = input('How many days back do you want to go? ')
            offset = days * 86400
            date = datetime.datetime.fromtimestamp(time.time()-offset).strftime('%Y-%m-%d')
            rf = rainfall(config,offset)
            print('Rainfall total for ' + str(date) + ': ' + str(rf) + ' mm.')
            break
        if str(ans) == 'F':
            #how far into the future do you want your forecast?
            hours = input('How many hours ahead do you want to look? ')
            frf = forecast(config,hours)
            print('Forecast rainfall for next ' + str(hours) + ' hour(s): ' + str(frf) + ' mm.')
            break
        if str(ans) == 'B':
            print('Starting with historical rainfall.')
            #enter number of days back you want to see the weather data for.
            days = input('How many days back do you want to go? ')
            offset = days * 86400
            date = datetime.datetime.fromtimestamp(time.time()-offset).strftime('%Y-%m-%d')
            rf = rainfall(config,offset)
            print('Now for the forecast rainfall.')
            #how far into the future do you want your forecast?
            hours = input('How many hours ahead do you want to look? ')
            frf = forecast(config,hours)
            print('Rainfall total for ' + str(date) + ' hour(s): ' + str(rf) + ' mm.')
            print('Forecast rainfall for next ' + str(hours) + ' hours: ' + str(frf) + ' mm.')
            break
        else:
            print('Invalid input, please enter either an H, F, or B.')
            
main()
    








