import os
import time
from dotenv import load_dotenv
import gspread
from tqdm import tqdm
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Import the batch analysis function
from risk_assessment.analyze_clauses import analyze_all_batches


def get_worksheet():
    """
    Connect to Google Sheets only when this function is called.
    """
    google_auth_file = "services.json"

    google_sheet_scope = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    gsheet_id = os.getenv("GSHEET_ID")
    sheet_name = "Sheet1"

    if not os.path.exists(google_auth_file):
        raise FileNotFoundError(
            "services.json is missing. Google Sheets upload is not configured."
        )

    if not gsheet_id:
        raise ValueError(
            "GSHEET_ID is missing from the .env file."
        )

    creds = Credentials.from_service_account_file(
        google_auth_file,
        scopes=google_sheet_scope
    )

    gs_client = gspread.authorize(creds)

    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            worksheet = (
                gs_client
                .open_by_key(gsheet_id)
                .worksheet(sheet_name)
            )
            return worksheet

        except gspread.exceptions.WorksheetNotFound:
            worksheet = (
                gs_client
                .open_by_key(gsheet_id)
                .add_worksheet(
                    title=sheet_name,
                    rows="100",
                    cols="20"
                )
            )
            return worksheet

        except gspread.exceptions.APIError as e:
            print(f"Attempt {attempt + 1} failed with APIError: {e}")

            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise e


def ingest_to_sheet(clauses, batch_size=6, max_workers=3):
    """
    Analyze clauses in batches and upload results to Google Sheets.
    """

    # Connect only when Google Sheets upload is requested
    worksheet = get_worksheet()

    rows = [
        [
            "Clause ID",
            "Contract Clause",
            "Regulation",
            "Risk Level",
            "Risk Score",
            "Clause Identification",
            "Clause Feedback & Fix",
            "AI-Modified Clause",
            "AI-Modified Risk Level"
        ]
    ]

    for i in tqdm(
        range(0, len(clauses), batch_size),
        desc="Processing Batches"
    ):
        batch = clauses[i:i + batch_size]

        results = analyze_all_batches(
            batch,
            start_id=i + 1,
            max_workers=max_workers
        )

        for res in results:
            rows.append([
                res.get("Clause ID"),
                res.get("Contract Clause"),
                res.get("Regulation"),
                res.get("Risk Level"),
                res.get("Risk Score", "0%"),
                res.get("Clause Identification"),
                res.get(
                    "Clause Feedback & Fix",
                    "No feedback or recommendation available."
                ),
                res.get(
                    "AI-Modified Clause",
                    "No AI-modified clause available."
                ),
                res.get("AI-Modified Risk Level", "Unknown")
            ])

    worksheet.clear()
    worksheet.update(
        values=rows,
        range_name="A1"
    )