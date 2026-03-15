#!/usr/bin/env python3
"""
画像データ取得プログラム
リストから画像表示データを取得し、DBに登録する
"""

import os
import sys
import django
import requests
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import instaloader

# Django settings
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from images.models import ImageData, IdolInfo
from openai import OpenAI

# 環境変数読み込み
load_dotenv()


class ImageFetcher:
    def __init__(self):
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.media_dir = Path(__file__).resolve().parent.parent / 'media' / 'images'
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def download_image(self, image_url: str, filename: str) -> Path:
        """画像をダウンロード"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            filepath = self.media_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
        except Exception as e:
            print(f"Error downloading image {image_url}: {e}")
            return None
    
    def extract_idol_info(self, sns_url: str) -> dict:
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
            print(f"Error extracting idol info: {e}")
            return {'group_name': '', 'idol_name': ''}
    
    def fetch_from_instagram(self, instagram_url: str):
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
            
            # URLからユーザー名を抽出
            username = instagram_url.rstrip('/').split('/')[-1]
            
            print(f"Fetching Instagram profile: {username}")
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
                    print(f"Saved: {image_filename}")
                    count += 1
                else:
                    print(f"Already exists: {image_filename}")
            
            print(f"Fetched {count} images from Instagram: {username}")
        
        except Exception as e:
            print(f"Error fetching from Instagram {instagram_url}: {e}")
    
    def fetch_from_twitter(self, twitter_url: str):
        """Twitter APIから画像を取得"""
        if not self.twitter_api_key:
            print("Twitter API key not configured. Skipping Twitter.")
            return
        
        try:
            # twitterapi.ioを使用した実装
            # 注: 実際の実装にはAPI仕様に基づいた詳細な処理が必要
            print(f"Twitter fetching not fully implemented for: {twitter_url}")
            print("Please implement based on twitterapi.io documentation")
            
            # アイドル情報を抽出
            idol_info = self.extract_idol_info(twitter_url)
            print(f"Extracted idol info: {idol_info}")
        
        except Exception as e:
            print(f"Error fetching from Twitter {twitter_url}: {e}")
    
    def process_sns_list(self, list_file: str):
        """SNSリストを処理"""
        if not os.path.exists(list_file):
            print(f"Error: File not found: {list_file}")
            sys.exit(1)
        
        with open(list_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        print(f"Processing {len(urls)} URLs from {list_file}")
        
        for url in urls:
            print(f"\nProcessing: {url}")
            
            if 'instagram.com' in url:
                self.fetch_from_instagram(url)
            elif 'twitter.com' in url or 'x.com' in url:
                self.fetch_from_twitter(url)
            else:
                print(f"Unknown SNS platform: {url}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_images.py <sns_list_file>")
        print("Example: python fetch_images.py sns_list.txt")
        sys.exit(1)
    
    list_file = sys.argv[1]
    fetcher = ImageFetcher()
    fetcher.process_sns_list(list_file)
