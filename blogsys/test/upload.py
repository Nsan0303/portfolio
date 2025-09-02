import os
import time
import re
import mysql.connector
from dotenv import load_dotenv

# .envファイルの絶対パス指定
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'blog_db')

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)

def create_file(path: str, content: str = ""):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def get_template_html(title, description, now):
    return f"""<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{title}</title>\n    <link rel=\"stylesheet\" href=\"/static/blog.css\">\n</head>\n<body>\n    <article>\n        <h1>{title}</h1>\n        <p>{description}</p>\n        <time>{now}</time>\n    </article>\n    <a href=\"/\">← トップへ戻る</a>\n</body>\n</html>\n"""

def register_article_to_mysql(title, url, description, publicity=None):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS URL_list_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                article_title VARCHAR(255) NOT NULL,
                url VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                publicity VARCHAR(16) NOT NULL DEFAULT 'public'
            )
        """)
        conn.commit()
        cur.execute(
            "INSERT INTO URL_list_table (article_title, url, description, publicity) VALUES (%s, %s, %s, %s)",
            (title, url, description, publicity or 'public')
        )
        conn.commit()
        return conn, cur
    except Exception as e:
        print(f"DB登録エラー: {e}")
        return None, None

def show_registered_articles(cur):
    try:
        cur.execute("SELECT * FROM URL_list_table")
        result = cur.fetchall()
        for row in result:
            print(f"ID: {row[0]}, Title: {row[1]}, URL: {row[2]}, Description: {row[3]}, Publicity: {row[4]}")
    except Exception as e:
        print(f"記事取得エラー: {e}")

def upload_article():
    print("=== 記事アップロードシステム ===")
    title = input("記事タイトルを入力してください: ")
    description = input("記事説明を入力してください: ")
    publicity = input("公開設定を入力してください (public/pb or private/pr): ").strip().lower()
    if publicity in ['public', 'pb']:
        publicity = 'public'
    elif publicity in ['private', 'pr']:
        publicity = 'private'
    else:
        print("公開設定が不正です。'public'で登録します。")
        publicity = 'public'
    now = time.strftime("%Y_%m_%d_%H_%M")
    safe_title = sanitize_filename(title)
    fname = f"{now}_{safe_title}.html"
    posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blog-posts'))
    file_path = os.path.join(posts_dir, fname)
    html_content = get_template_html(title, description, now)
    create_file(file_path, html_content)
    url = f"/posts/{fname}"
    conn, cur = register_article_to_mysql(title, url, description, publicity)
    if conn and cur:
        print(f"記事ファイル作成: {file_path}")
        print("MySQLに記事登録完了\n--- 登録済み記事一覧 ---")
        show_registered_articles(cur)
        cur.close()
        conn.close()
    else:
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")
