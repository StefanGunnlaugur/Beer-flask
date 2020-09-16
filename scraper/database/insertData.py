import psycopg2
from config import config
import json

def insert_beers(beers):
    """ insert multiple beers into the beers table """
    sql = "INSERT INTO beers(beer_name, beer_link, beer_id, beer_alcohol, beer_volume, beer_taste, beer_price, beer_stars) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
    conn = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.executemany(sql,beers)
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# insert_beers([("slots2","yo",100)])

# , beer_id, beer_alcohol, beer_size, beer_taste

file = open("../data.json")
beers = json.load(file)

for beer in beers:
    # print(beer)
    # print()
    beer_name = beer['title']
    beer_link = beer['link_to_vinbudin']
    beer_id = beer['product_number']
    #print(beer_id)
    # prosentu merki
    # print(beer['alcohol'])
    # print(beer['alcohol'][:-1])
    beer_alcohol = float(beer['alcohol'][:-1])

    #kemur bil svo ml
    beer_volume = int(beer['volume'][:-3])

    beer_taste = beer['taste']
    # kemur bil og svo kr. i price
    beer_price = beer['price'][:-4]
    beer_stars = -1;
    beer_votes = 0;
    # aetla ekki nota beervotess..........
    # print(beer_name, beer_link, beer_id, beer_alcohol, beer_volume, beer_taste, beer_price)
    insert_beers([(beer_name, beer_link, beer_id, beer_alcohol, beer_volume, beer_taste, beer_price, beer_stars)])
