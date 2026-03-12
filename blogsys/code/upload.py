import os  # OS操作用
import time  # 日時取得・整形用
import re  # ファイル名の正規表現処理
import sqlite3  # SQLite接続用
from dotenv import load_dotenv  # .envファイルの読み込み

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

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

# ファイル名に使えない文字を全て'_'に置換する（Windows/Linux両対応）
# 引数: name(str) - 元のファイル名
# 戻り値: 置換済みファイル名(str)
def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)

# 指定パスにディレクトリがなければ作成し、ファイルを書き込む
# 引数: path(str) - ファイルパス, content(str) - ファイル内容
def create_file(path: str, content: str = ""):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# 記事HTMLのテンプレートを生成
# 引数: title(str) - 記事タイトル, description(str) - 記事説明, now(str) - 投稿日時
# 戻り値: HTML文字列(str)
def get_template_html(title: str, description: str, now: str) -> str:
    return f"""<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{title}</title>\n    <link rel=\"stylesheet\" href=\"/static/blog.css\">\n</head>\n<body>\n    <article>\n        <h1>{title}</h1>\n        <p>{description}</p>\n        <time>{now}</time>\n    </article>\n    <a href=\"/\">← トップへ戻る</a>\n</body>\n</html>\n"""

# MySQLに記事情報を登録（公開設定追加）
# テーブルがなければ作成し、公開設定(publicity)も保存
# 引数: title(str), url(str), description(str), publicity(str)
# 戻り値: conn, cur (MySQL接続・カーソル)
def register_article_to_sqlite(
    title: str,
    url: str,
    description: str,
    publicity: str = None,
    tags: str = None
) -> tuple:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
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
        # draft_url, posts_url を追加
        draft_url = url
        posts_url = ''
        cur.execute(
            "INSERT INTO URL_list_table (article_title, url, draft_url, posts_url, description, publicity, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, url, draft_url, posts_url, description, publicity or 'public', tags if tags else '未設定')
        )
        conn.commit()
        article_id = cur.lastrowid
        return conn, cur, article_id
    except Exception as e:
        print(f"記事登録エラー: {e}")
        return None, None, None

# DB内の全記事情報を表示
# 引数: cur(MySQLカーソル)
def show_registered_articles(cur):
    try:
        cur.execute("SELECT id, article_title, url, draft_url, posts_url, description, publicity, tags, timestamp FROM URL_list_table")
        result = cur.fetchall()
        print("ID | タイトル | URL | draft_url | posts_url | 公開設定 | タグ | 投稿日時")
        for row in result:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[6]} | {row[7]} | {row[8]}")
    except Exception as e:
        print(f"記事取得エラー: {e}")

# 記事アップロード処理のメイン関数
# ユーザー入力から記事情報を取得し、ファイル作成・DB登録を行う
def upload_article():
    print("=== 記事管理システム（ID指定操作） ===")
    posts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'blog-posts'))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    show_registered_articles(cur)
    try:
        article_id = input("操作したい記事IDを入力してください: ").strip()
        cur.execute("SELECT id, article_title, url, description, publicity, tags FROM URL_list_table WHERE id=?", (article_id,))
        row = cur.fetchone()
        if not row:
            print(f"ID:{article_id} の記事が見つかりません。")
            cur.close()
            conn.close()
            return
        print(f"選択中の記事: ID={row[0]}, タイトル={row[1]}, 公開設定={row[4]}, タグ={row[5]}")
        print("操作: 1=公開設定変更 2=MD→HTML変換 3=記事内容表示 4=削除 0=終了")
        op = input("操作番号を入力してください: ").strip()
        if op == "1":
            new_pub = input("新しい公開設定 (public/private/pb/pr): ").strip().lower()
            if new_pub in ["public", "pb"]:
                cur.execute("UPDATE URL_list_table SET publicity=? WHERE id=?", ("public", article_id))
                conn.commit()
                print(f"公開設定を public に変更しました。")
                # 公開設定変更と同時にmd→html変換＆blog-posts移動も実行
                # === md→html変換処理 ===
                url = row[2]  # draft_url
                md_fname = f"{row[0]}_{os.path.basename(url).replace('.html', '.md')}"
                html_fname = f"{row[0]}_{os.path.basename(url).replace('.md', '.html').replace('.html', '.html')}"
                workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                md_path = os.path.abspath(os.path.join(workspace_root, url))
                md_path = os.path.normpath(md_path)
                # 記事ごとにディレクトリ作成
                article_dir = os.path.join(posts_root, f"{row[0]}_{sanitize_filename(row[1])}")
                os.makedirs(article_dir, exist_ok=True)
                html_path = os.path.join(article_dir, html_fname)
                posts_url = f"blog-posts/{row[0]}_{sanitize_filename(row[1])}/{html_fname}"
                if os.path.exists(md_path):
                    posts_md_path = os.path.join(article_dir, md_fname)
                    if not os.path.exists(posts_md_path):
                        with open(md_path, "r", encoding="utf-8") as fsrc, open(posts_md_path, "w", encoding="utf-8") as fdst:
                            fdst.write(fsrc.read())
                    with open(posts_md_path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    if HAS_MARKDOWN:
                        html_content = markdown.markdown(md_content)
                    else:
                        html_content = f"<h1>{row[1]}</h1><p>{row[3]}</p>"
                    create_file(html_path, html_content)
                    print(f"MD→HTML変換＆postsへ移動・コピー完了: {html_path}")
                    # posts_urlをDBに保存
                    cur.execute("UPDATE URL_list_table SET posts_url=? WHERE id=?", (posts_url, article_id))
                    conn.commit()
                else:
                    drafts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'drafts'))
                    found_md = None
                    for root_, dirs_, files_ in os.walk(drafts_root):
                        for file_ in files_:
                            if file_.endswith('.md'):
                                if str(row[0]) in file_ or row[1] in file_ or md_fname in file_:
                                    candidate = os.path.join(root_, file_)
                                    found_md = candidate
                                    break
                        if found_md:
                            break
                    if found_md and os.path.exists(found_md):
                        posts_md_path = os.path.join(article_dir, f"{row[0]}_{os.path.basename(found_md)}")
                        if not os.path.exists(posts_md_path):
                            with open(found_md, "r", encoding="utf-8") as fsrc, open(posts_md_path, "w", encoding="utf-8") as fdst:
                                fdst.write(fsrc.read())
                        with open(posts_md_path, "r", encoding="utf-8") as f:
                            md_content = f.read()
                        if HAS_MARKDOWN:
                            html_content = markdown.markdown(md_content)
                        else:
                            html_content = f"<h1>{row[1]}</h1><p>{row[3]}</p>"
                        create_file(html_path, html_content)
                        print(f"MD→HTML変換＆postsへ移動・コピー完了: {html_path}")
                        # posts_urlをDBに保存
                        cur.execute("UPDATE URL_list_table SET posts_url=? WHERE id=?", (posts_url, article_id))
                        conn.commit()
                    else:
                        print(f"MDファイルが存在しません: {md_path} または drafts配下にも該当ファイルがありません")
            elif new_pub in ["private", "pr"]:
                cur.execute("UPDATE URL_list_table SET publicity=? WHERE id=?", ("private", article_id))
                conn.commit()
                print(f"公開設定を private に変更しました。")
            else:
                print("公開設定が不正です。変更しません。")
        elif op == "2":
            # MD→HTML変換（ドラフト→posts移動＆変換）
            url = row[2]
            # ファイル名にIDを含める
            md_fname = f"{row[0]}_{os.path.basename(url).replace('.html', '.md')}"
            html_fname = f"{row[0]}_{os.path.basename(url).replace('.md', '.html').replace('.html', '.html')}"
            # ドラフトMDファイルの絶対パス（DBのurlは相対パスなのでワークスペースルートから組み立てる）
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            md_path = os.path.abspath(os.path.join(workspace_root, url))
            md_path = os.path.normpath(md_path)
            html_path = os.path.join(article_dir, html_fname)
            # postsディレクトリにMDファイルをコピー
            md_found = None
            # まずmd_pathが存在するか確認
            if os.path.exists(md_path):
                md_found = md_path
            else:
                # draftsディレクトリを再帰検索して該当MDファイルを探す
                drafts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'drafts'))
                for root, dirs, files in os.walk(drafts_root):
                    for file in files:
                        if file.endswith('.md'):
                            # ファイル名にID・記事タイトル・タイムスタンプが含まれているか判定
                            if str(row[0]) in file or row[1] in file or md_fname in file:
                                candidate = os.path.join(root, file)
                                md_found = candidate
                                break
                    if md_found:
                        break
            if md_found and os.path.exists(md_found):
                posts_md_path = os.path.join(article_dir, f"{row[0]}_{os.path.basename(md_found)}")
                # blog-postsディレクトリの存在を保証
                os.makedirs(os.path.dirname(posts_md_path), exist_ok=True)
                if not os.path.exists(posts_md_path):
                    with open(md_found, "r", encoding="utf-8") as fsrc, open(posts_md_path, "w", encoding="utf-8") as fdst:
                        fdst.write(fsrc.read())
                with open(posts_md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                if HAS_MARKDOWN:
                    html_content = markdown.markdown(md_content)
                else:
                    html_content = f"<h1>{row[1]}</h1><p>{row[3]}</p>"
                create_file(html_path, html_content)
                print(f"MD→HTML変換＆postsへ移動・コピー完了: {html_path}")
            else:
                print(f"MDファイルが存在しません: {md_path} または drafts配下にも該当ファイルがありません")
        elif op == "3":
            print(f"記事内容: {row[3]}")
        elif op == "4":
            cur.execute("DELETE FROM URL_list_table WHERE id=?", (article_id,))
            conn.commit()
            print(f"記事ID:{article_id} を削除しました。")
        elif op == "0":
            print("終了します。")
        else:
            print("不正な操作番号です。何も変更しません。")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    upload_article()
