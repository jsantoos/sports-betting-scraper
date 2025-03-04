
# Sports Betting Scraper

  

## Description

The Sports Betting Scraper is a robust Python script designed to extract live betting odds and sports data from [veri.bet](https://veri.bet/odds-picks). It continuously scrapes the website, converting data into a structured JSON format which can be easily utilized for data analysis or integration with other applications.

  

## Features

-  **Continuous Scraping:** Runs in a loop to continuously update with the latest data.

-  **Robust Error Handling:** Implements comprehensive logging and error handling to ensure reliable operation.

-  **Headless Browser Automation:** Uses Selenium with a headless Firefox browser to navigate and scrape data.

-  **Data Parsing:** Extracts and transforms complex sports betting data into a structured format.

  

## Installation

  

### Pre-requisites

- Python 3.8 or above

- Firefox browser installed on your machine

- Geckodriver (compatible with your Firefox version)

  

### Setup

1.  **Clone the repository:**

```bash

git clone https://github.com/jsantoos/sports-betting-scraper.git

cd sports-betting-scraper

```

2.  **Install required Python packages:**

```bash

pip install -r requirements.txt

```

  

3.  **Set up environment variables: Create a .env file in the root directory of the project with the following content:**

```bash

BASE_URL=https://veri.bet/odds-picks
SCRAPE_INTERVAL=15
MAX_RETRIES=3
```

  

## Usage

  

Run the script using:

```bash

python parse_veri_bet.py

```

  
  

## Data Classes

  

Item:  Represents  a  single  betting  line  entry  with  attributes  for  sports  league,  event  date,  teams,  betting  lines,  and  prices.

  

## Logging

  

Configured  to  log  various  levels  of  messages (INFO, WARNING,  ERROR) to provide insights into the operational status and to troubleshoot issues.

  

### Author

© João Santos 

  

