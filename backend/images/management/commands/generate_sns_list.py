"""
Djangoカスタムコマンド: SNSリスト自動作成
与えられたキーワードを元にLLMを用いて、関連するアイドルのグループの公式SNSや、
アイドル個人のSNSをすべて特定する
"""

import os
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数読み込み
load_dotenv()


class Command(BaseCommand):
    help = 'キーワードからLLMを使用してアイドルのSNSリストを自動生成'

    def add_arguments(self, parser):
        parser.add_argument(
            'keyword',
            type=str,
            help='検索キーワード（例: "東京 地下アイドル"）'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='sns_list.txt',
            help='出力ファイル名（デフォルト: sns_list.txt）'
        )

    def handle(self, *args, **options):
        keyword = options['keyword']
        output_file = options['output']
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise CommandError('OPENAI_API_KEY environment variable is not set')
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
あなたは地下アイドルの専門家です。以下のキーワードに関連する地下アイドルグループや個人のSNSアカウントを特定してください。

キーワード: {keyword}

以下のルールに従ってください:
1. TwitterとInstagramのアカウントURLを探してください
2. 公式アカウントと個人アカウントの両方を含めてください
3. 各行に1つのSNS URLのみを記載してください
4. URLは完全な形式で記載してください（例: https://twitter.com/username または https://www.instagram.com/username/）
5. 説明やコメントは一切含めないでください
6. 実在するアカウントのみを記載してください

出力形式の例:
https://twitter.com/idol_group
https://www.instagram.com/idol_group/
https://twitter.com/idol_member1
https://www.instagram.com/idol_member1/
"""
        
        try:
            self.stdout.write(f"Generating SNS list for keyword: {keyword}")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは地下アイドルのSNS情報を正確に提供するアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            sns_list = response.choices[0].message.content.strip()
            
            # ファイルに保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sns_list)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully saved SNS list to: {output_file}')
            )
            self.stdout.write(f'Total lines: {len(sns_list.splitlines())}')
        
        except Exception as e:
            raise CommandError(f'Error generating SNS list: {e}')
