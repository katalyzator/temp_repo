# Generated by Django 4.1.2 on 2023-09-21 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_product_rating_product_reviews_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.FloatField(null=True),
        ),
    ]
