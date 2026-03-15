from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ImageData, ImageTag
from .serializers import (
    ImageDataListSerializer,
    ImageDataDetailSerializer,
    TagStatSerializer
)


class ImageDataViewSet(viewsets.ReadOnlyModelViewSet):
    """画像データビューセット"""
    queryset = ImageData.objects.all().select_related('idol_info').prefetch_related('tags')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImageDataDetailSerializer
        return ImageDataListSerializer
    
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
        ).exclude(id=image.id).distinct()[:20]
        
        serializer = ImageDataListSerializer(similar_images, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """タグで画像を検索"""
        tag_name = request.query_params.get('tag', None)
        if not tag_name:
            return Response(
                {'error': 'tag parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
