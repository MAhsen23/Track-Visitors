import os
from datetime import datetime
import pyodbc
from flask import jsonify,request
import DB_Connection
conn_string = DB_Connection.conn_string()
url = DB_Connection.url()
from Extras_Func import load_records
import requests

def add_alert():
    try:
        camera_id = request.json['camera_id']
        visit_id = request.json['visit_id']
        type = request.json['type']
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = f"INSERT INTO Alert (visit_id, datetime, camera_id,type) VALUES ({visit_id}, '{current_datetime}', {camera_id},'{type}')"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Alert added successfully!'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to add alert.'}), 500




def get_alert_count():
    try:
        query=""

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        print(rows)
        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to get alert count.'}), 500



def get_current_alerts():
    try:
        query = """
        SELECT
            A.id AS AlertID, A.type as 'type', A.datetime AS AlertDateTime,V.id AS VisitID,V.visitor_id AS VisitorID,V.user_id AS UserID,
            V.date AS VisitDate,V.entry_time AS EntryTime,C.id AS CameraID,C.name AS CameraName
        FROM
            Alert A
        JOIN
            Visit V ON A.visit_id = V.id
        JOIN
            Camera C ON A.camera_id = C.id
        WHERE
            V.exit_time IS NULL
            AND A.id = (
                SELECT TOP 1 id
                FROM Alert
                WHERE visit_id = A.visit_id
                ORDER BY datetime)"""

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch current alerts.'}), 500



def get_all_alerts():
    try:
        query = """SELECT
            A.id,
            A.type as 'type',
            CONVERT(DATE, A.datetime) AS 'date', -- Separate date
            FORMAT(A.datetime, 'hh:mm tt') AS 'time', -- Separate time
            A.visit_id,
            VR.id AS 'visitor_id',
            VR.name AS 'visitor_name',
            VR.phone AS 'visitor_contact',
            A.camera_id,
            L.id AS 'location_id',
            STRING_AGG(L.name, ', ') AS 'destinations',
            C.name AS 'camera_name',
            (
                SELECT TOP 1 L.name
                FROM CameraLocation CL
                JOIN Location L ON L.id = CL.location_id
                WHERE CL.camera_id = A.camera_id
            ) AS 'current_location'
        FROM
            Alert A
        JOIN
            Camera C ON C.id = A.camera_id
        JOIN
            VisitDestination VD ON A.visit_id = VD.visit_id
        JOIN
            Location L ON L.id = VD.destination_id
        JOIN 
            VISIT VS ON VS.id = A.visit_id
        JOIN 
            Visitor VR ON VR.id = VS.visitor_id
         
        WHERE
        VS.exit_time IS NULL
                    
        GROUP BY
            A.id,
            A.datetime,
            A.visit_id,
            A.camera_id,
            L.id,
            C.name,
            VR.name,
            VR.id,
            A.type,
            VR.phone
            
            order by A.datetime desc
            ;"""

        # WHERE
        # VS.exit_time IS NULL AND A.id =
        # (SELECT TOP 1 id FROM Alert WHERE visit_id = A.visit_id ORDER BY datetime)

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch current alerts.'}), 500


def get_visitor_alerts():
    try:
        visitor_id = request.args.get('id')

        query = f"""SELECT
            A.id,
            A.type as 'type',
            CONVERT(DATE, A.datetime) AS 'date',
            FORMAT(A.datetime, 'hh:mm tt') AS 'time',
            A.visit_id,
            VR.id AS 'visitor_id',
            VR.name AS 'visitor_name',
            VR.phone AS 'visitor_contact',
            A.camera_id,
            L.id AS 'location_id',
            STRING_AGG(L.name, ', ') AS 'destinations',
            C.name AS 'camera_name',
            (
                SELECT TOP 1 L.name
                FROM CameraLocation CL
                JOIN Location L ON L.id = CL.location_id
                WHERE CL.camera_id = A.camera_id
            ) AS 'current_location'
        FROM
            Alert A
        JOIN
            Camera C ON C.id = A.camera_id
        JOIN
            VisitDestination VD ON A.visit_id = VD.visit_id
        JOIN
            Location L ON L.id = VD.destination_id
        JOIN 
            VISIT VS ON VS.id = A.visit_id
        JOIN 
            Visitor VR ON VR.id = VS.visitor_id

        WHERE
        VS.exit_time IS NULL AND VR.id = {visitor_id}

        GROUP BY
            A.id,
            A.datetime,
            A.visit_id,
            A.camera_id,
            L.id,
            C.name,
            VR.name,
            VR.id,
            A.type,
            VR.phone

            order by A.datetime desc
            ;"""

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                main_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if len(main_rows)>0:

            query = f"SELECT top 1 * FROM Visit where visitor_id = {visitor_id} and exit_time is NULL"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    columns = [column[0] for column in cursor.description]
                    visit_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            visit_id = visit_rows[0]['id'];

            query_to_chk_poss = f"select top 1 * from VisitPathHistory where is_violated=0 and visit_id={visit_id} order by id desc"
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_to_chk_poss)
                    columns = [column[0] for column in cursor.description]
                    cam_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            camera_id = cam_rows[0]['camera_id'];

            response = requests.get(f'{url}/GetCameraById?id={camera_id}', )
            new_rows = response.json()
            if len(new_rows) != 0:
                current_correct_camera = new_rows['name']

            folder_path = 'VisitCorrectPaths'
            file_name = os.path.join(folder_path, f"{visitor_id}.json")
            paths = load_records(file_name)

            print(current_correct_camera)
            next_moves = []

            for path in paths:
                print(len(path))
                for i in range(len(path)):
                    if path[i] == current_correct_camera:
                        
                        response = requests.get(f'{url}/GetLocationByCamera/{path[i+1]}', )
                        rows = response.json()
                        if len(rows) != 0:
                            next_moves.append(rows[0]['LocationName'])

            main_rows[0]['next_moves']=next_moves
            return jsonify(main_rows[0]), 200

        return jsonify({'success': 'No visitor alerts.'}),200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch current alerts.'}), 500