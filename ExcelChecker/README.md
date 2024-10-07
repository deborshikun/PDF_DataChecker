# Excel Data Extraction
### We want to create a data extractor  from Excel.
-------------------------------------------------

## About
#### A little project dealing with information retrieval from Excel documents.
For the time being, I am only dealing with a single txt file at a time, eventually using this model for a batch procedure. I will upload all the major iteration changes I go through!
My actual motive is to be able to extract marks from mark sheets from the database. These marks will be matched with the marksheet's marks provided as PDF 

## Installation 
#### 1. Dependencies
Install Pandas Numpy and openpyxl using 
```pip install pandas numpy openpyxl ```

#### 2. PATH
Enter the path to your Excel file in ```excel_file_path``` in the declaration outside.

Enter the path to your OCR corrected output text files folder in ```corrected_folder``` in the declaration outside.

#### 3. Working Flow Flag Representation
For each OCR corrected output text file we check the NAME, REGISTRATION NO., SUBJECT marks with the Excel database.
After checking it will generate a flag which will be stored in the Excel database and a discrepancy log file for each mismatched data.

Flag will be <= 4 digit number _ _ _ _ , these digit represents the following things:

x x 0 0 : OCR contains less data due poor quality of the pdf.

x x 0 1 : This means either data of the OCR text or in the Excel data the subject marks got interchanged so this requires a manual review.

x x 1 0 : This means the PDF's marks and excel database's marks have matched.

x 0 x x : This means the PDF's student name and the Excel database's student name have not matched.

x 1 x x : This means the PDF's student name and the Excel database's student name have matched.

0 x x x : This means the PDF's registration no and Excel database's registration no have not matched.

1 x x x : This means the PDF's registration no and Excel database's registration no have matched.

Example :

Flag = 1010 means registration no and marks have matched but the student's name is not matching.

Flag = 1101 means registration no and student's name have matched but the student's marks might be interchanged.

Flag = 1110 means all data have matched.


-------------------------------------------------
