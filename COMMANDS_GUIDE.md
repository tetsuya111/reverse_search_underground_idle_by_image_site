# Djangoカスタムコマンド使用ガイド

このドキュメントでは、地下アイドル画像ギャラリーシステムのDjangoカスタム管理コマンドの詳細な使用方法を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [コマンド1: SNSリスト自動作成](#コマンド1-snsリスト自動作成)
3. [コマンド2: 画像データ取得](#コマンド2-画像データ取得)
4. [コマンド3: 画像タグ付け](#コマンド3-画像タグ付け)
5. [ワークフロー例](#ワークフロー例)
6. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 環境変数の設定

コマンドを実行する前に、`backend/.env`ファイルに以下の環境変数を設定してください：

```bash
# 必須
OPENAI_API_KEY=your-openai-api-key-here

# Twitterから画像を取得する場合（オプション）
TWITTER_API_KEY=your-twitter-api-key-here
```

### 作業ディレクトリ

すべてのコマンドは`backend/`ディレクトリで実行してください：

```bash
cd /path/to/webapp/backend
```

## コマンド1: SNSリスト自動作成

### 概要

キーワードを指定すると、LLM（GPT-4o-mini）が関連する地下アイドルのSNSアカウントを自動的に特定し、リストを生成します。

### 使用方法

```bash
python manage.py generate_sns_list <キーワード> [オプション]
```

### 引数・オプション

- `<キーワード>`: 検索キーワード（必須）
  - 例: "東京 地下アイドル"、"大阪 ライブアイドル"
- `--output <ファイル名>`: 出力先ファイル名（オプション、デフォルト: `sns_list.txt`）

### 実行例

```bash
# 基本的な使用方法
python manage.py generate_sns_list "東京 地下アイドル"

# 出力ファイル名を指定
python manage.py generate_sns_list "大阪 ライブアイドル" --output osaka_idols.txt

# 特定のグループを検索
python manage.py generate_sns_list "BiSH メンバー"
```

### 出力形式

生成されるファイルには、各行に1つのSNS URLが記載されます：

```
https://twitter.com/idol_group_official
https://www.instagram.com/idol_group_official/
https://twitter.com/member1_account
https://www.instagram.com/member1_account/
https://twitter.com/member2_account
```

### ヘルプの表示

```bash
python manage.py generate_sns_list --help
```

### 注意事項

- LLMが生成するURLは必ずしも実在するとは限りません
- 生成されたリストは手動で確認・編集することを推奨します
- APIの使用料金が発生します（OpenAI API）

## コマンド2: 画像データ取得

### 概要

SNSリストファイルを読み込み、各URLから画像を取得してデータベースに保存します。

### 使用方法

```bash
python manage.py fetch_images <SNSリストファイル>
```

### 引数

- `<SNSリストファイル>`: コマンド1で生成したファイル、または手動で作成したSNSリスト（必須）

### 実行例

```bash
# 基本的な使用方法
python manage.py fetch_images sns_list.txt

# 別のリストファイルを使用
python manage.py fetch_images osaka_idols.txt
```

### 処理内容

1. **SNSリストの読み込み**: ファイルから1行ずつURLを読み込み
2. **プラットフォーム判定**: Instagram/Twitterを自動判定
3. **画像取得**:
   - **Instagram**: Instaloaderで最新20件の投稿から画像を取得
   - **Twitter**: twitterapi.io を使用（要実装）
4. **アイドル情報抽出**: LLMでグループ名とアイドル名を特定
5. **データベース保存**: 画像とメタデータをDBに保存

### Instagram取得の詳細

- 公開アカウントのみ対応
- 動画は除外、画像のみ取得
- 1アカウントあたり最大20件の投稿を取得
- 重複画像はスキップ

### Twitter取得の詳細

**twitterapi.io**を使用して実装されています。

- 認証: `x-api-key`ヘッダーでAPIキーを送信
- エンドポイント: `GET https://api.twitterapi.io/twitter/user/tweets`
- パラメータ:
  - `userName`: Twitterユーザー名
  - `count`: 取得するツイート数（最大20件）
- 画像のみを抽出（動画は除外）
- 高解像度版の画像を取得（`:orig`サフィックス付き）
- 重複画像はスキップ

#### twitterapi.io APIキーの取得方法

1. [twitterapi.io](https://twitterapi.io/)にアクセス
2. アカウントを作成してログイン
3. ダッシュボードでAPIキーを確認
4. `.env`ファイルに設定:
   ```bash
   TWITTER_API_KEY=your_api_key_here
   ```

#### 料金について

- **Instagram**: 無料（Instaloaderを使用）
- **Twitter (twitterapi.io)**:
  - $0.15 per 1,000 tweets
  - 最小料金: $0.00015 per request
  - 学生・研究機関向けの割引あり

### ヘルプの表示

```bash
python manage.py fetch_images --help
```

### 注意事項

- Instagramはレート制限があるため、大量のアカウントを処理する場合は時間がかかります
- APIキーが設定されていない場合、該当するSNSの処理はスキップされます
- ネットワークエラーや取得失敗は自動的にスキップされます

## コマンド3: 画像タグ付け

### 概要

データベース内のタグが付いていない画像を対象に、LLM（GPT-4o-mini vision）で画像を分析し、自動的にタグを付けます。

### 使用方法

```bash
# すべての未タグ画像を処理
python manage.py tag_images --all

# 処理件数を制限
python manage.py tag_images --all --limit <件数>

# 特定の画像を再タグ付け
python manage.py tag_images --image-id <画像ID>
```

### オプション

- `--all`: すべての未タグ画像を処理
- `--limit <件数>`: 処理する画像の最大数（`--all`と併用）
- `--image-id <画像ID>`: 特定の画像IDを再タグ付け

### 実行例

```bash
# すべての未タグ画像にタグ付け
python manage.py tag_images --all

# 最初の10件のみ処理（テスト用）
python manage.py tag_images --all --limit 10

# 画像ID 42 を再タグ付け
python manage.py tag_images --image-id 42
```

### タグ付けルール

#### 必須タグ（2個）

1. **人数**: `人数:X` 形式
   - 画像内の女の子の人数を数える
   - 例: `人数:1`, `人数:3`, `人数:5`

2. **露出度**: `露出度:X` 形式
   - 0-100点で画像の露出度を評価
   - 例: `露出度:30`, `露出度:65`

#### 一般タグ（18個以上）

アイドルを検索しやすい一般名詞を使用：

- **シーン系**: ライブ、ステージ、握手会、撮影会、リハーサル
- **服装系**: 制服、私服、衣装、ドレス、カジュアル、フォーマル
- **アクション系**: 笑顔、ポーズ、ダンス、歌、MC
- **場所系**: 屋内、屋外、会場、スタジオ、路上
- **雰囲気系**: カラフル、モノクロ、明るい、暗い、華やか
- **構図系**: グループショット、ソロショット、ツーショット、クローズアップ、全身

### タグ付けの例

```
人数:3
露出度:40
ライブ
ステージ
衣装
グループショット
笑顔
屋内
カラフル
ダンス
華やか
アイドル
パフォーマンス
照明
マイク
フォーメーション
若い
エネルギッシュ
プロフェッショナル
...（合計20個以上）
```

### ヘルプの表示

```bash
python manage.py tag_images --help
```

### 注意事項

- 画像分析にはOpenAI APIを使用するため、料金が発生します
- 1画像あたりの処理時間は約5-10秒です
- 大量の画像を処理する場合は、処理件数を制限して実行することを推奨します
- ネットワークエラーやAPI制限エラーが発生した画像はスキップされます

## ワークフロー例

### シナリオ1: 新しい地下アイドルグループを追加

```bash
cd backend

# 1. SNSリストを生成
python manage.py generate_sns_list "新規グループ名" --output new_group.txt

# 2. 生成されたリストを確認・編集（必要に応じて）
cat new_group.txt

# 3. 画像を取得
python manage.py fetch_images new_group.txt

# 4. 取得した画像にタグ付け（最初は少数でテスト）
python manage.py tag_images --all --limit 5

# 5. 問題なければ全件処理
python manage.py tag_images --all
```

### シナリオ2: 既存の画像を再タグ付け

```bash
cd backend

# 1. 管理画面で画像IDを確認
# http://localhost:8000/admin/images/imagedata/

# 2. 特定の画像を再タグ付け
python manage.py tag_images --image-id 15
python manage.py tag_images --image-id 16
python manage.py tag_images --image-id 17
```

### シナリオ3: 手動でSNSリストを作成

```bash
cd backend

# 1. リストファイルを手動作成
cat > manual_list.txt << EOF
https://www.instagram.com/account1/
https://www.instagram.com/account2/
https://twitter.com/account3
EOF

# 2. 画像を取得
python manage.py fetch_images manual_list.txt

# 3. タグ付け
python manage.py tag_images --all
```

## トラブルシューティング

### エラー: OPENAI_API_KEY environment variable is not set

**原因**: 環境変数が設定されていない

**解決方法**:
```bash
# .envファイルを確認
cat .env

# APIキーを設定
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### エラー: Image file not found

**原因**: 画像ファイルが存在しない、またはパスが正しくない

**解決方法**:
```bash
# メディアディレクトリを確認
ls -la ../media/images/

# データベースと実ファイルの整合性を確認
```

### Instagram: Login required

**原因**: 非公開アカウントまたはInstagramのレート制限

**解決方法**:
- 公開アカウントのみを対象にする
- しばらく待ってから再実行
- Instaloader の設定を調整

### Twitter API エラー

**原因**: Twitter API実装が未完成、またはAPIキーが無効

**解決方法**:
- `TWITTER_API_KEY`が正しく設定されているか確認
- twitterapi.io のドキュメントを参照して実装を完成させる

### タグ付けが遅い

**原因**: OpenAI APIの応答時間

**解決方法**:
```bash
# 少数ずつ処理
python manage.py tag_images --all --limit 10

# バックグラウンドで実行
nohup python manage.py tag_images --all &
```

## ベストプラクティス

1. **段階的な実行**: 最初は少数のデータでテストしてから本番実行
2. **リストの検証**: LLMが生成したSNSリストは必ず手動確認
3. **定期実行**: cronやタスクスケジューラで定期的に新しい画像を取得
4. **ログ監視**: コマンド出力を確認して問題を早期発見
5. **API使用量管理**: OpenAI APIの使用量を定期的にチェック

## さらなる改善案

- カスタムコマンドのスケジューリング（Celery統合）
- エラー時の自動リトライ機能
- 処理進捗のダッシュボード
- タグの品質評価とフィードバック機能
- 複数のLLMモデルの比較

---

**更新日**: 2026-03-15
