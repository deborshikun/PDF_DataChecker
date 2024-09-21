#Now i just do the same for a batch folder~!
import fitz
from PIL import Image
import cv2
import numpy as np
import os
from groq import Groq
from google.cloud import vision
from google.oauth2 import service_account
import io

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
        {"role": "system","content": "You are a highly accurate assistant proficient in correcting OCR text. You only provide corrected text without adding any extra words, notes, or explanations.",
        "role": "user","content": f"""The following is extracted text from a PDF, containing character recognition errors. The text is in English, but errors might involve subject names and student details. Correct these errors based on context, translating where needed. You will encounter fields like 'English', 'Physics', 'Chemistry', 'Mathematics', 'Computer Science', 'Bengali', 'Hindi', and 'Biology'. These could also appear as 'ENGS', 'PHYS', 'CHEM', 'MATH', 'BIOS', 'BNGA', etc. Correct similar-looking characters (e.g., 'K' and 'R', '4' and '8'). Only output the following, in the exact format below: \n\n1. Student Name (on the first line) \n2. Registration Number/UID/Roll Number (on the second line) \n3. Full subject names with corresponding TOTAL marks beside it. \n\nDo not add any extra words, explanations, or notes. Maximum marks can always be 100. Just the corrected output.\n\n **Output Format** \nStudent Name: [Corrected Student Name]\n UID: [Corrected UID or Registration Number or Roll Number] \n[Subject1 Name]: [Total Marks]\n[Subject2 Name]: [Total Marks]\n ... \n\n **Example Output** \nStudent Name: Akshay Kumar Singh\nRegistration Number/UID/Roll Number: 7044450\nEnglish: 78/100\nHindi: 84/100\nMathematics: 63/100\nPhysics: 50/100\nChemistry: 55/100\nBiology: 59/100.\n\n Do not change this format. Just replace the placeholders with the corrected information. Here's the text to correct:\n\n {text}"""
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

folder_path = r"C:\CERTIFICATES"  # Folder containing PDFs 
process_pdfs_in_folder(folder_path)
