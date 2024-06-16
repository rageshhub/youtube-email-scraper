import time
import re
from seleniumbase import SB
from twocaptcha import TwoCaptcha
import logging
import sys
import csv
import json
from pathlib import Path
from pathvalidate import sanitize_filename
from seleniumbase.common.exceptions import ElementNotVisibleException
# Configure global logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level to info
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create file handler and set level to info
file_handler = logging.FileHandler('scraper.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Add formatter to handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

class GoogleEmailScraper:
    def __init__(self, email: str, password: str, captcha_api_key: str, csv_file: str) -> None:
        """
        Initialize the GoogleEmailScraper with email, password, and CSV file path.

        Args:
            email (str): Email address for Google login.
            password (str): Password for Google login.
            csv_file (str): Path to the CSV file containing 'channel_url' and 'email_id'.
        """
        self.email = email
        self.password = password
        self.csv_file = csv_file
        self.captcha_api_key = captcha_api_key
        self.urls_to_scrape = self.load_urls_from_csv()
        self.output_file = 'extracted_emails.csv'  # Output file for saving extracted emails
        logger.info(f"Initialized scraper with CSV file: {self.csv_file}")

    def load_urls_from_csv(self) -> list[dict]:
        """
        Load channel URLs and email IDs from the CSV file.

        Returns:
            List[dict]: List of dictionaries containing 'channel_url' and 'email_id'.
        """
        urls = []
        with open(self.csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                urls.append({
                    'channel_url': row['channel_url'],
                    'email_id': row['email_id']
                })
        return urls

    def login_to_google(self, sb: SB) -> None:
        """
        Log in to a Google account using SeleniumBase.

        Args:
            sb (SB): SeleniumBase browser instance.
        """
        logger.info("Logging in to Google account...")
        sb.open("https://accounts.google.com/")
        current_url = sb.get_current_url()
        if "myaccount" in current_url:
            logger.info("Already logged in to Google.")
            return
        sb.type("//input[@name='identifier']", self.email)
        sb.click("//div[@id='identifierNext']")
        time.sleep(5)
        sb.type('input[type="password"]', self.password)
        sb.click('button:contains("Next")')
        time.sleep(5)
        logger.info("Successfully logged in to Google.")

    def navigate_to_url(self, sb: SB, url: str) -> None:
        """
        Navigate to the specified URL using SeleniumBase.

        Args:
            sb (SB): SeleniumBase browser instance.
            url (str): URL to navigate to.
        """
        logger.info(f"Navigating to URL: {url}")
        sb.open(url)
        time.sleep(5)
        sb.click('#channel-tagline')
        logger.info(f"Navigated to specified URL: {url}")

    def extract_email_content(self, sb: SB) -> list[str]:
        """
        Extract email content from the current page.

        Args:
            sb (SB): SeleniumBase browser instance.

        Returns:
            List[str]: List of unique email addresses found on the page.
        """
        logger.info("Extracting email content...")
        description = sb.get_page_source()
        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', description)
        logger.info(f"Extracted {len(emails)} emails from the page.")
        return list(set(emails))

    def solve_captcha(self, sb: SB) -> bool:
        """
        Solve the CAPTCHA on the page using 2Captcha service.

        Args:
            sb (SB): SeleniumBase browser instance.
        """
        try:
            sb.click("#view-email-button-container")
        except ElementNotVisibleException:
            logger.warning("Emails button not visible. Skipping...")
            return False
        
        logger.info("Attempting to solve Captcha...")
        site_key = sb.get_attribute("#recaptcha", "data-sitekey")
        current_url = sb.get_current_url()
        solver = TwoCaptcha(self.captcha_api_key)
        response = solver.recaptcha(sitekey=site_key, url=current_url)
        code = response['code']
        logger.info(f"Successfully solved the Captcha. Solve code: {code}")
        sb.execute_script(
            f'document.getElementById("g-recaptcha-response").value="{code}";')
        time.sleep(1)
        sb.click("#submit-btn > span")
        time.sleep(1)
        logger.info("Captcha solved and submitted successfully.")
        return True
    def save_emails_to_csv(self, url: str, email: str) -> None:
        """
        Save extracted emails to the original CSV file, updating 'email_id' column.

        Args:
            url (str): URL from which emails were extracted.
            emails (List[str]): List of extracted email addresses.
        """
        updated_rows = []
        with open(self.csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['channel_url'] == url:
                    row['email_id'] = email  # Join emails with delimiter if needed
                updated_rows.append(row)

        # Write updated rows back to the CSV file
        with open(self.csv_file, 'w', newline='') as csvfile:
            fieldnames = ['channel_url', 'email_id']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

    def run(self) -> None:
        """
        Run the email scraping process for each URL in self.urls_to_scrape.
        """
        logger.info("Starting email scraping process...")

        dir_name = sanitize_filename(self.email)
        with SB(uc=True, user_data_dir=f"{Path().absolute()}\\{dir_name}") as sb:
            self.login_to_google(sb)
            for url_info in self.urls_to_scrape:
                channel_url = url_info['channel_url']
                email_id = url_info['email_id']
                if not email_id:
                    self.navigate_to_url(sb, channel_url)
                    captcha_solved = self.solve_captcha(sb)
                    if not captcha_solved:
                        return
                    try:
                        email: str = sb.get_text("#email")
                    except Exception:
                        logger.error("Limit reached to read emails from the page.")
                        quit()
                    self.save_emails_to_csv(channel_url, email)  # Update CSV with extracted emails
                    logger.info(f"Extracted emails from {channel_url}: {email}")
                else:
                    logger.info(f"Skipping {channel_url} as email ID is provided: {email_id}")

        logger.info("Email scraping process completed.")

if __name__ == "__main__":
    # Load email and password from config.json
    with open("config.json", "r") as f:
        config = json.load(f)
        EMAIL = config["EMAIL"]
        PASSWORD = config["PASSWORD"]
        CAPTCHA_API_KEY = config["CAPTCHA_API_KEY"]

    # Initialize scraper and run
    scraper = GoogleEmailScraper(
        email=EMAIL,
        password=PASSWORD,
        captcha_api_key=CAPTCHA_API_KEY,
        csv_file="urls.csv"
    )
    scraper.run()
