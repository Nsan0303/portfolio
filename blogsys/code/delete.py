import os
import re
import sqlite3  # SQLite接続用
from dotenv import load_dotenv  # .envファイルの読み込み

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

# Linux環境でのパスの整合性を確保
def normalize_path(path):
    return os.path.normpath(path)

DB_PATH = normalize_path(DB_PATH)

def delete_article():
    # DB上で指定IDの記事の公開設定(publicity)を'private'に変更する
    print("=== 記事非公開処理 ===")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # --- DBとローカルファイルの整合性チェック ---
        posts_dir = normalize_path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'blog-posts')))
        drafts_root = normalize_path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'drafts')))
        cur.execute("SELECT id, article_title, url, draft_url, posts_url FROM URL_list_table")
        db_articles = cur.fetchall()
        for db_id, db_title, db_url, db_draft_url, db_posts_url in db_articles:
            # draftsファイル削除
            if db_draft_url:
                draft_path = normalize_path(os.path.join(drafts_root, db_draft_url))
                if os.path.exists(draft_path):
                    os.remove(draft_path)
                    print(f"ドラフトファイル削除: {draft_path}")
            # postsファイル削除
            if db_posts_url:
                post_path = normalize_path(os.path.join(posts_dir, db_posts_url))
                if os.path.exists(post_path):
                    os.remove(post_path)
                    print(f"公開記事ファイル削除: {post_path}")
        conn.commit()
        # --- 通常の非公開/物理削除処理 ---
        article_id = input("操作したい記事IDを入力してください: ").strip()
        if not article_id.isdigit():
            print("IDは数字で入力してください。終了します。")
            cur.close()
            conn.close()
            return
        print("操作: 1=非公開化 2=物理削除 0=終了")
        op = input("操作番号を入力してください: ").strip()
        if op == "1":
            try:
                cur.execute("UPDATE URL_list_table SET publicity='private' WHERE id=?", (article_id,))
                conn.commit()
                cur.execute("SELECT id, article_title, draft_url, posts_url, description, publicity, tags, timestamp FROM URL_list_table WHERE id=?", (article_id,))
                row = cur.fetchone()
                if row:
                    print(f"非公開にした記事情報: ID={row[0]}, タイトル={row[1]}, draft_url={row[2]}, posts_url={row[3]}, 公開設定={row[5]}, タグ={row[6]}, 投稿日時={row[7]}")
                else:
                    print(f"ID:{article_id} の記事が見つかりません。")
            except Exception as e:
                print(f"[ERROR] 非公開化失敗: id={article_id}, error={e}")
        elif op == "2":
            # DBから削除＋ファイル削除
            try:
                cur.execute("SELECT draft_url, posts_url FROM URL_list_table WHERE id=?", (article_id,))
                result = cur.fetchone()
            except Exception as e:
                print(f"[ERROR] DB検索失敗: id={article_id}, error={e}")
                result = None
            if result:
                db_draft_url, db_posts_url = result
                # draftsファイル削除
                if db_draft_url:
                    draft_path = normalize_path(os.path.join(drafts_root, os.path.basename(db_draft_url)))
                    if os.path.exists(draft_path):
                        try:
                            os.remove(draft_path)
                            print(f"ドラフトファイル削除: {draft_path}")
                        except Exception as e:
                            print(f"ファイル削除失敗: {e}")
                # blog-postsファイル削除
                if db_posts_url:
                    posts_path = normalize_path(os.path.join(posts_dir, os.path.basename(db_posts_url)))
                    if os.path.exists(posts_path):
                        try:
                            os.remove(posts_path)
                            print(f"公開記事ファイル削除: {posts_path}")
                        except Exception as e:
                            print(f"公開記事ファイル削除失敗: {e}")
                try:
                    cur.execute("DELETE FROM URL_list_table WHERE id=?", (article_id,))
                    conn.commit()
                    print(f"記事ID:{article_id} をDB・ファイルとも削除しました。")
                except Exception as e:
                    print(f"[ERROR] DB削除失敗: id={article_id}, error={e}")
            else:
                print(f"ID:{article_id} の記事が見つかりません。")
        elif op == "0":
            print("終了します。")
        else:
            print("不正な操作番号です。何も変更しません。")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[致命的エラー] DB更新エラー: {e}")