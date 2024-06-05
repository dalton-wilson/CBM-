import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os


# CLASS PLOT CREATION FUNCTIONS
# Function to plot progress for each test group with embedded keys
def plot_progress_by_test_group_with_embedded_keys(data, categories, test_groups, output_folder, subject,
                                                   current_grade_level):
    markers = ['o', 'x']  # Different symbols for differentiating repeated colors within a group
    grade_levels = {str(i): f"Grade {i}" for i in range(1, 13)}  # Map numbers to grade levels
    grade_levels.update({'K': 'Kindergarten', 'former_student': 'Former Student'})  # Add additional grade levels
    colormap = plt.get_cmap('tab20')  # Explicitly fetch the tab20 colormap

    for group in sorted(test_groups):
        print(f"Processing group: {group}")  # Debugging print
        group_data = data[data['Test Group'] == group]
        group_test_dates = group_data['Test Date'].dropna().sort_values().unique()
        group_test_dates_str = [pd.Timestamp(date).strftime('%m/%d/%Y') for date in group_test_dates]

        group_categories = [category for category in categories if f"{category} Item Count" in group_data.columns]
        group_progress_data = {category: [] for category in group_categories}

        for category in group_categories:
            item_count_col = f"{category} Item Count"
            for date in group_test_dates:
                relevant_rows = group_data[group_data['Test Date'] == date]
                if not relevant_rows.empty:
                    score = relevant_rows[category].mean()  # Calculate the mean score for the category
                else:
                    score = None
                group_progress_data[category].append(score)

        # Filter out dictionary items with all "None" in values
        group_progress_data = {category: scores for category, scores in group_progress_data.items()
                               if any(score is not None for score in scores)}

        # Check if there is data to plot
        if not group_progress_data:
            print(f"No valid data to plot for group: {group}")
            continue

        plt.figure(figsize=(14, 8))
        used_colors = set()  # Reset used colors for each group

        for idx, (category, scores) in enumerate(group_progress_data.items()):
            line_color = colormap(idx % 20)  # Use a colormap for unique colors
            if line_color in used_colors:
                marker = markers[1]  # Use 'x' if color is repeated within the group
            else:
                marker = markers[0]  # Use 'o' for unique color
                used_colors.add(line_color)

            plt.plot(group_test_dates_str, scores, marker=marker, label=category, color=line_color)

        plt.xlabel('Test Date')
        plt.ylabel('Average Score')
        plt.title(f"Class Progress in Each Category ({grade_levels.get(group, group)})")  # Use the group as fallback

        if group_progress_data:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the chart as an image file
        chart_folder = os.path.join(output_folder, f"{current_grade_level}", f"{current_grade_level} {subject}")
        if not os.path.exists(chart_folder):
            os.makedirs(chart_folder)
        chart_path = os.path.join(chart_folder, f"class_progress_grade_{group}_{subject}.png")
        plt.savefig(chart_path)
        plt.close()


# Function to process a single file
def process_file(input_file, output_folder):
    filename = os.path.basename(input_file)
    name_parts = filename.split('_')
    subject = name_parts[-1].split('.')[0]  # Ensure the subject is correctly extracted without the file extension

    # If "former_student" is in the filename, extract the grade level
    if "former_student" in filename:
        grade_level = "former_student"
    else:
        grade_level = None

    data = pd.read_csv(input_file)

    # Convert 'Test Date' to datetime for accurate range calculations
    data['Test Date'] = pd.to_datetime(data['Test Date'], errors='coerce')

    # Filter numeric columns only
    numeric_data = data.select_dtypes(include='number')

    # Extract all category names excluding 'Item Count' and 'Overall Score'
    all_categories = [col for col in numeric_data.columns if 'Item Count' not in col and col != 'Overall Score']

    # Print unique values in the 'Test' column for debugging
    print("Unique values in 'Test' column:", data['Test'].unique())

    # Extract unique test groups based on the "Test" column, accounting for Kindergarten (K) and former_student
    data['Test Group'] = data['Test'].str.extract(r'(\d+|k|former_student)', expand=False).replace('k', 'K')

    # If grade_level is set to "former_student", override the Test Group
    if grade_level:
        data['Test Group'] = grade_level

    # Debugging print to check extracted groups
    print("Extracted Test Groups:", data['Test Group'].unique())

    # Set the test group based on the highest value in the 'Test Group' column
    data['Test Group'] = data['Test Group'].astype(str).replace({'K': '0', 'former_student': '-1'}).astype(int)
    test_groups = pd.Series(data['Test Group'].unique()).dropna().unique()
    data['Test Group'] = data['Test Group'].replace(0, 'K').replace(-1, 'former_student')

    current_grade_level = data['Grade Level'].iloc[0]

    # Plot the progress data for each test group with embedded keys and differentiated symbols within each group
    plot_progress_by_test_group_with_embedded_keys(data, all_categories, test_groups, output_folder, subject,
                                                   current_grade_level)


# Create charts for all class files in a directory
def create_all_class_charts(input_directory):
    output_directory = os.path.join(Path.cwd().parent, "Processed Frames by Class")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(input_directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_directory, filename)
            process_file(file_path, output_directory)

    return output_directory


# STUDENT PLOT CREATION FUNCTIONS
# Function to plot progress for each grade level with embedded keys
def plot_student_progress_by_grade_level_with_embedded_keys(data, categories, test_groups, output_folder, student_name,
                                                            subject, current_grade_level):
    markers = ['o', 'x']  # Different symbols for differentiating repeated colors within a group
    grade_levels = {str(i): f"Grade {i}" for i in range(1, 13)}  # Map numbers to grade levels
    grade_levels.update({'K': 'Kindergarten'})  # Add Kindergarten
    colormap = plt.get_cmap('tab20')  # Explicitly fetch the tab20 colormap

    for group in sorted(test_groups):
        print(f"Processing group: {group}")  # Debugging print
        group_data = data[data['Test Group'] == group]
        group_test_dates = group_data['Test Date'].dropna().sort_values().unique()
        group_test_dates_str = [pd.Timestamp(date).strftime('%m/%d/%Y') for date in group_test_dates]

        group_categories = [category for category in categories if f"{category} Item Count" in group_data.columns]
        group_progress_data = {category: [] for category in group_categories}

        for category in group_categories:
            item_count_col = f"{category} Item Count"
            for date in group_test_dates:
                relevant_row = group_data[(group_data['Test Date'] == date) & (group_data[item_count_col].notnull())]
                if not relevant_row.empty:
                    score = relevant_row[category].values[0]
                else:
                    score = None
                group_progress_data[category].append(score)

        # Filter out dictionary items with all "None" in values
        group_progress_data = {category: scores for category, scores in group_progress_data.items()
                               if any(score is not None for score in scores)}

        plt.figure(figsize=(14, 8))
        used_colors = set()  # Reset used colors for each group

        for idx, (category, scores) in enumerate(group_progress_data.items()):
            line_color = colormap(idx % 20)  # Use a colormap for unique colors
            if line_color in used_colors:
                marker = markers[1]  # Use 'x' if color is repeated within the group
            else:
                marker = markers[0]  # Use 'o' for unique color
                used_colors.add(line_color)

            plt.plot(group_test_dates_str, scores, marker=marker, label=category, color=line_color)

        plt.xlabel('Test Date')
        plt.ylabel('Score')
        plt.title(f"{student_name}'s Progress in Each Category ({grade_levels.get(group, group)})")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the chart as an image file
        chart_folder = os.path.join(output_folder, f"{current_grade_level}", f"{current_grade_level} {subject}",
                                    f"{student_name} {subject}")
        if not os.path.exists(chart_folder):
            os.makedirs(chart_folder)
        chart_path = os.path.join(chart_folder, f"{student_name.replace(' ', '_').lower()}_"
                                  f"{grade_levels.get(group, group).replace(' ', '_').lower()}_{subject}_progress.png")
        plt.savefig(chart_path)
        plt.close()


# Extract student name from filename
def extract_student_name_and_subject(filename):
    name_parts = filename.split('_')
    student_name = '_'.join(name_parts[:-1])
    subject_parts = name_parts[-1].split('.')
    subject = subject_parts[0]
    return student_name, subject


# Process a single file
def process_student_file(input_file, output_folder):
    filename = os.path.basename(input_file)
    print(f"PROCESSING FILE {filename}")  # debug print statement
    student_name, subject = extract_student_name_and_subject(filename)
    data = pd.read_csv(input_file)

    # Convert 'Test Date' to datetime for accurate range calculations
    data['Test Date'] = pd.to_datetime(data['Test Date'], errors='coerce')

    # Filter numeric columns only
    numeric_data = data.select_dtypes(include='number')

    # Extract all category names excluding 'Item Count' and 'Overall Score'
    all_categories = [col for col in numeric_data.columns if 'Item Count' not in col and col != 'Overall Score']

    # Print unique values in the 'Test' column for debugging
    print("Unique values in 'Test' column:", data['Test'].unique())

    # Extract unique test groups based on the "Test" column, accounting for Kindergarten (K)
    data['Test Group'] = data['Test'].str.extract(r'(\d+|[kK])', expand=False).replace(['k', 'K'], 'K')

    # Debugging print to check extracted groups
    print("Extracted Test Groups:", data['Test Group'].unique())

    # Prepare the progress data for each test group
    test_groups = pd.Series(data['Test Group'].unique()).dropna().unique()

    current_grade_level = data['Grade Level'].iloc[0]

    # Plot the progress data for each test group with embedded keys and differentiated symbols within each group
    plot_student_progress_by_grade_level_with_embedded_keys(data, all_categories, test_groups, output_folder,
                                                            student_name, subject, current_grade_level)


# Create charts for all student files in a directory
def create_all_student_charts(input_directory, output_directory):
    for filename in os.listdir(input_directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_directory, filename)
            process_student_file(file_path, output_directory)

    return output_directory
