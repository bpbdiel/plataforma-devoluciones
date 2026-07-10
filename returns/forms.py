from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Appeal, Return, UserProfile


class ReturnForm(forms.ModelForm):
    sub_danos = forms.MultipleChoiceField(
        label='Sub daños',
        choices=Return.SUB_DANO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Return
        fields = [
            'seller',
            'numero_orden',
            'sku',
            'ean',
            'producto_nombre',
            'marca',
            'categoria',
            'precio_venta',
            'cantidad',
            'ingresado_bodega',
            'condicion_producto',
            'grado',
            'sub_danos',
            'detalles_dano',
        ]
        widgets = {
            'seller': forms.Select(attrs={'class': 'form-select'}),
            'numero_orden': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: ORD-2024-001'}),
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: SKU-12345'}),
            'ean': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 7800000000000'}),
            'producto_nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre del producto'}),
            'marca': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Marca'}),
            'categoria': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Categoría'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-input money-field', 'placeholder': '0', 'min': '0', 'step': '1', 'inputmode': 'numeric'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'step': '1'}),
            'ingresado_bodega': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'condicion_producto': forms.Select(attrs={'class': 'form-select'}),
            'grado': forms.Select(attrs={'class': 'form-select'}),
            'detalles_dano': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Describe el daño o motivo de devolución...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        condicion = self.data.get(self.add_prefix('condicion_producto')) if self.is_bound else self.initial.get('condicion_producto')
        if not condicion and self.instance and self.instance.pk:
            condicion = self.instance.condicion_producto
        grado = Return.grado_for_condicion(condicion or 'nuevo')
        self.fields['grado'].initial = grado
        self.fields['grado'].disabled = True
        self.fields['grado'].widget.attrs['data-grado-producto'] = ''
        if not self.is_bound and self.instance and self.instance.pk:
            self.fields['sub_danos'].initial = self.instance.sub_danos or []

    def save(self, commit=True):
        is_new = self.instance.pk is None
        instance = super().save(commit=False)
        if is_new:
            instance.estado = 'recibido'
        instance.grado = Return.grado_for_condicion(instance.condicion_producto)
        instance.sub_danos = self.cleaned_data.get('sub_danos', [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PlatformUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nombre',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre'}),
    )
    last_name = forms.CharField(
        label='Apellido',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apellido'}),
    )
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@empresa.cl'}),
    )
    is_staff = forms.BooleanField(
        label='Usuario administrador',
        required=False,
        help_text='Permite crear usuarios y acceder al panel de administración de plataforma.',
    )
    force_password_change = forms.BooleanField(
        label='Solicitar cambio de contraseña',
        required=False,
        initial=True,
        help_text='El usuario deberá cambiar su contraseña al iniciar sesión.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'is_staff', 'force_password_change']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirmar contraseña'})

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.force_password_change = self.cleaned_data.get('force_password_change', False)
            profile.save(update_fields=['force_password_change'])
        return user


class PlatformUserUpdateForm(forms.ModelForm):
    is_staff = forms.BooleanField(
        label='Usuario administrador',
        required=False,
    )
    is_active = forms.BooleanField(
        label='Usuario activo',
        required=False,
    )
    force_password_change = forms.BooleanField(
        label='Solicitar cambio de contraseña',
        required=False,
        help_text='El usuario deberá cambiar su contraseña al iniciar sesión.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'force_password_change']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@empresa.cl'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            profile, _ = UserProfile.objects.get_or_create(user=self.instance)
            self.fields['force_password_change'].initial = profile.force_password_change

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.force_password_change = self.cleaned_data.get('force_password_change', False)
            profile.save(update_fields=['force_password_change'])
        return user


class PlatformPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Contraseña actual'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Nueva contraseña'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirmar nueva contraseña'})


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(file, initial) for file in files]


class ReturnPhotoUploadForm(forms.Form):
    fotos = MultipleImageField(
        label='Fotos',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-file',
            'accept': 'image/*',
            'multiple': True,
        }),
    )


class AppealForm(forms.ModelForm):
    devolucion = forms.ModelChoiceField(
        label='Devolución',
        queryset=Return.objects.none(),
        empty_label='Selecciona una devolución sin apelación',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Appeal
        fields = [
            'devolucion',
            'numero_apelacion',
            'detalle',
            'status',
            'estado_cuenta',
        ]
        widgets = {
            'numero_apelacion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'N° de apelación o ticket'}),
            'detalle': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Detalle del seguimiento de la apelación...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'estado_cuenta': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Monto apelado en $ CLP', 'min': '0', 'step': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        devoluciones_disponibles = Return.objects.filter(apelaciones__isnull=True)
        if self.instance and self.instance.pk:
            devoluciones_disponibles = Return.objects.filter(
                Q(apelaciones__isnull=True) | Q(pk=self.instance.devolucion_id)
            ).distinct()
            self.fields['devolucion'].initial = self.instance.devolucion
        else:
            self.fields['status'].choices = [('en_proceso', 'En proceso')]
            self.fields['status'].initial = 'en_proceso'
            self.fields['status'].disabled = True
            self.fields['estado_cuenta'].required = True
        self.fields['devolucion'].queryset = devoluciones_disponibles.order_by('-fecha_ingreso', '-id')
        self.fields['devolucion'].label_from_instance = self.label_devolucion

    @staticmethod
    def label_devolucion(devolucion):
        producto = devolucion.producto_nombre or 'Sin nombre'
        return f'{devolucion.numero_orden} - {devolucion.sku} - {producto}'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.pk is None:
            instance.status = 'en_proceso'
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def clean_estado_cuenta(self):
        estado_cuenta = self.cleaned_data.get('estado_cuenta', '').strip()
        if not estado_cuenta:
            return ''
        if not estado_cuenta.isdigit():
            raise forms.ValidationError('Ingresa un monto válido en pesos chilenos.')
        return estado_cuenta
