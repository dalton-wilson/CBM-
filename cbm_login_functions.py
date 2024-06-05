import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Store site login credentials as variables to use throughout the program
def store_login_credentials():
    print("Please enter your Easy CBM login credentials. If you possess multiple administrator \n"
          "accounts, kindly provide each set of credentials in chronological order, as prompted.")
    cbm_username = input("Easy CBM user name: ")
    cbm_password = input("Easy CBM password: ")

    return cbm_username, cbm_password


# Create a folder to store processed and downloaded frames before combining into comprehensive csv file
def create_destination_folder(username):
    print('Creating destination directory for testing information files')
    frame_folder = (os.path.join(Path.cwd().parent, "Combined Frames by User", f"{username}"))
    if not os.path.exists(frame_folder):
        os.makedirs(frame_folder)
        print("Directory created.")
    else:
        print("Directory already exists.")

    return frame_folder


# Configure the web driver
def configure_driver(download_dir):
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=options)
    return driver


# Log in to the website
def login():
    # In case of login error, loop through the login process until there is a successful login
    while True:
        cbm_username, cbm_password = store_login_credentials()
        frame_folder = create_destination_folder(cbm_username)
        driver = configure_driver(frame_folder)

        driver.get("https://app.easycbm.com")

        # Wait for the page to load as evidenced by sign-in being clickable
        print("Logging in...")

        # Locate the email input field and fill it with your email
        wait = WebDriverWait(driver, 10)
        wait.until(ec.presence_of_element_located((By.ID, "username")))
        email_input = driver.find_element(By.ID, "username")
        email_input.send_keys(cbm_username)

        # Locate the password input field and fill it with your password
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys(cbm_password)

        # Click the login button
        sign_in_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        sign_in_button.click()

        try:
            wait = WebDriverWait(driver, 10)
            logout_button = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR,
                                                                   "a[href='/teachers/logout.php']")))
            # If login is successful, return objects and break the loop
            if logout_button:
                print("login successful")
                return driver, cbm_username, cbm_password, frame_folder
        except (TimeoutException, NoSuchElementException):
            print("ERROR: invalid login. Please re-enter your login credentials")
            driver.quit()
