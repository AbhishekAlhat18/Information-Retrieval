from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['web_crawler_db']
pages_collection = db['pages']
professors_collection = db['professors']

# Retrieve the "Permanent Faculty" page HTML from MongoDB
target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"
page_data = pages_collection.find_one({"url": target_url})

if not page_data:
    print("Permanent Faculty page not found in MongoDB.")
    exit()

html_content = page_data['html']

# Initialize a list to store faculty data
faculty_list = []

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

faculty_names = []
faculty_data = []
faculty_sections = soup.find_all('div', class_='clearfix')
for section in faculty_sections:
    all_h2_tags = section.find_all('h2')

    for h2 in all_h2_tags:
        faculty_names.append(h2)

    all_p_tags = section.find_all('p')
    for data in all_p_tags:
        faculty_data.append(data)

professor_data = []

for i in range(len(faculty_names)):
    name = faculty_names[i].get_text(strip=True)

    title_tag = faculty_data[i].find('strong', string=re.compile(r'Title'))
    if title_tag and title_tag.next_sibling:
        title = title_tag.next_sibling.strip()

    else:

        title = "No Title found"
    office_tag = faculty_data[i].find('strong', string=re.compile(r'Office'))
    if office_tag and office_tag.next_sibling:
        office = office_tag.next_sibling.strip()
    else:
        office = "No Office found"
    phone_tag = faculty_data[i].find('strong', string=re.compile(r'Phone'))
    if phone_tag and phone_tag.next_sibling:
        phone = phone_tag.next_sibling.strip()

    else:
        phone = "No Phone found"
    email_tag = faculty_data[i].find('strong', string=re.compile(r'Email'))
    if email_tag:
        email = email_tag.find_next('a').get_text(strip=True)

    else:
        email = "No Email found"
    web_tag = faculty_data[i].find('strong', string=re.compile(r'Web'))
    if web_tag:
        web = web_tag.find_next('a')['href']

    else:
        web = "No Web found"

    professor_data = {
        "name": name,
        "title": title,
        "office": office,
        "phone": phone,
        "email": email,
        "web": web
    }

    # print(professor_data)

    faculty_list.append(professor_data)

for professor_data in faculty_list:
    # Accessing each field within the dictionary
    print("Name:", professor_data["name"])
    print("Title:", professor_data["title"])
    print("Office:", professor_data["office"])
    print("Phone:", professor_data["phone"])
    print("Email:", professor_data["email"])
    print("Web:", professor_data["web"])
    print()

# save professors data to MongoDB collection "professors".
result = professors_collection.insert_many(faculty_list)

print("All Professor data Stored successfully in db")
