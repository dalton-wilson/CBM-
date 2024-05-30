from bs4 import BeautifulSoup
import json
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import glob
import pandas as pd


def save_test_date_data(driver, download_dir, timer):
    # time.sleep(timer)
    test_dates_button = driver.find_element(By.CSS_SELECTOR, '[id^="gid_link"]')
    print(test_dates_button.text)
    test_dates_button.click()
    # time.sleep(timer + 2)

    # Wait for the file to appear in the download directory
    wait_time = 0
    downloaded_file = None
    while wait_time < 30:  # Wait up to 30 seconds
        # Search for files starting with the specified prefix
        files = glob.glob(os.path.join(download_dir, f"All_Students*"))
        if files:
            downloaded_file = files[0]
            break
        time.sleep(timer)
        wait_time += 1

    if downloaded_file:
        print(f"File downloaded successfully: {downloaded_file}")
    else:
        print("Error: File download timed out.")
    # time.sleep(timer)

    return driver


def write_test_tables(driver, username, sleep_timer):

    print('Creating destination directory for testing information files')
    frame_folder = (os.path.join(Path.cwd().parent, "Extracted Data Frames", f"{username}"))
    if not os.path.exists(frame_folder):
        os.makedirs(frame_folder)
        print("Directory created.")
    else:
        print("Directory already exists.")

    # creating list of successfully saved test frames to send to student frame writer
    test_frame_names = []
    # test_frames_missing_info = []

    wait = WebDriverWait(driver, 10)
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "fleft")))
    time.sleep(sleep_timer)

    # parse the html
    source = driver.page_source.encode('utf-8').strip()
    soup = BeautifulSoup(source, 'html5lib')

    # Select the desired test:
    test_buttons = driver.find_elements(By.CLASS_NAME, "fleft")
    for button in test_buttons:
        if "Basic" in button.text or "Proficient" in button.text:
            button.click()

            # wait = WebDriverWait(driver, 10)
            # wait.until(ec.presence_of_element_located((By.ID, "reportingItemAnalysisTable")))
            time.sleep(sleep_timer)

            # Parse the html
            source = driver.page_source.encode('utf-8').strip()
            soup = BeautifulSoup(source, 'html5lib')

            # Find the test items data table
            test_items_data_table = soup.find('table', id='reportItemAnalysisTable')

            if test_items_data_table is None:
                print(f'No item analysis data available for {button.text}')
                continue
            else:
                print(f'Creating item analysis data frame for {button.text}...')
                # Create test items data frame
                test_items_headers = []
                headers_block = test_items_data_table.find('thead')
                headers_list = headers_block.find_all('th')
                for header in headers_list:
                    test_items_headers.append(header.text)

                data_table_body = test_items_data_table.find('tbody')
                test_items = []
                for test_item in data_table_body.find_all('tr'):
                    item_attributes = []
                    for val in test_item.find_all('td'):
                        item_attributes.append(val.text)
                    test_items.append(item_attributes)

                print(f"Saving item analysis data frame for {button.text} to csv")
                test_items_df = pd.DataFrame(data=test_items, columns=test_items_headers)
                if 'Type Description' in test_items_headers:
                    test_items_df.rename(columns={'Type Description': 'Type'}, inplace=True)
                test_items_df = test_items_df[['Item', 'Type', 'Student Names, Incorrect']]
                # if (test_items_df['Type'] == '').any():
                    # test_frames_missing_info.append(button.text)

                test_items_df.to_csv(os.path.join(frame_folder, f'{username}_{button.text}_test_data.csv'), index=False)

                test_frame_names.append(button.text)

    return test_frame_names, frame_folder       # test_frames_missing_info,


def write_student_tables(driver, test_list, username, folder, sleep_timer):

    wait = WebDriverWait(driver, 10)
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "fleft")))
    time.sleep(sleep_timer)

    # parse the html
    source = driver.page_source.encode('utf-8').strip()
    soup = BeautifulSoup(source, 'html5lib')

    # Select the desired test:
    test_buttons = driver.find_elements(By.CLASS_NAME, "fleft")
    for button in test_buttons:
        if button.text in test_list:
            button.click()

            wait = WebDriverWait(driver, 10)
            wait.until(ec.presence_of_element_located((By.ID, "studentReportingTable")))
            time.sleep(sleep_timer)

            # Parse the html
            source = driver.page_source.encode('utf-8').strip()
            soup = BeautifulSoup(source, 'html5lib')

            # Find the students data table
            students_data_table = soup.find('table', id='studentReportingTable')

            print(f'Creating student data frame for {button.text}...')
            # Create the students data frame
            students_headers = []
            headers_block = students_data_table.find('tr')
            headers_list = headers_block.find_all('td')
            for header in headers_list:
                students_headers.append(header.text)

            data_table_body = students_data_table.find('table', id='studentReportingDataTable')
            student_items = []
            for student_item in data_table_body.find_all('tr'):
                item_attributes = []
                for val in student_item.find_all('td'):
                    item_attributes.append(val.text)
                student_items.append(item_attributes)

            print(f'Saving student data frame for {button.text} to csv')

            students_df = pd.DataFrame(data=student_items, columns=students_headers)
            students_df['Student Name'] = students_df['Student Name'].str.replace('Show Graph', '', regex=False)
            students_df = students_df[students_df['View Test'] == 'View']
            students_df = students_df[['Student Name', 'Score']]
            students_df['Score'] = students_df['Score'].str.extract(r'\((\d+)%\)').astype(float)

            students_df.to_csv(os.path.join(folder, f'{username}_{button.text}_student_data.csv'), index=False)

    return driver


def get_grade_levels(cbm_username, cbm_password):

    driver = webdriver.Chrome()
    driver.get("https://app.easycbm.com")

    # Wait for the page to load as evidenced by sign-in being clickable
    print("Obtaining student grade-level information... ")

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
        if logout_button:
            print("login successful")

    except (TimeoutException, NoSuchElementException):
        print("ERROR: invalid login. Please re-enter your login credentials")
        driver.quit()

    try:
        page = f"https://app.easycbm.com/teachers/auth/students.php"
        # create page driver
        driver.maximize_window()
        driver.get(page)
    except WebDriverException:
        print(f"Error: Failed to load data from student grade levels table")

    grade_levels_dict = {}  # Initialize an empty dictionary

    grade_level_rows = driver.find_elements(By.CSS_SELECTOR, '[name="active-group"]')
    for item in grade_level_rows:
        label = driver.execute_script("return arguments[0].nextSibling.textContent.trim();", item)
        if label != "All Students":
            item.click()  # Click the grade level to load the students
            grade_level_students = driver.find_elements(By.CLASS_NAME, "checked")
            students_list = []  # Initialize list to store student names
            for student in grade_level_students:
                student_name = student.text.strip()
                if student_name != label:  # Filter out the grade level label from student names
                    students_list.append(student_name)

            grade_levels_dict[label] = students_list  # Assign list of names to the grade level key
            print(f"{label}: {students_list}")  # Optionally print each grade and its students

            time.sleep(1)  # Wait to avoid overwhelming the server or being detected as a bot

    driver.quit()

    with open(os.path.join(Path.cwd().parent, "grade_levels_dict.json"), "w") as f:
        json.dump(grade_levels_dict, f, indent=4)

    return grade_levels_dict


