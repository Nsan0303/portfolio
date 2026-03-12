# import mysql.connector
# from mysql.connector import Error

# # MySQLサーバー情報
# host = "localhost"       # サーバーのホスト名
# user = "root"            # MySQLユーザー名
# password = ""            # MySQLパスワード (.envで管理)
# database_name = "blog_db"   # 作成するデータベース名

# connection = None

# try:
#     # MySQLサーバーへ接続
#     connection = mysql.connector.connect(
#         host=host,
#         user=user,
#         password=password
#     )

#     if connection.is_connected():
#         cursor = connection.cursor()
#         # データベース作成クエリ
#         cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
#         print(f"データベース '{database_name}' を作成しました。")

# except Error as e:
#     print("エラーが発生しました:", e)

# finally:
#     if connection.is_connected():
#         cursor.close()
#         connection.close()
#         print("MySQL接続を閉じました。")
import mysql.connector
import os
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'blog_db')

def delete_all_articles():
    """URL_list_tableの全記事情報を削除（テーブル自体は残す）"""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM URL_list_table")
        conn.commit()
        cursor.close()
        conn.close()
        return "全記事情報を削除しました"
    except Exception as e:
        return f"Error: {e}"