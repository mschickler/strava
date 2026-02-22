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

def get_bike_miles(access_token, year, verbose=False):
  """
  Fetches activities from Strava for the given year and calculates mileage per bike.
  Returns a list of dictionaries containing bike details and mileage.
  """
  pattern = "%d.%m.%Y"
  date_time = f"01.01.{year}"
  start_epoch = int(time.mktime(time.strptime(date_time, pattern)))
  date_time = f"01.01.{year+1}"
  end_epoch = int(time.mktime(time.strptime(date_time, pattern)))

  # Query the athlete data to grab the bike IDs and names
  if verbose:
    print("\nRetrieving athlete information...\n")

  try:
    result = requests.get(
      f"{STRAVA_API_BASE}/athlete",
      headers = {
        "Authorization" : "Bearer " + access_token
      },
      timeout=10
    )
    athlete = result.json()
  except requests.exceptions.RequestException as e:
    if verbose:
      print(f"Error connecting to Strava: {e}")
    raise

  # For this first query, check to make sure we are authorized
  if "message" in athlete:
    if athlete["message"] == "Authorization Error":
      if verbose:
        print("\nAccess token is invalid.\n")
        print_token_help()
        print("")
      raise ValueError("Invalid access token")

  # Query the activities.  There is a limit to the number of activities
  # that will be returned at one time, so keep querying until we've
  # received all of the pages.
  page = 1
  all_activities = []
  while True:
    if verbose:
      print(f"Retrieving page {page} of activities...")

    try:
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
    except requests.exceptions.RequestException as e:
       if verbose:
         print(f"Error fetching activities: {e}")
       raise

    if isinstance(activities, list) and len(activities) > 0:
      all_activities += activities
    else:
      # If it's not a list (e.g. error dict) or empty, stop
      if isinstance(activities, dict) and "message" in activities:
         if verbose:
             print(f"Error from API: {activities}")
      break
    page += 1

  if verbose:
    print(f"\nRetrieved {len(all_activities)} total activities.")

  # Build a lookup table that maps bike IDs to bike names
  bike_name = {}
  # Handle case where 'bikes' might not be in athlete if scope is limited,
  # though usually it is for 'read' scope.
  if "bikes" in athlete:
      for bike in athlete["bikes"]:
        bike_name[bike["id"]] = bike["name"]

  # Count the number of miles traveled on each bike
  bike_distance = {}
  for activity in all_activities:
    # Some activities might not have gear_id
    bike_id = activity.get("gear_id")
    if not bike_id:
        continue

    distance = activity.get("distance", 0)
    if bike_id in bike_distance:
      bike_distance[bike_id] += distance
    else:
      bike_distance[bike_id] = distance

  # Prepare results
  results = []
  for bike_id in bike_distance.keys():
    miles = round(bike_distance[bike_id] / 1609.344, 1)
    name = bike_name.get(bike_id, "Unknown")
    results.append({
        "id": bike_id,
        "name": name,
        "miles": miles
    })

  return results

def main():
  # Check arguments
  if len(sys.argv) < 3:
    print("\nYou must specify the year and a valid access token.\n")
    print_token_help()
    print(f"\nUsage: {sys.argv[0]} <access-token> <year>\n")
    exit()

  access_token = sys.argv[1]

  try:
    year = int(sys.argv[2])
  except ValueError:
    print("Year must be an integer.")
    exit(1)

  try:
    results = get_bike_miles(access_token, year, verbose=True)
  except ValueError as e:
    # Auth error handled in get_bike_miles verbose output usually, but if raised:
    if str(e) == "Invalid access token":
       exit(1)
    else:
       print(f"Error: {e}")
       exit(1)
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

  # Calculate longest bike name for justification
  longest_bike_name = 0
  for bike in results:
      if len(bike["name"]) > longest_bike_name:
          longest_bike_name = len(bike["name"])

  # Print the miles for each bike
  print(f"\nMileage for {year}\n")
  for bike in results:
    justified_bike_name = bike["name"].ljust(longest_bike_name)
    print(f"{justified_bike_name} : {bike['miles']}")
  print("")

if __name__ == "__main__":
  main()
