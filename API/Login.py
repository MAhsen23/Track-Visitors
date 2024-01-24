import pyodbc
from flask import jsonify,request

import DB_Connection
conn_string = DB_Connection.conn_string()

def login():
    username = request.json['username']
    password = request.json['password']
    query = f"SELECT id,name,username,role,duty_location FROM [User] WHERE username='{username}' AND password='{password}'"

    try:
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return rows

    except Exception as e:
        print(e)
        return []
