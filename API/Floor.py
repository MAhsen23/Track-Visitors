import pyodbc
from flask import jsonify,request

import DB_Connection
conn_string = DB_Connection.conn_string()
def get_all_floors():
    try:
        query = "SELECT * FROM Floor"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch floors.'}), 500




def add_floor():
    try:
        name = request.json['name']

        query = f"INSERT INTO [Floor] (name) VALUES ('{name}')"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Floor added successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to add floor.'}), 500





def update_floor(id):
    try:
        name = request.json['name']

        query = f"UPDATE [Floor] SET name='{name}' WHERE id={id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Floor updated successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to update floor.'}), 500





def delete_floor(id):
    try:
        query = f"DELETE FROM [Floor] WHERE id={id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Floor deleted successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to delete floor.'}), 500





def delete_floors():
    try:
        selectedFloors = request.json['selectedItems'];
        for floor in selectedFloors:

            query = f"DELETE FROM [Floor] WHERE id={floor['id']}"

            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    conn.commit()

        if len(selectedFloors)==1:
            return jsonify({'message': 'Floor deleted successfully!'}), 200
        else:
            return jsonify({'message': 'Floors deleted successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to delete floor.'}), 500