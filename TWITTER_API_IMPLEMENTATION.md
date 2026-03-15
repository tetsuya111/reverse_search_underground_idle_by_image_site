# Twitter API (twitterapi.io) 実装ガイド

## 概要

fetch_imagesコマンドは、twitterapi.ioを使用してTwitter/Xから画像を自動取得できるようになりました。

## 実装内容

### API仕様

- **エンドポイント**: `GET https://api.twitterapi.io/twitter/user/tweets`
- **認証方式**: `x-api-key`ヘッダー
- **レスポンス形式**: JSON

### 主な機能

1. **ユーザー名からツイート取得**
   - 最大20件の最新ツイートを取得
   - ページネーション対応（将来の拡張用）

2. **画像の自動抽出**
   - ツイート内のメディア（画像）のみをフィルタリング
   - 動画は自動的に除外
   - 高解像度版の画像を取得（`:orig`サフィックス付き）

3. **データベース保存**
   - 画像ファイルを`media/images/`に保存
   - メタデータ（ツイートURL、画像パス）をDBに保存
   - 重複チェックで既存画像はスキップ

4. **アイドル情報の自動抽出**
   - LLM（GPT-4o-mini）を使用してグループ名・アイドル名を特定
   - TwitterプロフィールURLから情報を抽出

## セットアップ

### 1. APIキーの取得

1. [twitterapi.io](https://twitterapi.io/)にアクセス
2. アカウントを作成（無料トライアルあり）
3. ダッシュボードでAPIキーを確認

### 2. 環境変数の設定

`backend/.env`ファイルに以下を追加：

```bash
# Twitter API Settings (twitterapi.io)
TWITTER_API_KEY=your_api_key_here
```

### 3. 使用方法

```bash
cd backend

# SNSリストファイルを用意
cat > twitter_list.txt << EOF
https://twitter.com/idol_account1
https://x.com/idol_account2
https://twitter.com/idol_group_official
EOF

# 画像を取得
python manage.py fetch_images twitter_list.txt
```

## 実装詳細

### コード構造

```python
def fetch_from_twitter(self, twitter_url):
    # 1. URLからユーザー名を抽出
    username = extract_username(twitter_url)
    
    # 2. twitterapi.io APIを呼び出し
    headers = {'x-api-key': self.twitter_api_key}
    params = {'userName': username, 'count': 20}
    response = requests.get(api_url, headers=headers, params=params)
    
    # 3. レスポンスから画像を抽出
    tweets = response.json()['tweets']
    for tweet in tweets:
        media_list = tweet.get('media', [])
        for media in media_list:
            if media['type'] == 'photo':
                # 4. 画像をダウンロード
                download_image(media['media_url_https'] + ':orig')
                
                # 5. DBに保存
                save_to_database(image, tweet_url, idol_info)
```

### エラーハンドリング

- **APIキー未設定**: 警告メッセージを表示してスキップ
- **ネットワークエラー**: エラーログを出力して次のURLへ
- **APIエラー**: ステータスメッセージを表示
- **画像ダウンロード失敗**: ログを出力して次の画像へ

### メディア抽出ロジック

```python
# ツイートオブジェクトからメディアを取得
media_list = tweet.get('media', [])

# entitiesからもメディアを取得（フォールバック）
if not media_list:
    entities = tweet.get('entities', {})
    media_list = entities.get('media', [])

# 画像のみをフィルタリング
for media in media_list:
    if media.get('type') in ['photo', 'image']:
        # 画像URLを取得
        image_url = media.get('media_url_https', '') + ':orig'
```

## 料金体系

### twitterapi.io 料金

- **$0.15 per 1,000 tweets**
- **最小料金**: $0.00015 per request
- **学生・研究機関向け割引**あり

### 使用例の料金計算

```
例: 10アカウント × 20ツイート/アカウント = 200ツイート
料金: 200 / 1,000 × $0.15 = $0.03
```

## 出力例

```bash
$ python manage.py fetch_images twitter_list.txt

Processing 3 URLs from twitter_list.txt

Processing: https://twitter.com/idol_account1
Fetching Twitter profile: @idol_account1
Found 20 tweets
Saved: tw_idol_account1_1234567890_1.jpg
Saved: tw_idol_account1_1234567891_2.jpg
Already exists: tw_idol_account1_1234567892_3.jpg
Fetched 15 images from Twitter: @idol_account1

Processing: https://x.com/idol_account2
Fetching Twitter profile: @idol_account2
Found 18 tweets
Saved: tw_idol_account2_9876543210_1.jpg
Fetched 8 images from Twitter: @idol_account2
```

## トラブルシューティング

### エラー: "Twitter API key not configured"

**原因**: `TWITTER_API_KEY`が`.env`ファイルに設定されていない

**解決方法**:
```bash
echo "TWITTER_API_KEY=your_key_here" >> backend/.env
```

### エラー: "API Error: Authentication failed"

**原因**: APIキーが無効、または期限切れ

**解決方法**:
1. [twitterapi.io dashboard](https://twitterapi.io/dashboard)で新しいキーを生成
2. `.env`ファイルを更新

### エラー: "Error downloading image"

**原因**: 画像URLが無効、またはネットワークエラー

**解決方法**:
- インターネット接続を確認
- しばらく待ってから再実行
- 該当する画像はスキップされ、処理は継続されます

### 画像が取得されない

**考えられる原因**:
1. ツイートに画像が含まれていない
2. 非公開アカウント（twitterapi.ioは公開データのみアクセス可能）
3. 削除されたツイート

**確認方法**:
```bash
# ログを詳細に確認
python manage.py fetch_images twitter_list.txt -v 2
```

## ベストプラクティス

1. **APIキーの管理**
   - `.env`ファイルをGitにコミットしない（`.gitignore`に含まれています）
   - 本番環境では環境変数で管理

2. **レート制限への配慮**
   - 大量のアカウントを処理する場合は小分けにして実行
   - エラーが発生した場合は少し待ってから再実行

3. **コスト管理**
   - テスト時は少数のアカウントで試す
   - [twitterapi.io dashboard](https://twitterapi.io/dashboard)で使用量を定期的に確認

4. **画像の品質**
   - `:orig`サフィックスで高解像度版を取得
   - 必要に応じてコード内で画像サイズを調整可能

## 今後の拡張案

- [ ] ページネーション対応（20件以上のツイート取得）
- [ ] 特定期間のツイートのみ取得
- [ ] リツイートの除外オプション
- [ ] 並列処理による高速化
- [ ] リトライロジックの追加
- [ ] 進捗バーの表示

---

**最終更新**: 2026-03-15
