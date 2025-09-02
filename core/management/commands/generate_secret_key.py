"""
Comando para generar clave secreta para encriptación de emails
"""
from django.core.management.base import BaseCommand
from utils.security import generate_secret_key


class Command(BaseCommand):
    help = 'Genera una nueva clave secreta para encriptación de emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-to-env',
            action='store_true',
            help='Guardar la clave en el archivo .env',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔐 Generando clave secreta para encriptación...')
        )

        # Generar nueva clave
        secret_key = generate_secret_key()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Clave secreta generada: {secret_key}')
        )
        
        self.stdout.write(
            self.style.WARNING('⚠️  IMPORTANTE: Guarda esta clave en tu archivo .env como EMAIL_SECRET_KEY')
        )
        
        if options['save_to_env']:
            self.save_to_env_file(secret_key)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Clave generada exitosamente')
        )

    def save_to_env_file(self, secret_key):
        """Guardar la clave en el archivo .env"""
        try:
            env_file_path = '.env'
            
            # Leer archivo .env actual
            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                content = ''
            
            # Buscar si ya existe EMAIL_SECRET_KEY
            lines = content.split('\n')
            key_found = False
            
            for i, line in enumerate(lines):
                if line.startswith('EMAIL_SECRET_KEY='):
                    lines[i] = f'EMAIL_SECRET_KEY={secret_key}'
                    key_found = True
                    break
            
            # Si no se encontró, agregar al final
            if not key_found:
                if content and not content.endswith('\n'):
                    content += '\n'
                content += f'EMAIL_SECRET_KEY={secret_key}\n'
            else:
                content = '\n'.join(lines)
            
            # Escribir archivo actualizado
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Clave guardada en {env_file_path}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error guardando en .env: {e}')
            )
            self.stdout.write(
                self.style.WARNING('⚠️  Guarda manualmente la clave en tu archivo .env')
            )







