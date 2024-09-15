# ExtractPDF
### Trying to Extract Data from not-so-perfect PDF's

## About
### A little project dealing with information retreival from PDF documents.
For the time being I am only dealing with a single pdf at a time, eventually using this model for a batch procedure. I will upload all the major iteration changes I go through!

## Installation 
### 1. Dependencies
Install Dependencies using "pip install -r Dependencies.txt"

### 2. Download Tesseract OCR 
Use the "https://github.com/tesseract-ocr/tesseract/releases" repository (You will need it LOCALLY on your system for OCR).
You can get the Windows Installer from "https://github.com/UB-Mannheim/tesseract/wiki".

### 3. PATH
Enter path to your pdf in "pdf_path" in the declaration outside.
Add your Tesseract location to you PATH, or add your Tesseract PATH implicitly in the declared field.

### 4. Groq
Now before I started the project, I was convinced I could (obviously with the help of Github and Stackoverflow) get the PDF OCR running after using Tesseract. 
But boy o' boy was I wrong. 
Someone suggested me to try using AI, and well API keys don't come cheap. 

In comes Groq. I stumbled across a reddit thread which convinced me to use Groq, and so I did. You can read the documentation at "https://console.groq.com/docs/quickstart".

you need to run "export GROQ_API_KEY=<your-api-key-here>" on your terminal of choice. Use 'set' instead of 'export' if you are on CMD. I'd suggest using '$env:GROQ_API_KEY'="<your_api_key>". This worked for me.

![image](https://github.com/user-attachments/assets/889e8a6c-f621-480f-8270-0157384a1af6)

Many thanks to artworkjpm!

