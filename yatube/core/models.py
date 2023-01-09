from django.db import models


class CreatedModel(models.Model):
    """Abstract model to add publication date."""
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True
