import os
import shutil
import sqlite3
from dotenv import load_dotenv

# .envファイルのロード
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)

db_path_from_env = os.getenv('DB_PATH', 'blog_db.sqlite')
if os.path.isabs(db_path_from_env):
    DB_PATH = db_path_from_env
else:
    blogsys_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_PATH = os.path.join(blogsys_dir, db_path_from_env)

drafts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'drafts'))

# SQLite DBリセット
print(f"DBリセット: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS URL_list_table")
conn.commit()
cur.execute("""
    CREATE TABLE IF NOT EXISTS URL_list_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_title VARCHAR(255) NOT NULL,
        url VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        tags VARCHAR(255) DEFAULT '未設定',
        publicity VARCHAR(16) NOT NULL DEFAULT 'public'
    )
""")
conn.commit()
cur.close()
conn.close()
print("DBテーブル再作成完了")

# draftsディレクトリ配下を全削除
if os.path.exists(drafts_dir):
    print(f"draftsディレクトリリセット: {drafts_dir}")
    for entry in os.listdir(drafts_dir):
        path = os.path.join(drafts_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    print("drafts配下のファイル・フォルダを全削除しました")
else:
    print("draftsディレクトリが存在しません")

print("リセット完了")
