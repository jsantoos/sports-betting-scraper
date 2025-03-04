"""
Sports Betting Scraper

This script scrapes sports betting data from veri.bet and prints it in a formatted JSON output.
It runs in a loop, continuously appending new data while ensuring robust error handling.

Author: João Pedro de Souza Santos
"""

# Standard Library Imports
import json
import re
import time
import datetime
import logging
import os
import sys
from dataclasses import dataclass
from typing import List, Optional

# Third-Party Imports
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
BASE_URL = os.getenv("BASE_URL")
SCRAPE_INTERVAL = os.getenv("SCRAPE_INTERVAL")
MAX_RETRIES = os.getenv("MAX_RETRIES")

if not BASE_URL:
    logging.error("❌ BASE_URL is not defined in .env")
    sys.exit(1)


try:
    MAX_RETRIES = int(MAX_RETRIES)
    if MAX_RETRIES < 2:
        logging.warning("⚠️ MAX_RETRIES is too low. Setting to 3 times.")
        MAX_RETRIES = 3
except (ValueError, TypeError):
    logging.error("❌ MAX_RETRIES must be a valid integer in .env")
    sys.exit(1)


try:
    SCRAPE_INTERVAL = int(SCRAPE_INTERVAL)
    if SCRAPE_INTERVAL < 5:
        logging.warning("⚠️ SCRAPE_INTERVAL is too low. Setting to 10 seconds.")
        SCRAPE_INTERVAL = 10
except (ValueError, TypeError):
    logging.error("❌ SCRAPE_INTERVAL must be a valid integer in .env")
    sys.exit(1)


@dataclass
class Item:
    """Represents a single betting line entry."""
    sport_league: str
    event_date_utc: str
    team1: str
    team2: str
    period: str
    line_type: str
    price: str
    side: str
    team: str
    spread: float = 0.0
    pitcher: str = ""


class SportsScraper:
    """A scraper class to extract sports betting data from veri.bet."""

    def __init__(self) -> None:
        """Initializes the WebDriver in headless mode, with retry logic."""
        self.driver = self.setup_driver()
        self.cached_event_date = None  # Cache the event date

    def setup_driver(self) -> Optional[webdriver.Firefox]:
        """Sets up the Selenium WebDriver to run headless, with retry logic."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        for attempt in range(MAX_RETRIES):
            try:
                driver = webdriver.Firefox(options=options)
                logging.info("✅ WebDriver initialized in headless mode.")
                return driver
            except Exception as e:
                logging.error(f"❌ Failed to initialize WebDriver (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(10)

        logging.error("❌ All WebDriver initialization attempts failed. Exiting.")
        sys.exit(1)

    @staticmethod
    def extract_spread(value_str: str) -> float:
        """Extracts the spread value from text, ensuring the format is correctly recognized."""
        try:
            match = re.search(r"([-+]?\d+(\.\d+)?)", value_str)
            return float(match.group(1)) if match else 0.0
        except (ValueError, AttributeError):
            return 0.0

    @staticmethod
    def extract_price(value_str: str) -> str:
        """Extracts the odds price from the given text."""
        match = re.search(r"\(([-+]?\d+)\)", value_str)
        return match.group(1) if match else value_str.strip()

    def get_event_date(self) -> str:
        """Retrieves the event date once and caches it for efficiency."""
        if self.cached_event_date:
            return self.cached_event_date

        try:
            date_input = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.ID, "datepicker"))
            )
            raw_date = date_input.get_attribute("value")

            if not raw_date:
                logging.warning("⚠️ Date field is empty, using the current date.")
                self.cached_event_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
                return self.cached_event_date

            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            raw_datetime = f"{raw_date} {current_time}"

            parsed_date = datetime.datetime.strptime(raw_datetime, "%m-%d-%Y %H:%M:%S")
            self.cached_event_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            return self.cached_event_date

        except TimeoutException:
            logging.warning("⚠️ Failed to retrieve event date, using current date.")
            self.cached_event_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            return self.cached_event_date

    def parse_game_data(self) -> List[Item]:
        """Parses betting lines from the page."""
        items = []
        try:
            event_date_utc = self.get_event_date()
            game_rows = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".row.justify-content-md-center .col.col-md"))
            )

            for row in game_rows:
                try:
                    team_names = row.find_elements(By.CSS_SELECTOR, "a.text-muted")
                    moneyline_prices = row.find_elements(By.CSS_SELECTOR, "td:nth-child(2) span.text-muted")
                    spread_prices = row.find_elements(By.CSS_SELECTOR, "td:nth-child(3) span.text-muted")
                    total_prices = row.find_elements(By.CSS_SELECTOR, "td:nth-child(4) span.text-muted")

                    sport_league = "UNKNOWN"
                    try:
                        sport_elem = row.find_element(By.CSS_SELECTOR, "a[href*='betting-trends?f=']")
                        sport_league = sport_elem.get_attribute("href").split("f=")[-1].upper()
                    except NoSuchElementException:
                        pass

                    period = "FULL GAME"
                    try:
                        # period_elem = row.find_element(By.CSS_SELECTOR, "span.badge.badge-light")
                        period_elem = row.find_element(By.XPATH, ".//span[contains(@class, 'badge') and contains(@class, 'badge-light')]")
                        period_elem = self.driver.find_element(By.XPATH, ".//span[contains(@class, 'badge') and contains(@class, 'badge-light') and contains(text(), 'FINAL')]")
                        print(period_elem.get_attribute("outerHTML"))
                        period = period_elem.text.strip()
                    except NoSuchElementException:
                        pass

                    if len(team_names) < 2 or len(moneyline_prices) < 2:
                        logging.warning("⚠️ Missing data in row. Skipping...")
                        continue

                    team1, team2 = team_names[0].text, team_names[1].text

                    # Moneyline bets
                    if len(moneyline_prices) >= 2:
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "moneyline",
                                        self.extract_price(moneyline_prices[1].text), team1, team1,
                                        self.extract_spread(spread_prices[1].text)))
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "moneyline",
                                        self.extract_price(moneyline_prices[2].text), team2, team2,
                                        self.extract_spread(spread_prices[2].text)))

                    # Draw bet (only for Soccer)
                    if "SOCCER" in sport_league and len(moneyline_prices) >= 4:
                        draw_price = moneyline_prices[3].text.replace("DRAW\n", "").strip()
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "moneyline",
                                          draw_price, "draw", "draw"))

                    # Spread bets
                    if len(spread_prices) >= 2:
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "spread",
                                          self.extract_price(spread_prices[1].text), team1, team1,
                                          self.extract_spread(spread_prices[1].text)))
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "spread",
                                          self.extract_price(spread_prices[2].text), team2, team2,
                                          self.extract_spread(spread_prices[2].text)))

                    # Over/Under bets
                    if len(total_prices) >= 2:
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "over/under",
                                          self.extract_price(total_prices[1].text), "over", "total",
                                          self.extract_spread(spread_prices[1].text)))
                        items.append(Item(sport_league, event_date_utc, team1, team2, period, "over/under",
                                          self.extract_price(total_prices[2].text), "under", "total",
                                          self.extract_spread(spread_prices[2].text)))



                except Exception as e:
                    logging.warning(f"⚠️ Error parsing row: {e}")
                    continue

        except TimeoutException:
            logging.warning("⚠️ Timeout while loading the page.")

        return items


def save_data_to_json(items: List[Item], filename="betting_data.json"):
    """Saves the extracted betting data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([item.__dict__ for item in items], f, indent=2, ensure_ascii=False)
    logging.info(f"📂 Data saved to {filename}")


if __name__ == "__main__":
    scraper = SportsScraper()
    try:
        while True:
            scraper.driver.get(BASE_URL)
            items = scraper.parse_game_data()

            # Save the data to a JSON file
            save_data_to_json(items) 

            print(json.dumps([item.__dict__ for item in items], indent=2, ensure_ascii=False))
            logging.info(f"✅ Successfully scraped {len(items)} betting lines.")
            time.sleep(SCRAPE_INTERVAL)
    except KeyboardInterrupt:
        logging.info("🛑 Script interrupted. Closing WebDriver...")
        scraper.driver.quit()
        sys.exit(0)