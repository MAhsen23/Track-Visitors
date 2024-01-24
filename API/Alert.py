from datetime import datetime
import pyodbc
from flask import jsonify,request
import DB_Connection
conn_string = DB_Connection.conn_string()

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