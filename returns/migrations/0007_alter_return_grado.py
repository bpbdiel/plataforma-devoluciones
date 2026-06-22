from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0006_return_grado_estado_producto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='return',
            name='grado',
            field=models.CharField(choices=[('A', 'A'), ('C', 'C'), ('D', 'D')], default='A', max_length=1, verbose_name='Grado'),
        ),
    ]
