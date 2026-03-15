# 地下アイドル画像ギャラリーシステム

地下アイドルのSNS画像を管理・閲覧するためのWebアプリケーションです。LLMを使用した自動タグ付け機能と、SNSからの画像自動取得機能を備えています。

## 🎯 目的

- 地下アイドルのSNS画像を一覧表示
- 画像から元のSNS投稿へのリンク
- LLMを使用した自動タグ付けによる検索機能

## 🏗️ アーキテクチャ

- **Backend**: Django REST Framework
- **Frontend**: React + TypeScript + Material-UI
- **AI/ML**: OpenAI GPT-4o-mini
- **Database**: SQLite (デフォルト)

## 📋 機能一覧

### Webアプリケーション

1. **トップページ（画像一覧）**
   - グリッドレイアウトで画像を敷き詰め表示
   - 画像情報ブロックの表示/非表示切替
   - ランダム表示機能
   - 画像クリックで元SNSへリンク

2. **画像詳細ページ**
   - 画像を大きく表示
   - アイドル情報（グループ名、名前）
   - タグ一覧
   - 同じタグを持つ関連画像表示

3. **タグ一覧ページ**
   - 全タグを画像数とともに一覧表示
   - タグクリックで該当画像を検索

### バッチプログラム

1. **SNSリスト自動作成** (`scripts/generate_sns_list.py`)
   - キーワードからLLMでアイドルのSNSアカウントを特定
   
2. **画像データ取得** (`scripts/fetch_images.py`)
   - Instagram: Instaloaderを使用
   - Twitter: twitterapi.io API（要実装）
   - LLMでアイドル情報を自動抽出

3. **画像タグ付け** (`scripts/tag_images.py`)
   - GPT-4o-miniで画像を分析
   - 20個以上のタグを自動生成
   - 必須タグ：人数、露出度（0-100点）

## 🚀 セットアップ

### 必要な環境

- Python 3.8+
- Node.js 14+
- OpenAI API キー

### インストール手順

#### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd webapp
```

#### 2. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install django djangorestframework django-cors-headers pillow requests instaloader python-dotenv openai

# 環境変数の設定
cp ../.env.example .env
# .envファイルを編集してAPIキーを設定

# データベースのマイグレーション
python manage.py migrate

# 管理者ユーザーの作成
python manage.py createsuperuser

# 開発サーバーの起動
python manage.py runserver
```

#### 3. フロントエンドのセットアップ

```bash
cd ../frontend

# 依存パッケージのインストール
npm install

# 環境変数の設定
cp .env.example .env
# .envファイルを編集（デフォルトで動作します）

# 開発サーバーの起動
npm start
```

## 📝 環境変数

### バックエンド (.env)

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# OpenAI API Settings
OPENAI_API_KEY=your-openai-api-key-here

# Twitter API Settings (twitterapi.io)
TWITTER_API_KEY=your-twitter-api-key-here
```

### フロントエンド (frontend/.env)

```bash
REACT_APP_API_URL=http://localhost:8000/api
```

## 🔧 バッチプログラムの使用方法

### 1. SNSリストの自動作成

```bash
cd scripts
python generate_sns_list.py "東京 地下アイドル" sns_list.txt
```

### 2. 画像データの取得

```bash
python fetch_images.py sns_list.txt
```

### 3. 画像へのタグ付け

```bash
# すべての未タグ画像にタグ付け
python tag_images.py all

# 最大10件のみ処理
python tag_images.py all 10

# 特定の画像を再タグ付け
python tag_images.py 42
```

## 📊 データベース設計

### ImageData（画像データ）
- `id`: 主キー
- `image`: 画像ファイルパス
- `source_url`: 取得元SNS URL
- `created_at`: 作成日時
- `updated_at`: 更新日時

### IdolInfo（アイドル情報）
- `id`: 主キー
- `image`: ImageDataへの外部キー（1対1）
- `group_name`: グループ名
- `idol_name`: アイドル名
- `created_at`: 作成日時
- `updated_at`: 更新日時

### ImageTag（画像タグ）
- `id`: 主キー
- `image`: ImageDataへの外部キー（多対1）
- `tag_name`: タグ名
- `created_at`: 作成日時

## 🎨 画面設計

### トップページ
- 左サイドバー：ナビゲーション（トップ、タグ一覧）
- ヘッダー：ランダム表示ボタン、情報表示切替スイッチ
- メインエリア：画像グリッド（余白なし敷き詰め）

### 画像詳細ページ
- 左側：大きく画像表示
- 右側：詳細情報（グループ名、アイドル名、タグ）
- 下部：同じタグの画像を小さく一覧

### タグ一覧ページ
- タグをチップ形式で表示
- 表示形式：「タグ名 (画像数)」

## 🔑 API エンドポイント

### 画像関連
- `GET /api/images/` - 画像一覧
- `GET /api/images/{id}/` - 画像詳細
- `GET /api/images/random/` - ランダム画像
- `GET /api/images/{id}/similar/` - 類似画像
- `GET /api/images/by_tag/?tag={tag_name}` - タグで検索

### タグ関連
- `GET /api/tags/` - タグ一覧（画像数付き）

## 🛠️ 技術スタック

### バックエンド
- Django 6.0
- Django REST Framework 3.16
- django-cors-headers
- Pillow
- OpenAI Python SDK
- Instaloader
- python-dotenv

### フロントエンド
- React 18
- TypeScript
- Material-UI (MUI)
- React Router
- Axios

## 📚 タグ付けの仕様

LLMによる自動タグ付けは以下のルールに従います：

### 必須タグ
1. **人数**：`人数:X` 形式で画像内の女の子の人数
2. **露出度**：`露出度:X` 形式で0-100点評価

### 一般タグ（20個以上）
- シーン：ライブ、ステージ、握手会、撮影会
- 服装：制服、私服、衣装、ドレス
- アクション：笑顔、ポーズ、ダンス、歌
- 場所：屋内、屋外、会場
- 雰囲気：カラフル、モノクロ、明るい、暗い
- 構図：グループショット、ソロショット、ツーショット

## 🔐 セキュリティ注意事項

- `.env`ファイルは絶対にGitにコミットしないでください
- 本番環境では`DEBUG=False`に設定してください
- `SECRET_KEY`は本番環境で必ず変更してください
- CORS設定を本番環境では適切に制限してください

## 📄 ライセンス

このプロジェクトは個人利用を目的としています。商用利用の際は別途ライセンスが必要です。

## 🤝 貢献

バグ報告や機能要望はIssueで受け付けています。

## 📞 サポート

質問や問題がある場合は、Issueを作成してください。

---

**開発者**: GenSpark AI Developer
**最終更新**: 2026-03-15
