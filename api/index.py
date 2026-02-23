from flask import Flask, request, redirect, jsonify, send_from_directory
import os
import sys
import requests

# Add the parent directory to sys.path to import bike_miles
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bike_miles import get_bike_miles

# Set static folder to '../public' so send_from_directory works easily
app = Flask(__name__, static_folder='../public')

# Environment variables
STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
# STRAVA_REDIRECT_URI should be the full URL to /api/callback
# e.g. https://your-app.vercel.app/api/callback
STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI")

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login')
def login():
    if not STRAVA_CLIENT_ID or not STRAVA_REDIRECT_URI:
        return jsonify({"error": "Missing STRAVA_CLIENT_ID or STRAVA_REDIRECT_URI environment variables"}), 500

    # Strava scopes: activity:read_all is generally needed to see all activities including private ones
    # profile:read_all is needed to see detailed profile info (like bikes) if privacy is restricted
    scope = "activity:read_all,profile:read_all"

    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={STRAVA_CLIENT_ID}&"
        f"redirect_uri={STRAVA_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"approval_prompt=auto"
    )
    return redirect(auth_url)

@app.route('/api/callback')
def callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return jsonify({"error": error}), 400

    if not code:
        return jsonify({"error": "No code provided"}), 400

    if not STRAVA_CLIENT_SECRET:
         return jsonify({"error": "Missing STRAVA_CLIENT_SECRET"}), 500

    # Exchange code for token
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    try:
        res = requests.post(token_url, data=payload)
        res.raise_for_status()
        data = res.json()
        access_token = data.get("access_token")

        # Redirect back to the frontend root with the token in the query params or fragment
        # Using query param for simplicity in static hosting context
        return redirect(f"/?access_token={access_token}")

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to exchange token", "details": str(e)}), 500

@app.route('/api/miles')
def miles():
    token = request.args.get('token')
    year = request.args.get('year')

    if not token or not year:
        return jsonify({"error": "Missing token or year parameter"}), 400

    try:
        year_int = int(year)
        # Call the refactored function
        # Note: get_bike_miles might raise errors for invalid token
        results = get_bike_miles(token, year_int, verbose=False)
        return jsonify({"year": year_int, "miles": results})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An error occurred fetching miles", "details": str(e)}), 500

# Vercel requires the app object to be exposed, usually as `app` or `handler`
# For local testing:
if __name__ == '__main__':
    app.run(port=3000, debug=True)
