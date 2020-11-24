from urllib.request import urlopen
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import csv
import sqlite3
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mail import MY_ADDRESS, PASSWORD
from decorators import sleep


URL = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&region.id[0]=11&city.id[0]=76&price.currency=1&sort[0].order=dates.created.desc&abroad.not=0&custom.not=-1&damage.not=0&page=0&size=100"
headers = dict()
headers[
    "User-Agent"
] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169"

damaged_cars_links = []


@sleep(random.randrange(600))
def check_create_database():
    conn = sqlite3.connect("auto_scrapper.db")
    c = conn.cursor()
    try:
        c.execute(""" SELECT * FROM DAMAGED_CARS""")
        if c.fetchone()[0] == 1:
            print("Table exists.")
    except TypeError:
        print("Table already exists with no items.")
    except sqlite3.OperationalError:
        print("Table does not exist.")
        conn.execute("""CREATE TABLE DAMAGED_CARS
                    (ID INTEGER PRIMARY KEY   AUTOINCREMENT   NOT NULL,
                    CAR_NAME        TEXT    NOT NULL,
                    CAR_PRICE       REAL    NOT NULL,
                    CAR_LINK        CHAR(100),
                    CAR_TITLE       CHAR(200));""")
        print("Table created successfully")

    conn.commit()
    conn.close()


def car_create(car_data):
    conn = sqlite3.connect("auto_scrapper.db")
    damaged_cars_links.append(car_data)
    id = None
    conn.execute("INSERT INTO DAMAGED_CARS VALUES (?,?,?,?,?)",
                 (id, *car_data, ))
    conn.commit()
    conn.close()


def car_check(car_data):
    conn = sqlite3.connect("auto_scrapper.db")
    # checking car link exists in database or not
    car_price = car_data[1]
    car_link = car_data[2]
    print('inside car_check method')
    car_link_exists = conn.execute(
        "SELECT COUNT (*) FROM DAMAGED_CARS WHERE car_link = '%s'" % car_link)
    if car_link_exists.fetchone()[0] == 0:
        print("we need to create car instance")
        car_create(car_data)
    else:
        # checking the car price
        car_price_db = conn.execute(
            "SELECT car_price FROM DAMAGED_CARS WHERE car_link = '%s'" % car_link)
        if car_price_db.fetchone()[0] != car_price:
            damaged_cars_links.append(car_data)
        pass
    conn.commit()
    conn.close()


def parse_the_page(URL=URL):
    results = requests.get(URL, headers=headers)
    soup = BeautifulSoup(results.text, "html.parser")
    cars_damaged = soup.find_all("div", class_="content-bar")
    for car in cars_damaged:
        car_name = car.find("span", class_="blue bold").text
        car_price = car.find("span", class_="bold green size22").text
        car_link = car.find("a", class_="m-link-ticket")["href"]
        car_title = car.find("div", class_="footer_ticket").find(
            "span").attrs["title"]
        car_data = car_name, car_price, car_link, car_title
        car_check(car_data)


def send_message_to_me():
    # set up the SMTP server
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    msg = MIMEMultipart()       # create a message
    email = 'kr_trading@ukr.net'
    # add in the actual car info to the message template
    message = "We have some message for you. Some new cars {}".format(
        damaged_cars_links)

    # setup the parameters of the message
    msg['From'] = MY_ADDRESS
    msg['To'] = email
    msg['Subject'] = "This is TEST"

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)


check_create_database()
parse_the_page(URL=URL)

if damaged_cars_links:
    send_message_to_me()
