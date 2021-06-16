import requests
import json
import os.path
from os import path

def sendRequest(url):
    try:
        page = requests.get(url)

    except Exception as e:
        print("error:", e)
        return False

    # check status code

    if (page.status_code != 200):
        return False

    return page

def downloadImage(imageUrl, filePath):
    img = sendRequest(imageUrl)

    if (img == False):
        return False

    #if not img.content[:4] == b'\xff\xd8\xff\xe0': return False

    if img.content:
        with open(filePath, "wb") as f:
            f.write(img.content)

    return True


def get_images():
    with open('data-all-16-06-2021.json') as json_file:
        data = json.load(json_file)
        c = 0
        for b in data:
            if b['product_number']:
                url = 'https://www.vinbudin.is/Portaldata/1/Resources/vorumyndir/medium/{}_r.jpg'.format(b['product_number'])
                file_path = './images/{}.jpg'.format(b['product_number'])
                if not path.exists(file_path):
                    res = downloadImage(url, file_path)
                if c % 50 == 0:
                    print(c)
                #print(res, b['product_number'])
            c+=1


get_images()