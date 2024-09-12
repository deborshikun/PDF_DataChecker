import fitz 
from PIL import Image
import cv2
import numpy as np
import pytesseract

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

    #Trying to sharpen here
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(rotated, -1, kernel)

    return sharpened

def extract_text_from_image(img):
    text = pytesseract.image_to_string(img)  # Using Tesseract OCR to extract text
    return text

def extract_text_from_pdf(pdf_path):
    images = pdf_to_images(pdf_path)
    full_text = ""  
    # Processing each image
    for img in images:
        preprocessed_img = preprocess_image(img) 
        text = extract_text_from_image(preprocessed_img) 
        full_text += text + "\n" 

    return full_text 

# Example usage
pdf_path = r"C:\CERTIFICATES\03ecfa6c-d205-40b6-a690-e8c939ad32c7.pdf"
text = extract_text_from_pdf(pdf_path)  
print(text)
