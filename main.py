import gspread
from google.oauth2.service_account import Credentials
import cohere
from dotenv import load_dotenv
import os
import time
from googleapiclient.discovery import build 

# Load environment variables (Cohere API Key)
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Connect to Cohere API
co = cohere.Client(COHERE_API_KEY)

# Google Sheets credentials and connect
SERVICE_ACCOUNT_FILE = "C:\\Users\\baliq\\Desktop\\Review_Analysis\\creds.json"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open your Google Sheet
spreadsheet = client.open("Redmi6 data")
sheet = spreadsheet.worksheet("Redmi6")

# Read reviews and existing sentiments
reviews = sheet.col_values(2)  # Assuming Review is column B
existing_sentiments = sheet.col_values(4)  # Assuming Sentiment is column D
headers = reviews[0]
reviews = reviews[1:]  # skip header
existing_sentiments = existing_sentiments[1:]  # skip header

# Prepare data to write back
update_data = []
failed_reviews = []

for idx, review in enumerate(reviews, start=2):
    if review.strip() == "":
        continue

    # Check if sentiment already exists — skip if it does
    if idx-2 < len(existing_sentiments) and existing_sentiments[idx-2].strip() != "":
        print(f"Skipped review {idx-1}: Sentiment already exists.")
        continue

    try:
        # Sentiment analysis via prompt engineering
        sentiment_prompt = f"What is the sentiment of this review? Reply with Positive, Negative, or Neutral.\nReview: \"{review}\""
        sentiment_response = co.generate(
            model='command',
            prompt=sentiment_prompt,
            max_tokens=5,
            temperature=0.3,
            stop_sequences=["--"]
        )
        sentiment = sentiment_response.generations[0].text.strip()

        # Summary via prompt engineering
        summary_prompt = f"Summarize this review in one sentence: {review}"
        summary_response = co.generate(
            model='command',
            prompt=summary_prompt,
            max_tokens=50,
            temperature=0.5,
            stop_sequences=["--"]
        )
        summary = summary_response.generations[0].text.strip()

        # Determine if action is needed based on sentiment
        action = "Yes" if sentiment.lower() == "negative" else "No"

        # Prepare data for batch update
        update_data.append({'range': f'D{idx}', 'values': [[sentiment]]})
        update_data.append({'range': f'E{idx}', 'values': [[summary]]})
        update_data.append({'range': f'F{idx}', 'values': [[action]]})

        print(f"Processed review {idx-1}: Sentiment: {sentiment}, Summary: {summary}")

        time.sleep(1.6)  # To respect API rate limit

    except Exception as e:
        print(f"⚠️ Error processing review {idx-1}: {e}")
        failed_reviews.append((idx, str(e)))

# Perform batch update to write all data at once
if update_data:
    sheet.batch_update(update_data)

# Report failed reviews
if failed_reviews:
    print("\n Some reviews failed:")
    for fail in failed_reviews:
        print(f"Row {fail[0]}: {fail[1]}")

print("Done processing and updating reviews.")


# Build the Sheets API service
service = build('sheets', 'v4', credentials=creds)

# Create Sentiment Distribution Summary
sentiments = [row[3] for row in sheet.get_all_values()[1:] if len(row) > 3]
positive_count = sentiments.count("Positive")
negative_count = sentiments.count("Negative")
neutral_count = sentiments.count("Neutral")
total_count = len(sentiments)

summary_range = [
    ["Sentiment", "Count"],
    ["Positive", positive_count],
    ["Negative", negative_count],
    ["Neutral", neutral_count],
    ["Total", total_count]
]

# Update summary table in H1:I5
sheet.update(range_name='H1:I5', values=summary_range)

#  Create a pie chart via Google Sheets API
spreadsheet_id = spreadsheet.id
service = build('sheets', 'v4', credentials=creds)
requests = [
    {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Sentiment Distribution",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "threeDimensional": True,
                        "domain": {
                            "sourceRange": {
                                "sources": [
                                    {
                                        "sheetId": sheet.id,
                                        "startRowIndex": 1,
                                        "endRowIndex": 4,
                                        "startColumnIndex": 7,
                                        "endColumnIndex": 8
                                    }
                                ]
                            }
                        },
                        "series": {
                            "sourceRange": {
                                "sources": [
                                    {
                                        "sheetId": sheet.id,
                                        "startRowIndex": 1,
                                        "endRowIndex": 4,
                                        "startColumnIndex": 8,
                                        "endColumnIndex": 9
                                    }
                                ]
                            }
                        }
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet.id,
                            "rowIndex": 7,
                            "columnIndex": 7
                        },
                        "offsetXPixels": 20,
                        "offsetYPixels": 20
                    }
                }
            }
        }
    }
]

# Apply the chart request
service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": requests}
).execute()

print("📊 Sentiment distribution pie chart added to the sheet.")

#  Report failed reviews if any
if failed_reviews:
    print(" Some reviews failed:")
    for row, error in failed_reviews:
        print(f"Row {row}: {error}")
else:
    print(" All reviews processed successfully.")
