import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np
import pytesseract

# Function to convert each PDF page into images
def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF file
    images = []  # Store the images
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load each page
        pix = page.get_pixmap()  # Convert to a Pixmap
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Create a PIL image
        images.append(img)
    return images

# Function to preprocess the images (deskew and sharpen)
def preprocess_image(img):
    # Convert the image to grayscale
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    # Apply thresholding to binarize the image
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Deskew the image using its moments
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate the image to correct the skew
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Optional: Sharpen the image to improve clarity
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(rotated, -1, kernel)

    return sharpened

# Function to extract text from the preprocessed image
def extract_text_from_image(img):
    text = pytesseract.image_to_string(img)  # Use Tesseract OCR to extract text
    return text

# Main function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    images = pdf_to_images(pdf_path)  # Convert PDF pages to images
    full_text = ""  # To accumulate the extracted text

    # Process each image (i.e., each page)
    for img in images:
        preprocessed_img = preprocess_image(img)  # Preprocess the image
        text = extract_text_from_image(preprocessed_img)  # Extract text using OCR
        full_text += text + "\n"  # Add extracted text to the result

    return full_text  # Return the full extracted text

# Example usage
pdf_path = r"C:\CERTIFICATES\03ecfa6c-d205-40b6-a690-e8c939ad32c7.pdf"  # Provide your PDF path
text = extract_text_from_pdf(pdf_path)  # Call the function to extract text
print(text)  # Print the extracted text
