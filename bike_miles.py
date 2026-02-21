###############################################################################
'''
Copyright (c) 2017, Matthew Schickler (https://github.com/mschickler)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
###############################################################################

#!/usr/bin/env python3

import sys
import time
import json

try:
  import requests
except ImportError:
  print("This script requires the requests library. Please install it using:")
  print("  pip install requests")
  sys.exit(1)

STRAVA_API_BASE = "https://www.strava.com/api/v3"

def print_token_help():
  print("To learn more about acquiring an access token, go to:")
  print("  https://developers.strava.com/docs/authentication/")

def main():
  # Check arguments
  if len(sys.argv) < 3:
    print("\nYou must specify the year and a valid access token.\n")
    print_token_help()
    print(f"\nUsage: {sys.argv[0]} <access-token> <year>\n")
    exit()

  # The access token is a required argument
  access_token = sys.argv[1]

  # The year is a required argument.  Calculate the epoch starting
  # time and ending time for the specified year.
  year = int(sys.argv[2])
  pattern = "%d.%m.%Y"
  date_time = f"01.01.{year}"
  start_epoch = int(time.mktime(time.strptime(date_time, pattern)))
  date_time = f"01.01.{year+1}"
  end_epoch = int(time.mktime(time.strptime(date_time, pattern)))

  # Query the athlete data to grab the bike IDs and names
  print("\nRetrieving athlete information...\n")
  result = requests.get(
    f"{STRAVA_API_BASE}/athlete",
    headers = {
      "Authorization" : "Bearer " + access_token
    },
    timeout=10
  )
  athlete = result.json()

  # For this first query, check to make sure we are authorized
  if "message" in athlete:
    if athlete["message"] == "Authorization Error":
      print("\nAccess token is invalid.\n")
      print_token_help()
      print("")
      exit()

  # Query the activities.  There is a limit to the number of activities
  # that will be returned at one time, so keep querying until we've
  # received all of the pages.
  page = 1
  all_activities = []
  while True:
    print(f"Retrieving page {page} of activities...")
    result = requests.get(
      f"{STRAVA_API_BASE}/athlete/activities",
      params = {
        "page" : page,
        "after" : start_epoch,
        "before" : end_epoch,
        "per_page" : 200
      },
      headers = {
        "Authorization" : "Bearer " + access_token
      },
      timeout=10
    )
    activities = result.json()
    if len(activities) > 0:
      all_activities += activities
    else:
      break
    page += 1

  print(f"\nRetrieved {len(all_activities)} total activities.")

  # Build a lookup table that maps bike IDs to bike names
  longest_bike_name = 0
  bike_name = {}
  for bike in athlete["bikes"]:
    bike_name[bike["id"]] = bike["name"]
    if len(bike["name"]) > longest_bike_name:
      longest_bike_name = len(bike["name"])

  # Count the number of miles traveled on each bike
  bike_distance = {}
  for activity in all_activities:
    bike_id = activity["gear_id"]
    distance = activity["distance"]
    if bike_id in bike_distance:
      bike_distance[bike_id] += distance
    else:
      bike_distance[bike_id] = distance

  # Print the miles for each bike
  print(f"\nMileage for {year}\n")
  for bike_id in bike_distance.keys():
    bike_distance_miles = round(bike_distance[bike_id] / 1609.344,1)
    if bike_id in bike_name:
      justified_bike_name = bike_name[bike_id].ljust(longest_bike_name)
    else:
      justified_bike_name = "Unknown".ljust(longest_bike_name)
    print(f"{justified_bike_name} : {bike_distance_miles}")
  print("")

if __name__ == "__main__":
  main()
