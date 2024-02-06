import time
import queue
import threading
import random
from visitorsInFrame import *
import datetime
from flask import Flask, request,send_file,send_from_directory
from werkzeug.utils import secure_filename
from FaceNet import training
from FaceNet_perform_video import *
from FaceNet_perform_image import *
from API import User,Floor,Location,Camera,Login,Path,Visitor,Block,Reports,Alert,Visit
import requests
import base64
from Extras_Func import *
from rq import Queue
from redis import Redis


app = Flask(__name__)
has_started = False
GlobalFrameCounter = 0
redis_conn = Redis()
rq_queue = Queue(connection=redis_conn)

import DB_Connection

conn_string = DB_Connection.conn_string()
url = DB_Connection.url()
frame_queue = queue.Queue()


@app.route('/images/<path:image_name>')
def serve_image(image_name):
    return send_from_directory('result', image_name)


@app.route('/GetDumpImage')
def get_unknown_image():
    path = request.args.get('path')
    return send_file(path, as_attachment=True)


@app.route('/GetDumpImagesList')
def get_dump_images_list():
    try:
        base_path = 'Unknown_Persons'
        camera_param = request.args.get('camera')
        start_date_param = request.args.get('start_date')
        end_date_param = request.args.get('end_date')

        if start_date_param == end_date_param:
            end_date_param=None

        all_files = []
        if camera_param:
            camera_path = os.path.join(base_path, camera_param)
            if os.path.isdir(camera_path):
                files_in_camera = os.listdir(camera_path)
                for filename in files_in_camera:
                    full_path = os.path.join(base_path, camera_param, filename)
                    file_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    if (not start_date_param or file_datetime >= datetime.datetime.fromisoformat(start_date_param)) and \
                       (not end_date_param or file_datetime <= datetime.datetime.fromisoformat(end_date_param)):
                        all_files.append({
                            'filename': filename,
                            'camera': camera_param,
                            'full_path': full_path,
                            'date': file_datetime.date().isoformat(),
                            'time': file_datetime.strftime('%I:%M %p')
                        })
        else:
            for camera_folder in os.listdir(base_path):
                camera_path = os.path.join(base_path, camera_folder)
                if os.path.isdir(camera_path):
                    files_in_camera = os.listdir(camera_path)
                    for filename in files_in_camera:
                        full_path = os.path.join(base_path, camera_folder, filename)
                        file_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                        if (not start_date_param or file_datetime >= datetime.datetime.fromisoformat(start_date_param)) and \
                           (not end_date_param or file_datetime <= datetime.datetime.fromisoformat(end_date_param)):
                            all_files.append({
                                'filename': filename,
                                'camera': camera_folder,
                                'full_path': full_path,
                                'date': file_datetime.date().isoformat(),
                                'time': file_datetime.strftime('%I:%M %p')
                            })

        all_files.sort(key=lambda x: int(re.sub('\D', '', x['filename'])))
        return jsonify(images=all_files)

    except Exception as e:
        print(e)
        return str(e)


@app.route('/video')
def serve_video():
    video_path = 'testing/video3.mp4'
    return send_file(video_path)


@app.route('/VisitorImages/<string:id>')
def visitor_img(id):
    try:
        directory_path = f'Images/{id}'
        filename = os.listdir(directory_path)[0]
        with open(os.path.join(directory_path, filename), "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        return {'image': encoded_image}
    except Exception as e:
        return str(e)


@app.route('/Login', methods=['POST'])
def login_route():
    return Login.login()


@app.route('/GetAllUsers', methods=['GET'])
def get_all_users_route():
    return User.get_all_users()


@app.route('/GetAllGuardsLocation', methods=['GET'])
def get_all_guards_location_route():
    return User.get_all_guards_location()


@app.route('/GetGuardDutyLocation/<int:id>', methods=['GET'])
def get_guard_duty_location_route(id):
    return User.get_guard_duty_location(id)


@app.route('/GetUser/<int:id>', methods=['GET'])
def get_user_route(id):
    return User.get_user(id)


@app.route('/AddUser', methods=['POST'])
def add_user_route():
    return User.add_user()


@app.route('/UpdateUser/<int:id>', methods=['PUT'])
def update_user_route(id):
    return User.update_user(id)


@app.route('/DeleteUser/<int:id>', methods=['DELETE'])
def delete_user_route(id):
    return User.delete_user(id)


@app.route('/AllocateDutyLocation/<int:id>',methods=['PUT'])
def allocate_duty_location_route(id):
    return User.allocate_duty_location(id)


@app.route('/GetAllFloors', methods=['GET'])
def get_all_floors_route():
    return Floor.get_all_floors()


@app.route('/AddFloor', methods=['POST'])
def add_floor_route():
    return Floor.add_floor()


@app.route('/UpdateFloor/<int:id>', methods=['PUT'])
def update_floor_route(id):
    return Floor.update_floor(id)


@app.route('/DeleteFloor/<int:id>', methods=['DELETE'])
def delete_floor(id):
    return Floor.delete_floor(id)


@app.route('/DeleteFloors', methods=['POST'])
def delete_floors():
    return Floor.delete_floors()


@app.route('/GetAllLocations', methods=['GET'])
def get_all_locations_route():
    return Location.get_all_locations()


@app.route('/GetLocation/<int:id>', methods=['GET'])
def get_location_route(id):
    return Location.get_location(id)


@app.route('/GetLocationsByFloor/<int:id>', methods=['GET'])
def get_locations_by_floor_route(id):
    return Location.get_locations_by_floor(floor_id=id)


@app.route('/AddLocation', methods=['POST'])
def add_location_route():
    return Location.add_location()


@app.route('/UpdateLocation/<int:id>', methods=['PUT'])
def update_location_route(id):
    return Location.update_location(id)


@app.route('/DeleteLocation/<int:id>', methods=['DELETE'])
def delete_location_route(id):
    return Location.delete_location(id)


@app.route('/GetLocationByCamera/<string:name>', methods=['GET'])
def get_location_by_camera_route(name):
    return Location.get_location_by_camera(name)


@app.route('/GetLocationByCameraId/<int:id>', methods=['GET'])
def get_location_by_camera_id_route(id):
    return Location.get_location_by_camera_id(id)


@app.route('/GetRestrictedLocations', methods=['GET'])
def get_restricted_locations_route():
    return Location.get_restricted_locations()


@app.route('/RestrictLocation', methods=['POST'])
def restrict_location_route():
    return Location.restrict_location()

@app.route('/PermitLocation')
def permit_location_route():
    return Location.permit_location()

@app.route('/GetAllCameras', methods=['GET'])
def get_all_cameras():
    return Camera.get_all_cameras()

@app.route('/GetCameraById', methods=['GET'])
def get_camera_by_id():
    return Camera.get_camera_by_id()

@app.route('/AddCamera', methods=['POST'])
def add_camera_route():
    return Camera.add_camera()


@app.route('/DeleteCamera/<int:id>', methods=['DELETE'])
def delete_camera_route(id):
    return Camera.delete_camera(id)


@app.route('/UpdateCamera/<int:id>', methods=['PUT'])
def update_camera_route(id):
    return Camera.update_camera(id)


@app.route('/GetAllCamerasLocationsConnections', methods=['GET'])
def get_all_cameras_locations_connections_route():
    return Camera.get_all_cameras_locations_connections()


@app.route('/GetCameraByLocation/<int:id>')
def get_camera_by_location_route(id):
    return Camera.get_camera_by_location(location_id=id)


@app.route('/GetCameraMatrix', methods=['GET'])
def get_adjacency_matrix_route():
    return Camera.get_adjacency_matrix()


@app.route('/UpdateMatrix', methods=['POST'])
def update_adjacency_matrix_route():
    return Camera.update_adjacency_matrix()


@app.route('/GetRestrictedCameras')
def get_restricted_cameras_route():
    return Camera.get_restricted_cameras()


@app.route('/GetDumpImages')
def get_dump_images_route():
    return Camera.get_dump_images()


@app.route('/GetVisitorReport')
def get_visitor_report_route():
    return Reports.get_visitor_report()


@app.route('/GetVisitorsReport', methods=['POST'])
def get_visitors_report_route():
    response = Reports.get_visitors_report()
    return Reports.get_visitors_report()

@app.route('/DownloadVisitorsReport', methods=['POST'])
def download_visitors_report_route():
    return Reports.download_visitors_report()


@app.route('/AddAlert', methods=['POST'])
def add_alert_route():
    return Alert.add_alert()


@app.route('/GetAlertCount')
def get_alert_count_route():
    return Alert.get_alert_count()


@app.route('/GetCurrentAlerts', methods=['GET'])
def get_current_alert_route():
    return Alert.get_current_alerts()

@app.route('/GetAllAlerts', methods=['GET'])
def get_all_alerts_route():
    return Alert.get_all_alerts()

@app.route('/GetVisitorAlerts', methods=['GET'])
def get_visitor_alerts_route():
    return Alert.get_visitor_alerts()

@app.route('/AddVisitor', methods=['POST'])
def add_visitor():
    try:
        name = request.form.get('name')
        phone = request.form.get('contact')
        count = request.form.get('count')
        inserted_id = None

        query = "INSERT INTO [Visitor] (name, phone) VALUES (?, ?)"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, phone))

                cursor.execute("SELECT TOP 1 id FROM [Visitor] ORDER BY id DESC")
                inserted_id = cursor.fetchone()[0]
                conn.commit()

        folder_path = os.path.join("Images", str(inserted_id))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(int(count)):
            image = request.files[f'image{i+1}']
            filename = secure_filename(image.filename)
            image.save(os.path.join(folder_path, filename))

        training()

        image_urls = [str(inserted_id) + "/" + filename for filename in os.listdir(folder_path)]

        for image_url in image_urls:
            picture_query = "INSERT INTO [Picture] (visitor_id, image_url) VALUES (?, ?)"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(picture_query, (inserted_id, image_url))
                conn.commit()

        return jsonify({'message': 'Visitor data and images saved successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to process the request', 'details': str(e)}), 500


@app.route('/GetAllVisitors', methods=['GET'])
def get_all_visitors_route():
   return Visitor.get_all_visitors()


@app.route('/GetCurrentVisitors', methods=['GET'])
def get_current_visitors_route():
   return Visitor.get_current_visitors()

@app.route('/GetTodayVisitors', methods=['GET'])
def get_today_visitors_route():
    return Visitor.get_today_visitors()

@app.route('/GetSearchTodayVisitors', methods=['GET'])
def get_search_today_visitors_route():
    return Visitor.search_today_visitors()

@app.route('/GetWeeklyVisitors', methods=['GET'])
def get_weekly_visitors_route():
    return Visitor.get_weekly_visitors()

@app.route('/GetBlockVisitors', methods=['GET'])
def get_block_visitors_route():
    return Block.get_block_visitors()


@app.route('/BlockVisitor', methods=['POST'])
def block_visitor_route():
    return Block.block_visitor()

@app.route('/BlockVisitorForDay')
def block_visitor_for_day():
    return Block.block_visitor_for_one_day()

@app.route('/ExtendBlock/<int:id>', methods=['POST'])
def extend_block_route(id):
    return Block.extend_block(visitor_id=id)


@app.route('/UnblockVisitor', methods=['POST'])
def unblock_visitor_route():
    return Block.unblock_visitor()


@app.route('/CheckVisitorBlocked/<int:id>')
def check_visitor_blocked_route(id):
    return Block.check_visitor_blocked(visitor_id=id)


@app.route('/GetVisitorWithImage', methods=['POST'])
def get_visitor_with_image():
    try:
        image = request.files['image']
        image_data = image.read()

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result = recognizeVisitor(img)
        print(result)

        query = f"SELECT V.*, CASE WHEN B.id IS NOT NULL AND B.end_date >= GETDATE() THEN 'True' ELSE 'False' END AS block FROM Visitor V LEFT JOIN [Block] B ON V.id = B.visitor_id where V.id={result}"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        print(rows)
        return jsonify(rows), 200

    except Exception as e:
        return f"An error occurred while fetching visitor with image: {str(e)}", 500


@app.route('/CheckVisitorIsPresentInFrame', methods=['POST'])
def checkVisitorInFrame():
    try:
        image = request.files['image']
        image_data = image.read()
        visitor_id = request.form.get('visitor_id')

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result, annotated_image = recognizeOneVisitorInFrame(img, visitor_id)
        response_data = {
            "visitorFound": result
        }

        return jsonify(response_data), 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/CheckVisitorIsPresent', methods=['POST'])
def checkVisitorInVideo():
    try:
        time = request.form.get('time')
        time_format = datetime.datetime.strptime(time, '%I:%M %p').time()
        video = request.files['video']
        camera_id = request.form.get('camera_id')
        camera_name = request.form.get('camera_name')
        visitor_id = request.form.get('visitor_id')

        print("Camera data Received........")

        video_filename = video.filename
        video.save(video_filename)

        result = recognizeOneVisitorInVideo(video_filename,visitor_id,camera_name,camera_id)

        if result[0]:

            query_visit = f"select top 1 id from Visit where visitor_id = {visitor_id} and exit_time is NULL order by id desc"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_visit)
                    visit_id = cursor.fetchone()[0]

            query = f"SELECT c.name FROM VisitPathHistory v JOIN Camera c ON v.camera_id = c.id WHERE v.visit_id = {visit_id}"

            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    path_history = [record.name for record in cursor.fetchall()]

            path_history.append(camera_name)
            last_visited = path_history[-2]

            folder_path = 'VisitCorrectPaths'
            file_name = os.path.join(folder_path, f"{visitor_id}.json")
            paths = load_records(file_name)

            is_not_deviated = is_visitor_on_correct_path(path_history, paths)

            if last_visited != camera_name:

                if is_not_deviated or paths[1][-1] == camera_name:

                    path_history_query = f"insert into VisitPathHistory(visit_id,time,camera_id,is_violated) values ({visit_id}, '{time_format}', {camera_id}, 0)"
                    with pyodbc.connect(conn_string) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(path_history_query)
                            conn.commit()

                else:
                    path_history_query = f"insert into VisitPathHistory(visit_id,time,camera_id,is_violated) values ({visit_id}, '{time_format}', {camera_id}, 1)"
                    with pyodbc.connect(conn_string) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(path_history_query)
                            conn.commit()

                    json_data = {'camera_id': camera_id, 'visit_id': visit_id, 'type':'danger'}
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(f'{url}/AddAlert', json=json_data, headers=headers)

        else:
            is_not_deviated = None

        details = {
            "time":time,
            "camera":camera_name,
            "detect":result[0],
            "is_not_deviated":is_not_deviated,
        }

        os.remove(video_filename)
        return jsonify({'details': details}), 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/GetDetectedFrame/<string:visitor_id>/<string:camera_name>')
def get_detected_frame(visitor_id,camera_name):
    try:
        directory_path = 'CamerasResult'
        filename = f"{visitor_id}_{camera_name}.jpg"
        with open(os.path.join(directory_path, filename), "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        return {'image': encoded_image}
    except Exception as e:
        return str(e)


def generate_warnings(threshold,visit_id,entry_time,source_cam_id,paths):
    previous_visit_history_id = ""
    while True:
        check_query = f"select * from Visit where id={visit_id} and exit_time is NULL"
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(check_query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]


        if len(rows) < 1:
            print("Visit Ended... Generate Warning function Terminates...")
            break

        sec = int(int(threshold)*60)
        query = f"SELECT top 1 v.id, v.visit_id,is_violated,c.id as 'camera_id',c.name as 'camera_name',v.time as 'visit_cam_time' FROM VisitPathHistory v JOIN Camera c ON v.camera_id = c.id  WHERE v.visit_id = {visit_id} order by id desc"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if previous_visit_history_id == rows[0]['id']:

            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT top 2 v.id, v.visit_id,is_violated,c.id as 'camera_id',c.name as 'camera_name',v.time as 'visit_cam_time' FROM VisitPathHistory v JOIN Camera c ON v.camera_id = c.id  WHERE v.visit_id = {visit_id} order by id desc")
                    newCols = [column[0] for column in cursor.description]
                    newRows = [dict(zip(newCols, row)) for row in cursor.fetchall()]


            if rows[0]['camera_id'] == source_cam_id and len(newRows)<2:

                print("Visitor is on source camera")

                camera_name = rows[0]['camera_name']
                possible_destination_cameras = []
                for path in paths:
                    if camera_name in path:
                        index_of_camera = path.index(camera_name)
                        if index_of_camera < len(path) - 1:
                            next_element = path[index_of_camera + 1]
                            possible_destination_cameras.append(next_element)
                        else:
                            possible_destination_cameras.append(None)
                    else:
                        possible_destination_cameras.append(None)


                cost_matrix = get_cost_matrix(conn_string)
                time_values = []


                for destination_camera in possible_destination_cameras:
                    if destination_camera in cost_matrix:
                        destination_camera_index = list(cost_matrix.keys()).index(destination_camera)
                        time_value = cost_matrix[camera_name][destination_camera_index]
                        time_values.append(time_value)

                max_time = max([t for t in time_values if t is not None])

                current_datetime = datetime.datetime.now()
                current_time_str = current_datetime.strftime('%H:%M:%S.%f')[:-3]
                entry_time_str = entry_time.strftime('%H:%M:%S.%f')[:-3]
                time_difference = int((datetime.datetime.strptime(current_time_str, '%H:%M:%S.%f') - datetime.datetime.strptime(entry_time_str, '%H:%M:%S.%f')).total_seconds())

                if time_difference > sec+max_time:
                    json_data = {'camera_id': rows[0]['camera_id'], 'visit_id': visit_id, 'type': 'warning'}
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(f'{url}/AddAlert', json=json_data, headers=headers)
            else:

                print("Visitor is not on source camera")

                camera_name = newRows[0]['camera_name']
                possible_destination_cameras = []
                for path in paths:
                    if camera_name in path:
                        index_of_camera = path.index(camera_name)
                        if index_of_camera < len(path) - 1:
                            next_element = path[index_of_camera + 1]
                            possible_destination_cameras.append(next_element)
                        else:
                            possible_destination_cameras.append(None)
                    else:
                        possible_destination_cameras.append(None)


                cost_matrix = get_cost_matrix(conn_string)
                time_values = []

                for destination_camera in possible_destination_cameras:
                    if destination_camera in cost_matrix:
                        destination_camera_index = list(cost_matrix.keys()).index(destination_camera)
                        time_value = cost_matrix[camera_name][destination_camera_index]
                        time_values.append(time_value)

                max_time = max([t for t in time_values if t is not None])

                current_datetime = datetime.datetime.now()
                current_time_str = current_datetime.strftime('%H:%M:%S.%f')[:-3]

                visit_cam_time_str = newRows[0]['visit_cam_time']
                time_parts = visit_cam_time_str.split(".")
                time_components = time_parts[0].split(":")
                milliseconds = time_parts[1][:3]

                formatted_time_str = ":".join(time_components) + "." + milliseconds

                current_datetime = datetime.datetime.strptime(current_time_str, '%H:%M:%S.%f')
                visit_datetime = datetime.datetime.strptime(formatted_time_str, '%H:%M:%S.%f')
                time_difference = (current_datetime - visit_datetime).total_seconds()

                if time_difference > sec + max_time:
                    json_data = {'camera_id': newRows[0]['camera_id'], 'visit_id': visit_id, 'type': 'warning'}
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(f'{url}/AddAlert', json=json_data, headers=headers)

        else:
            previous_visit_history_id = rows[0]['id']
        time.sleep(60)


def automated(source_camera,visitor_id,visit_id):
    try:
        print(f"Automation has started for visitor: {visitor_id} and source_cam: {source_camera}")
        source_camera_id = source_camera

        while True:

            sleep_time = random.randint(30, 100)
            time.sleep(sleep_time)

            check_query = f"select * from Visit where id={visit_id} and exit_time is NULL"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(check_query)
                    columns = [column[0] for column in cursor.description]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if len(rows) < 1:
                print("Visit Ended... Automation function Terminates...")
                break

            response = requests.get(f'{url}/GetConnectionMatrix')
            connection_matrix = response.json()

            possible_movies = find_possible_moves(connection_matrix,str(source_camera_id))

            time_now = datetime.datetime.now().strftime('%I:%M %p')

            camera_id = random.choice(possible_movies)
            query_cam_name = f"select name from Camera where id={camera_id}"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_cam_name)
                    camera_name = cursor.fetchone()[0]

            is_detected = random.choice([True, False])

            if is_detected:

                query_visit = f"select top 1 id from Visit where visitor_id = {visitor_id} and exit_time is NULL order by id desc"
                with pyodbc.connect(conn_string) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query_visit)
                        visit_id = cursor.fetchone()[0]

                query = f"SELECT c.name FROM VisitPathHistory v JOIN Camera c ON v.camera_id = c.id WHERE v.visit_id = {visit_id}"

                with pyodbc.connect(conn_string) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        path_history = [record.name for record in cursor.fetchall()]

                path_history.append(camera_name)
                last_visited = path_history[-2]

                folder_path = 'VisitCorrectPaths'
                file_name = os.path.join(folder_path, f"{visitor_id}.json")
                paths = load_records(file_name)

                is_not_deviated = is_visitor_on_correct_path(path_history, paths)

                if last_visited != camera_name:

                    if is_not_deviated or paths[1][-1] == camera_name:

                        path_history_query = f"insert into VisitPathHistory(visit_id,time,camera_id,is_violated) values ({visit_id}, '{time_now}', {camera_id}, 0)"
                        with pyodbc.connect(conn_string) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute(path_history_query)
                                conn.commit()

                    else:
                        path_history_query = f"insert into VisitPathHistory(visit_id,time,camera_id,is_violated) values ({visit_id}, '{time_now}', {camera_id}, 1)"
                        with pyodbc.connect(conn_string) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute(path_history_query)
                                conn.commit()

                        json_data = {'camera_id': camera_id, 'visit_id': visit_id, 'type':'danger'}
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(f'{url}/AddAlert', json=json_data, headers=headers)

                source_camera_id=camera_id

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/GetVisitPathHistory', methods = ['POST'])
def get_visit_path_history_route():
    return Path.get_visit_path_history()


@app.route('/StartVisitWithThreads', methods=['POST'])
def start_visit_threads():
    try:
        startTime = request.json['starttime']
        visitor_id = request.json['id']
        source_id = request.json['source']
        destination_location_ids = request.json['destinations']
        user_id = request.json['user_id']
        threshold = 1

        query = f"SELECT * FROM [Visit] where visitor_id = {visitor_id} and exit_time is NULL"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if len(rows) > 0:
            print("An error occurred: A visit is already in progress with this visitor ID.")
            return jsonify({'error': f"An error occurred: A visit is already in progress with this visitor ID."}), 500


        entry_time = datetime.datetime.strptime(startTime, '%I:%M %p').time()
        current_date = datetime.datetime.now().date()
        query_visit = f"INSERT INTO Visit (visitor_id, user_id, date, entry_time,source) VALUES ({visitor_id}, {user_id}, '{current_date}', '{entry_time}',{source_id})"

        query = f"SELECT TOP 1 id FROM Visit WHERE visitor_id = {visitor_id} AND date = '{current_date}' ORDER BY id DESC"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_visit)
                conn.commit()
                cursor.execute(query)
                visit_id = cursor.fetchone()[0]


        for destination_id in destination_location_ids:
            query_visit_destination = f"""
                    INSERT INTO VisitDestination (visit_id, destination_id)
                    VALUES ({visit_id}, {destination_id});
                    """

            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_visit_destination)
                    conn.commit()


        destination_cameras = []
        for destination_id in destination_location_ids:
            response = requests.get(f'{url}/GetCameraByLocation/{destination_id}')
            camera_name = response.json()[0]['camera_name']
            destination_cameras.append(camera_name)

        response = requests.get(f'{url}/GetCameraByLocation/{source_id}')
        source_camera_id = response.json()[0]['camera_id']
        source_camera_name = response.json()[0]['camera_name']

        json_data = {'source': source_camera_name, 'destination': destination_cameras}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{url}/GetPaths', json=json_data, headers=headers)
        paths = response.json()

        print(paths)
        response = requests.get(f'{url}/GetRestrictedCameras')
        restricted_details = response.json()

        restricted_cam_names = []
        for restricted_detail in restricted_details:
            if restricted_detail['camera_id'] is not None:
                restricted_cam_names.append(restricted_detail['camera_name'])

        camera_paths = []
        for path in paths:
            if any(camera_name in restricted_cam_names for camera_name in path):
                continue
            else:
                camera_paths.append(path)
        paths = camera_paths


        locationPaths = []
        for path_index, path in enumerate(paths):

            locationPath = []
            last_camera_index = len(path) - 1

            for camera_index, each_camera_name in enumerate(path):
                is_last_camera = camera_index == last_camera_index
                if is_last_camera:

                    #only to match last location name with destination
                    location_index = destination_cameras.index(each_camera_name)
                    location_id = destination_location_ids[location_index]
                    response = requests.get(f'{url}/GetLocation/{location_id}', )
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['name'])

                else:
                    response = requests.get(f'{url}/GetLocationByCamera/{each_camera_name}',)
                    rows = response.json()
                    if len(rows) != 0:
                        locationPath.append(rows[0]['LocationName'])

            locationPaths.append(locationPath)

        path_history_query = f"insert into VisitPathHistory(visit_id,time,camera_id,is_violated) values ({visit_id}, '{entry_time}', {source_camera_id}, 0)"
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(path_history_query)
                conn.commit()

        folder_path = 'VisitCorrectPaths'
        file_name = os.path.join(folder_path, f"{visitor_id}.json")
        os.makedirs(folder_path, exist_ok=True)

        with open(file_name, 'w') as file:
            json.dump(paths, file)

        if visitor_id == 42:

            print(source_camera_id)
            thread = threading.Thread(target=automated, args=(source_camera_id,visitor_id,visit_id,))
            thread.start()

        thread = threading.Thread(target=generate_warnings, args=(threshold, visit_id, entry_time,source_camera_id,paths))
        thread.start()

        return jsonify({
            'locationPaths': locationPaths,
            'paths': paths,
            'paths': paths,
            'source': source_camera_name
        }), 200

    except Exception as e:
        print(str(e))
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@app.route('/GetVisitEntryTime/<string:id>')
def get_visit_entry_time_route(id):
    return Visit.get_visit_entry_time(id)

@app.route('/GetVisitDestinations')
def get_visit_destinations_route():
    return Visit.get_visit_destinations()

@app.route('/EndVisit', methods=['POST'])
def end_visit():
    try:
        data = request.get_json()
        visitor_id = data.get('visitor_id')
        exitTime = datetime.datetime.now()

        if not visitor_id:
            return jsonify({'error': 'Missing visitor_id in request'}), 400

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                query = "SELECT top 1 id FROM visit WHERE visitor_id = ? AND exit_time IS NULL order by id desc"
                cursor.execute(query, (visitor_id,))
                visit_id = cursor.fetchone()

                if not visit_id:
                    return jsonify({'error': f"No ongoing visit for visitor_id: {visitor_id}"}), 404

                visit_id = visit_id[0]

                exitQuery = "UPDATE visit SET exit_time = ? WHERE id = ?"
                cursor.execute(exitQuery, (exitTime, visit_id))
                conn.commit()


        folder_path = 'VisitCorrectPaths'
        file_name = os.path.join(folder_path, f"{visitor_id}.json")
        os.remove(file_name)

        return jsonify({'message': 'Visit ended successfully'}), 200

    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@app.route('/GetPaths',methods=['POST'])
def get_paths_route():
    return Path.get_paths()


@app.route('/GetLocationPaths',methods=['POST'])
def get_location_paths_route():
    return Path.get_location_paths()

@app.route('/GetLocationPathsWithTime',methods=['POST'])
def get_location_paths_with_time_route():
    return Path.get_location_paths_with_time()

@app.route('/GetConnectionMatrix')
def get_connection_matrix_route():
    return Path.get_connection_matrix()

def process_stream(camera_id, camera_name):

    print("Thread Started of Camera", camera_id, camera_name)

    while True:
        time.sleep(10)
        print("No visit.....")
        query_visit_chk = f"select * from Visit where exit_time is NULL"
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_visit_chk)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if len(rows) != 0:
            break

    videoPath = f"CamerasVideo/{camera_id}.webm"
    if not os.path.exists(videoPath):
        return

    cap = cv2.VideoCapture(videoPath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frameCounter = 1

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frameCounter += 1
            if frameCounter % int(fps) == 0:
                frame_queue.put((camera_id,camera_name, frame,frameCounter))
                time.sleep(1)
    cap.release()


def start_threads_for_camera():
    try:
        frame_queue.queue.clear()
        response = requests.get(f'{url}/GetAllCameras')
        cameras_data = response.json()

        threads = []
        for camera_data in cameras_data:
            thread = threading.Thread(target=process_stream, args=(camera_data['id'], camera_data['name'],))
            threads.append(thread)
            thread.start()

        while True:
            camera_id, camera_name, frame, frameCounter = frame_queue.get()
            print(f"Processing frame from Camera {camera_id}")
            visitors_in_one_frame = returnVisitorsInFrame(frame)
            print(f"Visitors Detected from Camera{camera_name} in frame {frameCounter} is :", visitors_in_one_frame)

            response = requests.get(f'{url}/GetCurrentVisitors')
            current_visitors = response.json()

            current_visitor_ids = [visitor['id'] for visitor in current_visitors]
            print(f"Current Visitors :",current_visitor_ids)

            current_visitors_detected_in_frame = [visitor for visitor in visitors_in_one_frame if int(visitor) in current_visitor_ids]
            print(f"Current Visitors detected in Camera{camera_name} is :", current_visitors_detected_in_frame)

            for current_visitor_detected in current_visitors_detected_in_frame:
                query_visit = f"select top 1 id from Visit where visitor_id = {current_visitor_detected} and exit_time is NULL order by id desc"
                with pyodbc.connect(conn_string) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query_visit)
                        visit_id = cursor.fetchone()[0]

                query = f"SELECT c.name FROM VisitPathHistory v JOIN Camera c ON v.camera_id = c.id WHERE v.visit_id = {visit_id}"

                with pyodbc.connect(conn_string) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        path_history = [record.name for record in cursor.fetchall()]

                path_history.append(camera_name)
                last_visited = path_history[-2]

                folder_path = 'VisitCorrectPaths'
                file_name = os.path.join(folder_path, f"{current_visitor_detected}.json")
                paths = load_records(file_name)

                is_not_deviated = is_visitor_on_correct_path(path_history, paths)

                if last_visited != camera_name:
                    if is_not_deviated or paths[1][-1] == camera_name:
                        path_history_query = f"insert into VisitPathHistory(visit_id, time, camera_id, is_violated) values ({visit_id}, '{datetime.datetime.now()}', {camera_id}, 0)"
                        with pyodbc.connect(conn_string) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute(path_history_query)
                                conn.commit()
                    else:
                        path_history_query = f"insert into VisitPathHistory(visit_id, time, camera_id, is_violated) values ({visit_id}, '{datetime.datetime.now()}', {camera_id}, 1)"
                        with pyodbc.connect(conn_string) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute(path_history_query)
                                conn.commit()

                        json_data = {'camera_id': camera_id, 'visit_id': visit_id, 'type': 'danger'}
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(f'{url}/AddAlert', json=json_data, headers=headers)

            time.sleep(2)
            frame_queue.task_done()

    except Exception as e:
        print(e)
        print("An error occurred..")


def on_startup():
    global has_started
    print("Executing on_startup function")
    if not has_started:
        thread = threading.Thread(target=start_threads_for_camera)
        thread.start()
        has_started = True


if __name__ == '__main__':
    #on_startup()
    app.run(debug=True, use_reloader=True)