# Despliegue en Coolify

Guia para desplegar la plataforma en Coolify usando Dockerfile.

Dominio de ejemplo:

```text
https://tuchi.bdiel.cloud
```

## 1. DNS

En tu proveedor DNS crea un registro `A`:

```text
tuchi.bdiel.cloud -> IP_DE_TU_SERVIDOR
```

Espera la propagacion y verifica:

```bash
ping tuchi.bdiel.cloud
```

## 2. Crear recurso en Coolify

1. Entra a Coolify.
2. Crea un nuevo **Project** o usa uno existente.
3. Selecciona **New Resource**.
4. Elige tu repositorio:

```text
https://github.com/bpbdiel/plataforma-devoluciones
```

5. Tipo de despliegue: **Dockerfile**.
6. Build context:

```text
devoluciones
```

Si en tu repositorio `manage.py`, `Dockerfile` y `requirements.txt` estan en la raiz, usa:

```text
.
```

En este proyecto actualmente estan dentro de la carpeta `devoluciones`.

## 3. Puerto

Configura el puerto de la aplicacion:

```text
8000
```

El Dockerfile tambien respeta la variable `PORT`, por lo que Coolify puede inyectarla automaticamente.

## 4. Dominio

En la seccion de dominios agrega:

```text
https://tuchi.bdiel.cloud
```

Coolify se encarga del proxy y HTTPS automaticamente.

## 5. Variables de entorno

Configura estas variables en Coolify:

```env
DJANGO_SECRET_KEY=pon-una-clave-larga-y-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuchi.bdiel.cloud
DJANGO_CSRF_TRUSTED_ORIGINS=https://tuchi.bdiel.cloud
DJANGO_TIME_ZONE=America/Santiago
DJANGO_SERVE_MEDIA=True
SQLITE_PATH=/app/data/db.sqlite3
DJANGO_MEDIA_ROOT=/app/media
DJANGO_STATIC_ROOT=/app/staticfiles
PORT=8000
GUNICORN_WORKERS=3
```

Para generar una clave segura:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 6. Volumenes persistentes

Agrega almacenamiento persistente en Coolify:

```text
/app/data
/app/media
```

Opcional:

```text
/app/staticfiles
```

Importante:

- `/app/data` guarda la base SQLite.
- `/app/media` guarda fotos y archivos subidos.
- Sin volumen persistente perderas datos al recrear el contenedor.

## 7. Healthcheck

La app expone:

```text
/health/
```

Respuesta esperada:

```text
ok
```

Puedes usarlo como healthcheck en Coolify si lo necesitas.

## 8. Primer deploy

Haz deploy desde Coolify.

El contenedor ejecuta automaticamente:

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

## 9. Crear usuario administrador

Despues del primer deploy, abre la terminal del contenedor en Coolify y ejecuta:

```bash
python manage.py createsuperuser
```

Luego entra en:

```text
https://tuchi.bdiel.cloud
```

## 10. Actualizaciones

Para actualizar:

1. Sube cambios a GitHub.
2. En Coolify ejecuta **Redeploy**.

Las migraciones y archivos estaticos se aplican automaticamente en cada arranque.

## 11. Notas

- Usa `DJANGO_DEBUG=False` en produccion.
- Mantiene `DJANGO_CSRF_TRUSTED_ORIGINS` con `https://`.
- Si cambias el dominio, actualiza `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Para muchos usuarios o datos criticos, considera migrar de SQLite a PostgreSQL.
