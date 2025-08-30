"""
Comando para limpiar verificaciones de email expiradas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import EmailVerification, EmailBounce


class Command(BaseCommand):
    help = 'Limpia verificaciones de email expiradas y bounces antiguos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Días para considerar verificaciones como expiradas (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin hacer cambios'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Limpiar verificaciones expiradas
        expired_verifications = EmailVerification.objects.filter(
            expires_at__lt=timezone.now(),
            verified=False
        )
        
        # Limpiar bounces antiguos
        old_bounces = EmailBounce.objects.filter(
            occurred_at__lt=cutoff_date,
            processed=True
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN - No se realizarán cambios')
            )
            self.stdout.write(
                f'Verificaciones expiradas a eliminar: {expired_verifications.count()}'
            )
            self.stdout.write(
                f'Bounces antiguos a eliminar: {old_bounces.count()}'
            )
        else:
            # Eliminar verificaciones expiradas
            expired_count = expired_verifications.count()
            expired_verifications.delete()
            
            # Eliminar bounces antiguos
            bounce_count = old_bounces.count()
            old_bounces.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Limpieza completada: {expired_count} verificaciones y {bounce_count} bounces eliminados'
                )
            )


