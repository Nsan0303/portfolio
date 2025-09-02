# import mysql.connector
# from mysql.connector import Error

# # MySQLサーバー情報
# host = "localhost"       # サーバーのホスト名
# user = "root"            # MySQLユーザー名
# password = "Nsan0303"  # MySQLパスワード
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
def delete_all_articles():
    """URL_list_tableの全記事情報を削除（テーブル自体は残す）"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Nsan0303",
            database="blog_db"
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM URL_list_table")
        conn.commit()
        cursor.close()
        conn.close()
        return "全記事情報を削除しました"
    except Exception as e:
        return f"Error: {e}"
# filepath: c:\Users\manat\Desktop\開発\個人\ポートフォリオ\portfolio\blogsys\mainpage.py
delete_all_articles()