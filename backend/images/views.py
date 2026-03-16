from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ImageData, ImageTag
from .serializers import (
    ImageDataListSerializer,
    ImageDataDetailSerializer,
    TagStatSerializer
)
import re


class ImageDataViewSet(viewsets.ReadOnlyModelViewSet):
    """画像データビューセット"""
    queryset = ImageData.objects.all().select_related('idol_info').prefetch_related('tags')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImageDataDetailSerializer
        return ImageDataListSerializer
    
    def get_queryset(self):
        """クエリパラメータでフィルタリング"""
        queryset = super().get_queryset()
        
        # 人数でフィルタリング
        person_count_min = self.request.query_params.get('person_count_min')
        person_count_max = self.request.query_params.get('person_count_max')
        
        if person_count_min or person_count_max:
            # 人数タグを持つ画像を取得
            person_queries = Q()
            
            if person_count_min and person_count_max:
                # 範囲内の人数タグを生成
                for count in range(int(person_count_min), int(person_count_max) + 1):
                    person_queries |= Q(tags__tag_name=f'人数:{count}')
            elif person_count_min:
                # 最小値以上
                for count in range(int(person_count_min), 21):  # 最大20人と仮定
                    person_queries |= Q(tags__tag_name=f'人数:{count}')
            elif person_count_max:
                # 最大値以下
                for count in range(1, int(person_count_max) + 1):
                    person_queries |= Q(tags__tag_name=f'人数:{count}')
            
            queryset = queryset.filter(person_queries)
        
        # 露出度でフィルタリング
        exposure_min = self.request.query_params.get('exposure_min')
        exposure_max = self.request.query_params.get('exposure_max')
        
        if exposure_min or exposure_max:
            # 露出度タグを持つ画像を取得
            # タグ名から露出度の数値を抽出してフィルタリング
            if exposure_min and exposure_max:
                # 両方指定された場合
                image_ids = []
                for image in ImageData.objects.all():
                    for tag in image.tags.all():
                        match = re.match(r'露出度:(\d+)', tag.tag_name)
                        if match:
                            exposure_value = int(match.group(1))
                            if int(exposure_min) <= exposure_value <= int(exposure_max):
                                image_ids.append(image.pk)
                                break
                queryset = queryset.filter(id__in=image_ids)
            elif exposure_min:
                # 最小値のみ
                image_ids = []
                for image in ImageData.objects.all():
                    for tag in image.tags.all():
                        match = re.match(r'露出度:(\d+)', tag.tag_name)
                        if match and int(match.group(1)) >= int(exposure_min):
                            image_ids.append(image.pk)
                            break
                queryset = queryset.filter(id__in=image_ids)
            elif exposure_max:
                # 最大値のみ
                image_ids = []
                for image in ImageData.objects.all():
                    for tag in image.tags.all():
                        match = re.match(r'露出度:(\d+)', tag.tag_name)
                        if match and int(match.group(1)) <= int(exposure_max):
                            image_ids.append(image.pk)
                            break
                queryset = queryset.filter(id__in=image_ids)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """ランダムに画像を取得"""
        random_images = self.get_queryset().order_by('?')[:20]
        serializer = self.get_serializer(random_images, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """同じタグを持つ画像を取得"""
        image = self.get_object()
        tag_names = image.tags.values_list('tag_name', flat=True)
        
        if not tag_names:
            return Response([])
        
        # 同じタグを持つ画像を取得（自身を除く）
        similar_images = ImageData.objects.filter(
            tags__tag_name__in=tag_names
        ).exclude(id=image.pk).distinct()[:20]
        
        serializer = ImageDataListSerializer(similar_images, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """タグで画像を検索"""
        tag_name = request.query_params.get('tag', None)
        if not tag_name:
            images = self.get_queryset().all().distinct()
        else:
            images = self.get_queryset().filter(tags__tag_name=tag_name).distinct()
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ViewSet):
    """タグビューセット"""
    
    def list(self, request):
        """タグ一覧を画像数とともに取得"""
        tags = ImageTag.objects.values('tag_name').annotate(
            count=Count('image', distinct=True)
        ).order_by('-count')
        
        serializer = TagStatSerializer(tags, many=True)
        return Response(serializer.data)
