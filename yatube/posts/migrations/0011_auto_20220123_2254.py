# Generated by Django 2.2.16 on 2022-01-23 19:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20220123_2248'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
    ]
