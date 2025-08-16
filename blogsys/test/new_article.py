import os
import time
import re
import mysql.connector as mydv


def Registration_MySQL(article_title, url, description):
    """
    MySQLに記事情報を登録し、コネクションとカーソルを返す
    """
    conn = mydv.connect(
        host="localhost",
        user="root",
        password="pass",
        database="db"
    )
    cur = conn.cursor()
    conn.ping(reconnect=True)
    print(conn.is_connected())
    cur.execute("""
        CREATE TABLE IF NOT EXISTS URL_list_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            article_title VARCHAR(255) NOT NULL,
            url VARCHAR(255) NOT NULL,
            description TEXT NOT NULL
        )
    """)
    conn.commit()
    print("Table created successfully.")
    cur.execute("INSERT INTO URL_list_table (article_title, url, description) VALUES (%s, %s, %s)", (article_title, url, description))
    conn.commit()
    return conn, cur

def sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を安全な形式に変換"""
    return re.sub(r'[^a-zA-Z0-9_\-一-龥ぁ-んァ-ヶ]', '_', name)

def create_file(path: str, content: str = ""):
    """ディレクトリを作成しつつファイルを書き込む"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def get_template_content(template_dir: str):
    """テンプレートファイルの内容を取得"""
    files = {
        "html": "template.html",
        "css": "template.css",
        "js": "template.js"
    }
    contents = {}
    for key, filename in files.items():
        path = os.path.join(template_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            contents[key] = f.read()
    return contents

def main():
    # 入力
    article_title = input("please enter the article Title: ")
    description = input("please enter the article Description: ")
    file_extension = input("please enter the file extension (html or md): ").strip().lower()
    print("Please create the thumbnail image as「tmb.png」")

    # 安全なファイル名に変換
    safe_title = sanitize_filename(article_title)
    timestamp = time.strftime("%Y_%m_%d_%H_%M")
    base_dir = os.path.join("blogsys", "drafts", f"{safe_title}_{timestamp}_{file_extension}")

    url = ""
    if file_extension == "md":
        md_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.md")
        md_content = f"# {article_title} {timestamp}\n"
        create_file(md_path, md_content)
        url = md_path.replace("\\", "/")
        print(f"Markdown draft created at: {md_path}")

    elif file_extension == "html":
        template_dir = os.path.join("blogsys", "test", "template")
        templates = get_template_content(template_dir)

        html_path = os.path.join(base_dir, f"{safe_title}_{timestamp}.html")
        css_path = os.path.join(base_dir, "style.css")
        js_path = os.path.join(base_dir, "main.js")

        create_file(html_path, templates["html"])
        create_file(css_path, templates["css"])
        create_file(js_path, templates["js"])
        url = html_path.replace("\\", "/")
        print(f"HTML draft created at: {html_path}")
    else:
        print("Invalid file extension. Please enter either 'html' or 'md'.")
        return

    # MySQLに登録
    conn, cur = Registration_MySQL(article_title, url, description)
    print("Article registered in MySQL database.\nthis is a Registration Content")
    try:
        cur.execute("SELECT * FROM URL_list_table")
        result = cur.fetchall()
        for row in result:
            print(f"ID: {row[0]}, Title: {row[1]}, URL: {row[2]}, Description: {row[3]}")
    except Exception as e:
        print(f"Error fetching articles: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
