"""
Djangoカスタムコマンド: 画像タグ付け
DBからタグが付いていない画像データを抽出し、LLMを用いてタグを付ける
"""

import os
import base64
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI
from images.models import ImageData, ImageTag

# 環境変数読み込み
load_dotenv()


class Command(BaseCommand):
    help = 'DBからタグが付いていない画像にLLMを使用してタグを付ける'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='すべての未タグ画像を処理'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='処理する画像の最大数'
        )
        parser.add_argument(
            '--image-id',
            type=int,
            help='特定の画像IDを再タグ付け'
        )

    def handle(self, *args, **options):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise CommandError('OPENAI_API_KEY environment variable is not set')
        
        self.client = OpenAI(api_key=api_key)
        self.media_root = Path(settings.MEDIA_ROOT)
        
        if options['image_id']:
            self.retag_image(options['image_id'])
        elif options['all']:
            self.tag_untagged_images(options.get('limit'))
        else:
            raise CommandError('Please specify --all or --image-id')
    
    def encode_image(self, image_path):
        """画像をBase64エンコード"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def generate_tags(self, image_path):
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
            self.stdout.write(self.style.ERROR(f"Error generating tags for {image_path}: {e}"))
            return []
    
    def tag_untagged_images(self, limit=None):
        """タグが付いていない画像にタグを付ける"""
        # タグが付いていない画像を取得
        untagged_images = ImageData.objects.filter(tags__isnull=True).distinct()
        
        if limit:
            untagged_images = untagged_images[:limit]
        
        total = untagged_images.count()
        self.stdout.write(f"Found {total} untagged images")
        
        for idx, image_data in enumerate(untagged_images, 1):
            self.stdout.write(f"\nProcessing [{idx}/{total}]: Image ID {image_data.id}")
            
            # 画像パスを取得
            image_path = self.media_root / image_data.image.name
            
            if not image_path.exists():
                self.stdout.write(self.style.ERROR(f"  Image file not found: {image_path}"))
                continue
            
            # タグを生成
            tags = self.generate_tags(image_path)
            
            if not tags:
                self.stdout.write(self.style.ERROR("  Failed to generate tags"))
                continue
            
            # タグをDBに保存
            for tag_name in tags:
                ImageTag.objects.create(
                    image=image_data,
                    tag_name=tag_name
                )
            
            self.stdout.write(
                self.style.SUCCESS(f"  Added {len(tags)} tags: {', '.join(tags[:5])}...")
            )
        
        self.stdout.write(self.style.SUCCESS(f"\nCompleted tagging {total} images"))
    
    def retag_image(self, image_id):
        """特定の画像のタグを再生成"""
        try:
            image_data = ImageData.objects.get(id=image_id)
        except ImageData.DoesNotExist:
            raise CommandError(f'Image with ID {image_id} not found')
        
        # 既存のタグを削除
        ImageTag.objects.filter(image=image_data).delete()
        
        # 画像パスを取得
        image_path = self.media_root / image_data.image.name
        
        if not image_path.exists():
            raise CommandError(f'Image file not found: {image_path}')
        
        # タグを生成
        tags = self.generate_tags(image_path)
        
        if not tags:
            raise CommandError('Failed to generate tags')
        
        # タグをDBに保存
        for tag_name in tags:
            ImageTag.objects.create(
                image=image_data,
                tag_name=tag_name
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Added {len(tags)} tags to image {image_id}')
        )
        self.stdout.write(f'Tags: {", ".join(tags)}')
