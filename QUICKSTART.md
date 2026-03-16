# クイックスタートガイド

地下アイドル画像ギャラリーシステムを素早く起動するためのガイドです。

## 📋 前提条件

- Python 3.8+ インストール済み
- Node.js 14+ インストール済み
- OpenAI API キー取得済み

## 🚀 5分で起動

### ステップ1: 環境変数の設定

```bash
# プロジェクトルートで
cp .env.example backend/.env

# .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=あなたのAPIキー
```

### ステップ2: バックエンド起動

```bash
cd backend

# 依存パッケージのインストール
pip install django djangorestframework django-cors-headers pillow requests instaloader python-dotenv openai

# データベース初期化（既に実行済み）
python manage.py migrate

# サーバー起動
python manage.py runserver
```

バックエンドが `http://localhost:8000` で起動します。

### ステップ3: フロントエンド起動（新しいターミナル）

```bash
cd frontend

# 依存パッケージのインストール（既に実行済み）
# npm install

# 開発サーバー起動
npm start
```

フロントエンドが `http://localhost:3000` で起動します。

## 🎨 初回セットアップ

### 管理者アカウント作成

```bash
cd backend
python manage.py createsuperuser
```

管理画面: `http://localhost:8000/admin/`

### テストデータ作成（オプション）

```bash
cd backend

# 1. SNSリストを生成
python manage.py generate_sns_list "地下アイドル" --output test_list.txt

# 2. 画像を取得（少数でテスト）
python manage.py fetch_images test_list.txt

# 3. タグを付ける（最初の5件のみ）
python manage.py tag_images --all --limit 5
```

## 📱 アプリケーションの使い方

### トップページ
- `http://localhost:3000/` にアクセス
- 「画像情報表示」スイッチでアイドル情報の表示/非表示を切替
- 「ランダム表示」ボタンでランダムに画像を表示
- 画像クリックで元のSNS投稿へジャンプ

### タグ一覧
- 左サイドバーの「タグ一覧」をクリック
- タグをクリックすると、そのタグを持つ画像一覧を表示

### 画像詳細
- 画像カード下部の矢印ボタンで詳細ページへ
- 大きな画像とアイドル情報を表示
- 同じタグを持つ関連画像も表示

## 🔧 Djangoカスタムコマンド

すべてのバッチ処理は、Djangoのカスタム管理コマンドとして実装されています。

### SNSリスト作成

```bash
cd backend
python manage.py generate_sns_list "東京 地下アイドル"
```

### 画像取得

```bash
cd backend
python manage.py fetch_images sns_list.txt
```

### タグ付け

```bash
cd backend
# すべての未タグ画像にタグ付け
python manage.py tag_images --all

# 最大10件のみ処理
python manage.py tag_images --all --limit 10
```

詳細は `COMMANDS_GUIDE.md` を参照してください。

## 🔧 トラブルシューティング

### ポートがすでに使用されている

**バックエンド**:
```bash
python manage.py runserver 8001
```

**フロントエンド**:
```bash
PORT=3001 npm start
```

### CORS エラー

`backend/config/settings.py` の `CORS_ALLOW_ALL_ORIGINS` が `True` になっていることを確認。

### 画像が表示されない

1. バックエンドが起動していることを確認
2. `media/images/` ディレクトリが存在することを確認
3. ブラウザのコンソールでエラーを確認

### API キーエラー

`.env` ファイルが `backend/` ディレクトリにあることを確認し、APIキーが正しく設定されているか確認。

## 📚 より詳しい情報

- **詳細なセットアップ**: `README.md`
- **カスタムコマンドの使い方**: `COMMANDS_GUIDE.md`
- **API仕様**: `http://localhost:8000/api/` (バックエンド起動時)

## 🎯 次のステップ

1. 実際のアイドルグループのSNSリストを作成
2. カスタムコマンドで画像を大量取得
3. タグ付けを実行
4. Webアプリで閲覧・検索

楽しんでください！ 🎉
