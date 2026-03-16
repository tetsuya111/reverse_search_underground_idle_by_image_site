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
あなたは地下アイドルの専門家です。以下に地下アイドルのグループ名の一覧が与えられます。以下「出力条件」と「出力形式」に従ってデータを出力して。

# グループ名の一覧
{keyword}

# 出力条件
1.グループ名の一覧から各々のグループ名を抽出すること
2.一つのグループの対して以下の出力条件に従いデータを抽出し出力する
2-1. TwitterとInstagramのアカウントURLを探してください
2-2. 公式アカウントと個人アカウントの両方を含めてください
2-3. 説明やコメントは一切含めないでください
2-4. 実在するアカウントのみを記載してください

#出力形式
- 各行に1つのSNS URLのみを記載してください
- URLは完全な形式で記載してください（例: https://twitter.com/username または https://www.instagram.com/username/）

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
