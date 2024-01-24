import pyodbc
from flask import jsonify,request

import DB_Connection
conn_string = DB_Connection.conn_string()

def get_all_users():
    try:
        query = "SELECT * FROM [User]"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch users.'}), 500




def get_all_guards_location():
    try:
        query = "select U.*,l.id as 'location_id',l.name as 'location_name' from [User] U LEFT JOIN Location L on l.id = U.duty_location where U.role='Guard'"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch guards location.'}), 500





def get_user(id):
    try:
        query = f"SELECT * FROM [User] where id = {id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch User.'}), 500





def add_user():
    try:
        name = request.json['name']
        username = request.json['username']
        password = request.json['password']
        role = request.json['role']

        query = f"INSERT INTO [User] (name, username, password, role) VALUES ('{name}', '{username}', '{password}', '{role}')"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'User added successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to add user.'}), 500





def update_user(id):
    try:
        name = request.json['name']
        username = request.json['username']
        password = request.json['password']
        role = request.json['role']

        query = f"UPDATE [User] SET name='{name}', username='{username}', password='{password}', role='{role}' WHERE id={id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'User updated successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to update user.'}), 500





def delete_user(id):
    try:
        query = f"DELETE FROM [User] WHERE id={id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'User deleted successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to delete user.'}), 500






def allocate_duty_location(id):
    try:
        location_id = request.json['location_id']
        query = f"UPDATE [User] SET duty_location={location_id} WHERE id={id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Guard duty location updated successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to update guard duty location.'}), 500




def get_guard_duty_location(id):
    try:
        query = f"select U.*,l.id as 'location_id',l.name as 'location_name' from [User] U LEFT JOIN Location L on l.id = U.duty_location where U.role='Guard' AND U.id = {id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows[0]), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch guard duty location.'}), 500