# Generated by Django 4.1.2 on 2022-12-06 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_miniature_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days_new', models.PositiveSmallIntegerField(default=30)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
