############################################################
# Flaskベースのポートフォリオ記事管理アプリ
# 記事一覧表示・編集・ドラフト配信・ログイン認証などを担当
############################################################
# ======== 必要なライブラリのインポート ========
import flask  # Flask本体
import os  # OS操作用
import re  # 正規表現
import datetime  # 日時操作
from dotenv import load_dotenv  # .envファイルの読み込み
from flask_wtf import FlaskForm  # Flask-WTFフォーム
from wtforms import PasswordField, SubmitField  # フォーム部品
from wtforms.validators import DataRequired  # バリデータ


# ======== 環境変数の読み込み ========
# .envファイルの明示的なパス指定
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
# DB接続情報・開発用パスワードを環境変数から取得
DB_HOST = os.getenv('DB_HOST', 'localhost')  # DBホスト
DB_USER = os.getenv('DB_USER', 'root')  # DBユーザー
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # DBパスワード
DB_NAME = os.getenv('DB_NAME', 'blog_db')  # DB名
DEV_PASSWORD = os.getenv('DEV_PASSWORD', 'default_password')  # 開発用パスワード


# ======== Flaskアプリケーション初期化 ========
# Flaskアプリ本体の初期化と設定
app = flask.Flask(
    __name__,
    static_folder='static',  # 静的ファイルのパス
    static_url_path='/static',  # 静的ファイルのURLパス
    template_folder='templates'  # テンプレートフォルダ
)
app.config['JSON_AS_ASCII'] = False  # 日本語対応
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret")  # Flask-WTFに必須


# ======== ログインフォーム定義 ========
# Flask-WTFを使ったログインフォームの定義
class LoginForm(FlaskForm):
    password = PasswordField('パスワード', validators=[DataRequired()])  # パスワード入力欄
    submit = SubmitField('ログイン')  # 送信ボタン



# ======== 記事スキャン関連関数 ========
def scan_drafts_articles():
    """
    draftsディレクトリ内のHTML記事をスキャンし、記事リストを返す
    - 記事ファイル名からタイトルを推定
    - URLを生成
    - 説明はデフォルト値
    """
    articles = []
    drafts_dir = os.path.join(os.path.dirname(__file__), 'drafts')  # draftsディレクトリの絶対パス
    if not os.path.exists(drafts_dir):
        return []  # draftsディレクトリがなければ空リスト
    for root, _, files in os.walk(drafts_dir):
        for file in files:
            if file.endswith('.html'):
                # ファイル名の先頭をタイトルとする
                title = file.split('_')[0]
                # 相対パスを取得しURL化
                rel_path = os.path.relpath(os.path.join(root, file), drafts_dir)
                url = f'/drafts/{rel_path.replace(os.sep, "/")}'  # URL生成（パス区切りを/に）
                description = '説明未設定'  # デフォルト説明
                articles.append({
                    'Title': title,
                    'URL': url,
                    'Description': description
                })
    return articles

def get_articles():
    """
    記事リストをテンプレート用の辞書リストとして整形して返す
    - ファイル名から日時を抽出し表示用に整形
    - サムネイル画像はダミー
    """
    articles_list = scan_drafts_articles()
    result = []
    for row in articles_list:
        # URLから日時情報を抽出
        match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2})', row['URL'])
        if match:
            # 日時を表示用に整形
            dt = datetime.datetime.strptime(match.group(1), '%Y_%m_%d_%H_%M')
            timeshow = dt.strftime('%Y年%m月%d日 %H:%M')
        else:
            timeshow = "日時不明"
        # 記事情報をテンプレート用辞書に整形
        result.append({
            "title": row["Title"],
            "url": row["URL"],
            "desc": row["Description"],
            "date": timeshow,
            "thumb": "https://picsum.photos/200/300"  # サムネイル画像（ダミー）
        })
    return result



# ======== ルーティング定義 ========
@app.route('/')
def index():
    """
    トップページ表示（記事一覧をテンプレートに渡す）
    - get_articles()で記事リストを取得
    - index.htmlテンプレートにarticlesを渡す
    """
    articles = get_articles()
    # 記事一覧をテンプレートに渡して表示
    return flask.render_template("index.html", articles=articles)

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
    # draftsディレクトリから指定ファイルを返す
    return flask.send_from_directory('drafts', filename)


############################################################
# スクリプトのエントリーポイント
############################################################
if __name__ == "__main__":
    # ======== アプリケーション起動 ========
    app.run(debug=True)
