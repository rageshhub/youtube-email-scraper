### Youtube Email Scraper

---

## Script Setup
**Email and Password Configuration:**

   - Create a file named `config.json` in the same directory as this script.
   - Inside `config.json`, add your Google account credentials:
     ```json
     {
         "EMAIL": "your_google_email@gmail.com",
         "PASSWORD": "your_google_password"
     }
     ```


**Install Dependencies:**
   - Before running the script for the first time, install required Python dependencies:
     ```
     pip install -r requirements.txt
     ```


**Prepare URLs CSV:**
   - Ensure your CSV file (`urls.csv`) is formatted correctly:
     - The CSV should contain headers: `channel_url` and `email_id`.
     - Each row should represent a channel URL and may optionally include an initial email ID.


**Script Overview:**
   - The script automates the extraction of email addresses from specified web pages (channel URLs).
   - It utilizes SeleniumBase for browser automation, logging, and CSV handling for input and output.

---
## Usage
**Execution:**

- Ensure `config.json` with valid Google credentials, `urls.csv` with correct formatting, and all dependencies are installed (`pip install -r requirements.txt`).
- Run the script (`python youtube_email_scraper.py`) to initiate the scraping process.

