# Plataforma de Devoluciones

Sistema web desarrollado en Django para gestionar devoluciones de productos, apelaciones, reportes y usuarios internos.

La plataforma permite registrar devoluciones, clasificar el estado del producto, generar grados automaticos, hacer seguimiento de apelaciones, visualizar indicadores en dashboard y exportar reportes a Excel.

## Funcionalidades

- Dashboard con graficos de devoluciones por grado.
- Dashboard con estados de apelaciones.
- Total pagado de apelaciones en CLP.
- Registro y edicion de devoluciones.
- Estado del producto con grado automatico:
  - Nuevo = A
  - Caja Dañada = C
  - Dañado = D
  - Daño Estetico = C
- Seguimiento de apelaciones.
- Estados de apelacion:
  - En proceso
  - Rechazado
  - Proceso de pago
  - Pagado
- Monto de apelacion en pesos chilenos.
- Reporte filtrable con exportacion Excel.
- Administracion de usuarios.
- Tema claro y oscuro.

## Tecnologias

- Python
- Django 4.2
- SQLite
- HTML/CSS
- OpenPyXL para exportacion Excel
- Gunicorn para despliegue en servidor
- Nginx recomendado como proxy inverso

## Instalacion local

Clonar el repositorio:

```bash
git clone https://github.com/bpbdiel/plataforma-devoluciones.git
cd plataforma-devoluciones
```

Si el proyecto Django esta dentro de la carpeta `devoluciones`:

```bash
cd devoluciones
```

Crear entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Aplicar migraciones:

```bash
python manage.py migrate
```

Crear usuario administrador:

```bash
python manage.py createsuperuser
```

Levantar servidor local:

```bash
python manage.py runserver
```

Entrar en:

```text
http://127.0.0.1:8000/
```

## Variables de entorno

Para produccion, crear un archivo `.env` usando `.env.example` como base:

```bash
cp .env.example .env
```

Variables principales:

```env
DJANGO_SECRET_KEY=una-clave-larga-y-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.cl,www.tu-dominio.cl,IP_DEL_SERVIDOR
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.cl,https://www.tu-dominio.cl
```

## Despliegue

La guia completa para servidor esta en:

```text
DEPLOY.md
```

La configuracion recomendada es:

- VPS Ubuntu
- Gunicorn
- Nginx
- Certbot para HTTPS
- SQLite para uso simple o PostgreSQL para mayor escala

## Archivos importantes

- `manage.py`: comando principal de Django.
- `devoluciones/settings.py`: configuracion del proyecto.
- `returns/models.py`: modelos de devoluciones, fotos y apelaciones.
- `returns/views.py`: vistas principales.
- `templates/returns/`: interfaces HTML.
- `requirements.txt`: dependencias.
- `DEPLOY.md`: instrucciones de despliegue.

## Notas de seguridad

- No subir `.env` a GitHub.
- No subir `db.sqlite3` si contiene datos reales.
- No subir la carpeta `media/` si contiene imagenes privadas.
- En produccion usar `DJANGO_DEBUG=False`.
- Cambiar siempre `DJANGO_SECRET_KEY`.

## Licencia

Proyecto privado para gestion interna de devoluciones.
