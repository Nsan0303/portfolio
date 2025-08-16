import flask
import os
import re
import datetime
import mysql.connector
import time
import threading

app = flask.Flask(__name__)
app.static_folder = 'static'
app.static_url_path = '/static'

Blog_List = []  # グローバル記事リスト
app.config['JSON_AS_ASCII'] = False  # 日本語対応

def Check_article_existence():
    while True:
        time.sleep(1)  # 1秒ごとに実行
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Nsan0303",
            database="blog_db"
    )
        conn.autocommit = False
        sqlcommond = ("""
        DELETE
        FROM blog_posts
        WHERE id NOT IN (SELECT id FROM URL_list_table)
        """)
        if conn.is_connected():
            try:
                conn.ping(reconnect=True)
            except mysql.connector.Error as e:
                print(f"Error reconnecting to database: {e}")
            path = 'blog-posts'
            if not os.path.exists(path):
                cursor = conn.cursor()
                cursor.execute(sqlcommond)
                conn.commit()
                cursor.close()
                conn.close()

def fetch_articles():
    """
    MySQLから記事一覧を取得し、Blog_Listを更新する
    並列処理用の関数
    """
    global Blog_List
    while True:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Nsan0303",
                database="blog_db"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM URL_list_table")
            result = cursor.fetchall()
            Blog_List = []
            for row in result:
                Blog_List.append({
                    "ID": row[0],
                    "Title": row[1],
                    "URL": row[2],
                    "Description": row[3]
                })
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching articles: {e}")
        time.sleep(5)  # 5秒ごとに更新

def get_articles():
    """
    Blog_Listの内容から記事一覧HTMLを生成して返す
    """
    global Blog_List
    articles = ""
    for row in Blog_List:
        match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2})', row['URL'])
        if match:
            timestr = match.group(1)
            dt = datetime.datetime.strptime(timestr, '%Y_%m_%d_%H_%M')
            timeshow = dt.strftime('%Y年%m月%d日 %H:%M')
        else:
            timeshow = "日時不明"
        articles += f'''
        <article>
            <img src="tmb.png">
            <time datetime="{timestr if match else ''}">{timeshow}</time>
            <h2><a href="{row['URL']}">{row['Title']}</a></h2>
            <p>{row['Description']}</p>
        </article>
        '''
    return articles

# 記事取得の並列スレッド起動
article_thread = threading.Thread(target=fetch_articles, daemon=True)
article_thread.start()

@app.route('/')
def blog():
    return f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nsanのポートフォリオ</title>
    <link rel="stylesheet" href="/static/blog.css">
</head>
<body>
    <header class="site-header">
        <div class="container header-flex">
            <h1 class="logo">Nsanのポートフォリオ</h1>
            <nav class="main-nav">
                <ul>
                    <li><a href="#">Home</a></li>
                    <li><a href="Works/Works.html">Works</a></li>
                    <li><a href="#blog">Blog</a></li>
                    <li><a href="#sns">SNS</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <section class="blog-posts">
        {get_articles()}
    </section>
    <footer class="site-footer">
        <div class="container">
            <p>&copy; 2025 Nsan. All rights reserved.</p>
            <button id="scrollTopBtn">▲ Top</button>
        </div>
    </footer>
    <script src="/static/Bmain.js"></script>
</body>
</html>
'''

@app.route('/posts/<path:filename>')
def serve_post(filename):
    return flask.send_from_directory('blog-posts', filename)

@app.route('/NsanBlogDev', methods=['GET', 'POST'])
def add_article():
    if flask.request.method == 'POST':
        DEV_PASSWORD = 'Nsan0303'  # ここにパスワードを設定
        password = flask.request.form.get('password', '')
        if not password == DEV_PASSWORD:
            #アラートにてパスワードが間違っていることを通知
            allart = "パスワードが間違っています。"
            allart += "正しいパスワードを入力してください。"
            return allart   
        title = flask.request.form.get('title', 'No Title')
        url = flask.request.form.get('url', 'No URL')
        description = flask.request.form.get('description', '')
        # MySQLに追加
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Nsan0303",
                database="blog_db"
            )
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO URL_list_table (Title, URL, Description) VALUES (%s, %s, %s)",
                (title, url, description)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return flask.redirect('/')
        except Exception as e:
            return f"Error: {e}"
    # GET時はフォームを表示
    return '''
    <form method="post">
        <label>タイトル: <input name="title"></label><br>
        <label>URL: <input name="url"></label><br>
        <label>説明: <input name="description"></label><br>
        <label>パスワード: <input name="password" type="password"></label><br>
        <button type="submit">追加</button>
    </form>
    '''

# TODO: 本番環境対応のための修正項目
# TODO パスワードやDB接続情報を環境変数で管理する
# TODO CSRF対策（Flask-WTF等の導入）
# TODO - HTTPS対応（SSL証明書の設定）
# TODO WSGIサーバー（gunicorn等）で運用する
# TODO 不要な <script src="mainpage.py"></script> の削除
# TODO エラーハンドリング強化（ユーザー向けメッセージ表示）

if __name__ == '__main__':
    app.run(debug=True)
