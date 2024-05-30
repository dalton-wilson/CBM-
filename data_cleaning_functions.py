import os
import glob
import pandas as pd
from pathlib import Path


# Reformatting names in student table for matching in test table
def shuffle_names(student_name):

    last_name, first_name = student_name.split(',')
    return f'{first_name} {last_name}'


def cat_score_column_creator(test_frame, admin_username, student_frame, test_, cat_header):
    # Creating rows for processed data frame
    student_rows = []

    categories = list(test_frame[cat_header].unique())
    item_count_headings = [f"{category} Item Count" for category in categories]
    columns = [item for pair in zip(categories, item_count_headings) for item in pair]

    try:
        for student in student_frame['Student Name']:
            student_row = [f'{student}', f'{admin_username}', f'{test_}']
            name = shuffle_names(student)
            first_last = name.split(' ')
            first_name_last_init = first_last[1] + ' ' + first_last[2][0]
            for category in categories:
                filtered_for_cat = test_frame.loc[test_frame[cat_header] == f'{category}']
                # filtering frame by student name appearance in Student Name, Incorrect column
                name_mask = filtered_for_cat['Student Names, Incorrect'].str.contains(f'{first_name_last_init}')
                filtered_for_cat_and_name = filtered_for_cat.loc[name_mask]
                cat_accuracy = int(round((len(filtered_for_cat) - len(filtered_for_cat_and_name)) /
                                         len(filtered_for_cat), 2) * 100)
                student_row.append(cat_accuracy)
                student_row.append(len(filtered_for_cat))
            student_rows.append(student_row)
    except ZeroDivisionError:
        print(f"ERROR: {cat_header} data missing from {test_} file. Please check the file in the \n"
              f"'Extracted Data Frames' folder and the test on the CBM website, determine the category of the \n"
              f"test item in question, and fill in the missing data.")

    return columns, student_rows


def get_category_scores(username, test_list):

    print('Creating destination directory for category information files')
    test_frame_folder = (os.path.join(Path.cwd().parent, "Single Test Data Frames", f"{username}"))
    if not os.path.exists(test_frame_folder):
        os.makedirs(test_frame_folder)
        print("Directory created")
    else:
        print("Directory already exists")

    for test in test_list:

        print(f"Creating scores-by-category file for {test}")

        test_table_path = os.path.join(Path.cwd().parent, 'Extracted Data Frames', f"{username}",
                                       f'{username}_{test}_test_data.csv')
        student_table_path = os.path.join(Path.cwd().parent, 'Extracted Data Frames', f"{username}",
                                          f'{username}_{test}_student_data.csv')
        # Reading files
        test_table = pd.read_csv(test_table_path)
        student_table = pd.read_csv(student_table_path)

        columns, student_rows = cat_score_column_creator(test_table, username, student_table, test, 'Type')

        # Creating headers for processed data frame
        headers = ['Student Name', 'Administrator', 'Test']
        for col in columns:
            headers.append(f'{col}')

        # Creating data frame
        processed_frame = pd.DataFrame(data=student_rows, columns=headers)
        processed_frame['Overall Score'] = student_table['Score']

        # Writing data frame to csv
        path = os.path.join(test_frame_folder, f'{username}_{test}.csv')
        processed_frame.to_csv(path, index=False)

    return test_frame_folder


def combine_csv_files(username, input_folder_path, output_folder_path):
    # List to hold dataframes
    dfs = []

    # Loop through all files in the folder
    for filename in os.listdir(input_folder_path):
        if filename.startswith(f"{username}"):
            # Construct full file path
            file_path = os.path.join(input_folder_path, filename)
            # Read the CSV file and append to the list
            df = pd.read_csv(file_path)
            dfs.append(df)

    # Concatenate all dataframes into one
    combined_df = pd.concat(dfs, ignore_index=True)

    combined_df.to_csv(os.path.join(output_folder_path, f"{username}_combined_df.csv"), index=False)

    return combined_df


def add_date_data(input_folder, username):
    # Load the datasets
    file_path_1 = os.path.join(input_folder, f"{username}_combined_df.csv")
    data = pd.read_csv(file_path_1)
    date_file_paths = glob.glob(os.path.join(input_folder, "All_Students*"))
    file_path_2 = date_file_paths[0]
    data_2 = pd.read_csv(file_path_2)

    # Normalize student names for matching
    data['Student Name'] = data['Student Name'].str.strip().str.lower()
    data_2['Full Name'] = (data_2['Last Name'].str.strip().str.lower() + ', ' +
                           data_2['First Name'].str.strip().str.lower())

    # Preparing math test names before processing
    data['Test'] = data['Test'].str.replace(r'(\d)\s', r'\1_', regex=True)

    # Debug: Print column names before preprocessing
    print("Before preprocessing:", data_2.columns)

    # Preprocess column names in data_2
    data_2.columns = data_2.columns.str.replace('RDG_BASIC:', 'Basic Reading', regex=True)
    data_2.columns = data_2.columns.str.replace('MATH_BASIC_BM:|MATH_BASIC:', 'Basic Math', regex=True)
    data_2.columns = data_2.columns.str.replace('RDG_PROF:', 'Proficient Reading', regex=True)
    data_2.columns = data_2.columns.str.replace('MATH_PROF_BM:|MATH_PROF:', 'Proficient Math', regex=True)

    # Remove the " - Date" suffix from the column headers
    data_2.columns = data_2.columns.str.replace(' - Date', '', regex=True)

    # Debug: Print column names after preprocessing
    print("After preprocessing:", data_2.columns)

    # Convert test names and column names to lowercase for case-insensitive matching
    data['Test'] = data['Test'].str.lower()
    data_2.columns = data_2.columns.str.lower()

    # Debug: Check if 'Full Name' column exists
    if 'full name' not in data_2.columns:
        raise KeyError("'Full Name' column is missing after preprocessing!")

    # Create the test_date_mapping dictionary using exact matching
    test_date_mapping = {test_name: test_name for test_name in data['Test'].unique() if test_name in data_2.columns}

    # Reset the 'Test Date' column in the first dataset
    data['Test Date'] = None

    # Populate 'Test Date' column based on exact matching for student names and test names
    for index, row in data.iterrows():
        student_name = row['Student Name']
        test_type = row['Test']
        date_column = test_date_mapping.get(test_type)

        if date_column:
            matching_row = data_2[data_2['full name'] == student_name]
            if not matching_row.empty:
                data.at[index, 'Test Date'] = matching_row[date_column].values[0]

    # Display the first few rows of the updated dataset to verify
    print(data.head())

    print('Creating destination directory for processed files')
    output_folder = os.path.join(os.path.dirname(input_folder), "Combined Data Frames With Dates")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print("Directory created.")
    else:
        print("Directory already exists.")

    # Save the updated dataset to a new CSV file
    path = os.path.join(output_folder, f"{username}_with_dates.csv")
    data.to_csv(path, index=False)

    return output_folder


def combine_big_frames(input_folder_path, grade_levels):
    # List to hold dataframes
    dfs = []

    # Loop through all files in the folder
    for filename in os.listdir(input_folder_path):
        if filename.endswith(".csv"):
            # Construct full file path
            file_path = os.path.join(input_folder_path, filename)
            # Read the CSV file and append to the list
            df = pd.read_csv(file_path)
            dfs.append(df)

    # Concatenate all dataframes into one
    combined_df = pd.concat(dfs, ignore_index=True)

    # Create a reverse lookup dictionary from grade_levels
    student_to_grade = {}
    for grade, students in grade_levels.items():
        for student in students:
            student_to_grade[student] = grade
    print("STUDENT TO GRADE DICTIONARY:")
    print(student_to_grade)

    # Normalize the student names in the student_to_grade dictionary
    normalized_student_to_grade = {student.strip().lower(): grade for student, grade in student_to_grade.items()}
    print("Normalized student_to_grade dictionary:")
    print(normalized_student_to_grade)

    # Normalize the 'Student Name' column in combined_df
    combined_df['Student Name'] = combined_df['Student Name'].str.strip().str.lower()

    # Define a function to map student names to grade levels, returning 'former student' if not found
    def map_grade_level(student_name):
        return normalized_student_to_grade.get(student_name, 'former student')

    # Map the normalized 'Student Name' to the 'Grade Level'
    combined_df['Grade Level'] = combined_df['Student Name'].apply(map_grade_level)

    combined_df.to_csv(os.path.join(Path.cwd().parent, "BIG_DF.csv"), index=False)

    # Debug: print sample of combined_df to verify
    print(combined_df.head())

    return combined_df


def save_files_by_student(big_df):
    print('Creating destination directory for student information files')
    output_folder = (os.path.join(Path.cwd().parent, "Student Data Frames"))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print("Directory created")
    else:
        print("Directory already exists")

    # filepath = os.path.join(Path.cwd().parent, 'BIG_DF.csv')
    # df = pd.read_csv(filepath)
    df = big_df

    # Group by 'Student Name' and test type and write to CSV
    # Add a new column to categorize test type based on the presence of "Math" or "Reading"
    df['Test Category'] = df['Test'].apply(
        lambda x: 'math' if 'math' in x else 'reading' if 'reading' in x else 'other')

    for (name, category, grade), group in df.groupby(['Student Name', 'Test Category', 'Grade Level']):
        # Reset the index and drop the previous index entirely to avoid it being added as a column
        group = group.reset_index(drop=True)

        # Remove columns where all entries are NaN
        group = group.dropna(axis=1, how='all')

        # Ensure "Overall Score" is the last column if it exists in the DataFrame
        if 'Overall Score' in group.columns:
            # Move "Overall Score" to the end
            cols = [col for col in group.columns if col != 'Overall Score'] + ['Overall Score']
            group = group[cols]

        # Drop the 'Test Category' column
        # group = group.drop(columns=['Administrator', 'Test Category', 'Grade Level'])

        # Create a valid filename for each student
        filename = f"{name.replace(' ', '_')}_{category}.csv"
        filepath = os.path.join(output_folder, filename)

        # Save the DataFrame to CSV without including the index
        group.to_csv(filepath, index=False)
        print(f"File saved: {filepath}")

    return output_folder


def save_files_by_class(big_df):
    print('Creating destination directory for class information files')
    output_folder = (os.path.join(Path.cwd().parent, "Class Data Frames"))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print("Directory created")
    else:
        print("Directory already exists")

    # filepath = os.path.join(Path.cwd().parent, 'BIG_DF.csv')
    # df = pd.read_csv(filepath)
    df = big_df

    # Group by 'Student Name' and test type and write to CSV
    # Add a new column to categorize test type based on the presence of "Math" or "Reading"
    df['Test Category'] = df['Test'].apply(
        lambda x: 'math' if 'math' in x else 'reading' if 'reading' in x else 'other')

    # df['Test Group'] = df['Test'].str.extract(r'(\d+|k|former_student)', expand=False).replace('k', 'K')

    for (grade_level, category), group in df.groupby(['Grade Level', 'Test Category']):
        # Reset the index and drop the previous index entirely to avoid it being added as a column
        group = group.reset_index(drop=True)

        # Remove columns where all entries are NaN
        group = group.dropna(axis=1, how='all')

        # Ensure "Overall Score" is the last column if it exists in the DataFrame
        if 'Overall Score' in group.columns:
            # Move "Overall Score" to the end
            cols = [col for col in group.columns if col != 'Overall Score'] + ['Overall Score']
            group = group[cols]

        # Drop the 'Test Category' column
        # group = group.drop(columns=['Administrator', 'Test Category', 'Grade Level'])
        # test_groups = pd.Series(df['Test Group'].unique()).dropna().unique()
        # grade_level = test_groups.max()

        # Create a valid filename for each student
        filename = f"{grade_level.replace(' ', '_')}_{category}.csv"
        filepath = os.path.join(output_folder, filename)

        # Save the DataFrame to CSV without including the index
        group.to_csv(filepath, index=False)
        print(f"File saved: {filepath}")

    return output_folder
