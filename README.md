# CBM-
math and reading test data cleaning, processing, visualization, and analysis

Data Processing and Visualization Tool
This repository contains a Python-based tool for collecting, processing, and visualizing educational data. The main script orchestrates the workflow, utilizing various functions from different modules to handle specific tasks. 

PURPOSE:
The EasyCBM program, authored by the University of Oregon, provides standardized math and reading exams, automated grading, and feedback at the class and individual student levels, as well as a question-by_question breakdown of the test including question type and a list of students who missed the question. One useful aspect that is missing from the EasyCBM website, however, is a breakdown of data by question type, which is very helpful for teachers when deciding which areas of curriculum to focus on moving forward throughout the year. This program is designed to take the data from the website, organize it by question category, and provide line charts of test-over-test performance by category at both the class and student levels, as well as recommendations on which aspects of curriculum teachers should focus on in order to most positively impact performance on subsequent exams and understanding of grade-level math as a whole.

FEATURES:

Automated login and data collection from the Easy CBM platform.

Data cleaning and consolidation.

Generation of visual reports and recommendations for classes and students.

Visualization of data trends and student progress.

INSTALLATION:
Clone the repository-
Copy code:
git clone https://github.com/yourusername/your-repo-name.git
Install the required packages-
Copy code:
pip install -r requirements.txt

USAGE:
Navigate to the project directory.
Run the main program-
Copy code:
python main_runner.py
Follow the on-screen instructions to input login details and other required information.

MODULES:
cbm_login_functions - Handles login operations:
store_login_credentials()
create_destination_folder(username)
configure_driver(download_dir)
login()

progressor_functions -Assists with navigation and data processing tasks:
nav_to_tables(driver)
change_timer_value()
check_and_fill_data(input_folder_path)

cbm_site_data_collection_functions - Collects data from the Easy CBM website. No API was available, so this section is basically a web scraper. In order to ensure proper performance, the browser window that opens during program execution should not be disturbed.
save_test_date_data(driver, download_dir, timer)
write_test_tables(driver, username, sleep_timer)
write_student_tables(driver, test_file_names, username, download_dir, timer)
get_grade_levels(username, password)

data_cleaning_functions - Cleans and processes the collected data:
shuffle_names(student_name)
cat_score_column_creator(test_frame, admin_username, student_frame, test_, cat_header)
get_category_scores(username, test_frame_folder)
combine_csv_files(username, test_frame_folder, combined_frame_folder)
add_date_data(combined_frame_folder, username)
combine_big_frames(big_frame_folder, grade_levels)
save_files_by_student(big_df)
save_files_by_class(big_df)

data_processing_functions - Processes the cleaned data to generate recommendations:
process_file(file_path)
processed_student_file_destination(processed_file_path, grade_level, subject, student_name, current_grade_level)
create_student_question_type_recommendations(input_folder_path)

data_visualization_functions - Generates visualizations based on the processed data:
plot_progress_by_test_group_with_embedded_keys(data, categories, test_groups, output_folder, subject, current_grade_level)
plot_student_progress_by_grade_level_with_embedded_keys(data, categories, test_groups, output_folder, student_name, subject, current_grade_level)
process_student_file(input_file, output_folder)
create_all_student_charts(input_directory, output_directory)

## License

This project is licensed under a Proprietary License. Unauthorized use, distribution, and modification of this software are strictly prohibited.

For permissions, please contact dalton.wilson.data@gmail.com.

