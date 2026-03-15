# バッチプログラム使用ガイド

このドキュメントでは、地下アイドル画像ギャラリーシステムのバッチプログラムの詳細な使用方法を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [バッチ1: SNSリスト自動作成](#バッチ1-snsリスト自動作成)
3. [バッチ2: 画像データ取得](#バッチ2-画像データ取得)
4. [バッチ3: 画像タグ付け](#バッチ3-画像タグ付け)
5. [ワークフロー例](#ワークフロー例)
6. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 環境変数の設定

バッチプログラムを実行する前に、`.env`ファイルに以下の環境変数を設定してください：

```bash
# 必須
OPENAI_API_KEY=your-openai-api-key-here

# Twitterから画像を取得する場合（オプション）
TWITTER_API_KEY=your-twitter-api-key-here
```

### パッケージのインストール

```bash
cd backend
pip install django djangorestframework pillow requests instaloader python-dotenv openai
```

## バッチ1: SNSリスト自動作成

### 概要

キーワードを指定すると、LLM（GPT-4o-mini）が関連する地下アイドルのSNSアカウントを自動的に特定し、リストを生成します。

### 使用方法

```bash
cd scripts
python generate_sns_list.py <キーワード> [出力ファイル名]
```

### パラメータ

- `<キーワード>`: 検索キーワード（必須）
  - 例: "東京 地下アイドル"、"大阪 ライブアイドル"
- `[出力ファイル名]`: 出力先ファイル名（オプション、デフォルト: `sns_list.txt`）

### 実行例

```bash
# 基本的な使用方法
python generate_sns_list.py "東京 地下アイドル"

# 出力ファイル名を指定
python generate_sns_list.py "大阪 ライブアイドル" osaka_idols.txt

# 特定のグループを検索
python generate_sns_list.py "BiSH メンバー"
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

### 注意事項

- LLMが生成するURLは必ずしも実在するとは限りません
- 生成されたリストは手動で確認・編集することを推奨します
- APIの使用料金が発生します（OpenAI API）

## バッチ2: 画像データ取得

### 概要

SNSリストファイルを読み込み、各URLから画像を取得してデータベースに保存します。

### 使用方法

```bash
cd scripts
python fetch_images.py <SNSリストファイル>
```

### パラメータ

- `<SNSリストファイル>`: バッチ1で生成したファイル、または手動で作成したSNSリスト

### 実行例

```bash
# 基本的な使用方法
python fetch_images.py sns_list.txt

# 別のリストファイルを使用
python fetch_images.py osaka_idols.txt
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

### Twitter取得について

現在のバージョンでは、Twitter APIの実装はスケルトンのみです。
twitterapi.io のドキュメントに基づいて実装を追加してください。

### 注意事項

- Instagramはレート制限があるため、大量のアカウントを処理する場合は時間がかかります
- APIキーが設定されていない場合、該当するSNSの処理はスキップされます
- ネットワークエラーや取得失敗は自動的にスキップされます

## バッチ3: 画像タグ付け

### 概要

データベース内のタグが付いていない画像を対象に、LLM（GPT-4o-mini vision）で画像を分析し、自動的にタグを付けます。

### 使用方法

```bash
cd scripts

# すべての未タグ画像を処理
python tag_images.py all

# 処理件数を制限
python tag_images.py all <件数>

# 特定の画像を再タグ付け
python tag_images.py <画像ID>
```

### 実行例

```bash
# すべての未タグ画像にタグ付け
python tag_images.py all

# 最初の10件のみ処理（テスト用）
python tag_images.py all 10

# 画像ID 42 を再タグ付け
python tag_images.py 42
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

### 注意事項

- 画像分析にはOpenAI APIを使用するため、料金が発生します
- 1画像あたりの処理時間は約5-10秒です
- 大量の画像を処理する場合は、処理件数を制限して実行することを推奨します
- ネットワークエラーやAPI制限エラーが発生した画像はスキップされます

## ワークフロー例

### シナリオ1: 新しい地下アイドルグループを追加

```bash
# 1. SNSリストを生成
cd scripts
python generate_sns_list.py "新規グループ名" new_group.txt

# 2. 生成されたリストを確認・編集（必要に応じて）
cat new_group.txt

# 3. 画像を取得
python fetch_images.py new_group.txt

# 4. 取得した画像にタグ付け（最初は少数でテスト）
python tag_images.py all 5

# 5. 問題なければ全件処理
python tag_images.py all
```

### シナリオ2: 既存の画像を再タグ付け

```bash
# 1. 管理画面で画像IDを確認
# http://localhost:8000/admin/images/imagedata/

# 2. 特定の画像を再タグ付け
cd scripts
python tag_images.py 15
python tag_images.py 16
python tag_images.py 17
```

### シナリオ3: 手動でSNSリストを作成

```bash
# 1. リストファイルを手動作成
cat > manual_list.txt << EOF
https://www.instagram.com/account1/
https://www.instagram.com/account2/
https://twitter.com/account3
EOF

# 2. 画像を取得
cd scripts
python fetch_images.py manual_list.txt

# 3. タグ付け
python tag_images.py all
```

## トラブルシューティング

### エラー: OPENAI_API_KEY environment variable is not set

**原因**: 環境変数が設定されていない

**解決方法**:
```bash
# .envファイルを確認
cat ../.env

# APIキーを設定
echo "OPENAI_API_KEY=sk-your-key-here" >> ../.env
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
python tag_images.py all 10

# バックグラウンドで実行
nohup python tag_images.py all &
```

## ベストプラクティス

1. **段階的な実行**: 最初は少数のデータでテストしてから本番実行
2. **リストの検証**: LLMが生成したSNSリストは必ず手動確認
3. **定期実行**: cronやタスクスケジューラで定期的に新しい画像を取得
4. **ログ監視**: エラーログを確認して問題を早期発見
5. **API使用量管理**: OpenAI APIの使用量を定期的にチェック

## さらなる改善案

- バッチ処理のスケジューリング（cron設定）
- エラー時の自動リトライ機能
- 処理進捗のダッシュボード
- タグの品質評価とフィードバック機能
- 複数のLLMモデルの比較

---

**更新日**: 2026-03-15
