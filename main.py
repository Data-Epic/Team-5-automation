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
co = cohere.ClientV2(COHERE_API_KEY)

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
spreadsheet = client.open("Redmi6 Data2")
sheet = spreadsheet.worksheet("Redmi6")

# Read reviews and existing sentiments 
reviews = sheet.col_values(2)  # Assuming Review is column B
existing_sentiments = sheet.col_values(4)  # Assuming Sentiment is column D

# Skip header and up to row 41 (which is index 0-40)
reviews = reviews[41:]  # start from row 42
existing_sentiments = existing_sentiments[41:]  # start from row 42

# only working on row 42-51 (10 rows)
reviews = reviews[:10]  # first 10 rows starting from row 42
existing_sentiments = existing_sentiments[:10]  # same for sentiments

# Prepare data to write back
update_data = []
failed_reviews = []


def get_summary(user_review):
    """Summarizes the review text if it's long, otherwise returns it as-is."""
    try:
        if len(user_review) > 250:
            response = co.summarize(
                length="short",
                extractiveness="low",
                additional_command="Generate a summary that is concise and focuses on keypoints of one sentence length.",
                text=user_review
            )
            return response.summary
        else:
            return user_review
    except Exception as e:
        print(f"Error in summarizing text: {e}")
        return None


def process_review(review):
    """Processes a single review to get sentiment, summary, and action needed."""
    try:
        # Sentiment analysis via fine-tuned model
        sentiment_response = co.classify(
            model='5a2495fc-208b-4bb1-9281-4ed0b5f0623e-ft',
            inputs=[review]
        )
        sentiment = sentiment_response.classifications[0].prediction.strip()

        # Summary generation
        summary = get_summary(review)

        # Determine if action is needed
        action = "Yes" if sentiment.lower() == "negative" else "No"

        return sentiment, summary, action

    except Exception as e:
        print(f"Error in processing review: {e}")
        return None, None, None


# Main loop
for idx, review in enumerate(reviews, start=42):
    if review.strip() == "":
        continue

    sentiment, summary, action = process_review(review)

    if sentiment is None:
        failed_reviews.append((idx, "Processing failed"))
        continue

    # Prepare data for batch update
    update_data.append({'range': f'D{idx}', 'values': [[sentiment]]})
    update_data.append({'range': f'E{idx}', 'values': [[summary]]})
    update_data.append({'range': f'F{idx}', 'values': [[action]]})

    print(f"Processed review {idx}: Sentiment: {sentiment}, Summary: {summary}")

    time.sleep(1.6)

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
# Get all rows from the sheet (excluding header)
all_rows = sheet.get_all_values()[1:]

# Get sentiments from rows 42–51 (index 41 to 50)
sentiments = [row[3] for row in all_rows[41:51] if len(row) > 3]

positive_count = sentiments.count("positive")
negative_count = sentiments.count("negative")
neutral_count = sentiments.count("neutral")
total_count = len(sentiments)  # Should now be 10 (or less if any empty rows)


summary_range = [
    ["Sentiment", "Count"],
    ["Positive", positive_count],
    ["Negative", negative_count],
    ["Neutral", neutral_count],
    ["Total", total_count]
]

# Update the summary table
sheet.update('H1:I5', summary_range)


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
