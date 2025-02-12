import asyncio
import json
import os

from crawl4ai import AsyncWebCrawler, CacheMode, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RANGE = "TWK!A1:H10000"
MATERIAL = "Campuran"
SPREADSHEET_ID = "1ZAfe0hi6gl1hdss8Qxi0L1T-_zu6TU5_Ysyk_r3wIyY"
FORMAT = "html"
SIZE = 258
URL = "https://belajarbro.id/cpns/soal/twk/"
SCHEMA = {
    "name": "Questions",
    "baseSelector": "ol.semua > li.nomor",
    "fields": [
        {
            "name": "question",
            "selector": "div",
            "type": FORMAT
        },
        {
            "name": "options",
            "selector": "ol.opsinya li",
            "type": "list",
            "fields": [
                {
                    "name": "option",
                    "type": FORMAT
                }
            ]
        },
        {
            "name": "explanation",
            "selector": "div.jawaban",
            "type": FORMAT,
        }
    ]
}

def credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def update_values(spreadsheet_id, range_name, value_input_option, _values):
    creds = credentials()
    try:
        service = build("sheets", "v4", credentials=creds)
        values = _values
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def convert_to_spreadsheet_format(data_list):
    spreadsheet_data = []  # Initialize the list

    for data in data_list:
        question = data.get("question", "")
        options = [opt.get("option", "") for opt in data.get("options", [])]

        # Ensure we always have exactly 5 options
        while len(options) < 5:
            options.append("")  # Fill missing options with empty strings

        explanation = data.get("explanation", "")
        material = data.get("material", MATERIAL)

        # Append formatted row
        spreadsheet_data.append([question] + options + [explanation] + [material])

    return spreadsheet_data

async def main():

    browser_cfg = BrowserConfig(
        headless=True,
        verbose=True,
        user_agent_mode="random",
        use_persistent_context=True,
        text_mode=True,
        light_mode=True
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        extraction_strategy=JsonCssExtractionStrategy(SCHEMA, verbose=True),
        scan_full_page=True,
        simulate_user=True,
        magic=True
    )

    urls = [URL + str(index) + "/" for index in range(1, SIZE)]
    print(f"Processing {urls}")

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=run_cfg,
            cache_mode=CacheMode.ENABLED,
            verbose=True,
        )

        for result in results:
            if result.success:
                data = json.loads(result.extracted_content)
                spreadsheet_format = convert_to_spreadsheet_format(data)

                update_values(
                    SPREADSHEET_ID,
                    RANGE,
                    "USER_ENTERED",
                    spreadsheet_format,
                )
            else:
                print(f"Crawl failed: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
