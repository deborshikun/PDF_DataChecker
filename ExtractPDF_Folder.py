import fitz
from PIL import Image
import cv2
import numpy as np
import pytesseract
import os
import re

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def preprocess_image(img):
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
    
    try: #because Tessearct don't understand Orientation
        # Detect text orientation using Tesseract
        osd = pytesseract.image_to_osd(rotated)
        rotate_angle = int(re.search(r"Rotate: (\d+)", osd).group(1))

        # Handle horizontal orientation (90 degrees or 270 degrees rotation)
        if rotate_angle == 90:
            rotated = cv2.rotate(rotated, cv2.ROTATE_90_CLOCKWISE)
        elif rotate_angle == 270:
            rotated = cv2.rotate(rotated, cv2.ROTATE_90_COUNTERCLOCKWISE)

    except Exception as e:
        print(f"Error during OSD detection: {e}")
        # Fallback to assuming image is in the correct orientation
        pass
    
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(rotated, -1, kernel)

    return sharpened

def extract_text_from_image(img):
    text = pytesseract.image_to_string(img)
    return text

def extract_text_from_pdf(pdf_path):
    images = pdf_to_images(pdf_path)
    full_text = ""
    for img in images:
        preprocessed_img = preprocess_image(img)
        text = extract_text_from_image(preprocessed_img)
        full_text += text + "\n"
    return full_text

def process_folder(folder_path):
    base_folder_name = os.path.basename(folder_path.rstrip("\\/"))  # Get the name of the folder
    output_folder = os.path.join(os.path.dirname(folder_path), f"{base_folder_name}_output")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"Processing {pdf_path}...")
            text = extract_text_from_pdf(pdf_path)
            
            base_name = os.path.splitext(filename)[0] 
            output_file_path = os.path.join(output_folder, f"{base_name}.txt")
            
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(text)
            print(f"Text has been extracted and saved to {output_file_path}")
            
# Example usage
folder_path = r"C:\CERTIFICATES"  # Folder containing PDFs
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files (Softwares)\Python\Tesseract\tesseract.exe'  # Tesseract PATH
process_folder(folder_path)
