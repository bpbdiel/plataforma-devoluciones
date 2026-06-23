from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIMEZONE_CHOICES = [
    ('America/Santiago', 'Chile - Santiago'),
    ('America/Punta_Arenas', 'Chile - Punta Arenas'),
    ('America/Argentina/Buenos_Aires', 'Argentina - Buenos Aires'),
    ('America/Bogota', 'Colombia - Bogota'),
    ('America/Lima', 'Peru - Lima'),
    ('America/La_Paz', 'Bolivia - La Paz'),
    ('America/Asuncion', 'Paraguay - Asuncion'),
    ('America/Montevideo', 'Uruguay - Montevideo'),
    ('America/Sao_Paulo', 'Brasil - Sao Paulo'),
    ('America/Mexico_City', 'Mexico - Ciudad de Mexico'),
    ('America/New_York', 'Estados Unidos - New York'),
    ('America/Los_Angeles', 'Estados Unidos - Los Angeles'),
    ('UTC', 'UTC'),
]


class SiteConfiguration(models.Model):
    timezone = models.CharField(
        max_length=64,
        choices=TIMEZONE_CHOICES,
        default='America/Santiago',
        verbose_name='Zona horaria',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de plataforma'
        verbose_name_plural = 'Configuración de plataforma'

    def __str__(self):
        return 'Configuración de plataforma'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            from django.core.exceptions import ValidationError
            raise ValidationError({'timezone': 'Selecciona una zona horaria válida.'})

    @classmethod
    def load(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')
    nombre = models.CharField(max_length=300, verbose_name='Nombre del producto')
    ean = models.CharField(max_length=50, blank=True, verbose_name='EAN')
    marca = models.CharField(max_length=150, blank=True, verbose_name='Marca')
    categoria = models.CharField(max_length=150, blank=True, verbose_name='Categoría')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['sku']

    def __str__(self):
        return f"{self.sku} - {self.nombre}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    force_password_change = models.BooleanField(default=False, verbose_name='Solicitar cambio de contraseña')

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.username}'


class Return(models.Model):
    SELLER_CHOICES = [
        ('falabella', 'Falabella'),
        ('ripley', 'Ripley'),
        ('mercado_libre', 'Mercado Libre'),
        ('paris', 'Paris'),
        ('walmart', 'Walmart'),
        ('shopify', 'Shopify'),
    ]

    ESTADO_CHOICES = [
        ('recibido', 'Recibido'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
        ('cerrado', 'Cerrado'),
    ]

    CONDICION_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('caja_danada', 'Caja Dañada'),
        ('danado', 'Dañado'),
        ('dano_estetico', 'Daño Estetico'),
    ]

    GRADO_CHOICES = [
        ('A', 'A'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    # Datos principales
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    seller = models.CharField(max_length=50, choices=SELLER_CHOICES, verbose_name='Seller')
    numero_orden = models.CharField(max_length=100, unique=True, verbose_name='Número de orden')
    sku = models.CharField(max_length=100, verbose_name='SKU')
    ean = models.CharField(max_length=50, blank=True, verbose_name='EAN')
    producto_nombre = models.CharField(max_length=300, verbose_name='Nombre del producto', blank=True)
    marca = models.CharField(max_length=150, blank=True, verbose_name='Marca')
    categoria = models.CharField(max_length=150, blank=True, verbose_name='Categoría')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Precio de venta')
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Cantidad')

    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='recibido', verbose_name='Estado')
    condicion_producto = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='nuevo', verbose_name='Estado del producto')
    grado = models.CharField(max_length=1, choices=GRADO_CHOICES, default='A', verbose_name='Grado')

    # Detalles del daño
    detalles_dano = models.TextField(blank=True, verbose_name='Detalles del daño')
    notas_internas = models.TextField(blank=True, verbose_name='Notas internas')

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='devoluciones_creadas')

    class Meta:
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        ordering = ['-fecha_ingreso', '-id']

    def __str__(self):
        return f"#{self.id} — {self.numero_orden} ({self.get_seller_display()})"

    @classmethod
    def grado_for_condicion(cls, condicion_producto):
        grados = {
            'nuevo': 'A',
            'caja_danada': 'C',
            'danado': 'D',
            'dano_estetico': 'C',
        }
        return grados.get(condicion_producto, 'A')

    def save(self, *args, **kwargs):
        self.grado = self.grado_for_condicion(self.condicion_producto)
        super().save(*args, **kwargs)

    def get_estado_color(self):
        colors = {
            'recibido': 'blue',
            'en_revision': 'yellow',
            'aprobado': 'green',
            'rechazado': 'red',
            'reembolsado': 'purple',
            'cerrado': 'gray',
        }
        return colors.get(self.estado, 'gray')


class ReturnPhoto(models.Model):
    devolucion = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='fotos')
    foto = models.ImageField(upload_to='devoluciones/%Y/%m/', verbose_name='Foto')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    subida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

    def __str__(self):
        return f"Foto de {self.devolucion}"


class Appeal(models.Model):
    STATUS_CHOICES = [
        ('en_proceso', 'En proceso'),
        ('rechazado', 'Rechazado'),
        ('proceso_pago', 'Proceso de pago'),
        ('pagado', 'Pagado'),
    ]

    devolucion = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='apelaciones', verbose_name='Orden')
    numero_apelacion = models.CharField(max_length=100, verbose_name='N° de apelación o ticket')
    detalle = models.TextField(verbose_name='Detalle')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_proceso', verbose_name='Status')
    estado_cuenta = models.CharField(max_length=200, blank=True, verbose_name='Estado de cuenta')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='apelaciones_creadas')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='apelaciones_actualizadas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Apelación'
        verbose_name_plural = 'Apelaciones'
        ordering = ['-creado_en', '-id']

    def __str__(self):
        return f"{self.numero_apelacion} - {self.devolucion.numero_orden}"

    def get_status_color(self):
        colors = {
            'en_proceso': 'yellow',
            'rechazado': 'red',
            'proceso_pago': 'purple',
            'pagado': 'green',
        }
        return colors.get(self.status, 'gray')

    @property
    def checklist_flujo(self):
        datos_completos = bool(self.numero_apelacion and self.detalle)
        decision_tomada = self.status in ['rechazado', 'proceso_pago', 'pagado']
        fue_rechazado = self.status == 'rechazado'

        return [
            {
                'numero': 1,
                'titulo': 'Apelación ingresada',
                'detalle': 'La apelación fue creada y asociada a una orden.',
                'completo': True,
            },
            {
                'numero': 2,
                'titulo': 'Ticket y datos añadidos',
                'detalle': 'Se registró el N° de apelación o ticket y el detalle.',
                'completo': datos_completos,
            },
            {
                'numero': 3,
                'titulo': 'Resultado seleccionado',
                'detalle': 'Se define si fue rechazada o pasó a proceso de pago.',
                'completo': decision_tomada,
            },
            {
                'numero': 4,
                'titulo': 'Flujo cerrado con pago' if not fue_rechazado else 'Flujo cerrado por rechazo',
                'detalle': 'Se marca como pagado para cerrar el flujo.' if not fue_rechazado else 'La apelación fue rechazada y no requiere pago.',
                'completo': self.status == 'pagado' or fue_rechazado,
            },
        ]


@receiver(post_delete, sender=ReturnPhoto)
def delete_return_photo_file(sender, instance, **kwargs):
    if instance.foto:
        instance.foto.delete(save=False)


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
