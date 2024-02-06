import pyodbc
from flask import jsonify,request
import DB_Connection
from datetime import datetime, timedelta
conn_string = DB_Connection.conn_string()

import pyodbc
from flask import jsonify

def get_all_visitors():
    try:
        query = "SELECT * FROM VISITOR"
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                for row in rows:
                    block_query = f"SELECT TOP 1 CASE WHEN id IS NOT NULL AND end_date >= GETDATE() THEN 'True' ELSE 'False' END AS block FROM Block WHERE visitor_id = {row['id']} ORDER BY id DESC"
                    cursor.execute(block_query)
                    block_result = cursor.fetchone()
                    row['block'] = block_result[0] if block_result else 'False'

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch visitors.'}), 500




import os
import base64

def get_current_visitors():
    try:
        #query = "SELECT VS.id AS 'id', VS.name, VS.phone, V.entry_time AS entry_time, STRING_AGG(L.id, ', ') AS location_ids, STRING_AGG(L.name, ', ') AS location_names, LC.name as 'current_location' FROM Visitor VS JOIN Visit V ON V.visitor_id = VS.id JOIN VisitDestination VD ON VD.visit_id = V.id JOIN Location L ON L.id = VD.destination_id JOIN VisitPathHistory VP on VP.visit_id=V.id JOIN Camera C on C.id = VP.camera_id JOIN CameraLocation CL on CL.camera_id = C.id JOIN Location LC on LC.id = CL.location_id WHERE V.exit_time IS NULL and VP.id = (select top 1 id from VisitPathHistory where visit_id=V.id order by time desc) GROUP BY V.id, VS.id, VS.name, VS.phone, V.entry_time,LC.name;"
        query="""WITH AggregatedLocations AS (
                SELECT
                    V.id AS 'id',
                    STRING_AGG(L.id, ', ') AS location_ids,
                    STRING_AGG(L.name, ', ') AS location_names
                FROM
                    Visit V
                JOIN
                    VisitDestination VD ON VD.visit_id = V.id
                JOIN
                    Location L ON L.id = VD.destination_id
                WHERE
                    V.exit_time IS NULL
                GROUP BY
                    V.id
            )
            
            SELECT
                VS.id AS 'id',
                VS.name,
                VS.phone,
                V.entry_time AS entry_time,
                AggLoc.location_ids,
                AggLoc.location_names,
                STRING_AGG(LC.name, ', ') AS current_location
            FROM
                Visitor VS
            JOIN
                Visit V ON V.visitor_id = VS.id
            JOIN
                VisitDestination VD ON VD.visit_id = V.id
            JOIN
                Location L ON L.id = VD.destination_id
            JOIN
                VisitPathHistory VP ON VP.visit_id = V.id
            JOIN
                Camera C ON C.id = VP.camera_id
            JOIN
                CameraLocation CL ON CL.camera_id = C.id
            JOIN
                Location LC ON LC.id = CL.location_id
            JOIN
                AggregatedLocations AggLoc ON AggLoc.id = V.id
            WHERE
                V.exit_time IS NULL
                AND VP.id = (SELECT TOP 1 id FROM VisitPathHistory WHERE visit_id = V.id ORDER BY time DESC)
            GROUP BY
                V.id, VS.id, VS.name, VS.phone, V.entry_time, AggLoc.location_ids, AggLoc.location_names;"""
        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for row in rows:
            visitor_id = row['id']
            directory_path = f'Images/{visitor_id}'
            filename = os.listdir(directory_path)[0]
            with open(os.path.join(directory_path, filename), "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            row['image'] = encoded_image

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch current Visitors.'}), 500




def get_today_visitors():
    try:
        query = f"""
        SELECT
        V.id AS VisitID,
        Vi.id As VisitorId,
        Vi.name AS VisitorName,
        Vi.phone AS VisitorPhone,
        STRING_AGG(L.name, ', ') AS LocationsVisited,
        V.date AS VisitDate,
        V.entry_time AS EntryTime,
        V.exit_time AS ExitTime
        FROM
            Visit AS V
        INNER JOIN
            Visitor AS Vi ON V.visitor_id = Vi.id
        INNER JOIN
            VisitDestination AS Vd ON V.id = Vd.visit_id
        INNER JOIN
            Location AS L ON Vd.destination_id = L.id
        where V.date='{(datetime.now()).date()}'
        GROUP BY
            V.id, Vi.id, Vi.name, Vi.phone, V.date, V.entry_time, V.exit_time
        ORDER BY
            VisitDate DESC, EntryTime
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for row in rows:
            visitor_id = row['VisitorId']
            directory_path = f'Images/{visitor_id}'
            filename = os.listdir(directory_path)[0]
            with open(os.path.join(directory_path, filename), "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            row['image'] = encoded_image

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch today visitors.'}), 500




def get_weekly_visitors():
    try:
        print(datetime.now().date())
        print((datetime.now() - timedelta(days=6)).date())

        query = f"""
        SELECT
        V.id AS VisitID,
        Vi.id As VisitorId,
        Vi.name AS VisitorName,
        Vi.phone AS VisitorPhone,
        STRING_AGG(L.name, ', ') AS LocationsVisited,
        V.date AS VisitDate,
        V.entry_time AS EntryTime,
        V.exit_time AS ExitTime
        FROM
            Visit AS V
        INNER JOIN
            Visitor AS Vi ON V.visitor_id = Vi.id
        INNER JOIN
            VisitDestination AS Vd ON V.id = Vd.visit_id
        INNER JOIN
            Location AS L ON Vd.destination_id = L.id
            
        WHERE V.date >= '{(datetime.now() - timedelta(days=6)).date()}' AND V.date <= '{datetime.now().date()}'
        
        GROUP BY
            V.id, Vi.id, Vi.name, Vi.phone, V.date, V.entry_time, V.exit_time
        ORDER BY
            VisitDate DESC, EntryTime
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for row in rows:
            visitor_id = row['VisitorId']
            directory_path = f'Images/{visitor_id}'
            filename = os.listdir(directory_path)[0]
            with open(os.path.join(directory_path, filename), "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            row['image'] = encoded_image

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch weekly visitors.'}), 500



def search_today_visitors():
    try:
        visitor_name = request.args.get('visitor_name')

        query = f"""
        SELECT
        V.id AS VisitID,
        Vi.id As VisitorId,
        Vi.name AS VisitorName,
        Vi.phone AS VisitorPhone,
        STRING_AGG(L.name, ', ') AS LocationsVisited,
        V.date AS VisitDate,
        V.entry_time AS EntryTime,
        V.exit_time AS ExitTime
        FROM
            Visit AS V
        INNER JOIN
            Visitor AS Vi ON V.visitor_id = Vi.id
        INNER JOIN
            VisitDestination AS Vd ON V.id = Vd.visit_id
        INNER JOIN
            Location AS L ON Vd.destination_id = L.id
        WHERE V.date = '{(datetime.now()).date()}' AND
        Vi.name LIKE '%{visitor_name}%'
        GROUP BY
            V.id, Vi.id, Vi.name, Vi.phone, V.date, V.entry_time, V.exit_time
        ORDER BY
            VisitDate DESC, EntryTime;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for row in rows:
            visitor_id = row['VisitorId']
            directory_path = f'Images/{visitor_id}'
            filename = os.listdir(directory_path)[0]
            with open(os.path.join(directory_path, filename), "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            row['image'] = encoded_image

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch search visitors.'}), 500