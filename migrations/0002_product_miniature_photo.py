# Generated by Django 4.1.2 on 2022-12-06 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='miniature_photo',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
