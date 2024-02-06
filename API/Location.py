import pyodbc
from flask import jsonify,request
from datetime import datetime, timedelta
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

                for row in rows:
                    restrict_check_query = f"SELECT TOP 1 CASE WHEN id IS NOT NULL AND end_datetime >= GETDATE() THEN 'True' ELSE 'False' END AS 'restrict' FROM RestrictedLocation WHERE location_id = {row['id']} ORDER BY id DESC"
                    cursor.execute(restrict_check_query)
                    restrict_result = cursor.fetchone()
                    row['restrict'] = restrict_result[0] if restrict_result else 'False'

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch locations.'}), 500


def restrict_location():
    try:
        location_ids = request.json['locations']
        start_datetime = request.json['start_datetime']
        end_datetime = request.json['end_datetime']

        if not all([location_ids, start_datetime, end_datetime]):
            return jsonify({'error': 'Invalid input data.'}), 400

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                try:
                    query = "INSERT INTO RestrictedLocation (location_id, start_datetime, end_datetime) VALUES (?, ?, ?)"
                    for location_id in location_ids:
                        cursor.execute(query, location_id, start_datetime, end_datetime)

                    conn.commit()

                except Exception as e:
                    print(e)
                    conn.rollback()
                    return jsonify({'error': 'Failed to restrict location. Database changes rolled back.'}), 500

        return jsonify({'success': 'Location restricted successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error':'Failed to restrict location.'}),500



def get_restricted_locations():
    try:
        query = "SELECT RL.id as 'restricted_id',L.id as 'location_id',L.name as 'location_name', RL.start_datetime as 'start_datetime',RL.end_datetime as 'end_datetime' from RestrictedLocation RL JOIN Location L on L.id = RL.location_id where RL.end_datetime >= GETDATE();"

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



def permit_location():
    try:
        location_id = request.args.get('location_id')

        if not location_id:
            return jsonify({'error': 'Location ID not provided.'}), 400

        query_check_blocked = f"SELECT TOP 1 id FROM [RestrictedLocation] WHERE location_id = {location_id} AND end_datetime >= GETDATE() ORDER BY end_datetime DESC"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_check_blocked)
                block_record = cursor.fetchone()

                if block_record:
                    block_id = block_record[0]
                    new_end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                    query_update_end_date = f"UPDATE [RestrictedLocation] SET end_datetime = '{new_end_date}' WHERE id = {block_id}"
                    cursor.execute(query_update_end_date)
                    conn.commit()
                    return jsonify({'message': 'Location permitted successfully.'}), 200
                else:
                    return jsonify({'error': 'Location is not currently restricted.'}), 400

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to permit location.'}), 500