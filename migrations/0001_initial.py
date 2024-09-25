# Generated by Django 4.1.2 on 2022-11-23 08:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0002_alter_category_options'),
        ('features', '0004_rename_is_enabled_feature_is_visible_and_more'),
        ('brands', '0001_initial'),
        ('colors', '0004_alter_colorgroup_options_colorgroup_position_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('common_name', models.CharField(max_length=255, null=True)),
                ('variant_name', models.CharField(blank=True, max_length=255, null=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('main_photo', models.JSONField()),
                ('photos', models.JSONField()),
                ('video_urls', models.JSONField()),
                ('description', models.TextField(blank=True, max_length=1000, null=True)),
                ('is_visible', models.BooleanField()),
                ('offers_count', models.PositiveSmallIntegerField(default=0)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='brands.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='categories.category')),
                ('color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='colors.color')),
                ('master', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='products.product')),
                ('variation_features', models.ManyToManyField(related_name='variation_products', to='features.feature')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='features.feature')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='products.product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductFeatureValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('feature_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='features.featurevalue')),
                ('product_feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selected_values', to='products.productfeature')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]