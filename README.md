# PDF Data Checker
### We want to create a data extractor and checker from PDF with a local database (mostly Excel in this case).
-------------------------------------------------

## ExtractPDF
#### Trying to Extract Data from not-so-perfect PDFs

## About
#### A little project dealing with information retrieval from PDF documents.
For the time being, I am only dealing with a single pdf at a time, eventually using this model for a batch procedure. I will upload all the major iteration changes I go through!
My actual motive is to be able to extract marks from mark sheets taken by students. These mark sheets might be taken in various orientations and could involve many real-world problems.

## Installation 
#### 1. Dependencies
Install Dependencies using 
```pip install -r Dependencies.txt```

#### 2. Download Tesseract OCR 
Use the *https://github.com/tesseract-ocr/tesseract/releases* repository (You will need it LOCALLY on your system for OCR).
You can get the Windows Installer from *https://github.com/UB-Mannheim/tesseract/wiki* directly.

#### 3. PATH
Enter the path to your pdf in ```pdf_path``` in the declaration outside.
Add your Tesseract location to your PATH, or add your Tesseract PATH implicitly in the declared field.

-------------------------------------------------

#### Even with all this, I had trouble finding meaningful output using Tesseract OCR. 
An error I received a lot was ```Error during OSD detection: (1, 'Estimating resolution as 346 <could be any number here between ranges 0 to 400 according to my observations> Warning. Invalid resolution 0 dpi. Using 70```
I only found 1 solution to the issue, which is more like a "bypass" rather than a cure. Thanks to Esraa anyhow!

![image](https://github.com/user-attachments/assets/69b335cf-f524-4ca4-8b36-802ca6291acc)

Let me share a sample input and output of one such case:

Input:

![image](https://github.com/user-attachments/assets/c23b91af-1404-42a1-9dd4-f08ee3280600)  

Output:

![image](https://github.com/user-attachments/assets/dd1677cf-e5ba-46cf-b687-3b3f9f682a40)

Not too great right?

#### 4. Groq
Now before I started the project, I was convinced I could (obviously with the help of Github and Stackoverflow) get the PDF OCR running after using Tesseract. 
I couldn't have possibly been more incorrect.
Someone suggested I try using AI, and well API keys don't come cheap. 

In comes Groq. I stumbled across a Reddit thread that convinced me to use Groq, and so I did.
You can read the documentation at *https://console.groq.com/docs/quickstart* directly.

You need to run ```export GROQ_API_KEY=<your-api-key-here>``` on your terminal of choice. Use ```set``` instead of ```export``` if you are on CMD. 
I'd suggest using ```$env:GROQ_API_KEY="<your_api_key>"``` because this worked for me.

![image](https://github.com/user-attachments/assets/889e8a6c-f621-480f-8270-0157384a1af6)

Many thanks to artworkjpm!

The main purpose of Groq is to use llama for any correction of the bad output from Tesseract OCR. 
This is where I hit a brick wall, as even with Groq the error bound was quite substantial. 

I had to change my approach to the OCR itself.

#### 5. Google Cloud Vision API
The strongest tool available to us - Google Cloud Vision API. This is famously used in image detection, mainly in Google Lens. So I had to give it a shot.
as always, you can read the documentation and the guides over at *https://cloud.google.com/vision/docs/how-to*.

Just like Groq, you need to set an environment variable ```GOOGLE_APPLICATION_CREDENTIALS``` . You can refer to ```Point 4```, or just simply use ```$env:GOOGLE_APPLICATION_CREDENTIALS="<your_api_key>"```.
You also need to create an "Application Credential Secret Key" from Google Cloud, which will authenticate your API use. This is going to be a .json download. You must specify the .json path in the ```credentials``` section of the code.
For more clarification on the process, you can refer to this video: *https://www.youtube.com/watch?v=TTeVtJNWdmI*. You can open your .json key and get the ```private_key_id```. This ID is to be used for the environment variable!

Now with the help of both llama3-8b and Vision AI, let me share a sample IO:

Input:

![image](https://github.com/user-attachments/assets/28edf135-52b1-4e64-aa37-1ab1ce84a2a4)

Output:

![image](https://github.com/user-attachments/assets/e21cdfd2-2b78-4811-9f2a-6343332d74f2)

#### That is almost Perfection! Now I just need to tweak the prompt a bit for Groq and we are golden!

With this, I conclude the "ExtractPDF" portion.

-------------------------------------------------

## Installation

### 1) Dependencies
Install the required libraries using the following command:
```bash
  pip install pandas numpy openpyxl
```
 ### 2)File Path
 i)Specify the path to your Excel file in the variable excel_file_path in the code. 

 ii)Specify the path to the folder containing OCR-corrected output text files in the variable corrected_folder.
 ### 3) Workflow and Flag Representation
  For each OCR-corrected output text file, the script will:

i)Validate the NAME, REGISTRATION NUMBER, and SUBJECT MARKS by comparing them with the data in the Excel database.

ii)Generate a flag based on the comparison results, which will be stored in the Excel database.

iii)Create a discrepancy log for any mismatched data.
#### Flag Representation System
The flag will be a 4-digit number ( _ _ _ _ ), where each digit represents the following:

x x 0 0: OCR output contains less data due to the poor quality of the PDF.

x x 0 1: Data mismatch—subject marks may have been interchanged between OCR output and Excel data. Requires manual review.

x x 1 0: Marks match between the PDF and Excel database.

x 0 x x: The student name does not match between the OCR output and the Excel database.

x 1 x x: The student name matches between the OCR output and the Excel database.

0 x x x: The registration number does not match between the OCR output and the Excel database.

1 x x x: The registration number matches between the OCR output and the Excel database.
#### Example Flags:
Flag = 1010: The registration number and marks match, but the student’s name does not match.

Flag = 1101: The registration number and student’s name match, but the marks may have been interchanged.

Flag = 1110: All data match (registration number, student name, and marks).

-------------------------------------------------

