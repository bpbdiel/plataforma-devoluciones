from django.contrib import admin
from django import forms
from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone
from io import StringIO
from pathlib import Path
import json
import tempfile
import zipfile
from .models import Appeal, Product, Return, ReturnPhoto, SiteConfiguration


class FullBackupImportForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo backup ZIP',
        help_text='Sube un backup .zip generado desde esta misma herramienta.',
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith('.zip'):
            raise forms.ValidationError('Sube un archivo .zip de backup.')
        return archivo


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fields = ['timezone', 'actualizado_en']
    readonly_fields = ['actualizado_en']
    change_list_template = 'admin/returns/siteconfiguration/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'backup/',
                self.admin_site.admin_view(self.backup_view),
                name='returns_full_backup',
            ),
            path(
                'backup/exportar/',
                self.admin_site.admin_view(self.export_backup_view),
                name='returns_full_backup_export',
            ),
            path(
                'limpiar-datos/',
                self.admin_site.admin_view(self.clear_work_data_view),
                name='returns_clear_work_data',
            ),
        ]
        return custom_urls + urls

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def backup_view(self, request):
        if request.method == 'POST':
            form = FullBackupImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    self.import_backup(form.cleaned_data['archivo'])
                except (KeyError, ValueError, zipfile.BadZipFile) as error:
                    self.message_user(request, f'No se pudo importar el backup: {error}', level='ERROR')
                    return redirect('admin:returns_full_backup')

                self.message_user(request, 'Backup importado correctamente.')
                return redirect('admin:returns_full_backup')
        else:
            form = FullBackupImportForm()

        return render(
            request,
            'admin/returns/siteconfiguration/backup.html',
            {
                'form': form,
                'title': 'Backup completo',
                'opts': self.model._meta,
            },
        )

    def export_backup_view(self, request):
        timestamp = timezone.localtime().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="backup_devoluciones_{timestamp}.zip"'

        data_output = StringIO()
        call_command(
            'dumpdata',
            'auth.User',
            'auth.Group',
            'returns',
            format='json',
            indent=2,
            stdout=data_output,
        )
        manifest = {
            'created_at': timezone.localtime().isoformat(),
            'format': 'devoluciones-full-backup-v1',
            'contains': ['data.json', 'media/'],
        }

        media_root = Path(settings.MEDIA_ROOT)
        with zipfile.ZipFile(response, mode='w', compression=zipfile.ZIP_DEFLATED) as backup_zip:
            backup_zip.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            backup_zip.writestr('data.json', data_output.getvalue())
            if media_root.exists():
                for path in media_root.rglob('*'):
                    if path.is_file():
                        backup_zip.write(path, Path('media') / path.relative_to(media_root))

        return response

    def import_backup(self, archivo):
        media_root = Path(settings.MEDIA_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(archivo) as backup_zip:
                names = backup_zip.namelist()
                if 'data.json' not in names:
                    raise ValueError('el ZIP no contiene data.json')

                for member in names:
                    target = temp_path / member
                    if not str(target.resolve()).startswith(str(temp_path.resolve())):
                        raise ValueError('el ZIP contiene rutas no permitidas')
                backup_zip.extractall(temp_path)

            call_command('loaddata', str(temp_path / 'data.json'))

            extracted_media = temp_path / 'media'
            if extracted_media.exists():
                media_root.mkdir(parents=True, exist_ok=True)
                for source in extracted_media.rglob('*'):
                    if source.is_file():
                        target = media_root / source.relative_to(extracted_media)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(source.read_bytes())

    def clear_work_data_view(self, request):
        if request.method == 'POST':
            counts = {
                'devoluciones': Return.objects.count(),
                'apelaciones': Appeal.objects.count(),
                'fotos': ReturnPhoto.objects.count(),
            }
            Return.objects.all().delete()
            self.message_user(
                request,
                (
                    'Datos de trabajo eliminados: '
                    f"{counts['devoluciones']} devoluciones, "
                    f"{counts['apelaciones']} apelaciones, "
                    f"{counts['fotos']} fotos."
                ),
            )
            return redirect('admin:returns_siteconfiguration_changelist')

        return render(
            request,
            'admin/returns/siteconfiguration/clear_work_data.html',
            {
                'title': 'Eliminar datos de trabajo',
                'opts': self.model._meta,
                'returns_count': Return.objects.count(),
                'appeals_count': Appeal.objects.count(),
                'photos_count': ReturnPhoto.objects.count(),
                'products_count': Product.objects.count(),
            },
        )


class ProductImportForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel',
        help_text='Usa una planilla .xlsx con columnas: sku, nombre, ean, marca, categoria.',
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Sube un archivo Excel con extension .xlsx.')
        return archivo


def clean_excel_value(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'nombre', 'ean', 'marca', 'categoria', 'actualizado_en']
    search_fields = ['sku', 'nombre', 'ean', 'marca', 'categoria']
    list_filter = ['marca', 'categoria']
    readonly_fields = ['creado_en', 'actualizado_en']
    change_list_template = 'admin/returns/product/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'importar-excel/',
                self.admin_site.admin_view(self.import_excel_view),
                name='returns_product_import_excel',
            ),
            path(
                'plantilla-excel/',
                self.admin_site.admin_view(self.download_excel_template_view),
                name='returns_product_excel_template',
            ),
        ]
        return custom_urls + urls

    def download_excel_template_view(self, request):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            self.message_user(
                request,
                'Para descargar la plantilla instala openpyxl: pip install openpyxl',
                level='ERROR',
            )
            return redirect('admin:returns_product_changelist')

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Productos'
        sheet.append(['sku', 'nombre', 'ean', 'marca', 'categoria'])
        sheet.append(['SKU-12345', 'Nombre del producto', '7800000000000', 'Marca ejemplo', 'Categoría ejemplo'])

        header_fill = PatternFill(fill_type='solid', fgColor='D9EAF7')
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = header_fill

        sheet.column_dimensions['A'].width = 18
        sheet.column_dimensions['B'].width = 38
        sheet.column_dimensions['C'].width = 18
        sheet.column_dimensions['D'].width = 22
        sheet.column_dimensions['E'].width = 24
        sheet.freeze_panes = 'A2'

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_productos.xlsx"'
        workbook.save(response)
        return response

    def import_excel_view(self, request):
        if request.method == 'POST':
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    from openpyxl import load_workbook
                except ImportError:
                    self.message_user(
                        request,
                        'Para importar Excel instala openpyxl: pip install openpyxl',
                        level='ERROR',
                    )
                    return redirect('admin:returns_product_changelist')

                workbook = load_workbook(form.cleaned_data['archivo'], read_only=True, data_only=True)
                sheet = workbook.active
                rows = sheet.iter_rows(values_only=True)
                headers = next(rows, None)

                if not headers:
                    self.message_user(request, 'El archivo no tiene encabezados.', level='ERROR')
                    return redirect('admin:returns_product_import_excel')

                header_map = {
                    clean_excel_value(header).lower().replace(' ', '_'): index
                    for index, header in enumerate(headers)
                }
                sku_index = header_map.get('sku')
                nombre_index = (
                    header_map.get('nombre')
                    if 'nombre' in header_map
                    else header_map.get(
                        'nombre_del_producto',
                        header_map.get('nombre_producto', header_map.get('producto')),
                    )
                )
                ean_index = header_map.get('ean')
                marca_index = header_map.get('marca')
                categoria_index = header_map.get('categoria', header_map.get('categoría'))

                if sku_index is None or nombre_index is None:
                    self.message_user(
                        request,
                        'El Excel debe incluir al menos las columnas "sku" y "nombre".',
                        level='ERROR',
                    )
                    return redirect('admin:returns_product_import_excel')

                created_count = 0
                updated_count = 0
                skipped_count = 0

                for row in rows:
                    sku = clean_excel_value(row[sku_index] if sku_index < len(row) else '')
                    nombre = clean_excel_value(row[nombre_index] if nombre_index < len(row) else '')
                    ean = clean_excel_value(row[ean_index] if ean_index is not None and ean_index < len(row) else '')
                    marca = clean_excel_value(row[marca_index] if marca_index is not None and marca_index < len(row) else '')
                    categoria = clean_excel_value(row[categoria_index] if categoria_index is not None and categoria_index < len(row) else '')

                    if not sku or not nombre:
                        skipped_count += 1
                        continue

                    _, created = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'nombre': nombre,
                            'ean': ean,
                            'marca': marca,
                            'categoria': categoria,
                        },
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                self.message_user(
                    request,
                    f'Importación lista: {created_count} creados, {updated_count} actualizados, {skipped_count} omitidos.',
                )
                workbook.close()
                return redirect('admin:returns_product_changelist')
        else:
            form = ProductImportForm()

        return render(
            request,
            'admin/returns/product/import_excel.html',
            {
                'form': form,
                'title': 'Importar productos desde Excel',
                'opts': self.model._meta,
            },
        )


class ReturnPhotoInline(admin.TabularInline):
    model = ReturnPhoto
    extra = 0


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero_orden', 'seller_display', 'sku', 'ean', 'producto_nombre', 'marca', 'categoria', 'cantidad', 'precio_venta', 'estado', 'condicion_producto', 'grado', 'fecha_ingreso', 'creado_por']
    list_filter = ['seller', 'estado', 'condicion_producto', 'grado', 'marca', 'categoria', 'fecha_ingreso']
    search_fields = ['numero_orden', 'seller', 'sku', 'ean', 'producto_nombre', 'marca', 'categoria']
    inlines = [ReturnPhotoInline]
    readonly_fields = ['estado', 'grado', 'fecha_ingreso', 'fecha_actualizacion', 'creado_por']

    @admin.display(description='Seller', ordering='seller')
    def seller_display(self, obj):
        return obj.get_seller_display()


@admin.register(ReturnPhoto)
class ReturnPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'devolucion', 'descripcion', 'subida_en']


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero_apelacion', 'orden_display', 'status', 'estado_cuenta', 'creado_en', 'creado_por', 'actualizado_en', 'actualizado_por']
    list_filter = ['status', 'creado_en']
    search_fields = ['numero_apelacion', 'devolucion__numero_orden', 'devolucion__sku', 'devolucion__producto_nombre', 'estado_cuenta']
    readonly_fields = ['creado_en', 'actualizado_en', 'creado_por', 'actualizado_por']

    @admin.display(description='Orden', ordering='devolucion__numero_orden')
    def orden_display(self, obj):
        return obj.devolucion.numero_orden
