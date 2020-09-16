import psycopg2
from config import config

def create_tables():
    """ create tables in the PostgreSQL database"""


    commands = (
        """
        DROP TABLE if exists beers cascade ;
        """,
        """
        CREATE TABLE beers (
            beer_id VARCHAR(128) PRIMARY KEY,
            beer_name VARCHAR(255) NOT NULL,
            beer_link VARCHAR(255),
            beer_alcohol FLOAT,
            beer_volume INTEGER,
            beer_taste VARCHAR(255),
            beer_stars FLOAT,
            beer_price INTEGER
        )
        """)



    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # cur.execute(commands)
        for command in commands:
            print("create table")
            cur.execute(command)
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as err:
        print(err)
    finally:
        if conn is not None:
            conn.close()

create_tables()
