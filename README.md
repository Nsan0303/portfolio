# Nsan's Portfolio

個人ポートフォリオサイト + ブログシステム (blogsys) のリポジトリです。

---

## リポジトリ構成

```
portfolio/
├── index.html          # ポートフォリオトップページ
├── style.css           # トップページのスタイル
├── script.js           # トップページのスクリプト
├── IndexIMG/           # トップページ用画像
├── Works/              # 制作物紹介ページ
│   ├── Works.html
│   ├── Works.css
│   └── Wmain.js
└── blogsys/            # ブログシステム (Flask)
    ├── mainpage.py     # Flaskアプリ本体
    ├── templates/      # Jinja2テンプレート
    ├── static/         # 静的ファイル (CSS, JS)
    ├── drafts/         # 公開済み記事ディレクトリ
    ├── editor/         # エディタUI
    ├── login/          # ログインUI
    └── test/           # 記事管理CLIスクリプト
```

---

## ポートフォリオサイト

`index.html` をブラウザで直接開くか、Webサーバー経由でアクセスします。

---

## ブログシステム (blogsys)

### 技術スタック

| 項目 | 内容 |
|------|------|
| バックエンド | Python / Flask |
| テンプレートエンジン | Jinja2 |
| データベース | MySQL |
| フロントエンド | HTML / CSS / JavaScript |
| 設定管理 | python-dotenv (.env) |

### セットアップ

#### 1. Python依存パッケージのインストール

```bash
cd blogsys
# 仮想環境の作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

#### 2. .envファイルの作成

`blogsys/` ディレクトリに `.env` ファイルを作成します。

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=<MySQLのパスワード>
DB_NAME=blog_db
DEV_PASSWORD=<管理画面のパスワード>
SECRET_KEY=<任意のランダム文字列>
```

作成後、ファイルのアクセス権限を制限してください:

```bash
chmod 600 blogsys/.env
```

#### 3. MySQLデータベースの準備

```sql
CREATE DATABASE IF NOT EXISTS blog_db;
```

`blog_db` データベースを作成すれば、テーブル (`URL_list_table`) はアプリ起動時に自動作成されます。

### Flaskサーバーの起動

```bash
cd blogsys
python mainpage.py
```

サーバーは `http://localhost:5000` で起動します。

### アクセスURL

| URL | 内容 |
|-----|------|
| `http://localhost:5000/` | ブログトップ（記事一覧） |
| `http://localhost:5000/NsanBlogEdit` | 管理者エディタ（パスワード認証あり） |
| `http://localhost:5000/drafts/<ファイルパス>` | 個別記事の表示 |

---

## systemdサービスとして登録する方法

本番環境（Linux）でサーバーを常時起動する場合、systemdサービスとして登録できます。

`blogsys/blogsys.service` を参考にしてください。

```bash
# サービスファイルのコピー
sudo cp blogsys/blogsys.service /etc/systemd/system/

# デーモン再読み込み
sudo systemctl daemon-reload

# サービス有効化（OS起動時に自動起動）
sudo systemctl enable blogsys

# サービス起動
sudo systemctl start blogsys

# 状態確認
sudo systemctl status blogsys

# ログ確認
sudo journalctl -u blogsys -f
```

---

## 記事管理 (CLI)

記事の作成・削除は `blogsys/test/main.py` から行います。

```bash
cd blogsys/test
python main.py
```

メニューが表示されます:

```
1. create drafts file  → 新規記事のドラフト作成
2. upload article      → 記事のアップロード（MySQL登録）
3. delete article      → 記事の削除
```

### 新規記事作成の手順

1. `python main.py` を実行し、`1` を選択
2. 記事タイトル、説明文、ファイル形式 (`html` or `md`) を入力
3. 公開設定 (`public` / `private`) を入力
4. `blogsys/drafts/` 以下にディレクトリとファイルが自動生成される
5. 生成されたHTMLファイルを編集して記事内容を作成
6. 管理画面 (`/NsanBlogEdit`) から公開設定を変更（未実装・今後対応予定）

### ドラフトのファイル命名規則

```
blogsys/drafts/<タイトル>_<YYYY_MM_DD_HH_MM>_html/
├── <タイトル>_<YYYY_MM_DD_HH_MM>.html
├── style.css
└── main.js
```

---

## セキュリティ注意事項

- `.env` ファイルは絶対にコミットしないでください（`.gitignore` で除外済み）
- `blogsys/test/SQLcreate.py` の認証情報は `.env` 経由で管理してください
- `DEV_PASSWORD` は十分に強いパスワードを設定してください
