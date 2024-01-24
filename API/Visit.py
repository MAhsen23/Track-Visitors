import pyodbc
from flask import jsonify,request
from datetime import datetime
import DB_Connection
import os
conn_string = DB_Connection.conn_string()

def get_visit_entry_time(visitor_id):
    try:
        query = f"SELECT top 1 entry_time FROM Visit where visitor_id = {visitor_id} and exit_time is NULL"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows[0]), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch entry time.'}), 500
