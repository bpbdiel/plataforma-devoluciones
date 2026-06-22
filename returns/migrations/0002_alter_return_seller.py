# Generated manually because Django is not installed in this environment.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='return',
            name='seller',
            field=models.CharField(
                choices=[
                    ('falabella', 'Falabella'),
                    ('ripley', 'Ripley'),
                    ('mercado_libre', 'Mercado Libre'),
                    ('paris', 'Paris'),
                    ('walmart', 'Walmart'),
                    ('shopify', 'Shopify'),
                ],
                max_length=50,
                verbose_name='Seller',
            ),
        ),
    ]
