# メインメニュー用スクリプト
# ユーザーの選択に応じてドラフト作成・記事アップロード・記事削除を実行
import os
from dotenv import load_dotenv

# .envファイルの絶対パスを取得し、環境変数をロード
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)

# SQLiteのデータベースファイルパス
db_path_from_env = os.getenv('DB_PATH', 'blog_db.sqlite')
if os.path.isabs(db_path_from_env):
    DB_PATH = db_path_from_env
else:
    blogsys_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_PATH = os.path.join(blogsys_dir, db_path_from_env)

# Linux環境用にパスの区切り文字を統一
def normalize_path(path):
    return os.path.normpath(path)

DB_PATH = normalize_path(DB_PATH)

def create_draft():
    # ドラフト作成システム
    # new_article.pyのmain()を呼び出して記事ドラフト作成処理を実行
    import new_article
    new_article.main()

def upload_article():
    # 記事アップロードシステム
    # upload.pyのupload_article()を呼び出して記事アップロード処理を実行
    import upload
    upload.upload_article()

def delete_article():
    # 記事削除システム
    # delete.pyのdelete_article()を呼び出して記事削除処理を実行
    import delete
    delete.delete_article()



# ユーザーに実行したいタスクを選択させるメニュー表示
print("Please enter the number of task you want to perform: \n1.create drafts file\n2.upload article\n3.delete article\nPlease select a task:and enter one of 1, 2, 3")



# ユーザーの入力を取得
execution_choice = input().strip()

if execution_choice == "1":
    # ドラフト作成処理
    create_draft()
elif execution_choice == "2":
    # 記事アップロード処理
    upload_article()
elif execution_choice == "3":
    # 記事削除処理
    delete_article()
else:
    # 不正な入力時のエラーメッセージ
    print("Invalid choice.")

