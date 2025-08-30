"""
Tareas de Celery para CotizaBelleza
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from core.models import (
    AlertaPrecioProductoPersistente, 
    PrecioHistorico, 
    MailLog,
    ProductoPersistente
)
from core.services.email_service import EmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_price_alerts(self):
    """
    Tarea 1: Revisar alertas de precio con histórico (1 semana)
    """
    try:
        logger.info("Iniciando revisión de alertas de precio con histórico...")
        
        # Obtener alertas activas dentro del período de 1 semana
        alertas_activas = AlertaPrecioProductoPersistente.objects.filter(
            activa=True
        ).filter(
            fecha_fin__gte=timezone.now()  # Solo alertas que no han expirado
        ).select_related('producto')
        
        logger.info(f"Encontradas {alertas_activas.count()} alertas activas dentro del período")
        
        alertas_procesadas = 0
        
        for alerta in alertas_activas:
            try:
                # Obtener el precio más reciente del producto
                precio_actual = PrecioHistorico.objects.filter(
                    producto=alerta.producto,
                    disponible=True
                ).order_by('-fecha_scraping').first()
                
                if not precio_actual:
                    logger.warning(f"No hay precio actual para producto {alerta.producto.internal_id}")
                    continue
                
                # Comparar con precio inicial
                if alerta.precio_inicial:
                    cambio = comparar_precios_historicos(alerta.precio_inicial, float(precio_actual.precio))
                    
                    # Enviar notificación si hay cambio significativo
                    if cambio['tipo'] != 'sin_cambio':
                        # Verificar si ya se notificó recientemente (evitar spam)
                        if not alerta.notificada or (
                            alerta.fecha_ultima_notificacion and 
                            (timezone.now() - alerta.fecha_ultima_notificacion).total_seconds() > 3600  # 1 hora
                        ):
                            # Disparar tarea de envío de email histórico
                            send_historical_alert_email.delay(
                                alerta_id=alerta.id,
                                cambio=cambio,
                                precio_actual=float(precio_actual.precio),
                                tienda_url=precio_actual.url_producto
                            )
                            alertas_procesadas += 1
                            logger.info(f"Alerta histórica disparada: {alerta.producto.nombre_original} - {cambio['tipo']}")
                
            except Exception as e:
                logger.error(f"Error procesando alerta {alerta.id}: {e}")
                continue
        
        # Desactivar alertas expiradas
        desactivar_alertas_expiradas.delay()
        
        logger.info(f"Revisión completada. {alertas_procesadas} alertas procesadas")
        return {
            'status': 'success',
            'alertas_revisadas': alertas_activas.count(),
            'alertas_procesadas': alertas_procesadas
        }
        
    except Exception as e:
        logger.error(f"Error en check_price_alerts: {e}")
        raise self.retry(countdown=60, exc=e)


def comparar_precios_historicos(precio_inicial, precio_actual, tolerancia=0.01):
    """
    Compara precios y determina el tipo de cambio
    """
    diferencia = abs(precio_actual - precio_inicial)
    porcentaje = ((precio_actual - precio_inicial) / precio_inicial) * 100
    
    if diferencia <= tolerancia:
        return {
            'tipo': 'sin_cambio',
            'precio_inicial': precio_inicial,
            'precio_actual': precio_actual,
            'diferencia': 0,
            'porcentaje': 0
        }
    elif precio_actual > precio_inicial:
        return {
            'tipo': 'subio',
            'precio_inicial': precio_inicial,
            'precio_actual': precio_actual,
            'diferencia': precio_actual - precio_inicial,
            'porcentaje': porcentaje
        }
    else:
        return {
            'tipo': 'bajo',
            'precio_inicial': precio_inicial,
            'precio_actual': precio_actual,
            'diferencia': precio_inicial - precio_actual,
            'porcentaje': abs(porcentaje)
        }


@shared_task(bind=True, max_retries=3)
def send_historical_alert_email(self, alerta_id, cambio, precio_actual, tienda_url=None):
    """
    Tarea 2: Enviar email de alerta histórica (subió/bajó/mantuvo)
    """
    try:
        with transaction.atomic():
            # Obtener la alerta
            alerta = AlertaPrecioProductoPersistente.objects.select_related(
                'producto'
            ).get(id=alerta_id)
            
            # Verificar que no se haya enviado recientemente
            if alerta.notificada and alerta.fecha_ultima_notificacion:
                tiempo_desde_ultima = (timezone.now() - alerta.fecha_ultima_notificacion).total_seconds()
                if tiempo_desde_ultima < 3600:  # 1 hora
                    logger.info(f"Email ya enviado recientemente para alerta {alerta_id}")
                    return {'status': 'skipped', 'reason': 'recently_sent'}
            
            # Determinar tipo de email según el cambio
            if cambio['tipo'] == 'subio':
                tipo_email = 'price_increased'
                asunto = f"📈 Precio Subió - {alerta.producto.nombre_original}"
            elif cambio['tipo'] == 'bajo':
                tipo_email = 'price_decreased'
                asunto = f"📉 Precio Bajó - {alerta.producto.nombre_original}"
            else:
                return {'status': 'skipped', 'reason': 'no_change'}
            
            # Enviar email usando el servicio
            success = EmailService.send_historical_alert_email(
                alerta=alerta,
                cambio=cambio,
                asunto=asunto,
                tipo_email=tipo_email,
                tienda_url=tienda_url
            )
            
            if success:
                # Actualizar estado de la alerta
                alerta.notificada = True
                alerta.fecha_ultima_notificacion = timezone.now()
                alerta.ultima_revision = timezone.now()
                alerta.notificaciones_enviadas += 1
                alerta.save()
                
                logger.info(f"Email histórico enviado: {alerta.producto.nombre_original} - {cambio['tipo']}")
                return {'status': 'success', 'tipo': cambio['tipo']}
            else:
                logger.error(f"Error enviando email histórico para alerta {alerta_id}")
                return {'status': 'error', 'reason': 'email_failed'}
                
    except AlertaPrecioProductoPersistente.DoesNotExist:
        logger.error(f"Alerta {alerta_id} no encontrada")
        return {'status': 'error', 'reason': 'alert_not_found'}
    except Exception as e:
        logger.error(f"Error en send_historical_alert_email: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def send_price_alert_email(self, alerta_id, precio_actual, precio_anterior=None, 
                          tipo_cambio=None, porcentaje_cambio=None, monto_cambio=None, 
                          tienda_url=None):
    """
    Tarea 2: Enviar email de alerta de precio con información del cambio
    """
    try:
        with transaction.atomic():
            # Obtener la alerta
            alerta = AlertaPrecioProductoPersistente.objects.select_related(
                'producto', 'usuario'
            ).get(id=alerta_id)
            
            # Verificar que no se haya enviado recientemente
            if alerta.notificada and alerta.fecha_ultima_notificacion:
                tiempo_desde_ultima = (timezone.now() - alerta.fecha_ultima_notificacion).total_seconds()
                if tiempo_desde_ultima < 3600:  # 1 hora
                    logger.info(f"Email ya enviado recientemente para alerta {alerta_id}")
                    return {'status': 'skipped', 'reason': 'recently_sent'}
            
            # Enviar email
            success = EmailService.send_price_alert_email(
                alert=alerta,
                precio_actual=precio_actual,
                precio_anterior=precio_anterior,
                tipo_cambio=tipo_cambio,
                porcentaje_cambio=porcentaje_cambio,
                monto_cambio=monto_cambio,
                tienda_url=tienda_url
            )
            
            if success:
                logger.info(f"Email enviado exitosamente para alerta {alerta_id}")
                return {'status': 'success', 'alerta_id': alerta_id}
            else:
                logger.error(f"Error enviando email para alerta {alerta_id}")
                raise Exception("Error enviando email")
                
    except AlertaPrecioProductoPersistente.DoesNotExist:
        logger.error(f"Alerta {alerta_id} no encontrada")
        return {'status': 'error', 'reason': 'alert_not_found'}
    except Exception as e:
        logger.error(f"Error en send_price_alert_email: {e}")
        raise self.retry(countdown=300, exc=e)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def send_pending_emails(self):
    """
    Tarea 3: Enviar emails pendientes (fallback)
    """
    try:
        # Obtener emails pendientes
        emails_pendientes = MailLog.objects.filter(
            status='pending'
        ).select_related('alerta', 'producto', 'usuario')
        
        logger.info(f"Encontrados {emails_pendientes.count()} emails pendientes")
        
        enviados = 0
        fallidos = 0
        
        for mail_log in emails_pendientes:
            try:
                # Verificar que la alerta aún existe y está activa
                if not mail_log.alerta.activa:
                    mail_log.status = 'cancelled'
                    mail_log.save()
                    continue
                
                # Reintentar envío
                success = EmailService.send_price_alert_email(
                    alert=mail_log.alerta,
                    precio_actual=mail_log.precio_actual,
                    tienda_url=mail_log.tienda_url
                )
                
                if success:
                    enviados += 1
                else:
                    fallidos += 1
                    mail_log.retry_count += 1
                    if mail_log.retry_count >= 3:
                        mail_log.status = 'failed'
                    mail_log.save()
                    
            except Exception as e:
                logger.error(f"Error procesando mail_log {mail_log.id}: {e}")
                fallidos += 1
                continue
        
        logger.info(f"Procesamiento completado: {enviados} enviados, {fallidos} fallidos")
        return {
            'status': 'success',
            'enviados': enviados,
            'fallidos': fallidos
        }
        
    except Exception as e:
        logger.error(f"Error en send_pending_emails: {e}")
        raise self.retry(countdown=300, exc=e)


@shared_task
def cleanup_old_mail_logs():
    """
    Tarea de limpieza: Eliminar logs de email antiguos
    """
    try:
        from datetime import timedelta
        
        # Eliminar logs de más de 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        logs_eliminados = MailLog.objects.filter(
            sent_at__lt=fecha_limite
        ).delete()[0]
        
        logger.info(f"Limpieza completada: {logs_eliminados} logs eliminados")
        return {'status': 'success', 'logs_eliminados': logs_eliminados}
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_mail_logs: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def reset_notified_alerts():
    """
    Tarea para resetear alertas notificadas (ejecutar diariamente)
    Permite que las alertas se vuelvan a disparar si el precio sigue bajo
    """
    try:
        from datetime import timedelta
        
        # Resetear alertas notificadas de hace más de 24 horas
        fecha_limite = timezone.now() - timedelta(hours=24)
        alertas_reseteadas = AlertaPrecioProductoPersistente.objects.filter(
            notificada=True,
            fecha_ultima_notificacion__lt=fecha_limite
        ).update(notificada=False)
        
        logger.info(f"Reset completado: {alertas_reseteadas} alertas reseteadas")
        return {'status': 'success', 'alertas_reseteadas': alertas_reseteadas}
        
    except Exception as e:
        logger.error(f"Error en reset_notified_alerts: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id, dashboard_url=None, catalog_url=None, help_url=None):
    """
    Tarea para enviar email de bienvenida
    """
    try:
        from django.contrib.auth import get_user_model
        from core.services.email_service import EmailService
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Enviar email de bienvenida
        success = EmailService.send_welcome_email(
            user=user,
            dashboard_url=dashboard_url,
            catalog_url=catalog_url,
            help_url=help_url
        )
        
        if success:
            logger.info(f"Email de bienvenida enviado exitosamente para usuario {user_id}")
            return {'status': 'success', 'user_id': user_id}
        else:
            logger.error(f"Error enviando email de bienvenida para usuario {user_id}")
            raise Exception("Error enviando email de bienvenida")
            
    except User.DoesNotExist:
        logger.error(f"Usuario {user_id} no encontrado")
        return {'status': 'error', 'reason': 'user_not_found'}
    except Exception as e:
        logger.error(f"Error en send_welcome_email_task: {e}")
        raise self.retry(countdown=300, exc=e)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def desactivar_alertas_expiradas(self):
    """
    Tarea: Desactivar alertas que han expirado (más de 1 semana)
    """
    try:
        logger.info("Revisando alertas expiradas...")
        
        # Obtener alertas que han expirado
        alertas_expiradas = AlertaPrecioProductoPersistente.objects.filter(
            activa=True,
            fecha_fin__lt=timezone.now()  # Fecha de fin ya pasó
        ).select_related('producto')
        
        alertas_desactivadas = 0
        
        for alerta in alertas_expiradas:
            try:
                # Desactivar alerta
                alerta.activa = False
                alerta.save()
                
                # Enviar email de expiración
                send_alert_expired_email.delay(alerta.id)
                
                alertas_desactivadas += 1
                logger.info(f"Alerta expirada desactivada: {alerta.producto.nombre_original}")
                
            except Exception as e:
                logger.error(f"Error desactivando alerta {alerta.id}: {e}")
                continue
        
        logger.info(f"Desactivadas {alertas_desactivadas} alertas expiradas")
        return {
            'status': 'success',
            'alertas_desactivadas': alertas_desactivadas
        }
        
    except Exception as e:
        logger.error(f"Error en desactivar_alertas_expiradas: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def send_alert_expired_email(self, alerta_id):
    """
    Tarea: Enviar email cuando la alerta expira
    """
    try:
        with transaction.atomic():
            # Obtener la alerta
            alerta = AlertaPrecioProductoPersistente.objects.select_related(
                'producto'
            ).get(id=alerta_id)
            
            # Obtener precio final
            precio_final = PrecioHistorico.objects.filter(
                producto=alerta.producto,
                disponible=True
            ).order_by('-fecha_scraping').first()
            
            # Enviar email de expiración
            success = EmailService.send_alert_expired_email(
                alerta=alerta,
                precio_final=float(precio_final.precio) if precio_final else None
            )
            
            if success:
                logger.info(f"Email de expiración enviado para alerta {alerta_id}")
                return {'status': 'success'}
            else:
                logger.error(f"Error enviando email de expiración para alerta {alerta_id}")
                return {'status': 'error', 'reason': 'email_failed'}
                
    except AlertaPrecioProductoPersistente.DoesNotExist:
        logger.error(f"Alerta {alerta_id} no encontrada")
        return {'status': 'error', 'reason': 'alert_not_found'}
    except Exception as e:
        logger.error(f"Error en send_alert_expired_email: {e}")
        raise self.retry(countdown=60, exc=e)
