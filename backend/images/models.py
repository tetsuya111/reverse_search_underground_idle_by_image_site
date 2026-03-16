from django.db import models


class ImageData(models.Model):
    """画像データモデル"""
    hashed=models.IntegerField(primary_key=True,verbose_name="ハッシュ値")
    image = models.ImageField(upload_to='images/', verbose_name='画像')
    source_url = models.URLField(max_length=500, verbose_name='取得元リンク')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        db_table = 'image_data'
        verbose_name = '画像データ'
        verbose_name_plural = '画像データ'
        ordering = ['-created_at']

    def __str__(self):
        return f"Image {self.id} - {self.source_url}"


class IdolInfo(models.Model):
    """アイドル情報モデル"""
    image = models.OneToOneField(
        ImageData,
        on_delete=models.CASCADE,
        related_name='idol_info',
        verbose_name='画像データ'
    )
    group_name = models.CharField(max_length=200, blank=True, verbose_name='グループ名')
    idol_name = models.CharField(max_length=200, blank=True, verbose_name='アイドル名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        db_table = 'idol_info'
        verbose_name = 'アイドル情報'
        verbose_name_plural = 'アイドル情報'

    def __str__(self):
        return f"{self.group_name} - {self.idol_name}"


class ImageTag(models.Model):
    """画像タグモデル"""
    image = models.ForeignKey(
        ImageData,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='画像データ'
    )
    tag_name = models.CharField(max_length=100, verbose_name='タグ名', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    class Meta:
        db_table = 'image_tag'
        verbose_name = '画像タグ'
        verbose_name_plural = '画像タグ'
        unique_together = [['image', 'tag_name']]
        indexes = [
            models.Index(fields=['tag_name']),
        ]

    def __str__(self):
        return f"{self.image.id} - {self.tag_name}"
