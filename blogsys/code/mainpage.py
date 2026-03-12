############################################################
# Flaskベースのポートフォリオ記事管理アプリ
# 記事一覧表示・編集・ドラフト配信・ログイン認証などを担当
############################################################
# ======== 必要なライブラリのインポート ========
import flask  # Flask本体
import os  # OS操作用
import re  # 正規表現
import datetime  # 日時操作
import sqlite3  # SQLiteデータベース
from dotenv import load_dotenv  # .envファイルの読み込み
from flask_wtf import FlaskForm  # Flask-WTFフォーム
from wtforms import PasswordField, SubmitField  # フォーム部品
from wtforms.validators import DataRequired  # バリデータ

# ======== サムネイル画像URL定数 ========
THUMBNAIL_URL = "https://picsum.photos/200/300"  # サムネイル画像（ダミー）


# ======== 環境変数の読み込み ========
# .envファイルの明示的なパス指定
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# SQLiteデータベースファイルパス・開発用パスワードを環境変数から取得
db_path_from_env = os.getenv('DB_PATH', 'blog_db.sqlite')
if os.path.isabs(db_path_from_env):
    # 絶対パスの場合はそのまま使用
    DB_PATH = db_path_from_env
else:
    # 相対パスの場合は blogsys ディレクトリからの相対パスとして解決
    blogsys_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_PATH = os.path.join(blogsys_dir, db_path_from_env)

DEV_PASSWORD = os.getenv('DEV_PASSWORD', 'default_password')  # 開発用パスワード


# ======== Linux環境用にパスの区切り文字を統一 ========
def normalize_path(path):
    return os.path.normpath(path)

DB_PATH = normalize_path(DB_PATH)


# ======== Flaskアプリケーション初期化 ========
# Flaskアプリ本体の初期化と設定
app = flask.Flask(
    __name__,
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static')),
    static_url_path='/static',
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
)
app.config['JSON_AS_ASCII'] = False  # 日本語対応
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret")  # Flask-WTFに必須


# ======== ログインフォーム定義 ========
# Flask-WTFを使ったログインフォームの定義
class LoginForm(FlaskForm):
    password = PasswordField('パスワード', validators=[DataRequired()])  # パスワード入力欄
    submit = SubmitField('ログイン')  # 送信ボタン



# ======== 記事スキャン関連関数 ========
def scan_published_articles():
    """
    公開済み記事（blog-posts ディレクトリ内のHTML記事）をスキャンし、記事リストを返す
    - 記事ファイル名からタイトルを推定
    - URLを生成
    """
    articles = []
    posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'blog-posts'))
    if not os.path.exists(posts_dir):
        return []
    # DBからpb(public)記事を取得
    db_path = DB_PATH
    print(f"[DEBUG] DBパス: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, article_title, posts_url, description, publicity, tags, timestamp FROM URL_list_table WHERE publicity='public' OR publicity='pb'")
    db_articles = cur.fetchall()
    print(f"[DEBUG] DB取得件数: {len(db_articles)}")
    for row in db_articles:
        print(f"[DEBUG] DB記事: {row}")
    cur.close()
    conn.close()
    # posts_urlカラムを利用して記事一覧を生成
    for row in db_articles:
        db_id, db_title, posts_url, db_desc, _, _, _ = row
        if posts_url and posts_url.endswith('.html'):
            # posts_urlはblog-posts/ファイル名.html形式
            # blog-posts/ を除去し、ファイル名のみ渡す
            filename = os.path.basename(posts_url)
            url = flask.url_for('serve_post', filename=filename)
            articles.append({
                'ID': db_id,
                'Title': db_title,
                'URL': url,
                'Description': db_desc,
                'thumb': THUMBNAIL_URL
            })
    return articles

def scan_drafts_articles():
    """
    下書き記事（drafts ディレクトリ内のHTML記事）をスキャンし、記事リストを返す
    - 記事ファイル名からタイトルを推定
    - URLを生成
    """
    articles = []
    # DBから下書き記事を取得
    db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, article_title, posts_url, description, publicity, tags, timestamp FROM URL_list_table WHERE publicity='draft'")
    db_articles = cur.fetchall()
    cur.close()
    conn.close()
    
    # posts_urlカラムを利用して記事一覧を生成
    for row in db_articles:
        db_id, db_title, posts_url, db_desc, _, _, _ = row
        if posts_url and posts_url.endswith('.html'):
            filename = os.path.basename(posts_url)
            url = flask.url_for('serve_draft', filename=filename)
            articles.append({
                'ID': db_id,
                'Title': db_title,
                'URL': url,
                'Description': db_desc,
                'thumb': THUMBNAIL_URL
            })
    return articles

def get_articles():
    """
    下書き記事リストをテンプレート用の辞書リストとして整形して返す
    - ファイル名から日時を抽出し表示用に整形
    - サムネイル画像はダミー
    """
    articles_list = scan_drafts_articles()
    result = []
    for row in articles_list:
        match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2})', row['URL'])
        if match:
            dt = datetime.datetime.strptime(match.group(1), '%Y_%m_%d_%H_%M')
            _ = dt.strftime('%Y年%m月%d日 %H:%M')
        else:
            _ = "日時不明"
        result.append({
            "id": row.get("ID"),
            "title": row["Title"],
            "url": row["URL"],
            "desc": row["Description"],
            "thumb": THUMBNAIL_URL
        })
    return result



# ======== ルーティング定義 ========
@app.route('/')
def index():
    articles = scan_published_articles()
    if not articles:
        error_message = "公開記事がありません。DB・blog-postsディレクトリ・公開設定を確認してください。"
        return flask.render_template("index.html", articles=[], error_message=error_message)
    return flask.render_template("index.html", articles=articles, error_message=None)

@app.route('/posts/<path:filename>')
def serve_post(filename):
    import os
    posts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'blog-posts'))
    # パストラバーサル防止・拡張子チェック
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith('.html'):
        flask.abort(404)
    return flask.send_from_directory(posts_dir, safe_filename)
@app.route('/NsanBlogEdit', methods=['GET', 'POST'])
def edit_monitor_route():
    """
    記事編集画面へのログイン・遷移
    - POST時はパスワード認証
    - 認証失敗時はlogin_error.html
    - 成功時はeditor.html
    - GET時はlogin.html
    """
    form = LoginForm()  
    # POST時はパスワード認証
    if flask.request.method == 'POST' and form.validate_on_submit():
        if form.password.data != DEV_PASSWORD:
            # パスワード不一致時はエラー画面
            return flask.render_template("login_error.html")
        # 認証成功時は編集画面
        return flask.render_template("editor.html")
    # GET時はログイン画面
    return flask.render_template("login.html", form=form)

@app.route('/drafts/<path:filename>')
def serve_draft(filename):
    """
    draftsディレクトリ内のファイルを配信
    - /drafts/以下のパスでファイルを返す
    """
    import os
    drafts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'drafts'))
    # パストラバーサル防止・拡張子チェック
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith('.html'):
        flask.abort(404)
    return flask.send_from_directory(drafts_dir, safe_filename)

# ======== アプリケーション起動 ========
if __name__ == '__main__':
    # === DB調査用コード（Flask起動前に実行） ===
    import sqlite3
    db_path = DB_PATH
    print("[DB調査] URL_list_table 全件表示:")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, article_title, posts_url, description, publicity, tags, timestamp FROM URL_list_table")
        rows = cur.fetchall()
        for row in rows:
            print(row)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB調査エラー] {e}")
    # Flaskアプリ起動（DEBUGは環境変数で制御、本番環境では .env の DEBUG=False を設定）
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true')
