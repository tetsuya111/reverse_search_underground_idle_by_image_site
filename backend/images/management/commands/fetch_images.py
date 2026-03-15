"""
Djangoカスタムコマンド: 画像データ取得
リストから画像表示データを取得し、DBに登録する
"""

import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dotenv import load_dotenv
import instaloader
from openai import OpenAI
from images.models import ImageData, IdolInfo

# 環境変数読み込み
load_dotenv()


class Command(BaseCommand):
    help = 'SNSリストから画像を取得してDBに保存'

    def add_arguments(self, parser):
        parser.add_argument(
            'sns_list_file',
            type=str,
            help='SNSリストファイルのパス'
        )

    def handle(self, *args, **options):
        list_file = options['sns_list_file']
        
        if not os.path.exists(list_file):
            raise CommandError(f'File not found: {list_file}')
        
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        self.media_dir = Path(settings.MEDIA_ROOT) / 'images'
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        with open(list_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        self.stdout.write(f"Processing {len(urls)} URLs from {list_file}")
        
        for url in urls:
            self.stdout.write(f"\nProcessing: {url}")
            
            if 'instagram.com' in url:
                self.fetch_from_instagram(url)
            elif 'twitter.com' in url or 'x.com' in url:
                self.fetch_from_twitter(url)
            else:
                self.stdout.write(self.style.WARNING(f"Unknown SNS platform: {url}"))
    
    def download_image(self, image_url, filename):
        """画像をダウンロード"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            filepath = self.media_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading image {image_url}: {e}"))
            return None
    
    def extract_idol_info(self, sns_url):
        """LLMを使用してSNS URLからアイドル情報を抽出"""
        if not self.openai_api_key:
            return {'group_name': '', 'idol_name': ''}
        
        try:
            prompt = f"""
以下のSNS URLから、アイドルグループ名とアイドル名を特定してください。

URL: {sns_url}

以下のJSON形式で出力してください:
{{
    "group_name": "グループ名",
    "idol_name": "アイドル名"
}}

情報が不明な場合は空文字を返してください。
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはアイドル情報を抽出する専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            info = json.loads(response.choices[0].message.content)
            return info
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error extracting idol info: {e}"))
            return {'group_name': '', 'idol_name': ''}
    
    def fetch_from_instagram(self, instagram_url):
        """Instagramから画像を取得"""
        try:
            L = instaloader.Instaloader(
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            
            # 環境変数からログイン情報を取得してログイン
            instagram_username = os.getenv('INSTAGRAM_USERNAME')
            instagram_password = os.getenv('INSTAGRAM_PASSWORD')
            
            if instagram_username and instagram_password:
                try:
                    self.stdout.write(f"Logging in to Instagram as {instagram_username}")
                    L.login(instagram_username, instagram_password)
                    self.stdout.write(self.style.SUCCESS("Instagram login successful"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Instagram login failed: {e}"))
                    self.stdout.write("Continuing without login (public posts only)")
            
            # URLからユーザー名を抽出
            username = instagram_url.rstrip('/').split('/')[-1]
            
            self.stdout.write(f"Fetching Instagram profile: {username}")
            profile = instaloader.Profile.from_username(L.context, username)
            
            # アイドル情報を抽出
            idol_info = self.extract_idol_info(instagram_url)
            
            # 最新の投稿から画像を取得（最大20件）
            count = 0
            for post in profile.get_posts():
                if count >= 20:
                    break
                
                if post.is_video:
                    continue
                
                # 画像をダウンロード
                image_filename = f"ig_{username}_{post.shortcode}.jpg"
                image_path = self.download_image(post.url, image_filename)
                
                if not image_path:
                    continue
                
                # DBに保存
                relative_path = f"images/{image_filename}"
                image_data, created = ImageData.objects.get_or_create(
                    source_url=f"https://www.instagram.com/p/{post.shortcode}/",
                    defaults={'image': relative_path}
                )
                
                if created:
                    # アイドル情報を保存
                    IdolInfo.objects.create(
                        image=image_data,
                        group_name=idol_info.get('group_name', ''),
                        idol_name=idol_info.get('idol_name', '')
                    )
                    self.stdout.write(self.style.SUCCESS(f"Saved: {image_filename}"))
                    count += 1
                else:
                    self.stdout.write(f"Already exists: {image_filename}")
            
            self.stdout.write(self.style.SUCCESS(f"Fetched {count} images from Instagram: {username}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching from Instagram {instagram_url}: {e}"))
    
    def fetch_from_twitter(self, twitter_url):
        """twitterapi.ioを使用してTwitterから画像を取得"""
        if not self.twitter_api_key:
            self.stdout.write(self.style.WARNING("Twitter API key not configured. Skipping Twitter."))
            return
        
        try:
            # URLからユーザー名を抽出
            # 例: https://twitter.com/username または https://x.com/username
            parts = twitter_url.rstrip('/').split('/')
            username = parts[-1]
            
            self.stdout.write(f"Fetching Twitter profile: @{username}")
            
            # twitterapi.io APIを使用してツイートを取得
            api_url = 'https://api.twitterapi.io/twitter/user/tweets'
            headers = {
                'x-api-key': self.twitter_api_key
            }
            params = {
                'userName': username,
                'count': 20  # 最大20件取得
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'success':
                self.stdout.write(self.style.ERROR(f"API Error: {data.get('message', 'Unknown error')}"))
                return
            
            tweets = data.get('tweets', [])
            self.stdout.write(f"Found {len(tweets)} tweets")
            
            # アイドル情報を抽出（1回のみ）
            idol_info = self.extract_idol_info(twitter_url)
            
            # 画像を含むツイートから画像を抽出
            count = 0
            for tweet in tweets:
                # メディアが含まれているか確認
                media_list = tweet.get('media', [])
                
                # entitiesからもメディアを取得を試みる
                entities = tweet.get('entities', {})
                if not media_list and 'media' in entities:
                    media_list = entities.get('media', [])
                
                if not media_list:
                    continue
                
                # 各メディア（画像）をダウンロード
                for media in media_list:
                    # 画像のみを処理（動画は除外）
                    media_type = media.get('type', '')
                    if media_type not in ['photo', 'image']:
                        continue
                    
                    # 画像URLを取得
                    # media_url_https または media_url を使用
                    image_url = media.get('media_url_https') or media.get('media_url') or media.get('url')
                    
                    if not image_url:
                        continue
                    
                    # 高解像度版のURLを取得（:orig を追加）
                    if not image_url.endswith(':orig'):
                        image_url = f"{image_url}:orig"
                    
                    tweet_id = tweet.get('id', '')
                    image_filename = f"tw_{username}_{tweet_id}_{media.get('id', count)}.jpg"
                    
                    # 画像をダウンロード
                    image_path = self.download_image(image_url, image_filename)
                    
                    if not image_path:
                        continue
                    
                    # DBに保存
                    relative_path = f"images/{image_filename}"
                    tweet_url = tweet.get('url', f"https://twitter.com/{username}/status/{tweet_id}")
                    
                    image_data, created = ImageData.objects.get_or_create(
                        source_url=tweet_url,
                        defaults={'image': relative_path}
                    )
                    
                    if created:
                        # アイドル情報を保存
                        IdolInfo.objects.create(
                            image=image_data,
                            group_name=idol_info.get('group_name', ''),
                            idol_name=idol_info.get('idol_name', '')
                        )
                        self.stdout.write(self.style.SUCCESS(f"Saved: {image_filename}"))
                        count += 1
                    else:
                        self.stdout.write(f"Already exists: {image_filename}")
            
            self.stdout.write(self.style.SUCCESS(f"Fetched {count} images from Twitter: @{username}"))
        
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API request error for {twitter_url}: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching from Twitter {twitter_url}: {e}"))
