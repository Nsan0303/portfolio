import os
import time
import re

def sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を安全な形式に変換"""
    return re.sub(r'[^a-zA-Z0-9_\-一-龥ぁ-んァ-ヶ]', '_', name)

def create_file(path: str, content: str = ""):
    """ディレクトリを作成しつつファイルを書き込む"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def get_template_content(template_dir: str, ext: str):
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
    file_extension = input("please enter the file extension (html or md): ").strip().lower()

    # 安全なファイル名に変換
    safe_title = sanitize_filename(article_title)
    timestamp = time.strftime("%Y_%m_%d_%H_%M")
    base_dir = os.path.join("blogsys", "drafts", f"{safe_title}_{timestamp}_{file_extension}")

    if file_extension == "md":
        md_dir = os.path.join(base_dir, "md")
        md_path = os.path.join(md_dir, f"{safe_title}_{timestamp}.md")
        md_content = f"# {article_title} {timestamp}\n"
        create_file(md_path, md_content)
        print(f"Markdown draft created at: {md_path}")

    elif file_extension == "html":
        html_dir = os.path.join(base_dir, "html")
        template_dir = os.path.join("blogsys", "test", "template")
        templates = get_template_content(template_dir, "html")

        html_path = os.path.join(html_dir, f"{safe_title}_{timestamp}.html")
        css_path = os.path.join(html_dir, "style.css")
        js_path = os.path.join(html_dir, "main.js")

        create_file(html_path, templates["html"])
        create_file(css_path, templates["css"])
        create_file(js_path, templates["js"])

        print(f"HTML draft created at: {html_path}")

    else:
        print("Invalid file extension. Please enter either 'html' or 'md'.")

if __name__ == "__main__":
    main()
