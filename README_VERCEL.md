# Deploying Bike Miles to Vercel

This project includes a web interface for calculating bike miles from Strava, powered by a Python backend running on Vercel.

## Prerequisites

1.  A **Strava Account**.
2.  A **Vercel Account** (Free tier is sufficient).
3.  **Strava API Application**:
    -   Go to [Strava API Settings](https://www.strava.com/settings/api).
    -   Create an application if you haven't already.
    -   Note down the `Client ID` and `Client Secret`.
    -   Set the **Authorization Callback Domain** to `localhost` (for testing) or your Vercel domain (e.g., `your-app.vercel.app`).

## Local Development

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Set environment variables (Linux/Mac):
    ```bash
    export STRAVA_CLIENT_ID="your_client_id"
    export STRAVA_CLIENT_SECRET="your_client_secret"
    export STRAVA_REDIRECT_URI="http://localhost:3000/api/callback"
    ```

3.  Run the server:
    ```bash
    python3 api/index.py
    ```

4.  Open `http://localhost:3000` in your browser.

## Deployment to Vercel

1.  Install the Vercel CLI or link your GitHub repository to Vercel.

2.  Import the project in Vercel.

3.  **Environment Variables**: In the Vercel project settings, add the following environment variables:
    -   `STRAVA_CLIENT_ID`: Your Strava Client ID.
    -   `STRAVA_CLIENT_SECRET`: Your Strava Client Secret.
    -   `STRAVA_REDIRECT_URI`: The full URL to your callback endpoint.
        -   Format: `https://<your-project-name>.vercel.app/api/callback`
        -   **Important**: You must also update your Strava API Application's "Authorization Callback Domain" to match this domain (e.g., `your-project-name.vercel.app`).

4.  Deploy!

## Troubleshooting

-   **Redirect URI Error**: Ensure the callback domain in Strava settings matches the domain in `STRAVA_REDIRECT_URI`.
-   **Token Error**: If authentication fails, check the logs in Vercel dashboard.
