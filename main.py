import sqlite3
import json
import requests
from lxml import html

# Data
with open("userpass.json") as auth_data:
    auth_creds = json.loads(auth_data.read())

uname = auth_creds["username"]
upass = auth_creds["password"]

# Session setup
session = requests.Session()

# Initial GET request
first_response = session.get("https://lms.pvpittssm.edu.in/")

# Parse the login page to extract the login token
first_dom_tree = html.fromstring(first_response.text)
login_token = first_dom_tree.cssselect("#pre-login-form > input:nth-child(1)")[0].get("value")

# Data for login
data = {
        "logintoken": login_token,
        "username": uname,
        "password": upass,
        }

# Send the POST request to login
second_response = session.post(
        "https://lms.pvpittssm.edu.in/login/index.php",
        data=data,
        allow_redirects=True
        )

# Initialize database
conn = sqlite3.connect("person_data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS persons (
    uid INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    laddr TEXT,
    paddr TEXT,
    aadhar TEXT,
    phone TEXT
)
""")
conn.commit()

class Person:
    def __init__(self, name, uid, laddr, paddr, aadhar, phone):
        self.name = name
        self.uid = uid
        self.laddr = laddr
        self.paddr = paddr
        self.aadhar = aadhar
        self.phone = phone
    
    def __str__(self):
        return f'"uid":"{self.uid}",name":"{self.name}","laddr":"{self.laddr}","paddr":"{self.paddr}","aadhar":"{self.aadhar}","phone":"{self.phone}"'

    def save_to_db(self, connection):
        cursor = connection.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO persons (uid, name, laddr, paddr, aadhar, phone) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (self.uid, self.name, self.laddr, self.paddr, self.aadhar, self.phone))
        connection.commit()


for x in range(7000):
    third_response = session.get(f"https://lms.pvpittssm.edu.in/user/profile.php?id={x}")
    third_dom_tree = html.fromstring(third_response.text)
    
    try:
        name = third_dom_tree.cssselect(".fullname > span:nth-child(1)")[0].text.strip('\n') 
    except IndexError:
        continue

    try:
        laddr = third_dom_tree.cssselect("li.contentnode:nth-child(3) > dl:nth-child(1) > dd:nth-child(2) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(1)")[0].text.strip('\n')
    except IndexError:
        laddr = ""
    
    try:
        paddr = third_dom_tree.cssselect(".custom_field_CorrespondenceAddressPermanent > dl:nth-child(1) > dd:nth-child(2) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(1)")[0].text.strip('\n')
    except IndexError:
        paddr = ""
    
    try:
        aadhar = third_dom_tree.cssselect(".custom_field_AaadharNo > dl:nth-child(1) > dd:nth-child(2)")[0].text.strip('\n')
    except IndexError:
        aadhar = ''
    
    try:
        phone  = third_dom_tree.cssselect(".custom_field_ContactNumber > dl:nth-child(1) > dd:nth-child(2)")[0].text.strip('\n')
    except IndexError:
        phone = ''

    person = Person(name, x, laddr, paddr, aadhar, phone)
    person.save_to_db(conn)  # Save each person to the database
    print(person)

# Close the connection
conn.close()

