from selenium import webdriver
from bs4 import BeautifulSoup
import json
from time import sleep
from datetime import date


url = "https://www.vinbudin.is/heim/vorur/vorur.aspx/?category=beer&order=price%20desc"
#ATH MIKILVÆGT:
# verðið að ná í driverinn https://github.com/mozilla/geckodriver/releases

# create a new Firefox session
driver = webdriver.Firefox()
driver.implicitly_wait(50)
driver.get(url)

next_button = driver.find_elements_by_class_name("next")
allBeers = []
for i in range(22):
    soup=BeautifulSoup(driver.page_source, 'html')
    for product in soup.find_all('li', class_="product"):
        title_a = product.find('a', class_="title")
        title = title_a.find_all('span')[0].text
        link = title_a['href']
        price = product.find('span', class_="price").text
        volume = product.find('span', class_="volume").text
        alcohol = product.find('span', class_="alcohol").text
        product_number = product.find('span', class_="product-number").text
        #það eru svigar utan um product number
        product_number = product_number[1:len(product_number)-1]


        taste = product.find("a", class_="taste")
        if taste:
            taste = taste.text
        else:
            taste = ""

        beer = {
        "name": title,
        "price":price,
        "volume": volume,
        "alcohol": alcohol,
        "product_number": product_number,
        "taste":taste,
        "link_to_vinbudin": link
        }

        allBeers.append(beer)

    next_button[0].click()
    #fer eftir internet tengingu hvad tharf ad sleepa lengi
    sleep(1)

today = date.today()
d4 = today.strftime("%d-%m-%Y")

with open('data-{}.json'.format(d4), 'w') as outfile:
    json.dump(allBeers, outfile,ensure_ascii=False)


driver.quit()
