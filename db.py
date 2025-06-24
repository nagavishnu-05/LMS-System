import mysql.connector

def get_connection():
    return mysql.connector.connect(
        user='root',
        host='localhost',
        password='',
        database='lms'
    )
