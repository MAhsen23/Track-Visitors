import pyodbc
from flask import jsonify,request

import DB_Connection
conn_string = DB_Connection.conn_string()


def get_all_locations():
    try:
        query = "SELECT l.id, l.name, f.id as 'floor_id', f.name as floor_name, l.type,l.isDestination FROM Location l JOIN Floor f ON l.floor_id = f.id"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch locations.'}), 500




def get_restricted_locations():
    try:
        query = "SELECT RL.id as 'restricted_id',L.id as 'location_id',L.name as 'location_name', RL.start_datetime as 'start_datetime',RL.end_datetime as 'end_datetime'"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch restricted locations.'}), 500


def get_locations_by_floor(floor_id):
    try:
        query = f"select l.id,l.name,l.type,l.isDestination,f.name as 'floor_name' from Location l Join Floor f on f.id=l.floor_id where f.id={floor_id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': f'Failed to fetch locations by floor_id: {floor_id}.'}), 500





def add_location():
    try:
        name = request.json['name']
        floor_id = request.json['floor_id']
        type = request.json['type']
        isDestination = request.json['isDestination']

        query = "INSERT INTO [Location] (name, floor_id, type,isDestination) VALUES (?, ?, ?,?)"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, floor_id, type,isDestination))
                conn.commit()

        return jsonify({'message': 'Location added successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to add location.'}), 500






def update_location(location_id):
    try:
        name = request.json['name']
        floor_id = request.json['floor_id']
        type = request.json['type']
        isDestination = request.json['isDestination']

        query = "UPDATE [Location] SET name = ?, floor_id = ?, type = ?, isDestination = ? WHERE id = ?"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, floor_id, type,isDestination, location_id))
                conn.commit()

        return jsonify({'message': 'Location updated successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to update location.'}), 500





def delete_location(location_id):
    try:
        query = "DELETE FROM [Location] WHERE id = ?"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (location_id,))
                conn.commit()

        return jsonify({'message': 'Location deleted successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to delete location.'}), 500





def get_location(id):
    try:
        query = f"SELECT * FROM [Location] where id = {id}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch Location.'}), 500







def get_location_by_camera(camera_name):
    try:
        query = """
                WITH RankedLocations AS (
            SELECT
                C.id AS CameraID,
                C.name AS CameraName,
                l.id AS LocationID,
                l.floor_id,
                f.name AS FloorName,
                l.name AS LocationName,
                l.type AS LocationType,
                ROW_NUMBER() OVER (PARTITION BY C.id ORDER BY l.id) AS RowNum
            FROM
                Location l
            JOIN
                CameraLocation CL ON CL.location_id = l.id
            JOIN
                Camera C ON C.id = CL.camera_id
            JOIN
                Floor F ON F.id = l.floor_id
        )
        SELECT
            CameraID,
            CameraName,
            LocationID,
            LocationName,
            floor_id,
            FloorName,
            LocationType
        FROM
            RankedLocations
        WHERE
            RowNum = 1
            AND CameraName = ?;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,(camera_name))
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch location by camera.'}), 500








def get_location_by_camera_id(camera_id):
    try:
        query = """
                WITH RankedLocations AS (
            SELECT
                C.id AS CameraID,
                C.name AS CameraName,
                l.id AS LocationID,
                l.floor_id,
                f.name AS FloorName,
                l.name AS LocationName,
                l.type AS LocationType,
                ROW_NUMBER() OVER (PARTITION BY C.id ORDER BY l.id) AS RowNum
            FROM
                Location l
            JOIN
                CameraLocation CL ON CL.location_id = l.id
            JOIN
                Camera C ON C.id = CL.camera_id
            JOIN
                Floor F ON F.id = l.floor_id
        )
        SELECT
            CameraID,
            CameraName,
            LocationID,
            LocationName,
            floor_id,
            FloorName,
            LocationType
        FROM
            RankedLocations
        WHERE
            RowNum = 1
            AND CameraID = ?;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,(camera_id))
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch location by camera.'}), 500


