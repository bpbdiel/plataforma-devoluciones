from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0003_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='marca',
            field=models.CharField(blank=True, max_length=150, verbose_name='Marca'),
        ),
        migrations.AddField(
            model_name='product',
            name='categoria',
            field=models.CharField(blank=True, max_length=150, verbose_name='Categoría'),
        ),
    ]
