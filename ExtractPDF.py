#Now i just do the same for a batch folder~!
import fitz
from PIL import Image
import cv2
import numpy as np
import pandas as pd
import os
from groq import Groq
from google.cloud import vision
from google.oauth2 import service_account
import io
import re
from difflib import get_close_matches

# Set up Google Vision client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'<your .json filename>.json'
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Deborshi Chakrabarti\Desktop\Extract PDF Project\<your .json filename>.json')
client = vision.ImageAnnotatorClient(credentials=credentials)

# Groq Llama API client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"),)

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def extract_text_from_image(img):
    # If img is a NumPy array, convert it back to a PIL image
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    
    # Convert the PIL image to bytes in PNG format
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    vision_image = vision.Image(content=img_bytes)     # Use Google Vision API to extract text
    response = client.text_detection(image=vision_image)
    
    # Get text
    text = response.full_text_annotation.text if response.full_text_annotation else ''
    
    return text

def extract_text_from_pdf(pdf_path):
    images = pdf_to_images(pdf_path)
    full_text = ""
    for img in images:
        #preprocessed_img = preprocess_image(img)
        text = extract_text_from_image(img) #used to be preprocessed_img in place of img but it was causing more faults.
        full_text += text + "\n"
    return full_text

def correct_extracted_text(text):
    response = groq_client.chat.completions.create(
        messages=[
        {"role": "system","content": "You are a highly accurate assistant proficient in correcting OCR text. You only provide corrected text without adding any extra words, notes, or explanations.",
        "role": "user","content": f"""The following is extracted text from a PDF, containing character recognition errors. The text is in English, but errors might involve subject names and student details. Correct these errors based on context, translating where needed. You will encounter fields like 'English', 'Physics', 'Chemistry', 'Mathematics', 'Computer Science', 'Bengali', 'Hindi', and 'Biology'. These could also appear as 'ENGS', 'PHYS', 'CHEM', 'MATH', 'BIOS', 'BNGA', etc. Correct similar-looking characters (e.g., 'K' and 'R', '4' and '8'). Only output the following, in the exact format below: \n\n1. Student Name (on the first line) \n2. Regn.No. (for West Bengal Students) OR UID (on the second line) \n3. Full subject names with corresponding TOTAL marks beside it. \n\nDo not add any extra words, explanations, or notes. Maximum marks can always be 100. You can read the total in words given beside or below the numeric marks, to check the TOTAL marks. Just the corrected output.\n\n **Output Format** \nStudent Name: [Corrected Student Name]\nUID: [Corrected UID]\n[Subject1 Name]: [Total Marks]\n[Subject2 Name]: [Total Marks]\n ... \n\n Do not change this format. Just replace the placeholders with the corrected information. Here's the text to correct:\n\n {text}"""
        }
    ],
        model="llama3-8b-8192"
    )
    return response.choices[0].message.content

def process_pdfs_in_folder(folder_path):
    base_folder_name = os.path.basename(folder_path.rstrip("\\/"))  # Getting folder name
    output_folder = os.path.join(os.path.dirname(folder_path), f"{base_folder_name}_output")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file_name)
            print(f"Processing {pdf_path}...")

            extracted_text = extract_text_from_pdf(pdf_path)
            corrected_text = correct_extracted_text(extracted_text)

            base_name = os.path.splitext(file_name)[0]
            output_file_path = os.path.join(output_folder, f"{base_name}_corrected.txt")

            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(corrected_text)

            print(f"Corrected text has been saved to {output_file_path}")
    return output_folder

# Subject mapping defined by you earlier
subject_mapping = {
    "lang1": ["ENG", "ENGS", "ENGLISH", "ENGB","HIN", "HINDI","BEN", "BENG", "BENGALI", "BNGA","Marathi"],
    "Physics": ["PHYS", "PHY", "PHYSICS"],
    "Chemistry": ["CHEM", "CHE", "CHEMISTRY"],
    "Mathematics": ["MATH", "MAT", "MATHEMATICS"],
    "Biology": ["BIO", "BIOLOGY", "BIOS"],
    "Computer Science": ["CS", "COMPSC", "COMPUTER SCIENCE"],
    "Commerce": ["COMS", "COMM", "COMMERCE"]
}
# Load Excel data
def load_excel_data(file_path):
    df_exam = pd.read_excel(file_path, sheet_name='EXAM DTLS')
    df_stud = pd.read_excel(file_path, sheet_name='BASIC DTLS')
    return df_exam, df_stud

# Parse corrected text from text file
def parse_txt_file(file_path):
    """Parse the text file to extract student name, UID, and marks."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    student_name = None
    uid = None
    marks = {}

    # Loop through all lines to find Student Name and UID dynamically
    for line in lines:
        # Search for Student Name
        if "Student Name:" in line:
            student_name_match = re.search(r"Student Name:\s*(.*)", line)
            if student_name_match:
                student_name = student_name_match.group(1).strip()

        # Search for UID
        if "UID:" in line:
            uid_match = re.search(r"UID:\s*(.*)", line)
            if uid_match:
                uid = uid_match.group(1).strip()

        # Search for subjects and their marks
        if ':' in line:
            parts = line.split(':', 1)  # Limit to 1 split to avoid unpacking issues
            subject = parts[0].strip()
            mark = parts[1].strip()
            # Handle cases where 'mark' might not be a valid integer
            try:
                marks[subject] = int(mark)
            except ValueError:
                marks[subject] = None  # Assign None or handle this case appropriately

    return student_name, uid, marks
# Function to get the correct subject name from the mapping
def get_subject_from_mapping(ocr_subject):
    # Check if the OCR subject matches any of the known abbreviations in subject_mapping
    for full_subject, abbreviations in subject_mapping.items():
        if ocr_subject in [abbr.lower() for abbr in abbreviations]:
            return full_subject
    return ocr_subject  # Return as-is if no match found

# Helper to handle Lang1 and Lang2 subject mapping
def get_language_subject_mapping(exam_record):
    """Determine the possible subjects for Lang1 and Lang2 from the exam record."""
    lang1 = exam_record['Lang1']
    lang2 = exam_record['Lang2']
    
    language_subjects = {}
    
    # Use the subject_mapping to identify possible languages for Lang1 and Lang2
    for lang_code, lang_value in {"LANG1": lang1, "LANG2": lang2}.items():
        for full_subject, abbreviations in subject_mapping.items():
            if str(lang_value).strip().lower() in [abbr.lower() for abbr in abbreviations]:
            #if lang_value.strip().lower() in [abbr.lower() for abbr in abbreviations]:
                language_subjects[lang_code] = full_subject

    return language_subjects

# Improved "HsRegNo" detection based on BoardCouncilNm
def detect_reg_no_by_board(exam_record):
    """Improves HsRegNo detection by considering BoardCouncilNm and expected patterns."""
    board_name = exam_record['BoardCouncilNm'].strip().lower()  # case-insensitive comparison
    hs_reg_no = exam_record['HsRegNo'].strip().lower()
    
    if 'west bengal council of higher secondary education' in board_name:
        if re.match(r'^\d{10}$', hs_reg_no):
            return hs_reg_no
        else:
            return None  # Missing or invalid RegNo case
    
    if 'council for the indian school certificate examinations' in board_name:
        if re.match(r'^\d{7}$', hs_reg_no):
            return hs_reg_no
    
    if 'central board of secondary education' in board_name:
        if re.match(r'^B\d{3}\/\d{5}\/\d{4}$', hs_reg_no):
            return hs_reg_no
    
    if 'bihar school examination board' in board_name:
        if re.match(r'^R-\d{9}-\d{2}$', hs_reg_no):
            return hs_reg_no
    
    if 'maharashtra state board of secondary and higher secondary education' in board_name:
        if re.match(r'^H\d{9}$', hs_reg_no):
            return hs_reg_no
    
    return hs_reg_no  # If no specific board conditions matched, return as is.

# Compare marks from text with Excel data
def compare_marks(parsed_marks, excel_marks, language_subjects):
    exact_match = True
    swapped = True
    total_txt_marks = sum(mark for mark in parsed_marks.values() if mark is not None)
    total_excel_marks = sum(excel_marks.values())
    count=0

    for ocr_subject, ocr_mark in parsed_marks.items():
        if(count<3):
            count+=1
            continue
        subject = get_subject_from_mapping(ocr_subject.lower())  # OCR subject to lowercase
        print(f"Comparing {ocr_subject} with {subject}")
        # Handle Lang1 and Lang2 flexibility
        lang1_mark = excel_marks.get('lang1', None)
        lang2_mark = excel_marks.get('lang2', None)
        subject=subject.lower()
        if subject == "lang1":
            # Check if marks match either Lang1 or Lang2
            if ocr_mark == lang1_mark or ocr_mark == lang2_mark:
                print("matched")
                continue  # Continue to next subject if matched
            else:
                exact_match = False
                print(ocr_mark, lang1_mark, lang2_mark)
                print("not matched")
        else:
            for subj in excel_marks.keys():
                # print(subj)
                if subject == subj.lower():  # Excel subject keys as lowercase
                    excel_mark = excel_marks[subject]
                    print(ocr_mark)
                    print(excel_mark)
                    if ocr_mark != excel_mark:
                        exact_match = False                        
                        print("not matched")
                        continue
                    # swapped &= excel_mark in parsed_marks.values()  # If marks exist but may be swapped
                    print("matched")
                    continue
                
            # exact_match = False


    # Flag conditions
    if exact_match:
        return 10  # All marks are correct
    else:
        return generate_flags(excel_marks, parsed_marks)

def generate_flags(excel_marks, parsed_marks):
    print(excel_marks)
    print(parsed_marks)
    excel_mark_values = [mark for mark in excel_marks.values() if mark is not None]
    parsed_mark_values = [mark for mark in parsed_marks.values() if mark is not None]

    # Count the number of matches in marks, ignoring subjects
    count_similar_marks = sum(1 for mark in excel_mark_values if mark in parsed_mark_values)

    print(f"Count of Similar Marks: {count_similar_marks}")

    # Return flag based on the count of similar marks
    if count_similar_marks >= 5:
        return 1
    else:
        return 0
# Process txt files in folder and compare with Excel
def process_txt_files_in_folder(txt_folder, excel_file):
    xls = pd.ExcelFile(excel_file)
    df_exam = pd.read_excel(xls, sheet_name='EXAM DTLS')
    df_stud = pd.read_excel(xls, sheet_name='BASIC DTLS')

    for txt_file in os.listdir(txt_folder):
        if txt_file.endswith('.txt'):
            print(txt_file)
            filename = txt_file.replace("_corrected.txt",".pdf")
            student_name, uid, parsed_marks = parse_txt_file(os.path.join(txt_folder, txt_file))
            exam_info = df_exam[df_exam['UploadCertificate'] == filename]
            if exam_info.empty:
                print(f"No exam info found for certificate: {filename}")
                continue
            exam_data = exam_info.iloc[0]
    
            ref = exam_data.get('RefNo', 'Not Found')
            stud_info = df_stud[df_stud['RefNo'] == ref]
            if stud_info.empty:
                print("No exam details found for the given certificate.")
                continue
            
            stud_data = stud_info.iloc[0]
            discrepancies = []

            # Get language subjects mapping
            language_subjects = get_language_subject_mapping(exam_data)

            # Detect HsRegNo based on board
            detected_hsregno = detect_reg_no_by_board(exam_data)

            # Ensure that both uid and detected_hsregno are valid and not None before comparing
            if detected_hsregno and uid:
                if detected_hsregno.strip().lower() != uid.strip().lower():
                    discrepancies.append(f"Mismatch in HsRegNo: {uid} (Excel) vs {detected_hsregno} (Detected)")
            else:
                discrepancies.append(f"UID or HsRegNo is missing for certificate: {filename}")

            exam_marks = {
                'lang1': exam_data.get('Lang1', 'Not Found'),
                'lang2': exam_data.get('Lang2', 'Not Found'),
                'mathematics': exam_data.get('Mathematis', 'Not Found'),  # Ensure this is not a typo
                'physics': exam_data.get('Physics', 'Not Found'),
                'chemistry': exam_data.get('Chemistry', 'Not Found'),
                'biology': exam_data.get('Biology', 'Not Found'),
                'computer science': exam_data.get('ComputerSc', 'Not Found'),
            }
            name = exam_data.get('StudentNm', 'Not Found')
            regno = exam_data.get('HsRegNo', 'Not Found')
            nf = True
            nr = True
            
            # Compare marks
            flag = compare_marks(parsed_marks, exam_marks, language_subjects)
            print(flag)
            n = parsed_marks.get('Student Name', 'Not Found')
            r = parsed_marks.get('UID', 'Not Found')
            r = str(r)
            if n is None:
                n = 'Not Found'
            if r is None:
                r = 'Not Found'
            
            if(name.lower() != n.lower()):
                nf = False
            if(regno.lower() != r.lower()):
                nr = False
            if(nf and nr):
                flag += 1100
            elif(nf):
                flag += 100
            elif(nr):
                flag += 1000

            if flag == 0:
                print(f"Mismatch in marks , name and regno for {student_name}, UID: {uid}")
                discrepancies.append("Mismatch in all.")
            df_exam.loc[df_exam['UploadCertificate'] == filename,'Flag'] = flag
            with pd.ExcelWriter(excel_file, mode='a', if_sheet_exists='replace') as writer:
                df_exam.to_excel(writer, sheet_name='EXAM DTLS', index=False)
            df_stud.loc[df_stud['RefNo'] == ref,'Flag'] = flag
            with pd.ExcelWriter(excel_file, mode='a', if_sheet_exists='replace') as writer:
                df_stud.to_excel(writer, sheet_name='BASIC DTLS', index=False)
            # Log discrepancies if any
            if discrepancies:
                with open(log_file_path, 'a') as log_file:
                    log_file.write(f"Discrepancies for {student_name}, UID: {uid}:\n" + "\n".join(discrepancies) + "\n")

    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        print("File is getting written to Flag")
        df_exam.to_excel(writer, sheet_name='EXAM DTLS', index=False)
        df_stud.to_excel(writer, sheet_name='BASIC DTLS', index=False)

excel_file_path = r"C:\Users\Deborshi Chakrabarti\Desktop\Extract PDF Project\CERAMIC COLLEGE.xlsx"
log_file_path = r"C:\Users\Deborshi Chakrabarti\Desktop\Extract PDF Project\discrepancy_log.txt"
pdf_folder_path = r"C:\CERTIFICATES"
corrected_folder = process_pdfs_in_folder(pdf_folder_path)
process_txt_files_in_folder(corrected_folder, excel_file_path)
