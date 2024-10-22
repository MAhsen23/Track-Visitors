import pyodbc
from flask import jsonify,request
import requests
import Extras_Func

import DB_Connection
conn_string = DB_Connection.conn_string()
url = DB_Connection.url()

def get_paths():
    try:
        source = request.json['source']
        destination = request.json['destination']

        connection = pyodbc.connect(conn_string)
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM Camera")
        camera_names = [row[0] for row in cursor.fetchall()]

        camera_dict = {name: [-1] * len(camera_names) for name in camera_names}

        for source_idx, source_camera in enumerate(camera_names):
            for destination_idx, destination_camera in enumerate(camera_names):
                query = f"SELECT timeToReach FROM Connection WHERE sourceCam_id = (SELECT id FROM Camera WHERE name = '{source_camera}') AND destinationCam_id = (SELECT id FROM Camera WHERE name = '{destination_camera}')"
                cursor.execute(query)
                time_row = cursor.fetchone()
                if time_row:
                    time_to_reach = time_row[0]
                    camera_dict[source_camera][destination_idx] = time_to_reach

        connection.close()

        costMatrix = {name: times for name, times in zip(camera_names, camera_dict.values())}
        print(costMatrix)
        paths = Extras_Func.find_all_paths(costMatrix, source, destination)

        return jsonify(paths)

    except Exception as e:
        return jsonify({'error': str(e)})



def get_location_paths():
    try:
        source = request.json['source']
        destinations = request.json['destinations']

        connection_matrix = Extras_Func.get_cost_matrix_with_ids(conn_string)

        destination_cam_ids = []
        for destination_id in destinations:
            response = requests.get(f'{url}/GetCameraByLocation/{destination_id}')
            camera_id = response.json()[0]['camera_id']
            destination_cam_ids.append(camera_id)

        response = requests.get(f'{url}/GetCameraByLocation/{source}')
        source_camera_id = response.json()[0]['camera_id']

        paths = Extras_Func.find_all_paths(connection_matrix,source_camera_id,destination_cam_ids)
        response = requests.get(f'{url}/GetRestrictedCameras')
        restricted_details = response.json()

        restricted_cam_ids = []
        for restricted_detail in restricted_details:
            if restricted_detail['camera_id'] is not None:
                restricted_cam_ids.append(restricted_detail['camera_id'])

        locationPaths = []

        for path_index, path in enumerate(paths):
            if any(camera_id in restricted_cam_ids for camera_id in path):
                continue

            locationPath = []
            last_camera_index = len(path) - 1

            for camera_index, each_camera_id in enumerate(path):
                is_last_camera = camera_index == last_camera_index
                if is_last_camera:

                    location_index = destination_cam_ids.index(each_camera_id)
                    location_id = destinations[location_index]
                    response = requests.get(f'{url}/GetLocation/{location_id}', )
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['name'])

                else:
                    response = requests.get(f'{url}/GetLocationByCameraId/{each_camera_id}', )
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['LocationName'])

            locationPaths.append(locationPath)

        return jsonify(locationPaths)

    except Exception as e:
        return jsonify({'error': str(e)})


def get_location_paths_with_time():
    try:
        source = request.json['source']
        destinations = request.json['destinations']

        connection_matrix = Extras_Func.get_cost_matrix_with_ids(conn_string)

        destination_cam_ids = []
        for destination_id in destinations:
            response = requests.get(f'{url}/GetCameraByLocation/{destination_id}')
            camera_id = response.json()[0]['camera_id']
            destination_cam_ids.append(camera_id)

        response = requests.get(f'{url}/GetCameraByLocation/{source}')
        source_camera_id = response.json()[0]['camera_id']

        paths = Extras_Func.find_all_paths(connection_matrix, source_camera_id, destination_cam_ids)
        response = requests.get(f'{url}/GetRestrictedCameras')
        restricted_details = response.json()

        restricted_cam_ids = []
        for restricted_detail in restricted_details:
            if restricted_detail['camera_id'] is not None:
                restricted_cam_ids.append(restricted_detail['camera_id'])

        locationPaths = []
        times = []

        for path_index, path in enumerate(paths):
            if any(camera_id in restricted_cam_ids for camera_id in path):
                continue

            total_time = 0
            locationPath = []
            last_camera_index = len(path) - 1

            for camera_index, each_camera_id in enumerate(path):
                is_last_camera = camera_index == last_camera_index
                if is_last_camera:
                    location_index = destination_cam_ids.index(each_camera_id)
                    location_id = destinations[location_index]
                    response = requests.get(f'{url}/GetLocation/{location_id}')
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['name'])
                else:
                    timeBtwCameras = Extras_Func.get_time_btw_cams(conn_string,each_camera_id,str(path[camera_index + 1]))
                    total_time += timeBtwCameras

                    response = requests.get(f'{url}/GetLocationByCameraId/{each_camera_id}')
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['LocationName'])

            locationPaths.append(locationPath)
            times.append(total_time)

        sorted_paths_with_times = sorted(zip(locationPaths, times), key=lambda x: x[1])
        sorted_paths, sorted_times = zip(*sorted_paths_with_times)

        return jsonify({'locationPaths': sorted_paths, 'times': sorted_times})

    except Exception as e:
        return jsonify({'error': str(e)})


def get_connection_matrix():
    try:
        connection = pyodbc.connect(conn_string)
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM Camera")
        camera_ids = [row[0] for row in cursor.fetchall()]

        camera_dict = {id: [-1] * len(camera_ids) for id in camera_ids}

        for source_idx, source_camera in enumerate(camera_ids):
            for destination_idx, destination_camera in enumerate(camera_ids):
                query = f"SELECT timeToReach FROM Connection WHERE sourceCam_id = {source_camera} AND destinationCam_id = {destination_camera}"
                cursor.execute(query)
                time_row = cursor.fetchone()
                if time_row:
                    time_to_reach = time_row[0]
                    camera_dict[source_camera][destination_idx] = time_to_reach

        connection.close()

        costMatrix = {id: times for id, times in zip(camera_ids, camera_dict.values())}

        return jsonify(costMatrix)

    except Exception as e:
        return jsonify({'error': str(e)})








def get_visit_path_history():
    try:
        visitor_id = request.json['visitor_id']

        query = """SELECT VP.visit_id, VP.time, VP.camera_id, VP.is_violated, C.id AS 'camera_id', C.name AS 'camera_name', F.name AS 'floor_name', STRING_AGG(L.name, ', ') AS locations
        FROM VisitPathHistory VP
        JOIN Visit V ON V.id = VP.visit_id
        JOIN Camera C ON C.id = VP.camera_id
        JOIN CameraLocation CL ON CL.camera_id = C.id
        JOIN Location L ON L.id = CL.location_id
        JOIN Floor F ON F.id = L.floor_id
        WHERE VP.visit_id = (SELECT id FROM Visit WHERE visitor_id = ? AND exit_time IS NULL)
        GROUP BY VP.visit_id, VP.time, VP.camera_id, VP.is_violated, C.id, C.name, F.name;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (visitor_id,))
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch visit path history.'}), 500
