############################################################
# mainpage.py仕様に完全準拠した記事登録スクリプト
# 記事情報の入力、ドラフトファイル作成、MySQLへの登録、一覧表示までを一括処理
############################################################
import os  # OS操作用
import time  # 日時取得・整形用
import re  # ファイル名の正規表現処理
import mysql.connector  # MySQL接続用
from dotenv import load_dotenv  # .envファイルの読み込み


# .envファイルの絶対パス指定
# 1. os.path.dirname(__file__) でこのファイルのディレクトリを取得
# 2. その親ディレクトリ（..）に .env ファイルがあることを想定
# 3. os.path.abspath で絶対パスに変換
# 4. env_path には .env ファイルの絶対パスが格納される
# .envファイルの絶対パスを取得し、環境変数をロード
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
print(f".env path: {env_path}")  # 実際に取得したパスを表示
load_dotenv(dotenv_path=env_path)  # .envファイルを読み込んで環境変数に反映
# DB接続情報を環境変数から取得
DB_HOST = os.getenv('DB_HOST', 'localhost')  # DBホスト
DB_USER = os.getenv('DB_USER', 'root')  # DBユーザー
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # DBパスワード
DB_NAME = os.getenv('DB_NAME', 'blog_db')  # DB名
print(f"DB_PASSWORD loaded: '{DB_PASSWORD}'")  # パスワード確認用


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

    templates["html"] = open(html_path, "r", encoding="utf-8").read() if os.path.exists(html_path) else (
        "<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>記事タイトル</title>\n    <link rel=\"stylesheet\" href=\"style.css\">\n</head>\n<body>\n    <h1>記事タイトル</h1>\n    <script src=\"main.js\"></script>\n</body>\n</html>"
    )
    templates["css"] = open(css_path, "r", encoding="utf-8").read() if os.path.exists(css_path) else "body { font-family: Arial, sans-serif; }"
    templates["js"] = open(js_path, "r", encoding="utf-8").read() if os.path.exists(js_path) else "// JavaScript template"
    return templates


def create_draft(article_title, file_extension, timestamp):
    # ドラフトファイル（html/md）を作成
    # ファイル名はタイトル＋タイムスタンプ
    # htmlの場合はテンプレートも生成
    # 引数: article_title(str), file_extension(str), timestamp(str)
    # 戻り値: 作成したファイルのパス(str)
    safe_title = sanitize_filename(article_title)
    base_dir = os.path.join("blogsys", "drafts", f"{safe_title}_{timestamp}_{file_extension}")

    if file_extension == "md":
        # Markdownドラフトファイルを作成
        # - md_path: 保存先パス（タイトルとタイムスタンプで一意化）
        # - md_content: Markdownの初期内容（タイトルと日時を記載）
        md_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.md")
        md_content = f"# {article_title} {timestamp}\n"
        create_file(md_path, md_content)
        print(f"Markdown draft created at: {md_path}")
        # パス区切りをスラッシュに変換して返却
        return md_path.replace("\\", "/")

    if file_extension == "html":
        # HTMLドラフトファイル一式を作成
        # - テンプレートディレクトリからhtml/css/jsを取得
        # - html_path, css_path, js_path: 保存先パス
        template_dir = os.path.join("blogsys", "test", "template")
        templates = get_template_content(template_dir)
        html_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.html")
        css_path = os.path.join(base_dir, "style.css")
        js_path = os.path.join(base_dir, "main.js")
        create_file(html_path, templates["html"])
        create_file(css_path, templates["css"])
        create_file(js_path, templates["js"])
        print(f"HTML draft created at: {html_path}")
        # パス区切りをスラッシュに変換して返却
        return html_path.replace("\\", "/")

    # 拡張子が不正な場合はNoneを返す
    print("Invalid file extension. Please enter either 'html' or 'md'.")
    return None


def register_article_to_mysql(title, url, description, publicity=None):
    # MySQLに記事情報を登録（公開設定追加）
    # テーブルがなければ作成し、公開設定(publicity)も保存
    # 引数: title(str), url(str), description(str), publicity(str)
    # 戻り値: conn, cur (MySQL接続・カーソル)
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


def show_registered_articles(cur):
    # DB内の全記事情報を表示
    # 引数: cur(MySQLカーソル)
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


def main():
    # 記事登録処理のメイン関数
    # 1. ユーザーから記事情報（タイトル・説明・拡張子・公開設定）を取得
    # 2. ドラフトファイル（html/md）を作成
    # 3. MySQLに記事情報を登録
    # 4. 登録済み記事一覧を表示
    print("=== 記事登録システム ===")
    print("ここで公開に設定するのは推奨されません。ファイル内容を編集したのちにmainpageから公開設定を行ってください。")
    article_title, description, file_extension = input_article_info()
    # 公開設定の入力追加
    publicity = input("公開設定を入力してください (public/pb or private/pr): ").strip().lower()
    if publicity in ['public', 'pb']:
        publicity = 'public'
    elif publicity in ['private', 'pr']:
        publicity = 'private'
    else:
        print("公開設定が不正です。'public'で登録します。")
        publicity = 'public'
    # 現在日時を取得
    timestamp = time.strftime("%Y_%m_%d_%H_%M")
    # ドラフトファイル作成（urlは作成したファイルのパス）
    url = create_draft(article_title, file_extension, timestamp)
    if not url:
        return
    # MySQLに記事情報を登録
    conn, cur = register_article_to_mysql(article_title, url, description, publicity)
    if conn and cur:
        print("MySQLに記事登録完了\n--- 登録済み記事一覧 ---")
        show_registered_articles(cur)
        cur.close()
        conn.close()
    else:
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")


############################################################
# スクリプトのエントリーポイント
############################################################
if __name__ == "__main__":
    main()
