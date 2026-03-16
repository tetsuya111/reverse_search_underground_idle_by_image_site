"""
Djangoカスタムコマンド: 地下アイドルグループ・メンバーSNS検索
地下アイドルのグループ名を列挙し、各グループのSNSと所属メンバーのSNSを取得する
Perplexity APIを使用してリアルタイムWeb検索を実行
"""

import os
import json
import sys
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv
from openai import OpenAI

from images.models import IdolInfo

# 環境変数読み込み
load_dotenv()


class Command(BaseCommand):
    help = '地下アイドルのグループとメンバーのSNSを検索・一覧化（Perplexity API使用）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            default='東京',
            help='地域指定（デフォルト: 東京）'
        )
        parser.add_argument(
            '--output-groups',
            type=str,
            default='underground_idol_groups.json',
            help='グループ情報の出力ファイル名（デフォルト: underground_idol_groups.json）'
        )
        parser.add_argument(
            '--output-sns',
            type=str,
            default='underground_idol_sns_list.txt',
            help='SNSリストの出力ファイル名（デフォルト: underground_idol_sns_list.txt）'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='取得するグループの最大数（デフォルト: 10）'
        )
        parser.add_argument(
            '--stdin',
            action='store_true',
            help='標準入力からグループ名を読み込む'
        )

    def handle(self, *args, **options):
        region = options['region']
        output_groups = options['output_groups']
        output_sns = options['output_sns']
        limit = options['limit']
        use_stdin = options['stdin']
        
        # Perplexity API キーを取得
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            raise CommandError('PERPLEXITY_API_KEY environment variable is not set')
        
        # Perplexity APIクライアントを初期化（OpenAI互換）
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # ステップ1: グループ名の取得
        if use_stdin:
            # 標準入力からグループ名を読み込み
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"ステップ1: 標準入力からグループ名を読み込み中...")
            self.stdout.write(f"{'='*60}\n")
            
            group_names = self.read_group_names_from_stdin()
        else:
            # LLMでグループ名を列挙
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"ステップ1: {region}の地下アイドルグループを検索中...")
            self.stdout.write(f"{'='*60}\n")
            
            group_names = self.enumerate_underground_idol_groups(region, limit)
        
        if not group_names:
            raise CommandError('グループが見つかりませんでした')
        
        self.stdout.write(self.style.SUCCESS(f"✓ {len(group_names)}個のグループが見つかりました"))
        for i, name in enumerate(group_names, 1):
            self.stdout.write(f"  {i}. {name}")
        
        # ステップ2: 各グループのSNSとメンバー情報を取得
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"ステップ2: 各グループの詳細情報を取得中...")
        self.stdout.write(f"{'='*60}\n")
        
        all_groups_data = []
        all_sns_urls = []
        
        for idx, group_name in enumerate(group_names, 1):
            self.stdout.write(f"\n[{idx}/{len(group_names)}] {group_name}")
            self.stdout.write("-" * 60)
            
            # グループSNSを取得
            group_sns = self.get_group_sns(group_name)
            
            # メンバーSNSを取得
            members_sns = self.get_members_sns(group_name)
            
            # データを構造化
            group_data = {
                'group_name': group_name,
                'group_sns': group_sns,
                'members': members_sns
            }
            
            all_groups_data.append(group_data)
            
            # すべてのSNS URLを収集
            all_sns_urls.extend(group_sns)
            for member in members_sns:
                all_sns_urls.extend(member.get('sns', []))
            
            # 進捗表示
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ グループSNS: {len(group_sns)}個"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ メンバー: {len(members_sns)}人"
            ))
        
        # ステップ3: 結果を保存
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"ステップ3: 結果を保存中...")
        self.stdout.write(f"{'='*60}\n")
        
        # JSON形式で詳細情報を保存
        with open(output_groups, 'w', encoding='utf-8') as f:
            json.dump(all_groups_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ グループ情報を保存: {output_groups}"
        ))
        
        # テキスト形式でSNSリストを保存
        with open(output_sns, 'w', encoding='utf-8') as f:
            for url in all_sns_urls:
                f.write(f"{url}\n")
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ SNSリストを保存: {output_sns}"
        ))
        
        # サマリー表示
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("サマリー")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"総グループ数: {len(all_groups_data)}")
        self.stdout.write(f"総SNS URL数: {len(all_sns_urls)}")
        self.stdout.write(self.style.SUCCESS("\n✓ 処理が完了しました！\n"))
    
    def read_group_names_from_stdin(self):
        """標準入力からグループ名を読み込み、LLMで抽出する"""
        self.stdout.write("標準入力からテキストを読み込んでいます...")
        self.stdout.write("（入力を終了するには Ctrl+D を押してください）\n")
        
        # 標準入力から全テキストを読み込み
        input_text = sys.stdin.read().strip()
        
        if not input_text:
            self.stdout.write(self.style.WARNING("入力が空です"))
            return []
        
        self.stdout.write(f"\n読み込んだテキスト（最初の200文字）:")
        self.stdout.write(f"{input_text[:200]}...\n")
        
        # LLMでグループ名を抽出
        return self.extract_group_names_from_text(input_text)
    
    def extract_group_names_from_text(self, text):
        """テキストからグループ名を抽出する（Perplexity使用）"""
        self.stdout.write("\nPerplexity APIでグループ名を抽出中...")
        
        prompt = f"""
以下のテキストから、地下アイドルグループ名を全て抽出してください。

テキスト:
{text}

以下のルールに従ってください:
1. テキスト内に含まれるアイドルグループ名のみを抽出
2. グループ名は正確に抽出（表記揺れに注意）
3. 重複は除外
4. グループ名のみで、説明やコメントは不要
5. JSON形式で出力

出力形式:
{{
    "groups": ["グループ名1", "グループ名2", "グループ名3", ...]
}}

グループ名が見つからない場合は空配列を返してください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはテキスト解析の専門家です。与えられたテキストからアイドルグループ名を正確に抽出してください。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Perplexityはresponse_formatをサポートしていないため、手動でJSON抽出
            content = response.choices[0].message.content
            
            # JSON部分を抽出
            try:
                # ```json ``` で囲まれている場合
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                groups = result.get('groups', [])
            except:
                # JSON抽出失敗時は空配列を返す
                self.stdout.write(self.style.WARNING("JSON形式の抽出に失敗しました"))
                groups = []
            
            if groups:
                self.stdout.write(self.style.SUCCESS(f"✓ {len(groups)}個のグループ名を抽出しました"))
                for i, name in enumerate(groups, 1):
                    self.stdout.write(f"  {i}. {name}")
            else:
                self.stdout.write(self.style.WARNING("グループ名が見つかりませんでした"))
            
            return groups
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error extracting group names: {e}"))
            return []
    
    def enumerate_underground_idol_groups(self, region, limit):
        """地下アイドルグループ名を列挙する（Perplexity Web検索使用）"""
        group_names=IdolInfo.objects.all().values_list("group_name",flat=True)
        group_names="\n".join(group_names)
        prompt = f"""
あなたは地下アイドルの専門家です。{region}で活動している地下アイドルグループを{limit}個列挙してください。

以下のルールに従ってください:
1. 実在する地下アイドルグループのみを記載
2. メジャーではなく、ライブハウスや小規模会場で活動しているグループを優先
3. 最新情報をみて活動中であると判断できるグループ
4. 各行に1つのグループ名のみを記載
5. グループ名のみで、説明やコメントは不要
6. JSON形式で出力
7. Web検索で最新の情報を確認すること

# 以下のグループ以外を取得すること
{group_names}

出力形式:
{{
    "groups": ["グループ名1", "グループ名2", "グループ名3", ...]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは地下アイドルに詳しい専門家です。Web検索で最新の正確な情報を提供してください。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # JSON部分を抽出
            content = response.choices[0].message.content
            try:
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                return result.get('groups', [])
            except:
                self.stdout.write(self.style.WARNING("JSON形式の抽出に失敗しました"))
                return []
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error enumerating groups: {e}"))
            return []
    
    def get_group_sns(self, group_name):
        """一つのグループのSNSアカウントを取得する（Perplexity Web検索使用）"""
        prompt = f"""
地下アイドルグループ「{group_name}」の公式SNSアカウントを特定してください。

以下のルールに従ってください:
1. Web検索で最新の情報を確認すること
2. Twitter（X）とInstagramのURLを探してください
3. 公式アカウントのみを記載
4. URLは完全な形式で記載（例: https://twitter.com/username）
5. 実在するアカウントのみを記載
6. JSON形式で出力

出力形式:
{{
    "sns_urls": [
        "https://twitter.com/groupname",
        "https://www.instagram.com/groupname/"
    ]
}}

アカウントが見つからない場合は空配列を返してください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは地下アイドルのSNS情報を正確に提供するアシスタントです。Web検索で最新の情報を確認してください。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # JSON部分を抽出
            content = response.choices[0].message.content
            try:
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                sns_urls = result.get('sns_urls', [])
            except:
                self.stdout.write(self.style.WARNING("    JSON形式の抽出に失敗しました"))
                sns_urls = []
            
            # ログ出力
            if sns_urls:
                for url in sns_urls:
                    self.stdout.write(f"    グループSNS: {url}")
            else:
                self.stdout.write(self.style.WARNING("    グループSNSが見つかりませんでした"))
            
            return sns_urls
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error getting group SNS: {e}"))
            return []
    
    def get_members_sns(self, group_name):
        """一つのグループに所属するメンバーのSNSを取得する（Perplexity Web検索使用）"""
        prompt = f"""
地下アイドルグループ「{group_name}」に所属するメンバーと、各メンバーの個人SNSアカウントを特定してください。

以下のルールに従ってください:
1. Web検索で最新の情報を確認すること
2. 実在するメンバーのみを記載
3. 各メンバーのTwitter（X）とInstagramのURLを探してください
4. URLは完全な形式で記載
5. JSON形式で出力

出力形式:
{{
    "members": [
        {{
            "name": "メンバー名1",
            "sns": [
                "https://twitter.com/member1",
                "https://www.instagram.com/member1/"
            ]
        }},
        {{
            "name": "メンバー名2",
            "sns": [
                "https://twitter.com/member2"
            ]
        }}
    ]
}}

メンバー情報が見つからない場合は空配列を返してください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは地下アイドルのメンバー情報に詳しい専門家です。Web検索で最新の情報を確認してください。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # JSON部分を抽出
            content = response.choices[0].message.content
            try:
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                members = result.get('members', [])
            except:
                self.stdout.write(self.style.WARNING("    JSON形式の抽出に失敗しました"))
                members = []
            
            # ログ出力
            if members:
                for member in members:
                    member_name = member.get('name', 'Unknown')
                    member_sns = member.get('sns', [])
                    self.stdout.write(f"    メンバー: {member_name} ({len(member_sns)}個のSNS)")
                    for url in member_sns:
                        self.stdout.write(f"      - {url}")
            else:
                self.stdout.write(self.style.WARNING("    メンバー情報が見つかりませんでした"))
            
            return members
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error getting members SNS: {e}"))
            return []
