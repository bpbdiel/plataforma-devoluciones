import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0004_product_marca_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='return',
            name='ean',
            field=models.CharField(blank=True, max_length=50, verbose_name='EAN'),
        ),
        migrations.AddField(
            model_name='return',
            name='marca',
            field=models.CharField(blank=True, max_length=150, verbose_name='Marca'),
        ),
        migrations.AddField(
            model_name='return',
            name='categoria',
            field=models.CharField(blank=True, max_length=150, verbose_name='Categoría'),
        ),
        migrations.AddField(
            model_name='return',
            name='precio_venta',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Precio de venta'),
        ),
        migrations.AddField(
            model_name='return',
            name='cantidad',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad'),
        ),
    ]
