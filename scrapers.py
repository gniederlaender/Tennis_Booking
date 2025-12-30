"""Web scrapers for tennis court booking portals."""

import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class BaseScraper:
    """Base class for court booking scrapers."""

    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def init_driver(self):
        """Initialize Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager(chrome_type="chromium").install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

    def scrape(self, date, start_time, end_time):
        """
        Scrape available courts for given timeframe.

        Args:
            date: datetime object
            start_time: string "HH:MM"
            end_time: string "HH:MM"

        Returns:
            list of dicts with court information
        """
        raise NotImplementedError("Subclasses must implement scrape()")


class DasSpielScraper(BaseScraper):
    """Scraper for reservierung.dasspiel.at (Tenniszentrum Arsenal)."""

    URL = "https://reservierung.dasspiel.at/"

    def scrape(self, date, start_time, end_time):
        """Scrape Das Spiel booking portal."""
        results = []

        try:
            if not self.driver:
                self.init_driver()

            print(f"Accessing {self.URL}...")
            self.driver.get(self.URL)

            # Wait for page to load
            time.sleep(3)

            # Try to find and interact with the booking interface
            # This will need to be adjusted based on the actual site structure
            print("Analyzing Das Spiel website structure...")

            # Look for common booking elements
            try:
                # Wait for any interactive elements
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Get page source for analysis
                page_source = self.driver.page_source

                # Look for date pickers, calendars, or booking forms
                date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[placeholder*='datum'], input[placeholder*='date']")

                if date_inputs:
                    print(f"Found {len(date_inputs)} date input fields")

                # Look for iframes (booking systems often use iframes)
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

                if iframes:
                    print(f"Found {len(iframes)} iframes")
                    for i, iframe in enumerate(iframes):
                        try:
                            self.driver.switch_to.frame(iframe)
                            print(f"Switched to iframe {i}")

                            # Try to find booking interface in iframe
                            time.sleep(2)
                            iframe_source = self.driver.page_source

                            # Look for availability indicators
                            available_slots = self._extract_slots_from_page(
                                iframe_source, date, start_time, end_time, "Das Spiel"
                            )
                            results.extend(available_slots)

                            self.driver.switch_to.default_content()
                        except Exception as e:
                            print(f"Error processing iframe {i}: {e}")
                            self.driver.switch_to.default_content()

                # If no iframes, analyze main page
                if not iframes or not results:
                    main_slots = self._extract_slots_from_page(
                        page_source, date, start_time, end_time, "Das Spiel"
                    )
                    results.extend(main_slots)

            except TimeoutException:
                print("Timeout waiting for page elements")

        except Exception as e:
            print(f"Error scraping Das Spiel: {e}")

        return results

    def _extract_slots_from_page(self, page_source, date, start_time, end_time, venue_name):
        """Extract available slots from page source."""
        slots = []

        # Look for common availability indicators in the HTML
        # This is a placeholder - needs to be adjusted based on actual site

        # Example: Look for time slots in the page
        import re

        # Common patterns for time slots
        time_pattern = r'(\d{1,2}):(\d{2})'
        matches = re.findall(time_pattern, page_source)

        if matches:
            print(f"Found {len(matches)} potential time slots")

        # For now, return a mock result to indicate the site was accessed
        # This will be refined once we see the actual structure
        return slots


class PostSVScraper(BaseScraper):
    """Scraper for buchen.postsv-wien.at."""

    URL = "https://buchen.postsv-wien.at/tennis.html"

    def scrape(self, date, start_time, end_time):
        """Scrape Post SV Wien booking portal."""
        results = []

        try:
            if not self.driver:
                self.init_driver()

            print(f"Accessing {self.URL}...")
            self.driver.get(self.URL)

            # Wait for page to load
            time.sleep(3)

            print("Analyzing Post SV Wien website structure...")

            try:
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Get page source
                page_source = self.driver.page_source

                # Look for booking interface elements
                date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[placeholder*='datum'], input[placeholder*='date']")

                if date_inputs:
                    print(f"Found {len(date_inputs)} date input fields")

                # Look for iframes
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

                if iframes:
                    print(f"Found {len(iframes)} iframes")
                    for i, iframe in enumerate(iframes):
                        try:
                            self.driver.switch_to.frame(iframe)
                            print(f"Switched to iframe {i}")

                            time.sleep(2)
                            iframe_source = self.driver.page_source

                            available_slots = self._extract_slots_from_page(
                                iframe_source, date, start_time, end_time, "Post SV Wien"
                            )
                            results.extend(available_slots)

                            self.driver.switch_to.default_content()
                        except Exception as e:
                            print(f"Error processing iframe {i}: {e}")
                            self.driver.switch_to.default_content()

                if not iframes or not results:
                    main_slots = self._extract_slots_from_page(
                        page_source, date, start_time, end_time, "Post SV Wien"
                    )
                    results.extend(main_slots)

            except TimeoutException:
                print("Timeout waiting for page elements")

        except Exception as e:
            print(f"Error scraping Post SV Wien: {e}")

        return results

    def _extract_slots_from_page(self, page_source, date, start_time, end_time, venue_name):
        """Extract available slots from page source."""
        slots = []

        import re

        time_pattern = r'(\d{1,2}):(\d{2})'
        matches = re.findall(time_pattern, page_source)

        if matches:
            print(f"Found {len(matches)} potential time slots")

        return slots


def scrape_all_portals(date, start_time, end_time):
    """Scrape all configured portals and return combined results."""
    all_results = []

    # Das Spiel
    print("\n" + "="*60)
    print("Scraping Das Spiel (Tenniszentrum Arsenal)...")
    print("="*60)
    dasspiel = DasSpielScraper()
    try:
        dasspiel_results = dasspiel.scrape(date, start_time, end_time)
        all_results.extend(dasspiel_results)
        print(f"Found {len(dasspiel_results)} slots from Das Spiel")
    finally:
        dasspiel.close()

    # Post SV
    print("\n" + "="*60)
    print("Scraping Post SV Wien...")
    print("="*60)
    postsv = PostSVScraper()
    try:
        postsv_results = postsv.scrape(date, start_time, end_time)
        all_results.extend(postsv_results)
        print(f"Found {len(postsv_results)} slots from Post SV Wien")
    finally:
        postsv.close()

    return all_results
