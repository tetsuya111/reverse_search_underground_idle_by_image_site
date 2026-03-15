#!/usr/bin/env python3
"""
SNSリスト自動作成プログラム
与えられたキーワードを元にLLMを用いて、関連するアイドルのグループの公式SNSや、
アイドル個人のSNSをすべて特定する
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数読み込み
load_dotenv()

def generate_sns_list(keyword: str, output_file: str = "sns_list.txt"):
    """
    キーワードからSNSリストを生成
    
    Args:
        keyword: 検索キーワード
        output_file: 出力ファイル名
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)
    
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
        print(f"Generating SNS list for keyword: {keyword}")
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
        
        print(f"SNS list saved to: {output_file}")
        print(f"Total lines: {len(sns_list.splitlines())}")
        
        return output_file
    
    except Exception as e:
        print(f"Error generating SNS list: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_sns_list.py <keyword> [output_file]")
        print("Example: python generate_sns_list.py '東京 地下アイドル' sns_list.txt")
        sys.exit(1)
    
    keyword = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "sns_list.txt"
    
    generate_sns_list(keyword, output_file)
