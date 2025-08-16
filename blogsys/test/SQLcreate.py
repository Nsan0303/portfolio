import mysql.connector
from mysql.connector import Error

# MySQLサーバー情報
host = "localhost"       # サーバーのホスト名
user = "root"            # MySQLユーザー名
password = "pass"  # MySQLパスワード
database_name = "db"   # 作成するデータベース名

connection = None

try:
    # MySQLサーバーへ接続
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password
    )

    if connection.is_connected():
        cursor = connection.cursor()
        # データベース作成クエリ
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"データベース '{database_name}' を作成しました。")

except Error as e:
    print("エラーが発生しました:", e)

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL接続を閉じました。")
