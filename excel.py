import re

file_path = r'C:\CERTIFICATES_output\1768e364-b991-416a-af19-b2c4d2d50e49_corrected.txt'


with open(file_path, 'r') as file:
    input_text = file.read()


name_pattern = r'Student Name:\s(.+)'    
uid_pattern = r'UID:\s(\d+)'            
marks_pattern = r'(\w+\s?\w*):\s(\d+)'   


student_name = re.search(name_pattern, input_text).group(1)
uid = re.search(uid_pattern, input_text).group(1)


matches = re.findall(marks_pattern, input_text)


print(f'Student Name: {student_name}')
print(f'UID: {uid}\n')

marks_list = []


for subject, mark in matches:
    print(f'{subject}: {mark}')
    marks_list.append(int(mark))