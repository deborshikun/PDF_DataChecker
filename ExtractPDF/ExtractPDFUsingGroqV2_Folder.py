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
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'regal-wall-428907-e1-8e4643c33092.json'
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Deborshi Chakrabarti\Desktop\Extract PDF Project\regal-wall-428907-e1-8e4643c33092.json')
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
