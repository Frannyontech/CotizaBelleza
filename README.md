# CotizaBelleza

Proyecto Django para sistema de cotizaciones de belleza.

## Requisitos

- Python 3.13+
- Django 5.2.4

## Instalación

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd CotizaBelleza
```

2. Instala las dependencias:
```bash
py -m pip install -r requirements.txt
```

3. Ejecuta las migraciones:
```bash
py manage.py migrate
```

4. Crea un superusuario (opcional):
```bash
py manage.py createsuperuser
```

5. Ejecuta el servidor de desarrollo:
```bash
py manage.py runserver
```

El proyecto estará disponible en `http://127.0.0.1:8000/`

## Estructura del Proyecto

- `cotizabelleza/` - Configuración principal del proyecto
- `core/` - App principal del proyecto
- `manage.py` - Script de administración de Django

## Apps

- **core**: App principal que contiene la funcionalidad base del sistema 