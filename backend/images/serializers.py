from rest_framework import serializers
from .models import ImageData, IdolInfo, ImageTag


class ImageTagSerializer(serializers.ModelSerializer):
    """画像タグシリアライザー"""
    class Meta:
        model = ImageTag
        fields = ['id', 'tag_name']


class IdolInfoSerializer(serializers.ModelSerializer):
    """アイドル情報シリアライザー"""
    class Meta:
        model = IdolInfo
        fields = ['id', 'group_name', 'idol_name']


class ImageDataListSerializer(serializers.ModelSerializer):
    """画像データ一覧用シリアライザー"""
    tags = ImageTagSerializer(many=True, read_only=True)
    idol_info = IdolInfoSerializer(read_only=True)
    
    class Meta:
        model = ImageData
        fields = ['pk', 'image', 'source_url', 'tags', 'idol_info', 'created_at']


class ImageDataDetailSerializer(serializers.ModelSerializer):
    """画像データ詳細用シリアライザー"""
    tags = ImageTagSerializer(many=True, read_only=True)
    idol_info = IdolInfoSerializer(read_only=True)
    
    class Meta:
        model = ImageData
        fields = ['pk', 'image', 'source_url', 'tags', 'idol_info', 'created_at', 'updated_at']


class TagStatSerializer(serializers.Serializer):
    """タグ統計用シリアライザー"""
    tag_name = serializers.CharField()
    count = serializers.IntegerField()
