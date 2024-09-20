import fitz
from PIL import Image
import cv2
import numpy as np
import os
from groq import Groq
from google.cloud import vision
from google.oauth2 import service_account
import io
import pandas as pd
import re
from difflib import get_close_matches


subject_mapping = {
    "English": ["ENG", "ENGS", "ENGLISH"],
    "Hindi": ["HIN", "HINDI"],
    "Bengali": ["BEN", "BENG", "BENGALI"],
    "Physics": ["PHYS", "PHY", "PHYSICS"],
    "Chemistry": ["CHEM", "CHE", "CHEMISTRY"],
    "Mathematics": ["MATH", "MAT", "MATHEMATICS"],
    "Biology": ["BIO", "BIOLOGY"],
    "ComputerScience": ["CS", "COMPSC", "COMPUTER SCIENCE"]
}
# Set up Google Vision client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'<json file name for Secret Key>.json'
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\...\<json file name for Secret Key>.json') #Add path of .json file with filename.json 
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

'''def preprocess_image(img):
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(rotated, -1, kernel)

    return sharpened
'''
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
        {"role": "system", "content": "You are a very helpful and assistant that is proficient in helping correct OCR text. You only answer the prompts to the point and do not add any extra notes.",
        "role": "user", "content": f"""The following is a extracted text from a PDF, which mainly has character recognition errors. 
        The entire PDF's are in English language, so you can try to translate the text to English and use your best judgement for the correction.
        The only fields you will face are 'English' 'Physics' 'Chemistry' 'Mathematics' 'Computer Science' 'Bengali' 'Hindi' 'Biology', which could also be represented in some pdf's as 'BNGA' for Bengali, 'ENGS' for English, 'BIOS' for Biology, 'CHEM' for Chemistry, 'PHYS' for Physics, etc, and 'MATH' for Mathematics.
        Do double check the characters which might look similar to another character (like K and R, 4 and 8, R and H).
        ONLY give me the student name on 1st line, the registration number/Unique ID (UID)/Roll number on 2nd line, the subject name with the corresponding marks in the next lines.
        Do not add any notes apart from what I asked.\n\n{text}"""}
    ],
        model="llama3-8b-8192"
    )
    return response.choices[0].message.content

def process_pdfs_in_folder(folder_path,excel_file_path):
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

            #txt_process_folder(file_name,excel_file_path,corrected_text)
            extract_student_data(excel_file_path, file_name,corrected_text)
            print(f"Corrected text has been saved to {output_file_path}")


def extract_student_data(file_path, user_certificate,text):
    # Load the Excel file
    xls = pd.ExcelFile(file_path)
    
    # Load the EXAM DTLS sheet into a dataframe
    df_exam = pd.read_excel(xls, sheet_name='EXAM DTLS')
    df_stud = pd.read_excel(xls, sheet_name='BASIC DTLS')
    # Print column names to verify
    #print("Column names in EXAM DTLS sheet:", df_exam.columns)
    
    # Find the student's exam details from the EXAM DTLS sheet
    exam_info = df_exam[df_exam['UploadCertificate'] == user_certificate]
    
    if exam_info.empty:
        print("No exam details found for the given certificate.")
        return
    
    exam_data = exam_info.iloc[0]
    
    ref = exam_data.get('RefNo', 'Not Found')
    #print(f"RefNo: {ref}")
    stud_info = df_stud[df_stud['RefNo'] == ref]
    if stud_info.empty:
        print("No exam details found for the given certificate.")
        #return
    
    stud_data = stud_info.iloc[0]
    # Extract exam details (verify column names here)
    
    student_name = stud_data.get('StudentNm', 'Not Found')
    board_council_nm = exam_data.get('BoardCouncilNm', 'Not Found')
    lang1 = exam_data.get('Lang1', 'Not Found')
    lang2 = exam_data.get('Lang2', 'Not Found')
    physics = exam_data.get('Physics', 'Not Found')
    chemistry = exam_data.get('Chemistry', 'Not Found')
    mathematics = exam_data.get('Mathematis', 'Not Found')
    biology = exam_data.get('Biology', 'Not Found')
    computer_sc = exam_data.get('ComputerSc', 'Not Found')
    total_marks = exam_data.get('TotalMarks', 'Not Found')
    HsRegNo = exam_data.get('HsRegNo', 'Not Found')
    result = check_strings_in_text(text, student_name, HsRegNo)
    marks = extract_marks_from_text(text)
    if result[0] == 1 and result[1] == 1:
        if(marks["Physics"] == physics and marks["Chemistry"] == chemistry and marks["Mathematics"] == mathematics and marks["Biology"] == biology and marks["Computer Science"] == computer_sc and marks["English"] == lang2 and (marks["Hindi"] == lang1 or marks["Bengali"]==lang1)):
            df_exam.loc[df_exam['UploadCertificate'] == user_certificate,'Flag'] = 1
            with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
                df_exam.to_excel(writer, sheet_name='EXAM DTLS', index=False)
            df_stud.loc[df_stud['RefNo'] == ref,'Flag'] = 1
            with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
                df_stud.to_excel(writer, sheet_name='BASIC DTLS', index=False)
    
    flag = exam_data.get('Flag','Not Found')
    
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
    print(f"Flag: {flag}")
    
def txt_process_folder(filename,excel_file_path,text):    
    if filename.endswith(".txt"):
        pdf_path = os.path.join(folder_path, filename)
        certificate = filename[:-14] + '.pdf'            
        extract_student_data(excel_file_path, certificate,text)



# Flatten the subject mapping for reverse lookups
abbreviation_to_subject = {}
for subject, abbrevs in subject_mapping.items():
    for abbrev in abbrevs:
        abbreviation_to_subject[abbrev.lower()] = subject

# Function to find the closest match with 70% similarity
def find_closest_subject(word, abbreviation_to_subject):
    match = get_close_matches(word.lower(), abbreviation_to_subject.keys(), n=1, cutoff=0.7)  # 70% similarity cutoff
    return abbreviation_to_subject[match[0]] if match else None

# Function to extract marks from "Theory: xx Practical: xx Total: xx" format
def extract_detailed_marks(block):
    theory_marks = practical_marks = total_marks = None
    theory_match = re.search(r'Theory: ?(\d+)', block)
    practical_match = re.search(r'Practical: ?(\d+)', block)
    total_match = re.search(r'Total: ?(\d+)', block)

    if theory_match:
        theory_marks = int(theory_match.group(1))
    if practical_match:
        practical_marks = int(practical_match.group(1))
    if total_match:
        total_marks = int(total_match.group(1))
    else:
        # If total is not provided, sum theory and practical
        if theory_marks is not None and practical_marks is not None:
            total_marks = theory_marks + practical_marks

    return total_marks

# Function to extract subject marks from text
def extract_marks_from_text(text):
    subject_marks = {subject: 0 for subject in subject_mapping.keys()}  # Initialize all subjects with 0 marks

    # Split the text into lines
    lines = text.splitlines()

    current_block = ""
    current_subject = None

    for line in lines:
        # Detect "Subject - Marks" format (e.g., "ENGLISH - 88")
        simple_match = re.match(r'([A-Za-z\s]+)\s*-\s*(\d+)', line)
        if simple_match:
            subject_name = simple_match.group(1).strip()
            marks = int(simple_match.group(2))
            
            # Find closest matching subject
            subject = find_closest_subject(subject_name, abbreviation_to_subject)
            if subject:
                subject_marks[subject] = marks
            continue

        # Check for detailed subject format (e.g., "ENGLISH Theory: 60 Practical: 20 Total: 80")
        for word in re.findall(r'\w+', line):
            subject = find_closest_subject(word, abbreviation_to_subject)
            if subject:
                if current_subject:
                    subject_marks[current_subject] = extract_detailed_marks(current_block)
                current_subject = subject
                current_block = ""

        # Add lines to current block for detailed format
        current_block += line + "\n"

    # Process the last block if there's one
    if current_subject:
        subject_marks[current_subject] = extract_detailed_marks(current_block)

    return subject_marks

def check_strings_in_text(text, string1, string2):
    # Convert text to lowercase to make the search case-insensitive
    text_lower = text.lower()
    
    # Check for presence of each string in the text
    is_string1_present = string1.lower() in text_lower
    is_string2_present = string2.lower() in text_lower

    return is_string1_present, is_string2_present






folder_path = r"C:\CERTIFICATES"  # Folder containing PDFs 
excel_file_path = r"C:\Users\hp\OneDrive\Desktop\MAKAUT\CERAMIC COLLEGE.xlsx"  # Replace with your Excel file path
process_pdfs_in_folder(folder_path,excel_file_path)
#txt_process_folder(txt_output_path,excel_file_path,text)