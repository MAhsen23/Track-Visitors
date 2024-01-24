import os

import pyodbc
from flask import jsonify, request, send_file, after_this_request
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


import DB_Connection
conn_string = DB_Connection.conn_string()

def get_visitors_report():
    try:
        request_data = request.json
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')

        where_clause = ""

        if start_date and end_date:
            where_clause = f"WHERE V.date >= '{start_date}' AND V.date <= '{end_date}'"

        elif start_date:
            where_clause = f"WHERE V.date >= '{start_date}'"

        elif end_date:
            where_clause = f"WHERE V.date <= '{end_date}'"

        query = f"""
        SELECT
        V.id AS VisitID,
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
        {where_clause}
        GROUP BY
            V.id, Vi.name, Vi.phone, V.date, V.entry_time, V.exit_time
        ORDER BY
            VisitDate DESC, EntryTime;
        """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch visitors report.'}), 500




def generate_pdf(rows, filename):

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('Poppins', 'F:\ReactNative\FirstProject\\assets\\fonts\Poppins-Regular.ttf'))
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Poppins", 10)

    column_widths = [30, 120, 80, 80, 80, 170]

    header = ["S.no", "Visitor Name", "Visit Date", "Entry Time", "Exit Time", "Locations Visited"]
    for i, column in enumerate(header):
        p.drawString(50 + sum(column_widths[:i]), 750, column)

    p.drawString(0, 730, "-" * sum(column_widths))

    for i, row in enumerate(rows):
        if i < 40:
            p.drawString(50, 710 - i * 20, str(i + 1))
            p.drawString(50 + column_widths[0], 710 - i * 20, row['VisitorName'][:20])
            p.drawString(50 + sum(column_widths[:2]), 710 - i * 20, str(row['VisitDate']))

            entry_time = row['EntryTime'].split('.')[0]
            entry_time_obj = datetime.strptime(entry_time, '%H:%M:%S')
            formatted_entry_time = entry_time_obj.strftime('%I:%M %p')
            p.drawString(50 + sum(column_widths[:3]), 710 - i * 20, formatted_entry_time)

            if row['ExitTime'] is not None:
                exit_time = row['ExitTime'].split('.')[0]
                exit_time_obj = datetime.strptime(exit_time, '%H:%M:%S')
                formatted_exit_time = exit_time_obj.strftime('%I:%M %p')
                p.drawString(50 + sum(column_widths[:4]), 710 - i * 20, formatted_exit_time)
            else:
                p.drawString(50 + sum(column_widths[:4]), 710 - i * 20, 'Active Visit')

            p.drawString(50 + sum(column_widths[:5]), 710 - i * 20, row['LocationsVisited'][:30])

    p.save()
    buffer.seek(0)

    with open(filename, 'wb') as file:
        file.write(buffer.read())




def download_visitors_report():
    try:
        request_data = request.json
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')

        where_clause = ""

        if start_date and end_date:
            where_clause = f"WHERE V.date >= '{start_date}' AND V.date <= '{end_date}'"
        elif start_date:
            where_clause = f"WHERE V.date >= '{start_date}'"
        elif end_date:
            where_clause = f"WHERE V.date <= '{end_date}'"

        query = f"""
            SELECT
            V.id AS VisitID,
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
            {where_clause}
            GROUP BY
                V.id, Vi.name, Vi.phone, V.date, V.entry_time, V.exit_time
            ORDER BY
                VisitDate DESC, EntryTime;
            """

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        pdf_path = 'visitors_report.pdf'
        generate_pdf(rows, pdf_path)
        return send_file(pdf_path, download_name='visitors_report.pdf', as_attachment=True)

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to download visitors report.'}), 500


