import base64
import re
import pyodbc
from flask import jsonify,request
import os
import DB_Connection
import datetime
conn_string = DB_Connection.conn_string()

def get_all_cameras():
    try:
        query = "SELECT * FROM CAMERA"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch cameras.'}), 500





def get_all_cameras_locations_connections():
    try:
        query = """
        SELECT
        c.id,
        c.name AS CameraName,
        locs.LocationIDs,
        locs.LocationNames,
        STRING_AGG(c2.name, ',') AS ConnectedCameraNames,
        STRING_AGG(CONVERT(VARCHAR(10), ct.timeToReach), ',') AS TimeToReach
        FROM
            Camera c
        JOIN (
            SELECT
                cl.camera_id,
                STRING_AGG(l.id, ',') AS LocationIDs,
                STRING_AGG(l.name, ',') AS LocationNames
            FROM
                CameraLocation cl
            JOIN
                Location l ON l.id = cl.location_id
            GROUP BY
                cl.camera_id
        ) AS locs ON c.id = locs.camera_id
        JOIN
            Connection ct ON ct.sourceCam_id = c.id
        JOIN
            Camera c2 ON c2.id = ct.destinationCam_id
        WHERE
            ct.timeToReach > 0
        GROUP BY
            c.id, c.name, locs.LocationIDs, locs.LocationNames
        ORDER BY
            c.id;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch cameras.'}), 500






def add_camera():
    try:
        name = request.json['name']
        cameraLocations = request.json['cameraLocations']
        connectedCameras = request.json.get('connectedCameras')
        times = request.json.get('time')

        camera_query = "INSERT INTO [Camera] (name) VALUES (?)"
        location_query = "INSERT INTO [CameraLocation] (camera_id, location_id) VALUES (?, ?)"
        cost_query = "INSERT INTO [Connection] (sourceCam_id, destinationCam_id, timeToReach) VALUES (?, ?, ?)"
        delete_connection_query = "DELETE FROM [Connection] WHERE sourceCam_id = ? AND destinationCam_id = ?"


        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(camera_query, (name,))
                    conn.commit()

                    cursor.execute("SELECT TOP 1 id FROM [Camera] ORDER BY id DESC")
                    camera_id = cursor.fetchone()[0]

                    for location_id in cameraLocations:
                        cursor.execute(location_query, (camera_id, location_id))
                        conn.commit()

                    cursor.execute(cost_query, (camera_id, camera_id, 0))
                    conn.commit()

                    if connectedCameras and times:
                        for i in range(len(connectedCameras)):
                            source_cam_id = camera_id
                            destination_cam_id = connectedCameras[i]
                            connection_time = times[i]

                            cursor.execute(cost_query, (source_cam_id, destination_cam_id, connection_time))
                            conn.commit()

                            cursor.execute(cost_query, (destination_cam_id, source_cam_id, connection_time))
                            conn.commit()

                    # Remove connections between cameras if a new camera is inserted
                    for rowCamId in connectedCameras:
                        for colCamId in connectedCameras:
                            if rowCamId == colCamId:
                                continue
                            else:
                                get_cost_query = "SELECT * FROM [Connection] WHERE sourceCam_id = ? AND destinationCam_id = ?"
                                cursor.execute(get_cost_query, (rowCamId, colCamId))
                                columns = [column[0] for column in cursor.description]
                                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                                if len(rows)>0:
                                    if rows[0]['timeToReach'] > 0:
                                        print(rows[0]['timeToReach'])
                                        print(rowCamId,colCamId)
                                        cursor.execute(delete_connection_query, (rowCamId, colCamId))
                                        conn.commit()

                except Exception as e:
                    print(e)
                    conn.rollback()
                    return jsonify({'error': 'Failed to add camera. Database changes rolled back.'}), 500

        return jsonify({'message': 'Camera added successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to add camera.'}), 500







def delete_camera(camera_id):
    try:
        camera_query = "DELETE FROM [Camera] WHERE id = ?"
        location_query = "DELETE FROM [CameraLocation] WHERE camera_id = ?"
        cost_query = "DELETE FROM [Connection] WHERE sourceCam_id = ? OR destinationCam_id = ?"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(cost_query, (camera_id, camera_id))
                    cursor.execute(location_query, (camera_id,))
                    cursor.execute(camera_query, (camera_id,))
                    conn.commit()
                    return jsonify({'message': 'Camera deleted successfully!'}), 200

                except Exception as e:
                    print(e)
                    conn.rollback()
                    return jsonify({'error': 'Failed to delete camera. Database changes rolled back.'}), 500

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to delete camera.'}), 500






def update_camera(camera_id):
    try:
        name = request.json['name']
        cameraLocations = request.json['cameraLocations']
        connectedCameras = request.json.get('connectedCameras')
        times = request.json.get('time')

        # Update camera's name in the Camera table
        camera_query = f"UPDATE [Camera] SET name = '{name}' WHERE id = {camera_id}"

        # Delete existing camera's locations from the CameraLocation table
        delete_location_query = "DELETE FROM [CameraLocation] WHERE camera_id = ?"

        # Create SQL query for camera location insertion
        location_query = "INSERT INTO [CameraLocation] (camera_id, location_id) VALUES (?, ?)"

        # Delete existing camera's costs from the Cost table
        delete_cost_query = "DELETE FROM [Connection] WHERE sourceCam_id = ? OR destinationCam_id = ?"

        # Create SQL query for cost insertion
        cost_query = "INSERT INTO [Connection] (sourceCam_id, destinationCam_id, timeToReach) VALUES (?, ?, ?)"

        delete_connection_query = "DELETE FROM [Connection] WHERE sourceCam_id = ? AND destinationCam_id = ?"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(camera_query)
                    conn.commit()

                    # Delete existing camera's locations
                    cursor.execute(delete_location_query, (camera_id,))
                    conn.commit()

                    # Insert new camera locations
                    for location_id in cameraLocations:
                        cursor.execute(location_query, (camera_id, location_id))
                        conn.commit()

                    # Delete existing camera's costs
                    cursor.execute(delete_cost_query, (camera_id, camera_id))
                    conn.commit()

                    cursor.execute(cost_query, (camera_id, camera_id, 0))
                    conn.commit()

                    # Insert new camera costs
                    for i in range(len(connectedCameras)):
                        source_cam_id = camera_id
                        destination_cam_id = connectedCameras[i]
                        connection_time = times[i]

                        cursor.execute(cost_query, (source_cam_id, destination_cam_id, connection_time))
                        conn.commit()

                        cursor.execute(cost_query, (destination_cam_id, source_cam_id, connection_time))
                        conn.commit()


                    for rowCamId in connectedCameras:
                        for colCamId in connectedCameras:
                            if rowCamId == colCamId:
                                continue
                            else:
                                get_cost_query = "SELECT * FROM [Connection] WHERE sourceCam_id = ? AND destinationCam_id = ?"
                                cursor.execute(get_cost_query, (rowCamId, colCamId))
                                columns = [column[0] for column in cursor.description]
                                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                                if len(rows) > 0:
                                    if rows[0]['timeToReach'] > 0:
                                        print(rows[0]['timeToReach'])
                                        print(rowCamId, colCamId)
                                        cursor.execute(delete_connection_query, (rowCamId, colCamId))
                                        conn.commit()


                except Exception as e:
                    print(e)
                    conn.rollback()
                    return jsonify({'error': 'Failed to update camera. Database changes rolled back.'}), 500

        return jsonify({'message': 'Camera updated successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to update camera.'}), 500





def get_camera_by_location(location_id):
    try:
        query = f"SELECT top 1 C.id AS camera_id, C.name AS camera_name FROM Camera C JOIN CameraLocation LC ON C.id = LC.camera_id JOIN Location L ON LC.location_id = L.id WHERE L.id = {location_id};"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': f'Failed to fetch camera by location_id: {location_id}.'}), 500







def get_adjacency_matrix():
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()

    # Fetch Camera data
    cursor.execute('SELECT id, name FROM Camera ORDER BY id')
    camera_data = cursor.fetchall()

    # Fetch Connection data
    cursor.execute('SELECT sourceCam_id, destinationCam_id, timeToReach FROM Connection')
    cost_data = cursor.fetchall()

    # Create a dictionary to map camera IDs to indices
    camera_indices = {camera[0]: i for i, camera in enumerate(camera_data)}

    # Get the number of cameras
    num_cameras = len(camera_indices)

    # Initialize the adjacency matrix with -1
    adjacency_matrix = [[-1] * num_cameras for _ in range(num_cameras)]

    # Populate the adjacency matrix with timeToReach values
    for cost in cost_data:
        source_cam = cost[0]
        dest_cam = cost[1]
        time_to_reach = cost[2]

        if source_cam in camera_indices and dest_cam in camera_indices:
            source_idx = camera_indices[source_cam]
            dest_idx = camera_indices[dest_cam]
            adjacency_matrix[source_idx][dest_idx] = time_to_reach

    # Get the sorted row and column names
    row_names = [camera[1] for camera in camera_data]
    column_names = [camera[1] for camera in camera_data]

    conn.close()

    # Prepare the response with sorted data
    response = {
        'matrix': adjacency_matrix,
        'rowNames': row_names,
        'columnNames': column_names
    }

    return jsonify(response)






def update_adjacency_matrix():
    # Create a cursor to execute SQL queries
    conn = pyodbc.connect(conn_string)

    # Create a cursor to execute SQL queries
    cursor = conn.cursor()

    matrix = request.json['matrix']
    rows = request.json['rowNames']
    columns = request.json['columnNames']

    # Loop through the cost matrix and update the cost values in the database
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            sourceCam = rows[i]
            destinationCam = columns[j]
            time = matrix[i][j]

            if int(time) >= 0:
                # Check if the record exists before updating
                cursor.execute(
                    "SELECT COUNT(*) FROM Connection ct join Camera sc on sc.id = ct.sourceCam_id join Camera dc on dc.id = ct.destinationCam_id WHERE sc.name = ? AND dc.name = ?",
                    (sourceCam, destinationCam)
                )
                record_count = cursor.fetchone()[0]

                if record_count > 0:
                    # Update cost value
                    cursor.execute(
                        "UPDATE Connection SET timeToReach = ? From Connection ct join Camera sc on sc.id = ct.sourceCam_id join Camera dc on dc.id = ct.destinationCam_id WHERE sc.name = ? AND dc.name = ?",
                        (time, sourceCam, destinationCam))

                    cursor.execute(
                        "UPDATE Connection SET timeToReach = ? From Connection ct join Camera sc on sc.id = ct.sourceCam_id join Camera dc on dc.id = ct.destinationCam_id WHERE sc.name = ? AND dc.name = ?",
                        (time, destinationCam, sourceCam))

                else:
                    cursor.execute(
                        "SELECT id FROM Camera WHERE name = ?",
                        (sourceCam)
                    )
                    source_cam_id = cursor.fetchone()[0]

                    # Fetch destinationCam_id based on destinationCamName
                    cursor.execute(
                        "SELECT id FROM Camera WHERE name = ?",
                        (destinationCam)
                    )
                    destination_cam_id = cursor.fetchone()[0]

                    #insert record
                    cursor.execute(
                        "INSERT INTO Connection (sourceCam_id, destinationCam_id, timeToReach) VALUES (?, ?, ?)",
                        (source_cam_id, destination_cam_id, time)
                    )

                    cursor.execute(
                        "INSERT INTO Connection (sourceCam_id, destinationCam_id, timeToReach) VALUES (?, ?, ?)",
                        (destination_cam_id, source_cam_id, time)
                    )

            else:
                # Delete the record
                cursor.execute(
                    "DELETE FROM Connection From Connection ct join Camera sc on sc.id = ct.sourceCam_id join Camera dc on dc.id = ct.destinationCam_id  WHERE sc.name = ? AND dc.name = ?",
                    (sourceCam, destinationCam)
                )

                cursor.execute(
                    "DELETE FROM Connection From Connection ct join Camera sc on sc.id = ct.sourceCam_id join Camera dc on dc.id = ct.destinationCam_id  WHERE sc.name = ? AND dc.name = ?",
                    (destinationCam, sourceCam)
                )
    conn.commit()
    conn.close()
    return 'Connections updated successfully'






def get_restricted_cameras():
    try:
        query = "SELECT RL.id as 'restricted_id',L.id as 'location_id',L.name as 'location_name', RL.start_datetime as 'start_datetime',RL.end_datetime as 'end_datetime' FROM [RestrictedLocation] RL JOIN Location L ON RL.location_id = L.id WHERE RL.end_datetime >= GETDATE();"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                for row in rows:
                    restricted_cam_query = f"SELECT TOP 1 C.id as 'camera_id', C.name as 'camera_name' FROM Camera C JOIN CameraLocation CL ON C.id = CL.camera_id JOIN Location L ON L.id = CL.location_id WHERE L.id={row['location_id']}"
                    cursor.execute(restricted_cam_query)
                    res_cam_result = cursor.fetchone()

                    if res_cam_result:

                        row['camera_id'] =  res_cam_result[0]
                        row['camera_name'] = res_cam_result[1]
                    else:
                        row['camera_id'] = None
                        row['camera_name'] = None

            return jsonify(rows)

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch restricted cameras.'}), 500







def get_dump_images():
    try:
        base_path = 'Unknown_Persons'
        camera_param = request.args.get('camera')
        start_date_param = request.args.get('start_date')
        end_date_param = request.args.get('end_date')

        all_files = []
        if camera_param:
            camera_path = os.path.join(base_path, camera_param)
            if os.path.isdir(camera_path):
                files_in_camera = os.listdir(camera_path)
                for filename in files_in_camera:
                    full_path = os.path.join(base_path, camera_param, filename)
                    file_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    if (not start_date_param or file_datetime.date() >= datetime.datetime.fromisoformat(
                            start_date_param).date()) and \
                            (not end_date_param or file_datetime.date() <= datetime.datetime.fromisoformat(
                                end_date_param).date()):
                        with open(full_path, "rb") as image_file:
                            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                        all_files.append({
                            'filename': filename,
                            'camera': camera_param,
                            'full_path': full_path,
                            'date': file_datetime.date().isoformat(),
                            'time': file_datetime.strftime('%I:%M %p'),
                            'image':encoded_image
                        })
        else:
            for camera_folder in os.listdir(base_path):
                camera_path = os.path.join(base_path, camera_folder)
                if os.path.isdir(camera_path):
                    files_in_camera = os.listdir(camera_path)
                    for filename in files_in_camera:
                        full_path = os.path.join(base_path, camera_folder, filename)
                        file_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                        if (not start_date_param or file_datetime.date() >= datetime.datetime.fromisoformat(
                                start_date_param).date()) and \
                                (not end_date_param or file_datetime.date() <= datetime.datetime.fromisoformat(
                                    end_date_param).date()):

                            with open(full_path, "rb") as image_file:
                                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                            all_files.append({
                                'filename': filename,
                                'camera': camera_folder,
                                'full_path': full_path,
                                'date': file_datetime.date().isoformat(),
                                'time': file_datetime.strftime('%I:%M %p'),
                                'image': encoded_image
                            })

        all_files.sort(key=lambda x: int(re.sub('\D', '', x['filename'])))
        return jsonify(images=all_files)

    except Exception as e:
        print(e)
        return str(e)