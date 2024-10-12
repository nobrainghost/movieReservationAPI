
import psycopg2
from psycopg2 import sql,Error

import os

class Config:
    ##below credentials are local and therefore not a security risk
    DATABASE_URL=os.environ.get('DATABASE_URL') or 'dbname=moviesreservation user=beamer password=allhailkingjulien host=localhost'

def start_connection():
    try:
        conn=psycopg2.connect(Config.DATABASE_URL)
        print("Connection Successful")
        return conn
    except Exception as e:
        print(f"Error Attempting Connection: {e}")

def create_table(table_name,columns,conn):
    """
    Creates a table, taking in:
        table_name: for table Name,
        columns: a string containing table columns 
        conn: database connection
    """

    create_table_query_gen=f"""
    CREATE TABLE IF NOT EXISTS {table_name}({columns});

    """
    with conn.cursor() as cursor:
        cursor.execute(create_table_query_gen)
    

    conn.commit()
    print(f"Table {table_name} Created Succefully")


seat_table_columns="""
seat_id SERIAL PRIMARY KEY,

seat_category VARCHAR(20) CHECK(seat_category IN ('Front','Middle','Backseat')),
seat_price DECIMAL(10,2),
seat_book_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
seat_free_time  TIMESTAMP,
seat_is_in_use BOOLEAN DEFAULT TRUE,
seat_is_corner BOOLEAN DEFAULT FALSE,
seat_has_headphones BOOLEAN DEFAULT FALSE,
seat_has_cupholder BOOLEAN DEFAULT FALSE,
movie_id INTEGER REFERENCES movie_table(movie_id) ON DELETE CASCADE

"""

movie_table_columns="""
movie_id SERIAL PRIMARY KEY,
movie_name VARCHAR(256),
movie_duration VARCHAR(50) NOT NULL,
start_time TIME,
end_time TIME,
available_seats INTEGER[],
start_times TIMESTAMP[],
movie_poster VARCHAR(256),
release_year INTEGER

"""

customer_table_columns="""
customer_id INTEGER REFERENCES registred_customers_table(customer_id) ON DELETE CASCADE,
customer_name VARCHAR(100),
customer_booked_seat INTEGER REFERENCES seats_table(seat_id) ON DELETE CASCADE,
customer_email VARCHAR(50),
customer_payment_method VARCHAR(50),
is_couple BOOLEAN DEFAULT FALSE

"""
registred_customers_columns="""
customer_id SERIAL PRIMARY KEY,
customer_username VARCHAR(255),
customer_password VARCHAR(255),
customer_email VARCHAR(255)
"""

def create_base_tables():
    conn=start_connection()
    create_table('movie_table',movie_table_columns,conn)
    create_table('seats_table',seat_table_columns,conn)
    create_table('registred_customers_table',registred_customers_columns,conn)
    create_table('customer_table',customer_table_columns,conn)

create_base_tables()

##move these to a separate file and import the commands
#basic functions
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin


def create_customer(username,password,email,conn):
    hashed_password=generate_password_hash(password,method='pbkdf2:sha256')
    cursor=conn.cursor()
    query=sql.SQL("INSERT INTO registred_customers_table (customer_username,customer_password,customer_email) VALUES (%s,%s,%s)")
    cursor.execute(query,[username,hashed_password,email])
    conn.commit()

# conn=start_connection()
# create_customer('benar','allhailkingjulien','bean@gmail.com',conn)

def verify_user(username,hashed_password,conn):
    try:
        cursor=conn.cursor()

        query='''SELECT customer_id,customer_username,email FROM registred_customers_table WHERE customer_username=? AND password = ?'''
        cursor.execute(query,(username,hashed_password))
        user=cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email":user[2]
            }
        else:
            return None
        
    except Error as e:
        print(f"Database error: {e}")

def get_user_by_username(username,conn):
    cursor=conn.cursor()
    query="SELECT customer_id,customer_username,customer_password FROM registred_customers_table WHERE customer_username=%s"
    cursor.execute(query,(username,))
    user=cursor.fetchone()
    cursor.close()
    print(user)
    return user
#test the get user
# conn=start_connection()
# get_user_by_username("johndoee",conn)

"""MOVIES API"""

def fetch_movies():
    import requests

    url = "https://imdb-top-lists-news.p.rapidapi.com/popularMovies"

    headers = {
	"x-rapidapi-key": "be623b818cmsh7d25d2e33a15fccp15ee38jsne2bef3c5c029",
	"x-rapidapi-host": "imdb-top-lists-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    response=response.json()
    trending_movies=[]
    for i in range(0,9):
        movie_name=response["movies"][i]['title']
        movie_duration=response["movies"][i]['runtime']
        movie_duration = movie_duration.replace('h', ' hours').replace('m', ' minutes')
        release_year=response["movies"][i]['releaseYear']['year']
        movie_poster=response["movies"][i]['primaryImage']['url']
        movie_list=[movie_name,movie_duration,movie_poster,release_year]
        trending_movies.append(movie_list)
        # print(movie_name, movie_duration)
        # print(release_year)

    return trending_movies

# print(fetch_movies())


def update_movies_to_be_shown(conn):
    sql_query=f"INSERt INTO movie_table(movie_name,movie_duration,movie_poster,release_year) VALUES (%s,%s,%s,%s)"

    cursor=conn.cursor()
    movies=fetch_movies()
    for movie in movies:
        # movie_name=movie[0]
        # movie_duration=movie[1]
        # release_year=movie[3]
        # movie_poster=movie[2]
        cursor.execute(sql_query,movie)
        conn.commit()
# conn=start_connection()
# update_movies_to_be_shown(conn)

"""SEATS API"""
##Entire theatre has 100 floor seats, 20 front,60 mid and 20 back

def populate_seats(conn):
    cursor=conn.cursor()
    query="""
    INSERT INTO seats_table (
    seat_category, seat_price, seat_book_time, seat_free_time, 
    seat_is_in_use, seat_is_corner, seat_has_headphones, 
    seat_has_cupholder, movie_id
)
VALUES


    ('Front', 42.50, '2024-10-12 12:00:00', '2024-10-12 18:00:00', TRUE, FALSE, TRUE, TRUE, 1),
    ('Front', 47.99, '2024-10-12 12:15:00', '2024-10-12 18:15:00', TRUE, TRUE, TRUE, FALSE, 2),
    ('Front', 45.00, '2024-10-12 12:30:00', '2024-10-12 18:30:00', FALSE, FALSE, TRUE, TRUE, 3),
    ('Front', 48.25, '2024-10-12 12:45:00', '2024-10-12 18:45:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Front', 46.75, '2024-10-12 13:00:00', '2024-10-12 19:00:00', TRUE, FALSE, TRUE, TRUE, 5),
    ('Front', 49.50, '2024-10-12 13:15:00', '2024-10-12 19:15:00', FALSE, TRUE, FALSE, FALSE, 1),
    ('Front', 41.25, '2024-10-12 13:30:00', '2024-10-12 19:30:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Front', 43.99, '2024-10-12 13:45:00', '2024-10-12 19:45:00', TRUE, TRUE, TRUE, FALSE, 3),
    ('Front', 45.50, '2024-10-12 14:00:00', '2024-10-12 20:00:00', FALSE, TRUE, FALSE, TRUE, 4),
    ('Front', 44.25, '2024-10-12 14:15:00', '2024-10-12 20:15:00', TRUE, FALSE, TRUE, TRUE, 5),
    ('Front', 40.00, '2024-10-12 14:30:00', '2024-10-12 20:30:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Front', 49.75, '2024-10-12 14:45:00', '2024-10-12 20:45:00', TRUE, TRUE, TRUE, FALSE, 2),
    ('Front', 46.00, '2024-10-12 15:00:00', '2024-10-12 21:00:00', FALSE, FALSE, TRUE, TRUE, 3),
    ('Front', 48.50, '2024-10-12 15:15:00', '2024-10-12 21:15:00', TRUE, TRUE, FALSE, TRUE, 4),
    ('Front', 47.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', TRUE, TRUE, TRUE, FALSE, 5),
    ('Front', 43.50, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, FALSE, TRUE, TRUE, 1),
    ('Front', 44.75, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, TRUE, FALSE, TRUE, 2),
    ('Front', 42.25, '2024-10-12 16:15:00', '2024-10-12 22:15:00', FALSE, FALSE, TRUE, TRUE, 3),
    ('Front', 41.99, '2024-10-12 16:30:00', '2024-10-12 22:30:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Front', 47.00, '2024-10-12 16:45:00', '2024-10-12 22:45:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Middle', 35.50, '2024-10-12 12:00:00', '2024-10-12 18:00:00', TRUE, FALSE, TRUE, FALSE, 1),
    ('Middle', 37.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', FALSE, TRUE, TRUE, TRUE, 2),
    ('Middle', 30.75, '2024-10-12 12:30:00', '2024-10-12 18:30:00', TRUE, TRUE, TRUE, FALSE, 3),
    ('Middle', 28.50, '2024-10-12 12:45:00', '2024-10-12 18:45:00', FALSE, FALSE, FALSE, TRUE, 4),
    ('Middle', 29.99, '2024-10-12 13:00:00', '2024-10-12 19:00:00', TRUE, TRUE, TRUE, TRUE, 5),
    ('Middle', 32.50, '2024-10-12 13:15:00', '2024-10-12 19:15:00', FALSE, FALSE, TRUE, TRUE, 1),
    ('Middle', 31.25, '2024-10-12 13:30:00', '2024-10-12 19:30:00', TRUE, TRUE, TRUE, FALSE, 2),
    ('Middle', 36.75, '2024-10-12 13:45:00', '2024-10-12 19:45:00', FALSE, TRUE, TRUE, TRUE, 3),
    ('Middle', 27.25, '2024-10-12 14:00:00', '2024-10-12 20:00:00', TRUE, FALSE, TRUE, TRUE, 4),
    ('Middle', 34.99, '2024-10-12 14:15:00', '2024-10-12 20:15:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Middle', 25.50, '2024-10-12 14:30:00', '2024-10-12 20:30:00', TRUE, FALSE, TRUE, FALSE, 1),
    ('Middle', 33.25, '2024-10-12 14:45:00', '2024-10-12 20:45:00', FALSE, TRUE, TRUE, TRUE, 2),
    ('Middle', 37.99, '2024-10-12 15:00:00', '2024-10-12 21:00:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 38.75, '2024-10-12 15:15:00', '2024-10-12 21:15:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 39.75, '2024-10-12 16:30:00', '2024-10-12 22:30:00', TRUE, TRUE, TRUE, TRUE, 4),
    ('Middle', 26.75, '2024-10-12 16:45:00', '2024-10-12 22:45:00', TRUE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.50, '2024-10-12 12:00:00', '2024-10-12 18:00:00', TRUE, FALSE, TRUE, FALSE, 1),
    ('Middle', 37.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', FALSE, TRUE, TRUE, TRUE, 2),
    ('Middle', 30.75, '2024-10-12 12:30:00', '2024-10-12 18:30:00', TRUE, TRUE, TRUE, FALSE, 3),
    ('Middle', 28.50, '2024-10-12 12:45:00', '2024-10-12 18:45:00', FALSE, FALSE, FALSE, TRUE, 4),
    ('Middle', 29.99, '2024-10-12 13:00:00', '2024-10-12 19:00:00', TRUE, TRUE, TRUE, TRUE, 5),
    ('Middle', 32.50, '2024-10-12 13:15:00', '2024-10-12 19:15:00', FALSE, FALSE, TRUE, TRUE, 1),
    ('Middle', 31.25, '2024-10-12 13:30:00', '2024-10-12 19:30:00', TRUE, TRUE, TRUE, FALSE, 2),
    ('Middle', 36.75, '2024-10-12 13:45:00', '2024-10-12 19:45:00', FALSE, TRUE, TRUE, TRUE, 3),
    ('Middle', 27.25, '2024-10-12 14:00:00', '2024-10-12 20:00:00', TRUE, FALSE, TRUE, TRUE, 4),
    ('Middle', 34.99, '2024-10-12 14:15:00', '2024-10-12 20:15:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Middle', 25.50, '2024-10-12 14:30:00', '2024-10-12 20:30:00', TRUE, FALSE, TRUE, FALSE, 1),
    ('Middle', 33.25, '2024-10-12 14:45:00', '2024-10-12 20:45:00', FALSE, TRUE, TRUE, TRUE, 2),
    ('Middle', 37.99, '2024-10-12 15:00:00', '2024-10-12 21:00:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 38.75, '2024-10-12 15:15:00', '2024-10-12 21:15:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 39.75, '2024-10-12 16:30:00', '2024-10-12 22:30:00', TRUE, TRUE, TRUE, TRUE, 4),
    ('Middle', 26.75, '2024-10-12 16:45:00', '2024-10-12 22:45:00', TRUE, FALSE, TRUE, TRUE, 5),
    ('Backseat', 12.99, '2024-10-12 12:00:00', '2024-10-12 18:00:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Backseat', 15.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', TRUE, TRUE, TRUE, TRUE, 2),
    ('Backseat', 17.50, '2024-10-12 12:30:00', '2024-10-12 18:30:00', TRUE, FALSE, TRUE, TRUE, 3),
    ('Backseat', 19.75, '2024-10-12 12:45:00', '2024-10-12 18:45:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Backseat', 24.99, '2024-10-12 13:00:00', '2024-10-12 19:00:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Backseat', 12.99, '2024-10-12 12:00:00', '2024-10-12 18:00:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Backseat', 15.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', TRUE, TRUE, TRUE, TRUE, 2),
    ('Backseat', 17.50, '2024-10-12 12:30:00', '2024-10-12 18:30:00', TRUE, FALSE, TRUE, TRUE, 3),
    ('Backseat', 19.75, '2024-10-12 12:45:00', '2024-10-12 18:45:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Backseat', 24.99, '2024-10-12 13:00:00', '2024-10-12 19:00:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Backseat', 12.99, '2024-10-12 12:00:00', '2024-10-12 18:00:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Backseat', 15.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', TRUE, TRUE, TRUE, TRUE, 2),
    ('Backseat', 17.50, '2024-10-12 12:30:00', '2024-10-12 18:30:00', TRUE, FALSE, TRUE, TRUE, 3),
    ('Backseat', 19.75, '2024-10-12 12:45:00', '2024-10-12 18:45:00', TRUE, TRUE, TRUE, FALSE, 4),
    ('Backseat', 24.99, '2024-10-12 13:00:00', '2024-10-12 19:00:00', FALSE, TRUE, TRUE, TRUE, 5),
    ('Backseat', 12.99, '2024-10-12 12:00:00', '2024-10-12 18:00:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Backseat', 15.25, '2024-10-12 12:15:00', '2024-10-12 18:15:00', TRUE, TRUE, TRUE, TRUE, 2),
    ('Backseat', 12.99, '2024-10-12 12:00:00', '2024-10-12 18:00:00', FALSE, FALSE, FALSE, TRUE, 1),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2),
    ('Middle', 27.99, '2024-10-12 16:15:00', '2024-10-12 22:15:00', TRUE, TRUE, TRUE, TRUE, 3),
    ('Middle', 26.25, '2024-10-12 15:30:00', '2024-10-12 21:30:00', FALSE, FALSE, TRUE, TRUE, 5),
    ('Middle', 35.00, '2024-10-12 15:45:00', '2024-10-12 21:45:00', TRUE, TRUE, TRUE, FALSE, 1),
    ('Middle', 29.50, '2024-10-12 16:00:00', '2024-10-12 22:00:00', TRUE, FALSE, TRUE, TRUE, 2)

    
    """
    cursor.execute(query)
    conn.commit()


# conn=start_connection()
# populate_seats(conn)
