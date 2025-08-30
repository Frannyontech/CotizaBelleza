"""
Comando para generar clave secreta para encriptación de emails
"""
from django.core.management.base import BaseCommand
from utils.security import generate_secret_key


class Command(BaseCommand):
    help = 'Genera una nueva clave secreta para encriptación de emails'

    def handle(self, *args, **options):
        try:
            secret_key = generate_secret_key()
            
            self.stdout.write(
                self.style.SUCCESS(f'Clave secreta generada exitosamente')
            )
            self.stdout.write(
                self.style.WARNING('Agrega esta línea a tu archivo .env:')
            )
            self.stdout.write(f'EMAIL_SECRET_KEY={secret_key}')
            
            # También mostrar en settings.py
            self.stdout.write(
                self.style.WARNING('\nO agrega esta línea a settings.py:')
            )
            self.stdout.write(f'EMAIL_SECRET_KEY = "{secret_key}"')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generando clave secreta: {e}')
            )


