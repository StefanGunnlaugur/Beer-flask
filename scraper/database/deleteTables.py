import psycopg2
from config import config

def delete_tables():
    """ delete tables in the PostgreSQL database"""


    commands = (
        """
        DROP TABLE if exists beers cascade ;
        """,
        """
        DROP TABLE if exists users cascade ;
        """,
        """
        DROP TABLE if exists comments ;
        """,
        """
        DROP TABLE if exists role cascade ;
        """,
        """
        DROP TABLE if exists my_beers ;
        """,
        """
        DROP TABLE if exists user_role ;
        """
    )


    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # cur.execute(commands)
        for command in commands:
            print("delete")
            cur.execute(command)
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as err:
        print(err)
    finally:
        if conn is not None:
            conn.close()

delete_tables()
