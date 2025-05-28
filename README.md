# LinkedIn Profile Scraper for Udacity Community and Local HTML Files


## Overview

The script provides the ability to:

- Dynamically scrape protected or JavaScript-heavy web pages (such as Udacity Community forums).

- Prompt the user for manual login during the dynamic scraping phase.

- Parse local HTML files for LinkedIn profile URLs.

- Collect and deduplicate all discovered LinkedIn profiles.

## Main Features

- **BeautifulSoup for static HTML:** Quickly extract LinkedIn links from provided HTML.

- **Selenium for dynamic content:** Automate Edge browser to handle pages requiring login and JavaScript rendering.

- **Manual login support:** Upon reaching a protected page, user is prompted to complete login and navigation manually, then resume automated scraping.

- **Iframe detection and handling:** Attempts to switch into community content iframe if present.

- **Customizable CSS Selectors:** Essential CSS selectors for triggers, profile links, and close buttons are clearly marked for user modification.

- **Comprehensive error handling and logging:** Extensive print statements guide troubleshooting.

## Requirements

- Python 3.7+

- `requests`

- `beautifulsoup4`

- `selenium`

- `webdriver-manager`

Install all dependencies with:

```
pip install requests beautifulsoup4 selenium webdriver-manager
```

Also ensure Microsoft Edge is installed and up-to-date, as the script uses Edge WebDriver.

## Usage

1. Place any saved forum pages as `saved_forum_page*.html` in the same folder as the script if you wish to parse local files.

2. Open a terminal and run:
```
python your_script_name.py
```

3. If dynamic scraping is enabled for a given URL (e.g., Udacity Community), Edge will launch. Follow console instructions to manually complete login if needed.

4. Once ready, press `Enter` in the console as prompted.

5. The script will process user profile entries, extracting all LinkedIn profile links it can find.

6. Results are printed and deduplicated.

## Configuration

Several variables and CSS selectors in the script should be inspected and modified based on the live site's HTML structure.

- `user_profile_trigger_selector`

- `profile_card_content_selector`

- `profile_card_close_button_selector`

**Tip:** Use your browser's developer tools (`F12`) to inspect elements and adjust these selectors as needed if scraping breaks due to UI changes.

## Limitations and Caveats

- The script requires manual intervention for login when scraping protected content.

- Selectors may need frequent updating due to ongoing UI changes on the target site(s).

- This script is for educational use. Be mindful of `robots.txt` and terms of service when scraping third-party websites.

## License

MIT License or adapt as needed.
