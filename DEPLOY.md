# Despliegue en servidor

Esta plataforma es una aplicacion Django para gestionar devoluciones, apelaciones, reportes, exportacion Excel y usuarios.

## Opcion recomendada

Usar un VPS Ubuntu con:

- Python 3
- Gunicorn
- Nginx
- SQLite para una instalacion simple o PostgreSQL para produccion con mas usuarios

## 1. Preparar el servidor

```bash
sudo apt update
sudo apt install python3-venv python3-pip nginx git
```

## 2. Clonar el proyecto

```bash
cd /var/www
sudo git clone https://github.com/bpbdiel/plataforma-devoluciones.git
sudo chown -R $USER:$USER plataforma-devoluciones
cd plataforma-devoluciones
```

Si el repositorio tiene la carpeta `devoluciones` como raiz del proyecto Django:

```bash
cd devoluciones
```

## 3. Crear entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Cambia:

```env
DJANGO_SECRET_KEY=una-clave-larga-y-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.cl,www.tu-dominio.cl,IP_DEL_SERVIDOR
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.cl,https://www.tu-dominio.cl
```

## 5. Migraciones y archivos estaticos

```bash
source .venv/bin/activate
set -a
source .env
set +a
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

## 6. Probar Gunicorn

```bash
gunicorn devoluciones.wsgi:application --bind 127.0.0.1:8000
```

Luego detente con `Ctrl+C`.

## 7. Crear servicio systemd

```bash
sudo nano /etc/systemd/system/devoluciones.service
```

Contenido:

```ini
[Unit]
Description=Plataforma de devoluciones
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/plataforma-devoluciones/devoluciones
EnvironmentFile=/var/www/plataforma-devoluciones/devoluciones/.env
ExecStart=/var/www/plataforma-devoluciones/devoluciones/.venv/bin/gunicorn devoluciones.wsgi:application --workers 3 --bind unix:/run/devoluciones.sock

[Install]
WantedBy=multi-user.target
```

Permisos:

```bash
sudo chown -R www-data:www-data /var/www/plataforma-devoluciones
sudo systemctl daemon-reload
sudo systemctl enable devoluciones
sudo systemctl start devoluciones
sudo systemctl status devoluciones
```

## 8. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/devoluciones
```

Contenido:

```nginx
server {
    listen 80;
    server_name tu-dominio.cl www.tu-dominio.cl IP_DEL_SERVIDOR;

    location /static/ {
        alias /var/www/plataforma-devoluciones/devoluciones/staticfiles/;
    }

    location /media/ {
        alias /var/www/plataforma-devoluciones/devoluciones/media/;
    }

    location / {
        proxy_pass http://unix:/run/devoluciones.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar:

```bash
sudo ln -s /etc/nginx/sites-available/devoluciones /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 9. HTTPS

Con dominio apuntando al servidor:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.cl -d www.tu-dominio.cl
```

## 10. Actualizar despues de cambios

```bash
cd /var/www/plataforma-devoluciones/devoluciones
sudo -u www-data git pull
sudo -u www-data .venv/bin/pip install -r requirements.txt
sudo -u www-data bash -c "set -a && source .env && set +a && .venv/bin/python manage.py migrate && .venv/bin/python manage.py collectstatic --noinput"
sudo systemctl restart devoluciones
```

## Notas importantes

- No subas `.env` a GitHub.
- Haz respaldo de `db.sqlite3` si usas SQLite.
- Para muchos usuarios, conviene migrar a PostgreSQL.
- `media/` contiene archivos subidos; respaldalo tambien.
