# Nsan Portfolio & Blog System

ポートフォリオサイト + ブログ管理システムのリポジトリです。

---

## 目次

1. [システム構成](#システム構成)
2. [必要環境](#必要環境)
3. [セットアップ手順](#セットアップ手順)
4. [環境変数の設定](#環境変数の設定)
5. [Webサーバーの起動](#webサーバーの起動)
6. [記事管理CLIの使い方](#記事管理cliの使い方)
7. [サービス化（systemd）](#サービス化systemd)
8. [ディレクトリ構成](#ディレクトリ構成)
9. [データベース構造](#データベース構造)

---

## システム構成

| コンポーネント | 概要 |
|---|---|
| `index.html` | ポートフォリオのトップページ（静的HTML） |
| `Works/Works.html` | 作品紹介ページ |
| `blogsys/code/mainpage.py` | Flask製ブログWebサーバー |
| `blogsys/code/main.py` | 記事管理CLIメニュー |

ブログシステムは **Flask (Python)** で動作します。記事の作成・公開・削除はCLIで行い、閲覧はWebブラウザから行います。

---

## 必要環境

- Python 3.9 以上
- pip

---

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
cd blogsys
pip install -r requirements.txt
```

### 2. データベースの初期化

データベースファイル (`dev/blog_db.sqlite`) はすでにリポジトリに含まれています。  
新規作成が必要な場合は次のコマンドを実行してください。

```bash
cd blogsys/code
python SQLcreate.py
```

---

## 環境変数の設定

`blogsys/.env` ファイルを編集して設定します。

```env
# SQLiteデータベースのパス（blogsys/ からの相対パス）
DB_PATH=dev/blog_db.sqlite

# ブログ編集画面のログインパスワード
DEV_PASSWORD=your_password_here

# FlaskのSECRET_KEY（セッション保護用・任意の文字列を設定）
SECRET_KEY=your_secret_key_here

# デバッグモード（本番環境では False に変更）
DEBUG=False
```

> **注意**: `DEV_PASSWORD` と `SECRET_KEY` は必ず変更してください。デフォルト値のまま本番環境で使用しないでください。

---

## Webサーバーの起動

```bash
cd blogsys/code
python mainpage.py
```

起動後、ブラウザで以下のURLにアクセスします。

| URL | 説明 |
|---|---|
| `http://localhost:5000/` | ブログトップ（公開記事一覧） |
| `http://localhost:5000/posts/<ファイル名>.html` | 公開記事の閲覧 |
| `http://localhost:5000/NsanBlogEdit` | 記事編集画面（要パスワード） |

---

## 記事管理CLIの使い方

```bash
cd blogsys/code
python main.py
```

実行するとメニューが表示されます。

```
Please enter the number of task you want to perform:
1.create drafts file
2.upload article
3.delete article
Please select a task: and enter one of 1, 2, 3
```

### 1. ドラフト作成 (`1`)

新しい記事のドラフトを作成します。

1. 記事タイトルを入力
2. 説明文を入力
3. ファイル形式を選択（`html` または `md`）
4. 公開設定を選択（`public` / `private`）
5. タグをカンマ区切りで入力

ドラフトは `blogsys/drafts/<タイトル>_<タイムスタンプ>/` に保存され、データベースに登録されます。

### 2. 記事のアップロード・管理 (`2`)

登録済みの記事を一覧表示し、IDを指定して操作します。

| 操作番号 | 内容 |
|---|---|
| `1` | 公開設定の変更（`public` にするとMD→HTML変換・blog-postsへ移動が自動実行） |
| `2` | MDファイルを手動でHTMLに変換 |
| `3` | 記事内容の表示 |
| `4` | 記事の削除（DBから削除） |
| `0` | 終了 |

公開設定を `public` に変更すると、記事が `blogsys/static/blog-posts/` に配置され、Webサイトに表示されます。

### 3. 記事の削除・非公開化 (`3`)

記事IDを指定して操作します。

| 操作 | 内容 |
|---|---|
| `1` | 非公開化（`publicity='private'` に変更、ファイルは残る） |
| `2` | 完全削除（DBから削除 + ファイル削除） |

---

## サービス化（systemd）

Flaskアプリを常時起動するサービスとして登録する手順です。

### 1. サービスファイルの編集

`blogsys/blogsys.service` を開き、パスをサーバーの実際のパスに書き換えます。

```ini
WorkingDirectory=/path/to/portfolio/blogsys/code
ExecStart=/usr/bin/python3 mainpage.py
EnvironmentFile=/path/to/portfolio/blogsys/.env
User=www-data
Group=www-data
```

仮想環境（venv）を使用している場合は `ExecStart` を次のように変更します。

```ini
ExecStart=/path/to/portfolio/blogsys/venv/bin/python mainpage.py
```

### 2. サービスファイルをsystemdに登録

```bash
sudo cp blogsys/blogsys.service /etc/systemd/system/blogsys.service
sudo systemctl daemon-reload
sudo systemctl enable blogsys
sudo systemctl start blogsys
```

### 3. 動作確認

```bash
# 状態確認
sudo systemctl status blogsys

# ログ確認
sudo journalctl -u blogsys -f
```

### 4. サービスの停止・再起動

```bash
sudo systemctl stop blogsys
sudo systemctl restart blogsys
```

---

## ディレクトリ構成

```
portfolio/
├── index.html              # ポートフォリオ トップページ
├── style.css               # ポートフォリオ スタイル
├── script.js               # ポートフォリオ スクリプト
├── IndexIMG/               # トップページ画像
├── Works/                  # 作品紹介ページ
├── blogsys/                # ブログシステム本体
│   ├── .env                # 環境変数（要編集）
│   ├── requirements.txt    # Python依存パッケージ
│   ├── blogsys.service     # systemdサービス定義
│   ├── code/               # バックエンドPythonスクリプト
│   │   ├── main.py         # CLIメニュー（記事管理の入口）
│   │   ├── mainpage.py     # FlaskアプリWeb サーバー
│   │   ├── new_article.py  # ドラフト作成
│   │   ├── upload.py       # 記事公開・管理
│   │   ├── delete.py       # 記事削除・非公開化
│   │   └── SQLcreate.py    # DBテーブル初期化
│   ├── dev/
│   │   └── blog_db.sqlite  # SQLiteデータベース
│   ├── drafts/             # 下書き記事
│   ├── static/             # 静的ファイル（CSS/JS/画像）
│   │   └── blog-posts/     # 公開済み記事HTML
│   └── templates/          # Jinja2テンプレート
└── mainsystem/             # 旧バージョン（MySQL版、参考用）
```

---

## データベース構造

テーブル名: `URL_list_table`

| カラム名 | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | 自動採番 |
| `article_title` | VARCHAR(255) | 記事タイトル |
| `url` | VARCHAR(255) | ドラフトURLパス |
| `draft_url` | VARCHAR(255) | ドラフトファイルパス |
| `posts_url` | VARCHAR(255) | 公開記事ファイルパス |
| `description` | TEXT | 記事の説明 |
| `timestamp` | DATETIME | 作成日時（自動） |
| `tags` | VARCHAR(255) | タグ（カンマ区切り） |
| `publicity` | VARCHAR(16) | 公開設定: `public` / `private` / `draft` |
