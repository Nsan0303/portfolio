# mainpage.py仕様に完全準拠した記事登録スクリプト
import os
import time
import re
import mysql.connector
from dotenv import load_dotenv


# .envファイルの絶対パス指定
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
print(f".env path: {env_path}")
load_dotenv(dotenv_path=env_path)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'blog_db')
print(f"DB_PASSWORD loaded: '{DB_PASSWORD}'")


def sanitize_filename(name: str) -> str:
    """
    OSごとのファイル名禁止文字を考慮して安全なファイル名に変換
    """
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def create_file(path: str, content: str = ""):
    """
    ディレクトリ作成＆ファイル書き込み
    """
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def get_template_html(title, description, now):
    """
    mainpage.pyのテンプレートに合わせたHTML生成
    """
    return f"""<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"/static/blog.css\">
</head>
<body>
    <article>
        <h1>{title}</h1>
        <p>{description}</p>
        <time>{now}</time>
    </article>
    <a href=\"/\">← トップへ戻る</a>
</body>
</html>
"""


def input_article_info():
    """
    記事情報の入力（タイトル・説明・拡張子）
    """
    title = input("記事タイトルを入力してください: ")
    description = input("記事説明を入力してください: ")
    file_extension = input("ファイル拡張子を入力してください (html or md): ").strip().lower()
    print("サムネイル画像は 'tmb.png' として作成してください。")
    return title, description, file_extension


def get_template_content(template_dir):
    """
    指定ディレクトリからテンプレート(html, css, js)を取得
    """
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
    """
    ドラフトファイル作成（html/md）
    """
    safe_title = sanitize_filename(article_title)
    base_dir = os.path.join("blogsys", "drafts", f"{safe_title}_{timestamp}_{file_extension}")

    if file_extension == "md":
        md_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.md")
        md_content = f"# {article_title} {timestamp}\n"
        create_file(md_path, md_content)
        print(f"Markdown draft created at: {md_path}")
        return md_path.replace("\\", "/")

    if file_extension == "html":
        template_dir = os.path.join("blogsys", "test", "template")
        templates = get_template_content(template_dir)
        html_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.html")
        css_path = os.path.join(base_dir, "style.css")
        js_path = os.path.join(base_dir, "main.js")
        create_file(html_path, templates["html"])
        create_file(css_path, templates["css"])
        create_file(js_path, templates["js"])
        print(f"HTML draft created at: {html_path}")
        return html_path.replace("\\", "/")

    print("Invalid file extension. Please enter either 'html' or 'md'.")
    return None


def register_article_to_mysql(title, url, description, publicity=None):
    """
    MySQLに記事情報を登録（公開設定追加）
    """
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
    """
    DB内の全記事表示
    """
    try:
        cur.execute("SELECT * FROM URL_list_table")
        result = cur.fetchall()
        for row in result:
            print(f"ID: {row[0]}, Title: {row[1]}, URL: {row[2]}, Description: {row[3]}, Publicity: {row[4]}")
    except Exception as e:
        print(f"記事取得エラー: {e}")


def main():
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
    timestamp = time.strftime("%Y_%m_%d_%H_%M")
    url = create_draft(article_title, file_extension, timestamp)
    if not url:
        return
    conn, cur = register_article_to_mysql(article_title, url, description, publicity)
    if conn and cur:
        print("MySQLに記事登録完了\n--- 登録済み記事一覧 ---")
        show_registered_articles(cur)
        cur.close()
        conn.close()
    else:
        print("記事登録に失敗しました（DB接続情報や.envを確認してください）")


if __name__ == "__main__":
    main()
