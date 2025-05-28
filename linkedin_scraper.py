import requests
from bs4 import BeautifulSoup
import os # For accessing environment variables
import glob
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService # Import EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager # Import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException # Import TimeoutException and NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


def _extract_linkedin_links_from_soup(soup_object):
    """Extracts LinkedIn profile URLs from a BeautifulSoup object."""
    found_profiles = set()
    for link_tag in soup_object.find_all('a', href=True):
        href = link_tag['href']
        if 'linkedin.com/in/' in href.lower():
            # Basic normalization: remove query parameters
            profile_url = href.split('?')[0]
            if profile_url.endswith('/'):
                profile_url = profile_url[:-1]
            found_profiles.add(profile_url)
            print(f"Found LinkedIn profile: {profile_url}")
    return found_profiles


def scrape_linkedin_profiles():
    # URLs to scrape (may fail if protected)
    urls = [
        "https://community.udacity.com/c/onetenc10-general-space/" # This one is known to be dynamic
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    linkedin_profiles = set()
    dynamic_community_url = "https://community.udacity.com/c/onetenc10-general-space/"
    
    # Scrape the web URLs
    for url in urls:
        if url == dynamic_community_url:
            print(f"\nAttempting dynamic scrape for {url} using Selenium...")
            try:
                dynamically_found_profiles = _scrape_url_dynamically_with_selenium(url, headers["User-Agent"])
                linkedin_profiles.update(dynamically_found_profiles)
            except Exception as e:
                print(f"Error during dynamic scraping of {url} ({type(e).__name__}): {e}")
        else:
            # This block is currently not reachable as only the dynamic_community_url is in the urls list.
            # Kept for potential future use if more static URLs are added.
            try:
                print(f"\nRequesting {url} (static)...")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    print(f"Successfully retrieved {url}")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    statically_found = _extract_linkedin_links_from_soup(soup)
                    linkedin_profiles.update(statically_found)
                else:
                    print(f"Failed to access {url}. Status code: {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                print(f"Error accessing {url}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {url} ({type(e).__name__}): {e}")

    # Now scrape local HTML files
    file_list = glob.glob("saved_forum_page*.html")  # Adjust pattern as needed
    print(f"\nScanning {len(file_list)} local HTML files for LinkedIn profiles...")
    
    for filename in file_list:
        try:
            print(f"Processing {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                locally_found = _extract_linkedin_links_from_soup(soup)
                linkedin_profiles.update(locally_found)
        except FileNotFoundError:
            print(f"Error: File not found {filename}")
        except Exception as e:
            print(f"Error processing file {filename} ({type(e).__name__}): {e}")

    # Print summary
    if linkedin_profiles:
        print(f"\nFound {len(linkedin_profiles)} unique LinkedIn profiles:")
        for profile in sorted(list(linkedin_profiles)): # Sort for consistent output
            print(f"- {profile}")
    else:
        print("\nNo LinkedIn profiles found on any of the pages or files.")
        print("Try visiting the Udacity website manually to find instructor LinkedIn profiles.")


def _scrape_url_dynamically_with_selenium(url, user_agent):
    """Scrapes a single URL using Selenium to handle JavaScript-loaded content."""
    found_profiles = set()

    options = webdriver.EdgeOptions()  # Use EdgeOptions
    options.add_argument(f"user-agent={user_agent}")
    # options.add_argument('--headless')  # Uncomment to run Edge in the background
    # options.add_argument('--disable-gpu') # Often recommended with headless
    options.add_argument("--log-level=3")  # Suppress console logs from WebDriver
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools listening message

    # --- Credentials for Login (fetch from environment variables) ---
    # udacity_email = os.getenv("UDACITY_EMAIL") # No longer needed for automated login
    # udacity_password = os.getenv("UDACITY_PASSWORD") # No longer needed for automated login
    logged_in = False
    login_element_to_check_staleness = None # To store the element we expect to disappear after login

    driver = None # Initialize driver to None for the finally block
    try:
        print(f"  Initializing WebDriver for {url}...")
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)  # Use Edge and EdgeChromiumDriverManager

        # Maximize window, as some sites behave differently with smaller viewports
        print("  Maximizing browser window...")
        driver.maximize_window()

        # Clear cookies for a fresh session before the first navigation
        print("  Clearing cookies for a fresh session...")
        driver.delete_all_cookies()

        print(f"\n  Opening browser to: {url}")
        driver.get(url)

        # --- Manual Login Pause ---
        print("\n" + "="*50)
        print("  MANUAL LOGIN REQUIRED")
        print("  Please log in to Udacity in the opened browser window and navigate to:")
        print(f"  {url}")
        print("  Once you are on the correct page and it has fully loaded,")
        input("  press Enter in this console window to continue scraping...")
        print("="*50 + "\n")

        print(f"  Resuming script. Current URL: {driver.current_url}")
        # Assume login was successful if the user proceeds.
        # You might want to add a check here for a known element on the target page
        # to be more certain (e.g., WebDriverWait for known_element_on_target_page_selector), but for manual mode, this is often sufficient.
        logged_in = True


        # --- Attempt to switch to iframe if one is detected ---
        # YOU MUST INSPECT THE PAGE TO FIND THE SELECTOR FOR THE IFRAME
        # This is a placeholder selector for the iframe that might contain the community content
        community_content_iframe_selector = "iframe[src*='inner.html']" # EXAMPLE - UPDATE THIS

        iframe_found = False
        try:
            print(f"  Checking for community content iframe (selector: '{community_content_iframe_selector}')...")
            iframe_element = WebDriverWait(driver, 10).until(
                 EC.presence_of_element_located((By.CSS_SELECTOR, community_content_iframe_selector))
            )
            driver.switch_to.frame(iframe_element)
            print("  Switched to community content iframe.")
            iframe_found = True
        except (TimeoutException, NoSuchElementException):
            print(f"  Community content iframe ('{community_content_iframe_selector}') not found. Assuming content is in the main document.")
        except Exception as e_iframe:
             print(f"  Error switching to iframe ({type(e_iframe).__name__}): {e_iframe}")
             # Decide whether to raise or continue assuming no iframe
             # For now, we'll continue assuming no iframe if an error occurs


        # NOTE: The user_profile_trigger_selector below was very specific (targets div:nth-child(1) and long parent chain).
        # If you want to scrape multiple profiles, or if the 1st item isn't always present/relevant,
        # you will need a more general selector.
        # Ensure this selector is correct for the content *inside* the iframe if one is used.
        # YOU MUST INSPECT THE LIVE PAGE TO FIND A RELIABLE, MORE GENERAL SELECTOR that works for ALL profile entries (with or without images).
        # Example: Target the clickable link (<a>) or a common container div.
        user_profile_trigger_selector = "div.post--list__user a" # EXAMPLE: Targets the link (<a>) within a specific div class. Adjust as needed.
        # Ensure this selector is correct for the profile card content.
        # Profile cards often appear in the main document, even if triggered from an iframe.
        # YOU MUST INSPECT THE LIVE PAGE TO FIND A RELIABLE SELECTOR FOR THE LINKEDIN LINK IN THE PROFILE CARD.
        # Example: Find a class name on the LinkedIn link or a container around it, or an aria-label.
        # Let's try a more general approach for the LinkedIn link within a modal.
        profile_card_content_selector = "div[role='dialog'] a[href*='linkedin.com/in/'], div[class*='modal'] a[href*='linkedin.com/in/']" # EXAMPLE: More general for modals. Adjust.
        
        # YOU MUST INSPECT THE LIVE PAGE TO FIND A RELIABLE, MORE FLEXIBLE CSS SELECTOR FOR THE PROFILE CARD'S CLOSE/BACK BUTTON.
        # The fallback selector was working, so let's make that the primary.
        # You should still inspect and refine this based on the actual modal structure.
        profile_card_close_button_selector = "div[role='dialog'] button[aria-label*='lose'], div[class*='modal'] button[aria-label*='lose']" # Primary, based on working fallback. Adjust.

        print(f"  Waiting for profile triggers (selector: '{user_profile_trigger_selector}')...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, user_profile_trigger_selector))
            )
        except (TimeoutException, NoSuchElementException) as e_wait_trigger: # Catch specific exceptions for clarity
            print(f"    Could not find profile triggers (selector: '{user_profile_trigger_selector}'). Page content might be different than expected or login failed.")
            # More specific error printing for TimeoutException
            error_message = e_wait_trigger.msg if isinstance(e_wait_trigger, TimeoutException) and hasattr(e_wait_trigger, 'msg') else str(e_wait_trigger)
            print(f"    Error type: {type(e_wait_trigger).__name__}, Message: {error_message}")
            # In manual mode, logged_in is True after the pause
            if logged_in:
                print("    Manual login was assumed successful, but triggers not found on the current page.")
            # The 'login_flow_initiated' and 'else' conditions are not relevant for the manual login path.
            # else: print("    Login not attempted or failed early, triggers not found.") # This was the original else
            raise

        profile_triggers = driver.find_elements(By.CSS_SELECTOR, user_profile_trigger_selector)
        print(f"  Found {len(profile_triggers)} potential profile triggers.")

        # It's often safer to iterate by index if the DOM might change,
        # but we need to be careful about the list length if elements disappear.
        # We'll re-fetch the list of triggers in each iteration to handle DOM changes.
        num_initial_triggers = len(profile_triggers)
        processed_trigger_elements = set() # Keep track of elements we've already tried to click
        MAX_TRIGGERS_TO_PROCESS = 50 # Safety limit for infinite scroll

        if num_initial_triggers == 0:
            print("  No profile triggers found to process.")

        # Loop as long as there are triggers, up to a max limit
        current_trigger_index = 0
        while current_trigger_index < MAX_TRIGGERS_TO_PROCESS:
            print(f"\n  Attempting to process trigger (current pass: {current_trigger_index + 1}).")
            # Add a small delay before re-finding, allowing DOM to settle after modal closure from previous iteration
            if current_trigger_index > 0: # No need to sleep before the first iteration
                print("    Pausing briefly for page to settle before finding next trigger...")
                time.sleep(0.75) # Slightly increased delay

            # Re-find all triggers in each iteration as the DOM might have changed
            current_triggers = driver.find_elements(By.CSS_SELECTOR, user_profile_trigger_selector)
            print(f"    Re-found {len(current_triggers)} triggers on the page using selector: '{user_profile_trigger_selector}'")

            # Find the next unprocessed trigger
            trigger_to_process = None
            for t in current_triggers:
                if t not in processed_trigger_elements:
                    trigger_to_process = t
                    break
            
            if not trigger_to_process:
                print("    No new, unprocessed triggers found. Assuming all available triggers processed.")
                break

            trigger = trigger_to_process
            processed_trigger_elements.add(trigger) # Mark as processed (or attempted)

            try:
                print(f"    Processing trigger (element: {trigger.tag_name}, location: {trigger.location}).")

                # Scroll to the trigger
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                # Wait for the element to be clickable after scrolling
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(trigger))
                # Small pause can sometimes still be beneficial after ensuring clickability if animations are involved
                # time.sleep(0.2) # Optional: very short pause if needed
                trigger.click() # Click happens in the current context (main doc or iframe)

                # If the trigger was clicked within an iframe, and the profile card
                # (modal) appears in the main document, switch back to default content.
                # This 'iframe_found' refers to whether an iframe was detected and switched into earlier.
                if iframe_found:  # If an iframe was active for finding triggers
                    print("    Trigger was in iframe. Switching to default content to find profile card.")
                    driver.switch_to.default_content()

                # Now, in the default content (or if we were already there), look for the LinkedIn link.
                # The profile_card_content_selector should ideally be specific to the <a> tag of the LinkedIn link.
                try:
                    print(f"    Waiting for LinkedIn link in profile card (selector: '{profile_card_content_selector}')...")
                    linkedin_link_webelement = WebDriverWait(driver, 3).until( # Reduced timeout to 3 seconds
                        EC.visibility_of_element_located((By.CSS_SELECTOR, profile_card_content_selector))
                    )
                    # Attempt to get the href directly from the found element
                    href = linkedin_link_webelement.get_attribute('href')
                    if href and 'linkedin.com/in/' in href.lower():
                        # Basic normalization
                        profile_url = href.split('?')[0]
                        if profile_url.endswith('/'):
                            profile_url = profile_url[:-1]
                        found_profiles.add(profile_url)
                        print(f"    Found LinkedIn profile directly from element: {profile_url}")
                    else:
                        # If the selector found an element, but it wasn't a direct LinkedIn <a> tag or href was missing/wrong,
                        # try parsing the element's HTML content.
                        print(f"    Selector '{profile_card_content_selector}' found, but not a direct LinkedIn link via attributes. Falling back to parsing its content.")
                        # Fall through to BeautifulSoup parsing of this specific element's source.
                        page_source_of_card_element = linkedin_link_webelement.get_attribute('outerHTML')
                        if page_source_of_card_element:
                            soup = BeautifulSoup(page_source_of_card_element, 'html.parser')
                            newly_found = _extract_linkedin_links_from_soup(soup)
                            if newly_found:
                                found_profiles.update(newly_found)
                                print(f"    Found {len(newly_found)} profiles by parsing element's outerHTML.")
                            else:
                                print("    No LinkedIn profiles found by parsing element's outerHTML.")
                        else: # Fallback to whole page if outerHTML is not available or empty
                            print(f"    Could not get outerHTML for '{profile_card_content_selector}'. Parsing whole page.")
                            page_source_after_click = driver.page_source
                            soup = BeautifulSoup(page_source_after_click, 'html.parser')
                            newly_found = _extract_linkedin_links_from_soup(soup)
                            if newly_found:
                                found_profiles.update(newly_found)
                                print(f"    Found {len(newly_found)} profiles by parsing whole page.")
                            else:
                                print("    No LinkedIn profiles found by parsing whole page.")

                except TimeoutException:
                    print(f"    Timed out waiting for specific LinkedIn link ('{profile_card_content_selector}').")
                    print(f"    Attempting to parse entire current page source for LinkedIn links as a fallback.")
                    page_source_after_click = driver.page_source
                    soup = BeautifulSoup(page_source_after_click, 'html.parser')
                    newly_found = _extract_linkedin_links_from_soup(soup)
                    found_profiles.update(newly_found)

                # --- Close the profile card ---
                try:
                    # Small pause to ensure modal is fully rendered before looking for close button
                    time.sleep(0.5) 
                    print(f"    Attempting to close profile card (selector: '{profile_card_close_button_selector}')...")
                    # Wait for the close button to be visible and clickable
                    close_button = WebDriverWait(driver, 7).until( # Increased wait time slightly
                        EC.element_to_be_clickable((By.CSS_SELECTOR, profile_card_close_button_selector))
                    )
                    close_button.click()
                    print("    Profile card close button clicked.")
                    # Wait for the profile card element to disappear
                    WebDriverWait(driver, 7).until( # Increased wait time slightly
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, profile_card_content_selector)) # Wait for the profile card content to be invisible
                    )
                    print("    Profile card is now invisible.")
                except (TimeoutException, NoSuchElementException) as e_close:
                    print(f"    Could not find or click profile card close button ('{profile_card_close_button_selector}') or wait for card to disappear: {e_close}")
                    # If the primary close fails, we might be stuck. 
                    # Consider if a more aggressive "escape" is needed, e.g., driver.refresh() or sending ESC key,
                    # but this can be risky. For now, we'll just log and continue.
                    print("    WARNING: Profile card might still be open, potentially interfering with next trigger.")


                # If triggers were originally found in an iframe, attempt to switch back for the next trigger.
                if iframe_found:
                    print("    Attempting to switch back into iframe for next trigger (if any).")
                    try:
                        # Re-locate the iframe before switching. This is safer.
                        iframe_element_for_next_trigger = driver.find_element(By.CSS_SELECTOR, community_content_iframe_selector)
                        driver.switch_to.frame(iframe_element_for_next_trigger)
                    except Exception as e_refind_iframe:
                        print(f"      Could not re-find or switch back to iframe ('{community_content_iframe_selector}'): {e_refind_iframe}")
                        print("      Subsequent triggers might fail if they are inside the iframe.")

            except Exception as e_trigger_processing: # Renamed from e_trigger
                 if iframe_found:
                     try:
                         print("    Error during trigger processing, attempting to switch to default content.")
                         driver.switch_to.default_content()
                     except Exception as e_switch_back_error:
                         print(f"        Error trying to switch back to default content after trigger error: {e_switch_back_error}")
                 print(f"    Error processing current trigger ({type(e_trigger_processing).__name__}): {e_trigger_processing}")
            time.sleep(1) # Politeness delay
            current_trigger_index += 1

    except Exception as e_selenium:
        print(f"  An error occurred during Selenium operation for {url} ({type(e_selenium).__name__}): {e_selenium}")
    finally:
        if driver:
            # Ensure we are in the default content before quitting
            try:
                print("  Ensuring driver is in default content before quitting.")
                driver.switch_to.default_content()
            except Exception as e_final_switch: # Corrected indentation
                print(f"  Error during final switch to default content: {e_final_switch}") # Corrected indentation

            print(f"  Quitting WebDriver for {url}.")
            driver.quit()

    return found_profiles




if __name__ == "__main__":
    print("Starting LinkedIn profile scraper for both URLs and local HTML files...")
    scrape_linkedin_profiles()
    print("\nScraping completed.")
