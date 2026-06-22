# Generated manually because Django is not installed in this environment.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0002_alter_return_seller'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=100, unique=True, verbose_name='SKU')),
                ('nombre', models.CharField(max_length=300, verbose_name='Nombre del producto')),
                ('ean', models.CharField(blank=True, max_length=50, verbose_name='EAN')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['sku'],
            },
        ),
    ]
