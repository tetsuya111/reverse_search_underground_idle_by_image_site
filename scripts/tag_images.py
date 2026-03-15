#!/usr/bin/env python3
"""
画像タグ付けプログラム
DBからタグが付いていない画像データを抽出し、LLMを用いてタグを付ける
"""

import os
import sys
import django
import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Django settings
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from images.models import ImageData, ImageTag

# 環境変数読み込み
load_dotenv()


class ImageTagger:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            print("Error: OPENAI_API_KEY environment variable is not set")
            sys.exit(1)
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.media_root = Path(__file__).resolve().parent.parent / 'media'
    
    def encode_image(self, image_path: Path) -> str:
        """画像をBase64エンコード"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def generate_tags(self, image_path: Path) -> list:
        """LLMを使用して画像にタグを付ける"""
        try:
            # 画像をBase64エンコード
            base64_image = self.encode_image(image_path)
            
            prompt = """
この画像を分析して、アイドルを検索するために使用しやすいタグを20個以上生成してください。

必須タグ:
1. 人数:{人数} - 画像内の女の子の人数
2. 露出度:{0-100の数値} - 画像の露出度を100点満点で判定

その他のタグは一般名詞を用いてください。例:
- ライブ、ステージ、握手会、撮影会
- 制服、私服、衣装、ドレス
- 笑顔、ポーズ、ダンス、歌
- 屋内、屋外、会場
- カラフル、モノクロ、明るい、暗い
- グループショット、ソロショット、ツーショット
など

JSON形式で以下のように出力してください:
{
    "tags": ["人数:2", "露出度:30", "ライブ", "ステージ", "衣装", ...]
}

タグは日本語で、20個以上記載してください。
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            tags = result.get('tags', [])
            
            return tags
        
        except Exception as e:
            print(f"Error generating tags for {image_path}: {e}")
            return []
    
    def tag_untagged_images(self, limit: int = None):
        """タグが付いていない画像にタグを付ける"""
        # タグが付いていない画像を取得
        untagged_images = ImageData.objects.filter(tags__isnull=True).distinct()
        
        if limit:
            untagged_images = untagged_images[:limit]
        
        total = untagged_images.count()
        print(f"Found {total} untagged images")
        
        for idx, image_data in enumerate(untagged_images, 1):
            print(f"\nProcessing [{idx}/{total}]: Image ID {image_data.id}")
            
            # 画像パスを取得
            image_path = self.media_root / image_data.image.name
            
            if not image_path.exists():
                print(f"  Image file not found: {image_path}")
                continue
            
            # タグを生成
            tags = self.generate_tags(image_path)
            
            if not tags:
                print("  Failed to generate tags")
                continue
            
            # タグをDBに保存
            for tag_name in tags:
                ImageTag.objects.create(
                    image=image_data,
                    tag_name=tag_name
                )
            
            print(f"  Added {len(tags)} tags: {', '.join(tags[:5])}...")
        
        print(f"\nCompleted tagging {total} images")
    
    def retag_image(self, image_id: int):
        """特定の画像のタグを再生成"""
        try:
            image_data = ImageData.objects.get(id=image_id)
        except ImageData.DoesNotExist:
            print(f"Error: Image with ID {image_id} not found")
            return
        
        # 既存のタグを削除
        ImageTag.objects.filter(image=image_data).delete()
        
        # 画像パスを取得
        image_path = self.media_root / image_data.image.name
        
        if not image_path.exists():
            print(f"Error: Image file not found: {image_path}")
            return
        
        # タグを生成
        tags = self.generate_tags(image_path)
        
        if not tags:
            print("Failed to generate tags")
            return
        
        # タグをDBに保存
        for tag_name in tags:
            ImageTag.objects.create(
                image=image_data,
                tag_name=tag_name
            )
        
        print(f"Added {len(tags)} tags to image {image_id}")
        print(f"Tags: {', '.join(tags)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tag_images.py all [limit]  - Tag all untagged images")
        print("  python tag_images.py <image_id>   - Retag specific image")
        print("\nExamples:")
        print("  python tag_images.py all")
        print("  python tag_images.py all 10")
        print("  python tag_images.py 42")
        sys.exit(1)
    
    tagger = ImageTagger()
    
    if sys.argv[1] == 'all':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        tagger.tag_untagged_images(limit)
    else:
        image_id = int(sys.argv[1])
        tagger.retag_image(image_id)
