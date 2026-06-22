import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('returns', '0008_appeal'),
    ]

    operations = [
        migrations.AddField(
            model_name='appeal',
            name='actualizado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apelaciones_actualizadas', to=settings.AUTH_USER_MODEL),
        ),
    ]
