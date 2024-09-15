import pandas as pd

def extract_student_data(file_path, user_hsregno):
    # Load the Excel file
    xls = pd.ExcelFile(file_path)
    
    # Load the EXAM DTLS sheet into a dataframe
    df_exam = pd.read_excel(xls, sheet_name='EXAM DTLS')
    
    # Print column names to verify
    #print("Column names in EXAM DTLS sheet:", df_exam.columns)
    
    # Find the student's exam details from the EXAM DTLS sheet
    exam_info = df_exam[df_exam['HsRegNo'] == user_hsregno]
    
    if exam_info.empty:
        print("No exam details found for the given HsRegNo.")
        return
    
    exam_data = exam_info.iloc[0]
    
    # Extract exam details (verify column names here)
    student_name = exam_data.get('StudentNm', 'Not Found')
    board_council_nm = exam_data.get('BoardCouncilNm', 'Not Found')
    lang1 = exam_data.get('Lang1', 'Not Found')
    lang2 = exam_data.get('Lang2', 'Not Found')
    physics = exam_data.get('Physics', 'Not Found')
    chemistry = exam_data.get('Chemistry', 'Not Found')
    mathematics = exam_data.get('Mathematis', 'Not Found')
    biology = exam_data.get('Biology', 'Not Found')
    computer_sc = exam_data.get('ComputerSc', 'Not Found')
    total_marks = exam_data.get('TotalMarks', 'Not Found')
    
    # Print or return the extracted data
    print(f"Student Name: {student_name}")
    print(f"Board Council Name: {board_council_nm}")
    print(f"Lang1: {lang1}")
    print(f"Lang2: {lang2}")
    print(f"Physics: {physics}")
    print(f"Chemistry: {chemistry}")
    print(f"Mathematics: {mathematics}")
    print(f"Biology: {biology}")
    print(f"Computer Science: {computer_sc}")
    print(f"Total Marks: {total_marks}")

# Example usage
excel_file_path = r"C:\Users\hp\OneDrive\Desktop\MAKAUT\CERAMIC COLLEGE.xlsx"  # Replace with your Excel file path
hs_reg_no_input = "7131078" # User input for HsRegNo
extract_student_data(excel_file_path, hs_reg_no_input)
