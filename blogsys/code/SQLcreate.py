import sqlite3
import os
from dotenv import load_dotenv

def get_db_path():
    """環境変数からデータベースパスを取得"""
    # .envファイルの絶対パスを取得し、環境変数をロード
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(dotenv_path=env_path)
    # SQLiteのデータベースファイルパス
    db_path_from_env = os.getenv('DB_PATH', 'blog_db.sqlite')
    if os.path.isabs(db_path_from_env):
        return db_path_from_env
    else:
        blogsys_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.join(blogsys_dir, db_path_from_env)

def display_table_contents():
    """テーブルの内容を表示する共通関数"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, article_title, url, description, publicity, tags, timestamp FROM URL_list_table")
        result = cursor.fetchall()
        print("ID | タイトル | URL | 説明 | 公開設定 | タグ | 投稿日時")
        for row in result:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error displaying table contents: {e}")

def delete_all_articles():
    """URL_list_tableの全記事情報を削除（テーブル自体は残す）"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM URL_list_table")
        conn.commit()
        cursor.close()
        conn.close()
        print("全記事情報を削除しました")
        # 削除後にテーブル内容を表示
        display_table_contents()
        return "全記事情報を削除しました"
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return error_msg

def create_database():
    """SQLiteデータベースとテーブルを作成"""
    try:
        db_path = get_db_path()
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # テーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS URL_list_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_title VARCHAR(255) NOT NULL,
                url VARCHAR(255) NOT NULL,
                draft_url VARCHAR(255),
                posts_url VARCHAR(255),
                description TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                tags VARCHAR(255) DEFAULT '未設定',
                publicity VARCHAR(16) NOT NULL DEFAULT 'public'
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"SQLiteデータベースとテーブルを作成しました: {db_path}")
        # 作成後にテーブル内容を表示
        display_table_contents()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_database()
    delete_all_articles()