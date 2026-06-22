from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from returns.models import Appeal, Product, Return


class Command(BaseCommand):
    help = 'Crea datos ficticios de devoluciones y apelaciones para demo.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Cantidad de devoluciones demo a crear.')
        parser.add_argument('--appeals', type=int, default=35, help='Cantidad aproximada de apelaciones demo a crear.')
        parser.add_argument('--clear', action='store_true', help='Elimina datos demo existentes antes de crear nuevos.')
        parser.add_argument('--seed', type=int, default=20260621, help='Semilla para datos reproducibles.')

    def handle(self, *args, **options):
        count = max(options['count'], 0)
        appeals_count = min(max(options['appeals'], 0), count)
        rng = random.Random(options['seed'])

        if options['clear']:
            Appeal.objects.filter(numero_apelacion__startswith='DEMO-TICKET-').delete()
            Return.objects.filter(numero_orden__startswith='DEMO-ORD-').delete()
            Product.objects.filter(sku__startswith='DEMO-SKU-').delete()

        user, _ = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'is_staff': True,
            },
        )

        sellers = [choice[0] for choice in Return.SELLER_CHOICES]
        condiciones = [choice[0] for choice in Return.CONDICION_CHOICES]
        marcas = ['Samsung', 'Apple', 'Xiaomi', 'Sony', 'LG', 'Lenovo', 'HP', 'JBL', 'Philips', 'Motorola']
        categorias = ['Smartphones', 'Audio', 'Computación', 'TV', 'Accesorios', 'Hogar', 'Gaming']
        nombres = [
            'Smartphone Galaxy S24 FE 256 GB',
            'Audífonos inalámbricos noise cancelling',
            'Notebook 15 pulgadas Ryzen 7',
            'Monitor LED 27 pulgadas 4K',
            'Parlante bluetooth portátil',
            'Tablet 10 pulgadas WiFi',
            'Teclado mecánico RGB',
            'Mouse inalámbrico ergonómico',
            'Smart TV UHD 55 pulgadas',
            'Cargador rápido USB-C',
            'Carcasa magnética premium',
            'Router WiFi mesh doble banda',
        ]
        detalles = [
            'Producto recibido desde seller para revisión operativa.',
            'Cliente reporta diferencia de estado al recibir el producto.',
            'Embalaje presenta marcas visibles y requiere clasificación.',
            'Unidad ingresada para control de devolución.',
            'Producto con observaciones registradas por bodega.',
        ]
        appeal_details = [
            'Se ingresa apelación por diferencia entre estado recibido y cobro aplicado.',
            'Se adjuntan antecedentes de revisión interna para seguimiento.',
            'Seller solicita revisión de la devolución y posible compensación.',
            'Apelación abierta por discrepancia en condición del producto.',
            'Se registra caso para evaluación del equipo de pagos.',
        ]
        appeal_statuses = [choice[0] for choice in Appeal.STATUS_CHOICES]

        devoluciones = []
        created_returns = 0
        created_products = 0

        for index in range(1, count + 1):
            sku = f'DEMO-SKU-{index:04d}'
            nombre = rng.choice(nombres)
            marca = rng.choice(marcas)
            categoria = rng.choice(categorias)
            ean = f'780{rng.randint(1000000000, 9999999999)}'

            _, product_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    'nombre': nombre,
                    'ean': ean,
                    'marca': marca,
                    'categoria': categoria,
                },
            )
            if product_created:
                created_products += 1

            numero_orden = f'DEMO-ORD-{index:04d}'
            condicion = rng.choice(condiciones)
            devolucion, return_created = Return.objects.update_or_create(
                numero_orden=numero_orden,
                defaults={
                    'seller': rng.choice(sellers),
                    'sku': sku,
                    'ean': ean,
                    'producto_nombre': nombre,
                    'marca': marca,
                    'categoria': categoria,
                    'precio_venta': Decimal(rng.randrange(9990, 899990, 1000)),
                    'cantidad': rng.randint(1, 3),
                    'estado': 'recibido',
                    'condicion_producto': condicion,
                    'detalles_dano': rng.choice(detalles),
                    'creado_por': user,
                },
            )
            if return_created:
                created_returns += 1
            devoluciones.append(devolucion)

        created_appeals = 0
        for index, devolucion in enumerate(rng.sample(devoluciones, appeals_count), start=1):
            status = rng.choice(appeal_statuses)
            monto = ''
            if status in ['proceso_pago', 'pagado']:
                monto = str(rng.randrange(10000, 250000, 5000))

            _, appeal_created = Appeal.objects.update_or_create(
                numero_apelacion=f'DEMO-TICKET-{index:04d}',
                defaults={
                    'devolucion': devolucion,
                    'detalle': rng.choice(appeal_details),
                    'status': status,
                    'estado_cuenta': monto,
                    'creado_por': user,
                    'actualizado_por': user,
                },
            )
            if appeal_created:
                created_appeals += 1

        self.stdout.write(self.style.SUCCESS(
            f'Datos demo listos: {created_returns} devoluciones nuevas, '
            f'{created_appeals} apelaciones nuevas, {created_products} productos nuevos.'
        ))
