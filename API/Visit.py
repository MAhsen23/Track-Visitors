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



def get_visit_destinations():
    try:
        visitor_id = request.args.get('id')
        query = f"SELECT top 1 * FROM Visit where visitor_id = {visitor_id} and exit_time is NULL"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        visit_id = rows[0]['id'];
        get_destinations_query = f"select V.id,V.date,V.entry_time,STRING_AGG(VD.destination_id, ',') AS visit_destinations ,STRING_AGG(L.name, ',') AS visit_destinations_names from Visit V INNER JOIN VisitDestination VD on VD.visit_id = V.id INNER JOIN Location L on L.id = VD.destination_id where V.id={visit_id} GROUP BY  V.id, V.date, V.entry_time"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_destinations_query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        rows[0]['visit_destinations'] = [int(dest_id) for dest_id in rows[0]['visit_destinations'].split(',')]
        destinations_names = rows[0]['visit_destinations_names'].split(',')
        converted_destinations = []

        for dest_name in destinations_names:
            converted_destinations.append(str(dest_name))

        rows[0]['visit_destinations_names'] = converted_destinations
        print(rows[0]['visit_destinations_names'])
        return jsonify(rows[0]), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch visit destinations.'}), 500
