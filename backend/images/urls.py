from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImageDataViewSet, TagViewSet

router = DefaultRouter()
router.register(r'images', ImageDataViewSet, basename='image')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
