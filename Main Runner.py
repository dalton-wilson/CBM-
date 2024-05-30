from cbm_login_functions import login
from progressor_functions import nav_to_tables
from progressor_functions import change_timer_value
from progressor_functions import check_and_fill_data
from cbm_site_data_collection_functions import save_test_date_data
from cbm_site_data_collection_functions import write_test_tables
from cbm_site_data_collection_functions import write_student_tables
from cbm_site_data_collection_functions import get_grade_levels
from data_cleaning_functions import get_category_scores
from data_cleaning_functions import combine_csv_files
from data_cleaning_functions import add_date_data
from data_cleaning_functions import combine_big_frames
from data_cleaning_functions import save_files_by_student
from data_cleaning_functions import save_files_by_class
from data_processing_functions import create_class_question_type_recommendations
from data_processing_functions import create_student_question_type_recommendations
from data_visualization_functions import create_all_class_charts
from data_visualization_functions import create_all_student_charts


def data_collector(timer):
    while True:
        logged_in_driver, un, pw, combined_frames_folder = login()
        tables_driver = nav_to_tables(logged_in_driver)
        date_data_saved_driver = save_test_date_data(tables_driver, combined_frames_folder, timer)
        test_file_names, extracted_data_frames_folder = write_test_tables(date_data_saved_driver, un, timer)
        check_and_fill_data(extracted_data_frames_folder)
        tests_written_driver = nav_to_tables(tables_driver)
        student_tables_written_driver = write_student_tables(tests_written_driver, test_file_names, un,
                                                             extracted_data_frames_folder, timer)
        single_test_frames_folder = get_category_scores(un, test_file_names)
        combine_csv_files(un, single_test_frames_folder, combined_frames_folder)
        processed_files_folder = add_date_data(combined_frames_folder, un)
        student_tables_written_driver.quit()

        additional_login = input("Do you have any additional EasyCBM logins for your school? yes/no: ")
        if additional_login.lower() != 'yes':
            break
    return processed_files_folder, un, pw


def process_data():
    timer = 1
    while True:
        try:
            folder, un, pw = data_collector(timer)
            grade_levels = get_grade_levels(un, pw)
            big_df = combine_big_frames(folder, grade_levels)
            class_file_folder = save_files_by_class(big_df)
            student_file_folder = save_files_by_student(big_df)
            processed_files_folder_class = create_all_class_charts(class_file_folder)
            create_class_question_type_recommendations(class_file_folder)
            processed_files_folder = create_all_student_charts(student_file_folder, processed_files_folder_class)
            create_student_question_type_recommendations(student_file_folder)
            print("Data processing complete. Check the 'Processed Frames by Class' folder in your File Explorer to view"
                  " your testing data.")
            return processed_files_folder  # If successful, return and exit
        except ValueError:
            print("A ValueError occurred. Attempting to adjust timer and retry...")
            timer = change_timer_value()  # Adjust timer if needed


process_data()
