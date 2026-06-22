import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('returns', '0007_alter_return_grado'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_apelacion', models.CharField(max_length=100, verbose_name='N° de apelación o ticket')),
                ('detalle', models.TextField(verbose_name='Detalle')),
                ('status', models.CharField(choices=[('en_proceso', 'En proceso'), ('rechazado', 'Rechazado'), ('proceso_pago', 'Proceso de pago'), ('pagado', 'Pagado')], default='en_proceso', max_length=20, verbose_name='Status')),
                ('estado_cuenta', models.CharField(blank=True, max_length=200, verbose_name='Estado de cuenta')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apelaciones_creadas', to=settings.AUTH_USER_MODEL)),
                ('devolucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apelaciones', to='returns.return', verbose_name='Orden')),
            ],
            options={
                'verbose_name': 'Apelación',
                'verbose_name_plural': 'Apelaciones',
                'ordering': ['-creado_en', '-id'],
            },
        ),
    ]
