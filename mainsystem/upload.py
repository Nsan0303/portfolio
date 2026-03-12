import os  # OS操作用
import time  # 日時取得・整形用
import re  # ファイル名の正規表現処理
import mysql.connector  # MySQL接続用
from dotenv import load_dotenv  # .envファイルの読み込み

# .envファイルの絶対パスを取得し、環境変数をロード
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)
# DB接続情報を環境変数から取得
DB_HOST = os.getenv('DB_HOST', 'localhost')  # DBホスト
DB_USER = os.getenv('DB_USER', 'root')  # DBユーザー
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # DBパスワード
DB_NAME = os.getenv('DB_NAME', 'blog_db')  # DB名

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
def get_template_html(title, description, now):
    return f"""<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{title}</title>\n    <link rel=\"stylesheet\" href=\"/static/blog.css\">\n</head>\n<body>\n    <article>\n        <h1>{title}</h1>\n        <p>{description}</p>\n        <time>{now}</time>\n    </article>\n    <a href=\"/\">← トップへ戻る</a>\n</body>\n</html>\n"""

# MySQLに記事情報を登録（公開設定追加）
# テーブルがなければ作成し、公開設定(publicity)も保存
# 引数: title(str), url(str), description(str), publicity(str)
# 戻り値: conn, cur (MySQL接続・カーソル)
def register_article_to_mysql(title, url, description, publicity=None):
    try:
        # DB接続
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor()
        # テーブルがなければ作成
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
        # 記事情報を挿入
        cur.execute(
            "INSERT INTO URL_list_table (article_title, url, description, publicity) VALUES (%s, %s, %s, %s)",
            (title, url, description, publicity or 'public')
        )
        conn.commit()
        return conn, cur
    except Exception as e:
        # DB登録エラー時
        print(f"DB登録エラー: {e}")
        return None, None

# DB内の全記事情報を表示
# 引数: cur(MySQLカーソル)
def show_registered_articles(cur):
    try:
        # 全記事情報を取得
        cur.execute("SELECT * FROM URL_list_table")
        result = cur.fetchall()
        # 1件ずつ表示
        for row in result:
            print(f"ID: {row[0]}, Title: {row[1]}, URL: {row[2]}, Description: {row[3]}, Publicity: {row[4]}")
    except Exception as e:
        # 取得エラー時
        print(f"記事取得エラー: {e}")

# 記事アップロード処理のメイン関数
# ユーザー入力から記事情報を取得し、ファイル作成・DB登録を行う
def upload_article():
    print("=== 記事アップロードシステム ===")
    # 記事タイトル入力
    title = input("記事タイトルを入力してください: ")
    # 記事説明入力
    description = input("記事説明を入力してください: ")
    # ファイル拡張子入力（html or md）
    file_ext = input("ファイル拡張子を入力してください (html or md): ").strip().lower()
    # 公開設定入力
    publicity = input("公開設定を入力してください (public/pb or private/pr): ").strip().lower()
    # 公開設定の値を判定
    if publicity in ['public', 'pb']:
        publicity = 'public'
    elif publicity in ['private', 'pr']:
        publicity = 'private'
    else:
        print("公開設定が不正です。'public'で登録します。")
        publicity = 'public'
    # 現在日時を取得
    now = time.strftime("%Y_%m_%d_%H_%M")
    # ファイル名を安全に生成
    safe_title = sanitize_filename(title)
    # htmlの場合は従来通り
    if file_ext == "html":
        fname = f"{now}_{safe_title}.html"
        posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blog-posts'))
        file_path = os.path.join(posts_dir, fname)
        html_content = get_template_html(title, description, now)
        create_file(file_path, html_content)
        url = f"/posts/{fname}"
    # markdownの場合はHTMLへ変換
    elif file_ext == "md":
        fname = f"{now}_{safe_title}.md"
        posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blog-posts'))
        file_path = os.path.join(posts_dir, fname)
        # Markdownファイル作成
        md_content = f"# {title}\n{description}\n{now}\n"
        create_file(file_path, md_content)
        # Markdown→HTML変換（簡易）
        try:
            import markdown
            html_content = markdown.markdown(md_content)
        except ImportError:
            html_content = f"<h1>{title}</h1><p>{description}</p><time>{now}</time>"
        # 変換したHTMLを同名で保存
        html_fname = f"{now}_{safe_title}.html"
        html_path = os.path.join(posts_dir, html_fname)
        create_file(html_path, html_content)
        url = f"/posts/{html_fname}"
    else:
        print("拡張子が不正です。htmlで登録します。")
        fname = f"{now}_{safe_title}.html"
        posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blog-posts'))
        file_path = os.path.join(posts_dir, fname)
        html_content = get_template_html(title, description, now)
        create_file(file_path, html_content)
        url = f"/posts/{fname}"
    # DB登録
    conn, cur = register_article_to_mysql(title, url, description, publicity)
    if conn and cur:
        # ファイル作成成功・DB登録成功
        print(f"記事ファイル作成: {file_path}")
        print("MySQLに記事登録完了\n--- 登録済み記事一覧 ---")
        show_registered_articles(cur)
        cur.close()
        conn.close()
    else:
        # DB登録失敗
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")
