def optimize_database():
    """
    DBテーブルのカラム不足時に自動でテーブル再作成（最適化）
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # テーブル情報取得
    cur.execute("PRAGMA table_info(URL_list_table)")
    columns = [row[1] for row in cur.fetchall()]
    required = {'id', 'article_title', 'url', 'draft_url', 'posts_url', 'description', 'timestamp', 'tags', 'publicity'}
    if not required.issubset(set(columns)):
        print("DBテーブルのカラム不足を検知。テーブルを再作成します。")
        cur.execute("DROP TABLE IF EXISTS URL_list_table")
        cur.execute("""
            CREATE TABLE URL_list_table (
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
    cur.close()
    conn.close()
def show_registered_articles(cur):
    """
    DBカーソルから登録済み記事一覧を表示
    """
    cur.execute("SELECT id, article_title, url, draft_url, posts_url, description, publicity, tags, timestamp FROM URL_list_table ORDER BY id DESC")
    articles = cur.fetchall()
    if not articles:
        print("記事は登録されていません。")
        return
    print("ID | タイトル | URL | draft_url | posts_url | 公開設定 | タグ | 投稿日時")
    for row in articles:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[6]} | {row[7]} | {row[8]}")
############################################################
# mainpage.py仕様に完全準拠した記事登録スクリプト
# 記事情報の入力、ドラフトファイル作成、SQLiteへの登録、一覧表示までを一括処理
############################################################
import os  # OS操作用
import time  # 日時取得・整形用
import re  # ファイル名の正規表現処理
import sqlite3  # SQLite接続用
from dotenv import load_dotenv  # .envファイルの読み込み


# .envファイルの絶対パス指定
# 1. os.path.dirname(__file__) でこのファイルのディレクトリを取得
# 2. その親ディレクトリ（..）に .env ファイルがあることを想定
# 3. os.path.abspath で絶対パスに変換
# 4. env_path には .env ファイルの絶対パスが格納される
# .envファイルの絶対パスを取得し、環境変数をロード
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)  # .envファイルを読み込んで環境変数に反映

# SQLiteのデータベースファイルパス
db_path_from_env = os.getenv('DB_PATH', 'blog_db.sqlite')
if os.path.isabs(db_path_from_env):
    DB_PATH = db_path_from_env
else:
    blogsys_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_PATH = os.path.join(blogsys_dir, db_path_from_env)

# Linux環境用にパスの区切り文字を統一
import os

def normalize_path(path):
    return os.path.normpath(path)

DB_PATH = normalize_path(DB_PATH)

if os.getenv('DEBUG', 'False').lower() == 'true':
    print(f"DB_PATH loaded: '{DB_PATH}'")  # DBパス確認用

def sanitize_filename(name: str) -> str:
    # ファイル名に使えない文字を全て'_'に置換する（Windows/Linux両対応）
    # 引数: name(str) - 元のファイル名
    # 戻り値: 置換済みファイル名(str)
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def create_file(path: str, content: str = ""):
    # 指定パスにディレクトリがなければ作成し、ファイルを書き込む
    # 引数: path(str) - ファイルパス, content(str) - ファイル内容
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def get_template_html(title, description, now):
    # 記事HTMLのテンプレートを生成
    # - title: 記事タイトル
    # - description: 記事説明
    # - now: 投稿日時
    # 戻り値: HTML文字列(str)
    return f"""<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{title}</title>\n    <link rel=\"stylesheet\" href=\"/static/blog.css\">\n</head>\n<body>\n    <article>\n        <h1>{title}</h1>\n        <p>{description}</p>\n        <time>{now}</time>\n    </article>\n    <a href=\"/\">← トップへ戻る</a>\n</body>\n</html>\n"""


def input_article_info():
    # ユーザーから記事情報（タイトル・説明・拡張子）を取得
    # 戻り値: タイトル(str), 説明(str), 拡張子(str)
    title = input("記事タイトルを入力してください: ")
    description = input("記事説明を入力してください: ")
    file_extension = input("ファイル拡張子を入力してください (html or md): ").strip().lower()
    print("サムネイル画像は 'tmb.png' として作成してください。")
    return title, description, file_extension


def get_template_content(template_dir):
    # 指定ディレクトリからテンプレート(html, css, js)を取得
    # 存在しない場合はデフォルトテンプレートを使用
    # 引数: template_dir(str) - テンプレートディレクトリ
    # 戻り値: テンプレート辞書
    templates = {}
    html_path = os.path.join(template_dir, "template.html")
    css_path = os.path.join(template_dir, "style.css")
    js_path = os.path.join(template_dir, "main.js")

    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            templates["html"] = f.read()
    else:
        templates["html"] = "<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>記事タイトル</title>\n    <link rel=\"stylesheet\" href=\"style.css\">\n</head>\n<body>\n    <h1>記事タイトル</h1>\n    <script src=\"main.js\"></script>\n</body>\n</html>"

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            templates["css"] = f.read()
    else:
        templates["css"] = "body { font-family: Arial, sans-serif; }"

    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            templates["js"] = f.read()
    else:
        templates["js"] = "// JavaScript template"

    return templates


def create_draft(article_title, file_extension, timestamp):
    # ドラフトファイル（html/md）を作成
    # ファイル名はタイトル＋タイムスタンプ
    # htmlの場合はテンプレートも生成
    # 引数: article_title(str), file_extension(str), timestamp(str)
    # 戻り値: 作成したファイルのパス(str)
    safe_title = sanitize_filename(article_title)
    # blogsys/drafts/配下に一意ディレクトリを作成
    base_dir = os.path.join(os.path.dirname(__file__), "..", "drafts", f"{safe_title}_{timestamp}_{file_extension}")

    if file_extension == "md":
        md_fname = f"{safe_title}_{timestamp}.md"
        md_path = os.path.join(base_dir, md_fname)
        md_content = f"# {article_title} {timestamp}\n"
        create_file(md_path, md_content)
        print(f"Markdown draft created at: {md_path}")
        return md_path.replace("\\", "/")

    if file_extension == "html":
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        templates = get_template_content(template_dir)
        html_fname = f"{safe_title}_{timestamp}.html"
        html_path = os.path.join(base_dir, html_fname)
        css_path = os.path.join(base_dir, "style.css")
        js_path = os.path.join(base_dir, "main.js")
        create_file(html_path, templates["html"])
        create_file(css_path, templates["css"])
        create_file(js_path, templates["js"])
        print(f"HTML draft created at: {html_path}")
        return html_path.replace("\\", "/")

    # 拡張子が不正な場合はNoneを返す
    print("Invalid file extension. Please enter either 'html' or 'md'.")
    return None


def register_article_to_mysql(title, url, description, publicity=None, tags=None):
    # SQLiteに記事情報を登録（公開設定追加）
    # テーブルがなければ作成し、公開設定(publicity)も保存
    # 引数: title(str), url(str), description(str), publicity(str), tags(str)
    # 戻り値: conn, cur (SQLite接続・カーソル)
    # DB接続
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # テーブルがなければ作成
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
    # 記事情報を挿入
    final_publicity = str(publicity) if publicity is not None else 'public'
    final_tags = str(tags) if tags is not None else '未設定'
    draft_url = url
    posts_url = ''
    if os.getenv('DEBUG', 'False').lower() == 'true':
        print(f"パラメータ確認: title={title}, url={url}, draft_url={draft_url}, posts_url={posts_url}, description={description}, publicity={final_publicity}, tags={final_tags}")
    cur.execute(
        "INSERT INTO URL_list_table (article_title, url, draft_url, posts_url, description, publicity, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, url, draft_url, posts_url, description, final_publicity, final_tags)
    )
    conn.commit()
    article_id = cur.lastrowid
    return conn, cur, article_id

def main():
    # --- DBとローカルファイルの整合性チェック ---
    posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blog-posts'))
    local_files = set(os.listdir(posts_dir)) if os.path.exists(posts_dir) else set()
    conn_check = sqlite3.connect(DB_PATH)
    cur_check = conn_check.cursor()
    cur_check.execute("SELECT id, article_title, url FROM URL_list_table")
    db_articles = cur_check.fetchall()
    for db_id, db_title, db_url in db_articles:
        safe_title = sanitize_filename(db_title)
        html_pattern = re.compile(rf".*_{safe_title}\.html$")
        md_pattern = re.compile(rf".*_{safe_title}\.md$")
        found = any(html_pattern.match(f) or md_pattern.match(f) for f in local_files)
        if not found:
            print(f"DBから削除: id={db_id}, title={db_title}（ローカルにファイルなし）")
            cur_check.execute("DELETE FROM URL_list_table WHERE id=?", (db_id,))
    conn_check.commit()
    cur_check.close()
    conn_check.close()
    print("ここで公開に設定するのは推奨されません。ファイル内容を編集したのちにmainpageから公開設定を行ってください。")
    article_title, description, file_extension = input_article_info()
    # 公開設定の入力説明を追加
    print("公開設定を入力してください。")
    print("公開: public または pb（例: public）")
    print("非公開: private または pr（例: private）")
    # 公開設定の入力追加（不正な値の場合は再入力を促す）
    while True:
        publicity = input("公開設定を入力してください (public/pb or private/pr): ").strip().lower()
        if publicity in ['public', 'pb']:
            publicity = 'public'
            break
        elif publicity in ['private', 'pr']:
            publicity = 'private'
            break
        else:
            print("公開設定が不正です。'public'または'private'で入力してください。")
    # 現在日時を取得
    timestamp = time.strftime("%Y%m%d%H%M%S")
    url = create_draft(article_title, file_extension, timestamp)
    if not url:
        print("記事ドラフトの作成に失敗しました。拡張子が不正です。'html' または 'md' を指定してください。")
        return
    print("タグを指定してください（カンマ区切りで複数指定可）。例: python,webdev")
    tags_input = input("タグ: ").strip()
    tags_list = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
    tags = ','.join(tags_list) if tags_list else '未設定'
    print(f"指定されたタグ: {tags}")
    conn, cur, article_id = register_article_to_mysql(article_title, url, description, publicity, tags)
    if conn and cur and article_id:
        try:
            print(f"記事ID: {article_id}")
            print("SQLiteに記事登録完了\n--- 登録済み記事一覧 ---")
            show_registered_articles(cur)
        finally:
            cur.close()
            conn.close()
    else:
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")


############################################################
# スクリプトのエントリーポイント
############################################################
# スクリプトのエントリーポイント
############################################################


def main():
    print("ここで公開に設定するのは推奨されません。ファイル内容を編集したのちにmainpageから公開設定を行ってください。")
    article_title, description, file_extension = input_article_info()
    print("公開設定を入力してください。")
    print("公開: public または pb（例: public）")
    print("非公開: private または pr（例: private）")
    while True:
        publicity = input("公開設定を入力してください (public/pb or private/pr): ").strip().lower()
        if publicity in ['public', 'pb']:
            publicity = 'public'
            break
        elif publicity in ['private', 'pr']:
            publicity = 'private'
            break
        else:
            print("公開設定が不正です。'public'または'private'で入力してください。")
    print("タグを指定してください（カンマ区切りで複数指定可）。例: python,webdev")
    tags_input = input("タグ: ").strip()
    tags_list = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
    tags = ','.join(tags_list) if tags_list else '未設定'
    print(f"指定されたタグ: {tags}")
    timestamp = time.strftime("%Y%m%d%H%M%S")
    url = create_draft(article_title, file_extension, timestamp)
    if not url:
        print("記事ドラフトの作成に失敗しました。拡張子が不正です。'html' または 'md' を指定してください。")
        return
    conn, cur, article_id = register_article_to_mysql(article_title, url, description, publicity, tags)
    if conn and cur and article_id:
        try:
            print(f"記事ID: {article_id}")
            print("SQLiteに記事登録完了\n--- 登録済み記事一覧 ---")
            show_registered_articles(cur)
        finally:
            cur.close()
            conn.close()
    else:
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")

if __name__ == "__main__":
    optimize_database()
    main()
