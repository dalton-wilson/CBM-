import pandas as pd
import os
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import WebDriverException, NoSuchElementException


# Direct the web driver to the appropriate location to begin data collection
def nav_to_tables(driver):

    print("Navigating to testing information page...")
    # Navigate to page
    try:
        page = f"https://app.easycbm.com/teachers/auth/reporting.php"
        # create page driver
        driver.maximize_window()
        driver.get(page)
    except WebDriverException:
        print(f"Error: Failed to load stats from item analysis table")

    # Navigate to item analysis tables:
    # Navigate to grade level groupings
    wait = WebDriverWait(driver, 10)
    wait.until(ec.presence_of_element_located((By.ID, "reportsSubTab_GroupingsButton")))
    try:
        groups_button = driver.find_element(By.ID, "reportsSubTab_GroupingsButton")
        groups_button.click()
    except NoSuchElementException:
        print(f"Error: Groups button not found ")

    # Choosing list of all tests
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(ec.presence_of_element_located((By.CLASS_NAME, "reportingGroupingNameCol")))
        grouping_columns = driver.find_elements(By.CLASS_NAME, "reportingGroupingNameCol")
        for button in grouping_columns:
            if button.text == "All Students":
                button.click()
    except NoSuchElementException:
        print(f"Error: All Students button not found ")

    return driver


# This function runs if there is a calculation error in data processing due to the absence of data. It will reset the
# "timer" variable to allow the internet connection more time to load data
def change_timer_value():
    print("\nERROR: No data was saved to your directories. You may need to give your computer more time to process the"
          " online data.")
    timer_preference = input("Would you like to adjust the wait time to allow your browser more time to load data? "
                             "\nRespond YES to change (default is 1 sec). Press ENTER to bypass: ")
    if timer_preference == "yes".lower():
        sleep_timer = int(input("Please enter the amount of seconds you'd like to allow your browser to load each"
                                "\ntable (default is 1 sec): "))
    else:
        sleep_timer = 1

    return sleep_timer


# This function combines all single-test files into one frame and adds student grade-level data
def combine_csv_files(input_folder_path, grade_levels):
    # List to hold dataframes
    dfs = []

    # Loop through all files in the folder
    for filename in os.listdir(input_folder_path):
        if filename.endswith('.csv'):
            # Construct full file path
            file_path = os.path.join(input_folder_path, filename)
            # Read the CSV file and append to the list
            df = pd.read_csv(file_path)
            dfs.append(df)

    # Concatenate all dataframes into one
    combined_df = pd.concat(dfs, ignore_index=True)

    # Create a reverse lookup dictionary from the "grade_levels" dictionary
    student_to_grade = {}
    for grade, students in grade_levels.items():
        for student in students:
            student_to_grade[student] = grade

    # Add the "Grade Level" column to the data frame
    combined_df['Grade Level'] = combined_df['Student Name'].map(student_to_grade)

    # Save the frame as a csv file
    combined_df.to_csv(os.path.join(Path.cwd().parent, "BIG_DF.csv"), index=False)


# Check for missing question category values and give the user options on how to account for the missing data
def check_and_fill_data(input_folder_path):
    # Continue prompting the user to address missing data until it is resolved
    while True:
        incomplete_tests = []

        # Loop through all the files in the folder
        for filename in os.listdir(input_folder_path):
            file_path = os.path.join(input_folder_path, filename)
            print(f"Checking file: {file_path}")

            try:
                df = pd.read_csv(file_path)
                # Check if 'Type' column exists and if it has missing data
                if 'Type' in df.columns and ((df['Type'].isnull() | (df['Type'] == '')).any()):
                    print(f"Missing data found in {filename}")
                    # If data is missing, add the file name to the incomplete tests list
                    incomplete_tests.append(filename)
                elif 'Type' not in df.columns:
                    print(f"'Type' column missing in {filename}")
                else:
                    print(f"No missing 'Type' data in {filename}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")

        if incomplete_tests:
            print(f"\nERROR: The following files are missing QUESTION TYPE data: {incomplete_tests}")
            response = input("To fill in missing data, cross-reference the test data on the EasyCBM website \n"
                             "with the listed files, located in the 'Extracted Data Frames' folder, and manually \n"
                             "input missing item TYPE values. Enter 'complete' when all test files are updated, \n"
                             "'check' to verify again, or 'bypass' to remove rows with missing data: ")
            # If user elects to fill in missing data, the program will re-check for completeness
            if response.lower() == "complete":
                continue  # This will restart the check to confirm user update
            # If the user elects to ignore the missing data, the program will eliminate those rows and continue running
            elif response.lower() == "bypass":
                for test_file in incomplete_tests:
                    file_path = os.path.join(input_folder_path, test_file)
                    df = pd.read_csv(file_path)
                    # Remove rows where 'Type' column is empty or NaN
                    df = df[df['Type'].notna() & (df['Type'] != '')]
                    df.to_csv(file_path, index=False)  # Save the modified DataFrame back to the file
                print("Missing data removed from files. Proceeding with updated files.")
                continue  # Recheck to confirm the removals before proceeding
        else:
            print("All test files updated.")
            break  # Exit the loop if all files are complete
