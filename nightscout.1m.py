#!/usr/bin/env PYTHONIOENCODING=UTF-8 python3
# -*- coding: utf-8 -*-

# <xbar.title>Nightscout - Blood Glucose Monitoring</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Ricky Grassmuck</xbar.author>
# <xbar.author.github>https://github.com/RickyGrassmuck/Nightscout-Swiftbar-Plugin</xbar.author.github>
# <xbar.desc>Display current blood glucose information gathered from Nightscout</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/nightscout/cgm-remote-monitor/master/static/images/favicon.ico</xbar.image>
# <xbar.dependencies>python,requests</xbar.dependencies>
  

import emoji
import requests
import sys
from datetime import datetime as dt
from datetime import timedelta as td
from pprint import pprint as pp

## CONFIGURATION
ns_domain = "" # Ex. https://nightscout.example.com
access_token = '' # If unsure, use an admin token
units = "mg/dL" # Script only supports mg/dL at the moment since that's what the nightscout API returns
high_threshold = 160 # BG value above which the script will display in yellow
low_threshold = 70 # BG value below which the script will display in red
debug = False
## END CONFIGURATION

ns_url = f"{ns_domain}/api/v3"

# print output to stderr for debugging
def debug_print(message):
  if debug:
    print(message, file=sys.stderr)

def get_direction_icon(direction):
  directions = {
    'Flat': ':right_arrow:',
    'FortyFiveUp': ':up-right_arrow:',
    'FortyFiveDown': ':down-right_arrow:',
    'SingleUp': ':up_arrow:',
    'SingleDown': ':down_arrow:',
    'DoubleUp': '⇈',
    'DoubleDown': '⇊'
  }
  selected = directions.get(direction, ":red_question_mark:")
  return emoji.emojize(selected, variant="text_type")
     
def api_request(path, method='GET', params={}):
  url = f"{ns_url}/{path}"
  params['token'] = access_token
  headers = {"accept": "application/json", "Last-Modified": dt.strftime(dt.utcnow() - td(minutes=5), "%a, %d %b %Y %H:%M:%S GMT")}
  res = requests.get(url, headers=headers, params=params)
  if res.status_code == 200:
    return res.json()['result'][0]
  else:
    print(f"API Error [{res.status_code}]: {res.text}")
    return None

def get_device_status(debug=False):
  result = api_request('devicestatus/history', params={"limit": 1, "fields": "_all"})
  if result is not None:
    dev_status = {}
    try:
      dev_status["pump"] = result.get('pump')
    except (IndexError, KeyError):
      debug_print(result)
    try:
      dev_status["suggested"] = result['openaps'].get('suggested')
    except (IndexError, KeyError):
      debug_print(result)
    return dev_status
  else:
    return None    

def get_entries():
  result = api_request('entries/history', params={"limit": 1, "fields": "_all"})
  if result is not None:
    return result
  else:
    return None

class Entry():
  def __init__(self, glucose, direction, carbs_on_board, insulin_on_board, basal_rate=None) -> None:
    self.glucose = glucose
    self.direction = direction
    self.carbs_on_board = carbs_on_board
    self.insulin_on_board = insulin_on_board
    if basal_rate is not None:
      self.basal_rate = round(basal_rate, 2)
  def glucose_color(self):
    if self.glucose > high_threshold:
      return "#f5e615"
    elif self.glucose < low_threshold:
      return "#f51515"
    else:
      return "#51de26"
  def render(self):
    output = f"🩸 {self.glucose} {units} {get_direction_icon(self.direction)} | color={self.glucose_color()}"
    output += "\n---\n"
    output += f"Carbs on Board: {self.carbs_on_board}g | color=white\n"
    output += f"Insulin on Board: {self.insulin_on_board} units | color=white\n"
    output += f"Basal Rate: {self.basal_rate} u/hr | color=white\n"
    return output
  
if __name__ == "__main__":
  device_status = get_device_status(debug=debug)
  entry = get_entries()

  if device_status['suggested'] is not None:
    cob = device_status['suggested'].get('COB', "??")
    iob = device_status['suggested'].get('IOB', "??")
  if device_status['pump'] is not None:
    basal_rate = device_status['pump']['extended'].get('TempBasalAbsoluteRate')
  if device_status is not None and entry is not None:
    result = Entry(
      entry['sgv'], 
      entry['direction'], 
      cob,
      iob,
      basal_rate)
    print(result.render())
