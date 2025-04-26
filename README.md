Team 5 Redmi 6 Review Analysis Automation
Overview
This Python script automates the analysis of user reviews for the Redmi 6 smartphone, stored in a Google Sheet. It uses the Cohere AI API for sentiment analysis and summarization, writes results back to the sheet, and generates a pie chart to visualize sentiment distribution.
Purpose

Read reviews from the "Redmi6" sheet in a Google Spreadsheet.
Analyze each review using Cohere AI to determine sentiment (Positive, Negative, Neutral) and generate a one-sentence summary.
Write results to the Google Sheet in columns: "AI Sentiment", "AI Summary", and "Action Needed?" (Yes for Negative, No otherwise).
Visualize sentiment breakdown with a pie chart saved as an image.

Prerequisites

Python 3.7+
Libraries: Install required packages using:pip install gspread oauth2client cohere pandas matplotlib google-api-python-client google-auth-httplib2 google-auth-oauthlib


Google Sheets API:
Enable Google Sheets and Drive APIs in Google Cloud Console.
Download a service account JSON key (creds.json) and place it in the script directory.
Share the target Google Sheet with the service account's email.


Cohere API:
Obtain an API key from Cohere.
Replace YOUR_COHERE_API_KEY in the script with your key.



Setup

Clone or download the script (automate.py).
Place creds.json in the same directory as the script.
Update the script with your Google Sheet name and Cohere API key.
Run the script:python automate.py



Functionality

Input: Reads reviews from the "Review" column in the "Redmi6" sheet.
Processing:
Uses Cohere’s generate endpoint for sentiment analysis and summarization.
Determines if action is needed based on sentiment.


Output:
Updates the Google Sheet with sentiment, summary, and action columns.
Saves a pie chart (sentiment_pie_chart.png) showing sentiment distribution.
(Optional) Uploads the pie chart to Google Drive and inserts it into the sheet.



Notes:

Ensure the Google Sheet has a "Redmi6" sheet with a "Review" column.
Handle Cohere API rate limits by adding delays if needed.
Keep creds.json secure and exclude it from version control.


