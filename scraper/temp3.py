from selenium import webdriver
from bs4 import BeautifulSoup
import json
from time import sleep
from datetime import date


url = "https://www.vinbudin.is/heim/vorur/vorur"
#ATH MIKILVÆGT:
# verðið að ná í driverinn https://github.com/mozilla/geckodriver/releases

# create a new Firefox session
driver = webdriver.Firefox()
driver.implicitly_wait(50)
driver.get(url)

next_button = driver.find_elements_by_class_name("next")
allDrinks = []
for i in range(120):
    soup=BeautifulSoup(driver.page_source, 'html')
    for product in soup.find_all('li', class_="product"):
        if product.find('span', class_="category") and product.find('span', class_="category").text:
            category = product.find('span', class_="category").text
        else:
            category = ''
        if category == 'Umbúðir og aðrar söluvörur':
            continue
        title_a = product.find('a', class_="title")

        if title_a.find_all('span')[0].text:
            title = title_a.find_all('span')[0].text
        else:
            title = ''

        link = title_a['href']

        if product.find('span', class_="price") and product.find('span', class_="price").text:
            price = product.find('span', class_="price").text
        else:
            price = ''

        if product.find('span', class_="volume") and product.find('span', class_="volume").text:
            volume = product.find('span', class_="volume").text
        else:
            volume = ''

        if product.find('span', class_="alcohol") and product.find('span', class_="alcohol").text:
            alcohol = product.find('span', class_="alcohol").text  
        else:
            alcohol = ''

        if product.find('span', class_="product-number") and product.find('span', class_="product-number").text:
            product_number = product.find('span', class_="product-number").text
        else:
            product_number = ''
        
        #það eru svigar utan um product number
        product_number = product_number[1:len(product_number)-1] if product_number != '' else ''

        if product.find('span', class_="text") and product.find('span', class_="text").text:
            drink_type = product.find('span', class_="text").text  
        else:
            drink_type = ''
            
        if product.find('span', class_="taste") and product.find('span', class_="taste").text:
            taste = product.find("a", class_="taste").text 
        else:
            taste = ''

        drink = {
        "name": title,
        "price":price,
        "volume": volume,
        "alcohol": alcohol,
        "product_number": product_number,
        "taste":taste,
        "type": drink_type,
        "category": category,
        "link_to_vinbudin": link
        }

        allDrinks.append(drink)

    next_button[0].click()
    #fer eftir internet tengingu hvad tharf ad sleepa lengi
    sleep(1)

today = date.today()
d4 = today.strftime("%d-%m-%Y")

with open('data-all-{}.json'.format(d4), 'w') as outfile:
    json.dump(allBeers, outfile,ensure_ascii=False)


driver.quit()
