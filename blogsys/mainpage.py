import flask
import os
import re
import datetime
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

# .envファイルの明示的なパス指定
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'blog_db')
DEV_PASSWORD = os.getenv('DEV_PASSWORD', 'default_password')

app = flask.Flask(
    __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)
app.config['JSON_AS_ASCII'] = False  # 日本語対応
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret")  # Flask-WTFに必須

# ======== フォーム ==========
class LoginForm(FlaskForm):
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

# ======== 記事スキャン ==========
def scan_drafts_articles():
    articles = []
    drafts_dir = os.path.join(os.path.dirname(__file__), 'drafts')
    if not os.path.exists(drafts_dir):
        return []
    for root, _, files in os.walk(drafts_dir):
        for file in files:
            if file.endswith('.html'):
                title = file.split('_')[0]
                rel_path = os.path.relpath(os.path.join(root, file), drafts_dir)
                url = f'/drafts/{rel_path.replace(os.sep, "/")}'
                description = '説明未設定'
                articles.append({
                    'Title': title,
                    'URL': url,
                    'Description': description
                })
    return articles

def get_articles():
    articles_list = scan_drafts_articles()
    result = []
    for row in articles_list:
        match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2})', row['URL'])
        if match:
            dt = datetime.datetime.strptime(match.group(1), '%Y_%m_%d_%H_%M')
            timeshow = dt.strftime('%Y年%m月%d日 %H:%M')
        else:
            timeshow = "日時不明"
        result.append({
            "title": row["Title"],
            "url": row["URL"],
            "desc": row["Description"],
            "date": timeshow,
            "thumb": "https://picsum.photos/200/300"
        })
    return result

# ======== ルート ==========
@app.route('/')
def index():
    articles = get_articles()
    return flask.render_template("index.html", articles=articles)

@app.route('/NsanBlogEdit', methods=['GET', 'POST'])
def edit_monitor_route():
    form = LoginForm()
    if flask.request.method == 'POST' and form.validate_on_submit():
        if form.password.data != DEV_PASSWORD:
            return flask.render_template("login_error.html")
        return flask.render_template("editor.html")
    return flask.render_template("login.html", form=form)
	
@app.route('/drafts/<path:filename>')
def serve_draft(filename):
    return flask.send_from_directory('drafts', filename)

if __name__ == "__main__":
    app.run(debug=True)
