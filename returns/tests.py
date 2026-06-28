import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import AppealForm, ReturnForm
from .models import Appeal, Return, ReturnPhoto


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ReturnPhotoDeletionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def create_return_with_photo(self):
        devolucion = Return.objects.create(
            seller='falabella',
            numero_orden='ORD-TEST-001',
            sku='SKU-TEST-001',
            producto_nombre='Producto test',
        )
        foto = ReturnPhoto.objects.create(
            devolucion=devolucion,
            foto=SimpleUploadedFile(
                'foto-test.jpg',
                b'contenido-de-prueba',
                content_type='image/jpeg',
            ),
        )
        return devolucion, foto

    def test_deleting_return_deletes_linked_photo_file(self):
        devolucion, foto = self.create_return_with_photo()
        storage = foto.foto.storage
        file_name = foto.foto.name

        self.assertTrue(storage.exists(file_name))

        devolucion.delete()

        self.assertFalse(ReturnPhoto.objects.filter(pk=foto.pk).exists())
        self.assertFalse(storage.exists(file_name))

    def test_deleting_photo_deletes_file(self):
        _, foto = self.create_return_with_photo()
        storage = foto.foto.storage
        file_name = foto.foto.name

        self.assertTrue(storage.exists(file_name))

        foto.delete()

        self.assertFalse(storage.exists(file_name))


class ReturnFormTests(TestCase):
    def form_data(self, **overrides):
        data = {
            'seller': 'falabella',
            'numero_orden': 'ORD-FORM-001',
            'sku': 'SKU-FORM-001',
            'ean': '',
            'producto_nombre': 'Producto test',
            'marca': '',
            'categoria': '',
            'precio_venta': '',
            'cantidad': '1',
            'estado': 'aprobado',
            'condicion_producto': 'caja_danada',
            'grado': 'D',
            'detalles_dano': '',
        }
        data.update(overrides)
        return data

    def test_estado_is_always_recibido_from_form(self):
        form = ReturnForm(data=self.form_data())

        self.assertTrue(form.is_valid(), form.errors)
        devolucion = form.save()

        self.assertEqual(devolucion.estado, 'recibido')

    def test_estado_is_preserved_when_editing(self):
        devolucion = Return.objects.create(
            seller='falabella',
            numero_orden='ORD-EXISTING-001',
            sku='SKU-EXISTING-001',
            producto_nombre='Producto existente',
            estado='aprobado',
        )
        form = ReturnForm(data=self.form_data(
            numero_orden=devolucion.numero_orden,
            sku=devolucion.sku,
            estado='rechazado',
        ), instance=devolucion)

        self.assertTrue(form.is_valid(), form.errors)
        devolucion = form.save()

        self.assertEqual(devolucion.estado, 'aprobado')

    def test_grado_is_calculated_from_condicion_producto(self):
        cases = {
            'nuevo': 'A',
            'caja_danada': 'C',
            'danado': 'D',
            'dano_estetico': 'C',
            'extraviado': 'E',
        }

        for condicion, grado in cases.items():
            with self.subTest(condicion=condicion):
                form = ReturnForm(data=self.form_data(
                    numero_orden=f'ORD-{condicion}',
                    condicion_producto=condicion,
                ))

                self.assertTrue(form.is_valid(), form.errors)
                devolucion = form.save()

                self.assertEqual(devolucion.grado, grado)

    def test_sub_danos_are_saved_from_form(self):
        form = ReturnForm(data=self.form_data(
            numero_orden='ORD-SUB-DANOS',
            sub_danos=['rayado', 'sin_accesorios', 'producto_cambiado'],
        ))

        self.assertTrue(form.is_valid(), form.errors)
        devolucion = form.save()

        self.assertEqual(devolucion.sub_danos, ['rayado', 'sin_accesorios', 'producto_cambiado'])
        self.assertEqual(
            devolucion.get_sub_danos_display_text(),
            'Rayado, Sin Accesorios, Producto Cambiado (Cambiazo o Robo)',
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ReturnPhotoUploadViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='uploader', password='secret')
        self.client.force_login(self.user)

    def image_file(self, name):
        return SimpleUploadedFile(
            name,
            (
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
                b'\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00'
                b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
                b'\x44\x01\x00\x3b'
            ),
            content_type='image/gif',
        )

    def return_data(self, **overrides):
        data = {
            'seller': 'falabella',
            'numero_orden': 'ORD-UPLOAD-001',
            'sku': 'SKU-UPLOAD-001',
            'ean': '',
            'producto_nombre': 'Producto con fotos',
            'marca': '',
            'categoria': '',
            'precio_venta': '',
            'cantidad': '1',
            'condicion_producto': 'nuevo',
            'grado': 'A',
            'detalles_dano': '',
        }
        data.update(overrides)
        return data

    def test_create_return_accepts_multiple_photos(self):
        response = self.client.post(reverse('return_create'), {
            **self.return_data(),
            'fotos': [
                self.image_file('foto-1.gif'),
                self.image_file('foto-2.gif'),
            ],
        })

        devolucion = Return.objects.get(numero_orden='ORD-UPLOAD-001')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(devolucion.fotos.count(), 2)
        self.assertEqual(
            list(devolucion.fotos.order_by('id').values_list('foto', flat=True)),
            [
                'devoluciones/ord-upload-001-1.gif',
                'devoluciones/ord-upload-001-2.gif',
            ],
        )

    def test_edit_return_adds_multiple_photos_and_deletes_selected_photos(self):
        devolucion = Return.objects.create(
            seller='falabella',
            numero_orden='ORD-UPLOAD-EDIT',
            sku='SKU-UPLOAD-EDIT',
            producto_nombre='Producto editable',
            creado_por=self.user,
        )
        old_photo = ReturnPhoto.objects.create(
            devolucion=devolucion,
            foto=self.image_file('foto-antigua.gif'),
        )

        response = self.client.post(reverse('return_edit', args=[devolucion.pk]), {
            **self.return_data(
                numero_orden=devolucion.numero_orden,
                sku=devolucion.sku,
            ),
            'delete_photos': [str(old_photo.pk)],
            'fotos': [
                self.image_file('foto-nueva-1.gif'),
                self.image_file('foto-nueva-2.gif'),
            ],
        })

        devolucion.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ReturnPhoto.objects.filter(pk=old_photo.pk).exists())
        self.assertEqual(devolucion.fotos.count(), 2)
        self.assertEqual(
            list(devolucion.fotos.order_by('id').values_list('foto', flat=True)),
            [
                'devoluciones/ord-upload-edit-1.gif',
                'devoluciones/ord-upload-edit-2.gif',
            ],
        )


class AppealFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret')
        self.devolucion = Return.objects.create(
            seller='falabella',
            numero_orden='ORD-APPEAL-001',
            sku='SKU-APPEAL-001',
            producto_nombre='Producto apelable',
        )

    def form_data(self, **overrides):
        data = {
            'devolucion': str(self.devolucion.pk),
            'numero_apelacion': 'TICKET-001',
            'detalle': 'Seguimiento inicial de la apelación.',
            'status': 'pagado',
            'estado_cuenta': '25990',
        }
        data.update(overrides)
        return data

    def test_appeal_requires_available_return(self):
        form = AppealForm(data=self.form_data(devolucion='999999'))

        self.assertFalse(form.is_valid())
        self.assertIn('devolucion', form.errors)

    def test_new_appeal_starts_in_process(self):
        form = AppealForm(data=self.form_data())

        self.assertTrue(form.is_valid(), form.errors)
        apelacion = form.save()

        self.assertEqual(apelacion.devolucion, self.devolucion)
        self.assertEqual(apelacion.status, 'en_proceso')

    def test_returns_with_appeal_are_not_available_to_create(self):
        Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-EXISTING',
            detalle='Apelación existente.',
        )

        form = AppealForm()

        self.assertNotIn(self.devolucion, form.fields['devolucion'].queryset)

    def test_checklist_closes_with_paid_status(self):
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-PAID',
            detalle='Apelación pagada.',
            status='pagado',
        )

        self.assertTrue(apelacion.checklist_flujo[-1]['completo'])
        self.assertEqual(apelacion.checklist_flujo[-1]['titulo'], 'Flujo cerrado con pago')

    def test_checklist_closes_with_rejected_status(self):
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-REJECTED',
            detalle='Apelación rechazada.',
            status='rechazado',
        )

        self.assertTrue(apelacion.checklist_flujo[-1]['completo'])
        self.assertEqual(apelacion.checklist_flujo[-1]['titulo'], 'Flujo cerrado por rechazo')

    def test_status_update_tracks_user(self):
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-STATUS',
            detalle='Cambio de status.',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('appeal_update_status', args=[apelacion.pk]), {'status': 'pagado'})
        apelacion.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(apelacion.status, 'pagado')
        self.assertEqual(apelacion.actualizado_por, self.user)

    def test_payment_process_requires_amount(self):
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-AMOUNT',
            detalle='Proceso de pago.',
        )
        self.client.force_login(self.user)

        self.client.post(reverse('appeal_update_status', args=[apelacion.pk]), {'status': 'proceso_pago'})
        apelacion.refresh_from_db()

        self.assertEqual(apelacion.status, 'en_proceso')
        self.assertEqual(apelacion.estado_cuenta, '')

    def test_payment_process_saves_clp_amount(self):
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-AMOUNT-OK',
            detalle='Proceso de pago.',
        )
        self.client.force_login(self.user)

        self.client.post(reverse('appeal_update_status', args=[apelacion.pk]), {
            'status': 'proceso_pago',
            'estado_cuenta': '25990',
        })
        apelacion.refresh_from_db()

        self.assertEqual(apelacion.status, 'proceso_pago')
        self.assertEqual(apelacion.estado_cuenta, '25990')

    def test_paid_difference_uses_total_return_value(self):
        self.devolucion.precio_venta = '10000'
        self.devolucion.cantidad = 3
        self.devolucion.save()
        apelacion = Appeal.objects.create(
            devolucion=self.devolucion,
            numero_apelacion='TICKET-DIFF',
            detalle='Pago parcial.',
            status='pagado',
            estado_cuenta='25000',
        )

        self.assertEqual(apelacion.devolucion.valor_total, 30000)
        self.assertEqual(apelacion.diferencia_pagada, 5000)
