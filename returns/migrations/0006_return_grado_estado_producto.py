from django.db import migrations, models


def migrate_condicion_and_grado(apps, schema_editor):
    Return = apps.get_model('returns', 'Return')
    condicion_map = {
        'nuevo': 'nuevo',
        'bueno': 'nuevo',
        'caja_danada': 'caja_danada',
        'danado': 'danado',
        'muy_danado': 'danado',
        'irreparable': 'danado',
        'dano_estetico': 'dano_estetico',
    }
    grado_map = {
        'nuevo': 'A',
        'caja_danada': 'C',
        'danado': 'D',
        'dano_estetico': 'C',
    }

    for devolucion in Return.objects.all():
        condicion = condicion_map.get(devolucion.condicion_producto, 'nuevo')
        devolucion.condicion_producto = condicion
        devolucion.grado = grado_map[condicion]
        devolucion.save(update_fields=['condicion_producto', 'grado'])


class Migration(migrations.Migration):

    dependencies = [
        ('returns', '0005_return_order_product_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='return',
            name='grado',
            field=models.CharField(choices=[('A', 'Grado A'), ('C', 'Grado C'), ('D', 'Grado D')], default='A', max_length=1, verbose_name='Grado'),
        ),
        migrations.RunPython(migrate_condicion_and_grado, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='return',
            name='condicion_producto',
            field=models.CharField(choices=[('nuevo', 'Nuevo'), ('caja_danada', 'Caja Dañada'), ('danado', 'Dañado'), ('dano_estetico', 'Daño Estetico')], default='nuevo', max_length=20, verbose_name='Estado del producto'),
        ),
    ]
