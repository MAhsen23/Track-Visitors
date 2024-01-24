from datetime import datetime, timedelta
import pyodbc
from flask import jsonify,request
import requests

import DB_Connection
conn_string = DB_Connection.conn_string()
url = DB_Connection.url()
def get_block_visitors():
    try:
        query = """SELECT 
        V.id as 'visitor_id',
        V.name as 'visitor_name',
        v.phone as 'phone',
        B.user_id,
        U.name as 'blocked_by_user',
        B.start_date,
        B.end_date
        FROM [Block] B
        JOIN Visitor V ON B.visitor_id = V.id JOIN [User] U on u.id=B.user_id
        WHERE B.end_date >= GETDATE();"""

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(rows), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to fetch visitors.'}), 500





def block_visitor():
    try:
        visitor_id = request.form.get('visitor_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        user_id = request.form.get('user_id')

        start_date = datetime.strptime(start_date_str, '%Y/%m/%d').date()
        end_date = datetime.strptime(end_date_str, '%Y/%m/%d').date()

        if not visitor_id:
            return jsonify({'error': 'Visitor ID not provided.'}), 400

        query=f"INSERT INTO Block (user_id, visitor_id, start_date, end_date) VALUES ({user_id}, {visitor_id}, '{start_date}', '{end_date}')"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()

        return jsonify({'message': 'Visitor blocked successfully.'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to block visitor.'}), 500





def unblock_visitor():
    try:
        data = request.json
        visitor_id = data.get('visitor_id')

        if not visitor_id:
            return jsonify({'error': 'Visitor ID not provided.'}), 400

        query_check_blocked = f"SELECT TOP 1 id FROM [Block] WHERE visitor_id = {visitor_id} AND end_date >= GETDATE() ORDER BY end_date DESC"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_check_blocked)
                block_record = cursor.fetchone()

                if block_record:
                    block_id = block_record[0]
                    new_end_date = (datetime.now() - timedelta(days=1)).date()
                    query_update_end_date = f"UPDATE [Block] SET end_date = '{new_end_date}' WHERE id = {block_id}"
                    cursor.execute(query_update_end_date)
                    conn.commit()
                    return jsonify({'message': 'Visitor unblocked successfully.'}), 200
                else:
                    return jsonify({'error': 'Visitor is not currently blocked.'}), 400

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to unblock visitor.'}), 500







def check_visitor_blocked(visitor_id):
    try:
        query_check_blocked = f"SELECT TOP 1 id FROM [Block] WHERE visitor_id = {visitor_id} AND end_date >= '{datetime.now()}' ORDER BY end_date DESC"

        with pyodbc.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_check_blocked)
                block_record = cursor.fetchone()

                blocked = True if block_record else False

                return jsonify({'blocked': blocked}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to check visitor status.'}), 500




def extend_block(visitor_id):
    try:
        end_date_str = request.form.get('end_date')

        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if not visitor_id:
            return jsonify({'error': 'Visitor ID not provided.'}), 400

        response = requests.get(f'{url}/CheckVisitorBlocked/{visitor_id}')
        if response.json()['blocked']:
            query=f"Update Block set end_date = '{end_date}'"

            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    conn.commit()

            return jsonify({'message': 'Block extend successfully.'}), 200

        else:
            return jsonify({'error': 'This visitor is not blocked.'}), 400

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to extend block.'}), 500