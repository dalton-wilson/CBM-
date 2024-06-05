import pandas as pd
from pathlib import Path
import os


# CLASS FILE PROCESSING FUNCTIONS
# Helper function for processing all class files in the directory
def process_file(file_path):

    filename = os.path.basename(file_path)
    print(f"PROCESSING FILE {filename}")  # debug print statement
    name_parts = filename.split('_')
    subject = name_parts[-1].split('.')[0]  # Ensure the subject is correctly extracted without the file extension

    if "former_student" in filename:
        grade_level = "former_student"
    else:
        grade_level = None

    # Load the CSV file
    data = pd.read_csv(file_path)

    current_grade_level = data['Grade Level'].iloc[0]

    # Extract unique test groups based on the "Test" column, accounting for Kindergarten (K) and former_student
    data['Test Group'] = data['Test'].str.extract(r'(\d+|k|former_student)', expand=False).replace('k', 'K')

    if grade_level:
        data['Test Group'] = grade_level

    # Debugging print to check extracted groups
    print("Extracted Test Groups:", data['Test Group'].unique())

    # Set the test group based on the highest value in the 'Test Group' column
    data['Test Group'] = data['Test Group'].astype(str).replace({'K': '0', 'former_student': '-1'}).astype(int)
    max_test_group = data['Test Group'].max()
    if max_test_group == -1:
        max_test_group = 'former_student'
    elif max_test_group == 0:
        max_test_group = 'K'

    # Convert 'Test Date' to datetime for accurate range calculations
    data['Test Date'] = pd.to_datetime(data['Test Date'], errors='coerce')

    # Filter numeric columns only
    numeric_data = data.select_dtypes(include='number')

    # Extract all category names excluding 'Item Count' and 'Overall Score'
    all_categories = [col for col in numeric_data.columns if 'Item Count' not in col and col != 'Overall Score']

    # Initialize a DataFrame to collect all top 3 rankings
    all_tests_ranking_df = pd.DataFrame()

    # Sort data by 'Test Date' in descending order
    data = data.sort_values(by='Test Date', ascending=False)

    for test in data['Test'].unique():
        test_data = data[data['Test'] == test]
        test_numeric_data = test_data.select_dtypes(include='number')

        # Calculate average scores for all categories
        average_all_category_scores = round(test_numeric_data[all_categories].mean(), 1)

        # Identify corresponding item count columns and filter only existing ones
        all_item_count_cols = [f"{category} Item Count" for category in all_categories if
                               f"{category} Item Count" in test_numeric_data.columns]
        existing_categories = [category for category in all_categories if f"{category} Item Count" in test_numeric_data.columns]

        # Calculate total item counts for the existing categories
        all_item_counts = test_numeric_data[all_item_count_cols].mean()

        # Calculate the ranking values using the specified formula
        all_ranking_values = (100 - average_all_category_scores[existing_categories]) * all_item_counts.values

        # Create a DataFrame for better readability
        all_ranking_df = pd.DataFrame({
            'Category': existing_categories,
            'Average Score': average_all_category_scores[existing_categories].values,
            'Item Count': all_item_counts.values,
            'Ranking Value': all_ranking_values
        })

        # Sort by the ranking value
        sorted_all_ranking_df = all_ranking_df.sort_values(by='Ranking Value', ascending=False)

        # Replace 'Ranking Value' with integer ranks
        sorted_all_ranking_df['Ranking Value'] = sorted_all_ranking_df['Ranking Value'].rank(method='dense', ascending=False)

        # Fill NaN values with 0 (or any other appropriate value) before converting to integers
        sorted_all_ranking_df['Ranking Value'] = sorted_all_ranking_df['Ranking Value'].fillna(0).astype(int)

        # Select top 3 categories
        top_3_ranking_df = sorted_all_ranking_df.head(3).copy()

        # Define a function to get correct date range, including the most recent date
        def get_correct_date_range_with_latest(category):
            item_count_col = f"{category} Item Count"
            if item_count_col in test_data.columns:
                relevant_rows = test_data[test_data[item_count_col].notnull()]
                if not relevant_rows.empty:
                    date_range = relevant_rows['Test Date'].min(), relevant_rows['Test Date'].max()
                else:
                    date_range = (None, None)
            else:
                date_range = (None, None)
            return date_range

        # Correctly calculate the test date ranges for each category
        correct_test_date_ranges_with_latest = {category: get_correct_date_range_with_latest(category) for category in
                                                top_3_ranking_df['Category']}

        # Convert test date ranges to a readable format
        correct_test_date_ranges_with_latest_str = {
            k: f"{v[0].strftime('%m/%d/%Y')} - {v[1].strftime('%m/%d/%Y')}" if v[0] and v[1] else "N/A" for k, v in
            correct_test_date_ranges_with_latest.items()}

        # Add the correct test date ranges to the top 3 ranking dataframe using .loc
        top_3_ranking_df.loc[:, 'Test Date Range'] = top_3_ranking_df['Category'].map(correct_test_date_ranges_with_latest_str)

        # Add the test name to the DataFrame
        top_3_ranking_df['Test'] = test

        # Append to the all tests ranking DataFrame
        all_tests_ranking_df = pd.concat([all_tests_ranking_df, top_3_ranking_df], ignore_index=True)

    # Check if all_tests_ranking_df is empty
    if not all_tests_ranking_df.empty:
        print(all_tests_ranking_df)  # Debugging: Print the DataFrame to check if 'Test' exists

        # Append the rankings to the input CSV file
        with open(file_path, 'a') as f:
            f.write("\n\nTop 3 Question Types to Focus on, Grouped by Test:\n")
            all_tests_ranking_df.to_csv(f, index=False)

    return all_tests_ranking_df, max_test_group, subject, current_grade_level


# Helper function for saving all processed class files in directory
def processed_file_destination(processed_file_path, grade_level, subject, current_grade_level):
    processed_frame = pd.read_csv(processed_file_path)
    file_folder = os.path.join(Path.cwd().parent, "Processed Frames by Class", f"{current_grade_level}",
                               f"{current_grade_level} {subject}")
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    processed_frame.to_csv(os.path.join(file_folder, f"Grade {grade_level} {subject} Scores and Recommendations.csv"))


# Create recommendations for teachers on which areas to focus on moving forward for a given class
def create_class_question_type_recommendations(input_folder_path):
    results = []
    for file_name in os.listdir(input_folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(input_folder_path, file_name)
            result_df, test_group, subject, current_grade_level = process_file(file_path)
            results.append((file_name, result_df))
            processed_file_destination(file_path, test_group, subject, current_grade_level)
    return results


# STUDENT FILE PROCESSING FUNCTIONS
# Helper function for processing all student files in the directory
def process_student_file(file_path):

    filename = os.path.basename(file_path)
    print(f"PROCESSING FILE {filename}")  # debug print statement
    name_parts = filename.split('_')
    subject = name_parts[-1].split('.')[0]  # Ensure the subject is correctly extracted without the file extension
    student_name = "_".join(name_parts[:-1])

    # Load the CSV file
    data = pd.read_csv(file_path)

    current_grade_level = data['Grade Level'].iloc[0]

    # Extract unique test groups based on the "Test" column, accounting for Kindergarten (K) and former_student
    data['Test Group'] = data['Test'].str.extract(r'(\d+|k|former_student)', expand=False)

    # Debugging print to check extracted groups
    print("Extracted Test Groups:", data['Test Group'].unique())

    # Convert 'Test Group' to string, replace values, and then convert back to integers
    data['Test Group'] = data['Test Group'].replace({'k': '0', 'former_student': '-1'}).astype(int)
    max_test_group = data['Test Group'].max()
    if max_test_group == -1:
        max_test_group = 'former_student'
    elif max_test_group == 0:
        max_test_group = 'K'

    # Convert 'Test Date' to datetime for accurate range calculations
    data['Test Date'] = pd.to_datetime(data['Test Date'], errors='coerce')

    # Extract the test year from the 'Test' column
    data['Test Year'] = data['Test'].str.extract(r'(\d+)', expand=False)

    # Filter numeric columns only
    numeric_data = data.select_dtypes(include='number')

    # Extract all category names excluding 'Item Count' and 'Overall Score'
    all_categories = [col for col in numeric_data.columns if 'Item Count' not in col and col != 'Overall Score']

    # Initialize a DataFrame to collect all top 3 rankings
    all_years_ranking_df = pd.DataFrame()

    for year in sorted(data['Test Year'].unique(), reverse=True):  # Sort years in descending order
        if pd.isna(year):
            continue
        year_data = data[data['Test Year'] == year]
        year_numeric_data = year_data.select_dtypes(include='number')

        # Calculate average scores for all categories
        average_all_category_scores = year_numeric_data[all_categories].mean()

        # Identify corresponding item count columns and filter only existing ones
        all_item_count_cols = [f"{category} Item Count" for category in all_categories if
                               f"{category} Item Count" in year_numeric_data.columns]
        existing_categories = [category for category in all_categories if f"{category} Item Count" in year_numeric_data.columns]

        # Calculate total item counts for the existing categories
        all_item_counts = year_numeric_data[all_item_count_cols].sum()

        # Calculate the ranking values using the specified formula
        all_ranking_values = (100 - average_all_category_scores[existing_categories]) * all_item_counts.values

        # Create a DataFrame for better readability
        all_ranking_df = pd.DataFrame({
            'Category': existing_categories,
            'Average Score': average_all_category_scores[existing_categories].values,
            'Item Count': all_item_counts.values,
            'Ranking Value': all_ranking_values
        })

        # Sort by the ranking value
        sorted_all_ranking_df = all_ranking_df.sort_values(by='Ranking Value', ascending=False)

        # Replace 'Ranking Value' with integer ranks
        sorted_all_ranking_df['Ranking Value'] = sorted_all_ranking_df['Ranking Value'].rank(method='dense', ascending=False)

        # Fill NaN values with 0 (or any other appropriate value) before converting to integers
        sorted_all_ranking_df['Ranking Value'] = sorted_all_ranking_df['Ranking Value'].fillna(0).astype(int)

        # Select top 3 categories
        top_3_ranking_df = sorted_all_ranking_df.head(3).copy()

        # Define a function to get correct date range, including the most recent date
        def get_correct_date_range_with_latest_by_student(category):
            item_count_col = f"{category} Item Count"
            if item_count_col in year_data.columns:
                relevant_rows = year_data[year_data[item_count_col].notnull()]
                if not relevant_rows.empty:
                    date_range = relevant_rows['Test Date'].min(), relevant_rows['Test Date'].max()
                else:
                    date_range = (None, None)
            else:
                date_range = (None, None)
            return date_range

        # Correctly calculate the test date ranges for each category
        correct_test_date_ranges_with_latest = {category: get_correct_date_range_with_latest_by_student(category) for category in
                                                top_3_ranking_df['Category']}

        # Convert test date ranges to a readable format
        correct_test_date_ranges_with_latest_str = {
            k: f"{v[0].strftime('%m/%d/%Y')} - {v[1].strftime('%m/%d/%Y')}" if v[0] and v[1] else "N/A" for k, v in
            correct_test_date_ranges_with_latest.items()}

        # Add the correct test date ranges to the top 3 ranking dataframe using .loc
        top_3_ranking_df.loc[:, 'Test Date Range'] = top_3_ranking_df['Category'].map(correct_test_date_ranges_with_latest_str)

        # Add the year to the DataFrame
        top_3_ranking_df['Test Year'] = year

        # Append to the all years ranking DataFrame
        all_years_ranking_df = pd.concat([all_years_ranking_df, top_3_ranking_df], ignore_index=True)

    # Check if all_years_ranking_df is empty
    if not all_years_ranking_df.empty:
        print(all_years_ranking_df)  # Debugging: Print the DataFrame to check if 'Test Year' exists

        # Sort the final DataFrame by 'Test Year' in descending order
        all_years_ranking_df = all_years_ranking_df.sort_values(by='Test Year', ascending=False)

        # Append the rankings to the input CSV file
        with open(file_path, 'a') as f:
            f.write("\n\nTop 3 Areas to Focus on Grouped by Year:\n")
            all_years_ranking_df.to_csv(f, index=False)

    return all_years_ranking_df, max_test_group, subject, student_name, current_grade_level


# Helper function for saving all processed student files in directory
def processed_student_file_destination(processed_file_path, grade_level, subject, student_name, current_grade_level):
    processed_frame = pd.read_csv(processed_file_path)
    file_folder = os.path.join(Path.cwd().parent, "Processed Frames by Class", f"{current_grade_level}",
                               f"{current_grade_level} {subject}", f"{student_name} {subject}")
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    processed_frame.to_csv(os.path.join(file_folder, f"{student_name} Grade {grade_level} {subject} "
                                                     f"Scores and Recommendations.csv"))
    return file_folder


# Create recommendations for teachers on which areas to focus on moving forward for a given student
def create_student_question_type_recommendations(input_folder_path):
    results = []
    for file_name in os.listdir(input_folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(input_folder_path, file_name)
            result_df, test_group, subject, student_name, current_grade_level = process_student_file(file_path)
            results.append((file_name, result_df))
            processed_student_file_destination(file_path, test_group, subject, student_name, current_grade_level)
    return results
