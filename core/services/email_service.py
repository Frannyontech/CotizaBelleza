"""
Servicio de email para CotizaBelleza
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from core.models import MailLog, EmailTemplate, EmailVerification, EmailPreference, EmailBounce
from utils.security import mask_email
import secrets
import hashlib

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para manejo de emails"""
    
    @staticmethod
    def create_email_verification(email):
        """
        Crea un token de verificación para un email
        
        Args:
            email (str): Email a verificar
            
        Returns:
            EmailVerification: Objeto de verificación creado
        """
        try:
            # Generar token único
            token = secrets.token_urlsafe(32)
            
            # Crear verificación
            verification = EmailVerification.objects.create(
                email=email,
                token=token,
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
            
            logger.info(f"Verificación creada para {mask_email(email)}")
            return verification
            
        except Exception as e:
            logger.error(f"Error creando verificación para {mask_email(email)}: {e}")
            return None
    
    @staticmethod
    def verify_email_token(token):
        """
        Verifica un token de email
        
        Args:
            token (str): Token a verificar
            
        Returns:
            tuple: (success, message, email)
        """
        try:
            verification = EmailVerification.objects.get(token=token)
            
            if verification.is_expired():
                return False, "Token expirado", None
            
            if verification.verified:
                return False, "Email ya verificado", None
            
            # Marcar como verificado
            verification.verify()
            
            # Crear preferencias por defecto
            EmailPreference.objects.get_or_create(
                email=verification.email,
                defaults={
                    'unsubscribe_token': secrets.token_urlsafe(32)
                }
            )
            
            logger.info(f"Email verificado: {mask_email(verification.email)}")
            return True, "Email verificado exitosamente", verification.email
            
        except EmailVerification.DoesNotExist:
            return False, "Token inválido", None
        except Exception as e:
            logger.error(f"Error verificando token: {e}")
            return False, "Error interno", None
    
    @staticmethod
    def send_verification_email(email):
        """
        Envía email de verificación
        
        Args:
            email (str): Email a verificar
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Crear verificación
            verification = EmailService.create_email_verification(email)
            if not verification:
                return False
            
            # Preparar contexto
            context = {
                'email': email,
                'verification_url': f"http://localhost:5173/verify-email?token={verification.token}",
                'expires_at': verification.expires_at.strftime('%d/%m/%Y %H:%M'),
            }
            
            # Renderizar templates
            html_message = render_to_string('emails/email_verification.html', context)
            text_message = render_to_string('emails/email_verification.txt', context)
            
            # Enviar email
            email_msg = EmailMultiAlternatives(
                subject='Verifica tu email - CotizaBelleza',
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            
            # Agregar headers de seguridad
            email_msg.extra_headers.update({
                'List-Unsubscribe': f'<mailto:unsubscribe@cotizabelleza.com?subject=unsubscribe_{email}>',
                'Precedence': 'bulk',
                'X-Auto-Response-Suppress': 'OOF, AutoReply',
            })
            
            email_msg.send()
            
            logger.info(f"Email de verificación enviado a {mask_email(email)}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de verificación a {mask_email(email)}: {e}")
            return False
    
    @staticmethod
    def check_email_preferences(email):
        """
        Verifica las preferencias de email de un usuario
        
        Args:
            email (str): Email a verificar
            
        Returns:
            tuple: (can_send, reason)
        """
        try:
            # Verificar si el email está verificado
            verification = EmailVerification.objects.filter(
                email=email, 
                verified=True
            ).first()
            
            if not verification:
                return False, "Email no verificado"
            
            # Verificar preferencias
            preference = EmailPreference.objects.filter(email=email).first()
            if not preference:
                return False, "Sin preferencias configuradas"
            
            if not preference.alerts_enabled:
                return False, "Alertas deshabilitadas"
            
            if not preference.can_send_email():
                return False, "Frecuencia de email no permitida"
            
            # Verificar bounces recientes
            recent_bounce = EmailBounce.objects.filter(
                email=email,
                bounce_type__in=['hard', 'spam'],
                occurred_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).first()
            
            if recent_bounce:
                return False, "Email con bounces recientes"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error verificando preferencias de {mask_email(email)}: {e}")
            return False, "Error interno"
    
    @staticmethod
    def record_bounce(email, bounce_type, reason=""):
        """
        Registra un bounce de email
        
        Args:
            email (str): Email que rebotó
            bounce_type (str): Tipo de bounce
            reason (str): Razón del bounce
        """
        try:
            EmailBounce.objects.create(
                email=email,
                bounce_type=bounce_type,
                bounce_reason=reason
            )
            
            # Si es hard bounce o spam, deshabilitar alertas
            if bounce_type in ['hard', 'spam']:
                EmailPreference.objects.filter(email=email).update(
                    alerts_enabled=False
                )
            
            logger.warning(f"Bounce registrado: {mask_email(email)} - {bounce_type}")
            
        except Exception as e:
            logger.error(f"Error registrando bounce: {e}")
    
    @staticmethod
    def unsubscribe_email(token):
        """
        Desuscribe un email usando token
        
        Args:
            token (str): Token de unsubscribe
            
        Returns:
            tuple: (success, message)
        """
        try:
            preference = EmailPreference.objects.get(unsubscribe_token=token)
            preference.alerts_enabled = False
            preference.save()
            
            # Registrar como unsubscribe
            EmailService.record_bounce(
                preference.email, 
                'unsubscribe', 
                'Usuario se desuscribió'
            )
            
            logger.info(f"Email desuscrito: {mask_email(preference.email)}")
            return True, "Email desuscrito exitosamente"
            
        except EmailPreference.DoesNotExist:
            return False, "Token de unsubscribe inválido"
        except Exception as e:
            logger.error(f"Error desuscribiendo email: {e}")
            return False, "Error interno"
    
    @staticmethod
    def send_price_alert_email(alert, precio_actual, precio_anterior=None, tipo_cambio=None, 
                              porcentaje_cambio=None, monto_cambio=None, tienda_url=None):
        """
        Envía email de alerta de precio con información del cambio
        
        Args:
            alert: AlertaPrecioProductoPersistente
            precio_actual: Precio actual del producto
            precio_anterior: Precio anterior del producto
            tipo_cambio: Tipo de cambio (increased, decreased, unchanged, new_price)
            porcentaje_cambio: Porcentaje de cambio
            monto_cambio: Monto del cambio
            tienda_url: URL de la tienda (opcional)
        """
        try:
            # Crear log de email
            mail_log = MailLog.objects.create(
                alerta=alert,
                producto=alert.producto,
                usuario=alert.usuario,
                user_email=alert.usuario.email,
                precio_actual=precio_actual,
                precio_inicial=alert.precio_inicial,
                tienda_url=tienda_url or '',
                status='pending'
            )
            
            # Preparar datos del email
            context = {
                'product_name': alert.producto.nombre_original,
                'product_brand': alert.producto.marca,
                'current_price': precio_actual,
                'previous_price': precio_anterior,
                'target_price': alert.precio_inicial,
                'price_difference': alert.precio_inicial - precio_actual,
                'change_type': tipo_cambio,
                'change_percentage': porcentaje_cambio,
                'change_amount': monto_cambio,
                'store_url': tienda_url,
                'user_name': alert.usuario.first_name or alert.usuario.username,
                'alert_id': alert.id,
                'product_id': alert.producto.internal_id,
            }
            
            # Obtener plantilla según el tipo de cambio
            template_name = EmailService._get_template_name_for_change(tipo_cambio)
            template = EmailTemplate.objects.filter(name=template_name, is_active=True).first()
            
            if template:
                subject = template.subject.format(product_name=context['product_name'])
                html_content = template.html_content
                text_content = template.text_content
            else:
                # Plantilla por defecto
                subject = EmailService._get_subject_for_change(tipo_cambio, context['product_name'])
                html_content = EmailService._get_default_html_template_for_change(tipo_cambio)
                text_content = EmailService._get_default_text_template_for_change(tipo_cambio)
            
            # Renderizar contenido
            html_message = render_to_string('emails/price_alert.html', context)
            text_message = render_to_string('emails/price_alert.txt', context)
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[alert.usuario.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            # Enviar
            email.send()
            
            # Actualizar log
            mail_log.status = 'sent'
            mail_log.save()
            
            # Marcar alerta como notificada
            alert.notificada = True
            alert.fecha_ultima_notificacion = timezone.now()
            alert.save()
            
            logger.info(f"Email enviado exitosamente: {alert.usuario.email} - {context['product_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            
            # Actualizar log con error
            if 'mail_log' in locals():
                mail_log.status = 'failed'
                mail_log.error_message = str(e)
                mail_log.save()
            
            return False
    
    @staticmethod
    def _get_template_name_for_change(tipo_cambio):
        """Obtiene el nombre de la plantilla según el tipo de cambio"""
        if tipo_cambio == 'decreased':
            return 'price_alert_decreased'
        elif tipo_cambio == 'increased':
            return 'price_alert_increased'
        elif tipo_cambio == 'new_price':
            return 'price_alert_new_price'
        else:
            return 'price_alert'
    
    @staticmethod
    def _get_subject_for_change(tipo_cambio, product_name):
        """Obtiene el asunto del email según el tipo de cambio"""
        if tipo_cambio == 'decreased':
            return f"¡Precio bajó! {product_name} 🎉"
        elif tipo_cambio == 'increased':
            return f"Precio subió: {product_name} ⚠️"
        elif tipo_cambio == 'new_price':
            return f"Nuevo precio disponible: {product_name} 📢"
        else:
            return f"Actualización de precio: {product_name}"
    
    @staticmethod
    def _get_default_html_template_for_change(tipo_cambio):
        """Plantilla HTML por defecto según el tipo de cambio"""
        if tipo_cambio == 'decreased':
            return EmailService._get_decreased_price_html_template()
        elif tipo_cambio == 'increased':
            return EmailService._get_increased_price_html_template()
        elif tipo_cambio == 'new_price':
            return EmailService._get_new_price_html_template()
        else:
            return EmailService._get_default_html_template()
    
    @staticmethod
    def _get_default_text_template_for_change(tipo_cambio):
        """Plantilla de texto por defecto según el tipo de cambio"""
        if tipo_cambio == 'decreased':
            return EmailService._get_decreased_price_text_template()
        elif tipo_cambio == 'increased':
            return EmailService._get_increased_price_text_template()
        elif tipo_cambio == 'new_price':
            return EmailService._get_new_price_text_template()
        else:
            return EmailService._get_default_text_template()
    
    @staticmethod
    def _get_default_html_template():
        """Plantilla HTML por defecto"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Alerta de Precio - CotizaBelleza</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e91e63;">¡Precio alcanzado! 🎉</h2>
                
                <p>Hola {{ user_name }},</p>
                
                <p>¡Excelentes noticias! El producto que estás monitoreando ha alcanzado tu precio objetivo.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{{ product_name }}</h3>
                    <p><strong>Marca:</strong> {{ product_brand }}</p>
                    <p><strong>Precio actual:</strong> <span style="color: #e91e63; font-size: 18px; font-weight: bold;">${{ current_price }}</span></p>
                    <p><strong>Tu precio objetivo:</strong> ${{ target_price }}</p>
                    <p><strong>Ahorro:</strong> <span style="color: #4caf50; font-weight: bold;">${{ price_difference }}</span></p>
                </div>
                
                {% if store_url %}
                <p style="text-align: center;">
                    <a href="{{ store_url }}" style="background-color: #e91e63; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ver Producto
                    </a>
                </p>
                {% endif %}
                
                <p>¡No pierdas esta oportunidad!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Este email fue enviado por CotizaBelleza.<br>
                    ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_default_text_template():
        """Plantilla de texto por defecto"""
        return """
¡Precio alcanzado! 🎉

Hola {{ user_name }},

¡Excelentes noticias! El producto que estás monitoreando ha alcanzado tu precio objetivo.

PRODUCTO: {{ product_name }}
MARCA: {{ product_brand }}
PRECIO ACTUAL: ${{ current_price }}
TU PRECIO OBJETIVO: ${{ target_price }}
AHORRO: ${{ price_difference }}

{% if store_url %}
Ver producto: {{ store_url }}
{% endif %}

¡No pierdas esta oportunidad!

---
Este email fue enviado por CotizaBelleza.
ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
        """
    
    @staticmethod
    def _get_decreased_price_html_template():
        """Plantilla HTML para precio que bajó"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>¡Precio bajó! - CotizaBelleza</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4caf50;">¡Precio bajó! 🎉</h2>
                
                <p>Hola {{ user_name }},</p>
                
                <p>¡Excelentes noticias! El precio del producto que estás monitoreando ha bajado.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{{ product_name }}</h3>
                    <p><strong>Marca:</strong> {{ product_brand }}</p>
                    <p><strong>Precio anterior:</strong> <span style="text-decoration: line-through; color: #666;">${{ previous_price }}</span></p>
                    <p><strong>Precio actual:</strong> <span style="color: #4caf50; font-size: 18px; font-weight: bold;">${{ current_price }}</span></p>
                    <p><strong>Tu precio objetivo:</strong> ${{ target_price }}</p>
                    <p><strong>Bajó:</strong> <span style="color: #4caf50; font-weight: bold;">${{ change_amount|abs }} ({{ change_percentage|floatformat:1 }}%)</span></p>
                    <p><strong>Ahorro vs objetivo:</strong> <span style="color: #4caf50; font-weight: bold;">${{ price_difference }}</span></p>
                </div>
                
                {% if store_url %}
                <p style="text-align: center;">
                    <a href="{{ store_url }}" style="background-color: #4caf50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Comprar Ahora
                    </a>
                </p>
                {% endif %}
                
                <p>¡Es el momento perfecto para comprar!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Este email fue enviado por CotizaBelleza.<br>
                    ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_decreased_price_text_template():
        """Plantilla de texto para precio que bajó"""
        return """
¡Precio bajó! 🎉

Hola {{ user_name }},

¡Excelentes noticias! El precio del producto que estás monitoreando ha bajado.

PRODUCTO: {{ product_name }}
MARCA: {{ product_brand }}
PRECIO ANTERIOR: ${{ previous_price }}
PRECIO ACTUAL: ${{ current_price }}
BAJÓ: ${{ change_amount|abs }} ({{ change_percentage|floatformat:1 }}%)
TU PRECIO OBJETIVO: ${{ target_price }}
AHORRO VS OBJETIVO: ${{ price_difference }}

{% if store_url %}
Comprar ahora: {{ store_url }}
{% endif %}

¡Es el momento perfecto para comprar!

---
Este email fue enviado por CotizaBelleza.
ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
        """
    
    @staticmethod
    def _get_increased_price_html_template():
        """Plantilla HTML para precio que subió"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Precio subió - CotizaBelleza</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ff9800;">Precio subió ⚠️</h2>
                
                <p>Hola {{ user_name }},</p>
                
                <p>El precio del producto que estás monitoreando ha subido, pero aún está por debajo de tu objetivo.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{{ product_name }}</h3>
                    <p><strong>Marca:</strong> {{ product_brand }}</p>
                    <p><strong>Precio anterior:</strong> <span style="color: #4caf50;">${{ previous_price }}</span></p>
                    <p><strong>Precio actual:</strong> <span style="color: #ff9800; font-size: 18px; font-weight: bold;">${{ current_price }}</span></p>
                    <p><strong>Tu precio objetivo:</strong> ${{ target_price }}</p>
                    <p><strong>Subió:</strong> <span style="color: #ff9800; font-weight: bold;">${{ change_amount }} ({{ change_percentage|floatformat:1 }}%)</span></p>
                    <p><strong>Ahorro vs objetivo:</strong> <span style="color: #4caf50; font-weight: bold;">${{ price_difference }}</span></p>
                </div>
                
                {% if store_url %}
                <p style="text-align: center;">
                    <a href="{{ store_url }}" style="background-color: #ff9800; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ver Producto
                    </a>
                </p>
                {% endif %}
                
                <p>El precio aún está por debajo de tu objetivo, pero considera comprar pronto.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Este email fue enviado por CotizaBelleza.<br>
                    ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_increased_price_text_template():
        """Plantilla de texto para precio que subió"""
        return """
Precio subió ⚠️

Hola {{ user_name }},

El precio del producto que estás monitoreando ha subido, pero aún está por debajo de tu objetivo.

PRODUCTO: {{ product_name }}
MARCA: {{ product_brand }}
PRECIO ANTERIOR: ${{ previous_price }}
PRECIO ACTUAL: ${{ current_price }}
SUBIÓ: ${{ change_amount }} ({{ change_percentage|floatformat:1 }}%)
TU PRECIO OBJETIVO: ${{ target_price }}
AHORRO VS OBJETIVO: ${{ price_difference }}

{% if store_url %}
Ver producto: {{ store_url }}
{% endif %}

El precio aún está por debajo de tu objetivo, pero considera comprar pronto.

---
Este email fue enviado por CotizaBelleza.
ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
        """
    
    @staticmethod
    def _get_new_price_html_template():
        """Plantilla HTML para nuevo precio"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Nuevo precio disponible - CotizaBelleza</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2196f3;">Nuevo precio disponible 📢</h2>
                
                <p>Hola {{ user_name }},</p>
                
                <p>¡Hay un nuevo precio disponible para el producto que estás monitoreando!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{{ product_name }}</h3>
                    <p><strong>Marca:</strong> {{ product_brand }}</p>
                    <p><strong>Nuevo precio:</strong> <span style="color: #2196f3; font-size: 18px; font-weight: bold;">${{ current_price }}</span></p>
                    <p><strong>Tu precio objetivo:</strong> ${{ target_price }}</p>
                    <p><strong>Ahorro vs objetivo:</strong> <span style="color: #4caf50; font-weight: bold;">${{ price_difference }}</span></p>
                </div>
                
                {% if store_url %}
                <p style="text-align: center;">
                    <a href="{{ store_url }}" style="background-color: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ver Producto
                    </a>
                </p>
                {% endif %}
                
                <p>¡Revisa si este precio te conviene!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Este email fue enviado por CotizaBelleza.<br>
                    ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_new_price_text_template():
        """Plantilla de texto para nuevo precio"""
        return """
Nuevo precio disponible 📢

Hola {{ user_name }},

¡Hay un nuevo precio disponible para el producto que estás monitoreando!

PRODUCTO: {{ product_name }}
MARCA: {{ product_brand }}
NUEVO PRECIO: ${{ current_price }}
TU PRECIO OBJETIVO: ${{ target_price }}
AHORRO VS OBJETIVO: ${{ price_difference }}

{% if store_url %}
Ver producto: {{ store_url }}
{% endif %}

¡Revisa si este precio te conviene!

---
Este email fue enviado por CotizaBelleza.
ID de alerta: {{ alert_id }} | ID de producto: {{ product_id }}
        """
    
    @staticmethod
    def _get_welcome_html_template():
        """Plantilla HTML de bienvenida"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>¡Bienvenido a CotizaBelleza! - Tu plataforma de comparación de precios</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #e91e63 0%, #ff6b9d 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: bold;">¡Bienvenido a CotizaBelleza! 🎉</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Tu plataforma de comparación de precios de belleza</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #e91e63; margin-top: 0; font-size: 24px;">¡Hola {{ user_name }}! 👋</h2>
                    
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        ¡Nos alegra mucho que te hayas unido a <strong>CotizaBelleza</strong>! 
                        Estamos aquí para ayudarte a encontrar los mejores precios en productos de belleza y cuidado personal.
                    </p>
                    
                    <!-- Features Section -->
                    <div style="background-color: #f8f9fa; padding: 25px; border-radius: 10px; margin: 25px 0;">
                        <h3 style="color: #e91e63; margin-top: 0; font-size: 20px;">✨ ¿Qué puedes hacer con CotizaBelleza?</h3>
                        
                        <div style="margin: 20px 0;">
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="background-color: #4caf50; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 12px;">1</span>
                                <div>
                                    <strong style="color: #333;">Comparar precios</strong>
                                    <p style="margin: 5px 0 0 0; color: #666;">Encuentra el mejor precio entre múltiples tiendas</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="background-color: #4caf50; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 12px;">2</span>
                                <div>
                                    <strong style="color: #333;">Alertas de precio</strong>
                                    <p style="margin: 5px 0 0 0; color: #666;">Recibe notificaciones cuando los precios bajen</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="background-color: #4caf50; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 12px;">3</span>
                                <div>
                                    <strong style="color: #333;">Historial de precios</strong>
                                    <p style="margin: 5px 0 0 0; color: #666;">Monitorea cómo cambian los precios en el tiempo</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; align-items: center;">
                                <span style="background-color: #4caf50; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 12px;">4</span>
                                <div>
                                    <strong style="color: #333;">Productos de calidad</strong>
                                    <p style="margin: 5px 0 0 0; color: #666;">Solo productos auténticos de marcas reconocidas</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Start -->
                    <div style="background-color: #e3f2fd; padding: 25px; border-radius: 10px; margin: 25px 0; border-left: 4px solid #2196f3;">
                        <h3 style="color: #2196f3; margin-top: 0; font-size: 20px;">🚀 Comienza ahora mismo</h3>
                        <p style="margin-bottom: 20px;">
                            <strong>Paso 1:</strong> Explora nuestro catálogo de productos<br>
                            <strong>Paso 2:</strong> Encuentra el producto que te interesa<br>
                            <strong>Paso 3:</strong> Configura una alerta de precio<br>
                            <strong>Paso 4:</strong> ¡Ahorra dinero en tus compras!
                        </p>
                    </div>
                    
                    <!-- CTA Buttons -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ dashboard_url }}" style="background-color: #e91e63; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 0 10px; font-weight: bold; font-size: 16px;">
                            🏠 Ir al Dashboard
                        </a>
                        <a href="{{ catalog_url }}" style="background-color: #2196f3; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 0 10px; font-weight: bold; font-size: 16px;">
                            🛍️ Ver Catálogo
                        </a>
                    </div>
                    
                    <!-- Tips Section -->
                    <div style="background-color: #fff3e0; padding: 25px; border-radius: 10px; margin: 25px 0; border-left: 4px solid #ff9800;">
                        <h3 style="color: #ff9800; margin-top: 0; font-size: 20px;">💡 Consejos para ahorrar más</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li style="margin-bottom: 8px;">Configura alertas de precio para productos que uses regularmente</li>
                            <li style="margin-bottom: 8px;">Compara precios antes de comprar</li>
                            <li style="margin-bottom: 8px;">Revisa el historial de precios para identificar patrones</li>
                            <li style="margin-bottom: 8px;">Suscríbete a nuestras notificaciones para ofertas especiales</li>
                        </ul>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">
                        Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos. 
                        ¡Estamos aquí para ayudarte a ahorrar en tus productos de belleza favoritos!
                    </p>
                    
                    <p style="font-size: 16px; margin-bottom: 0;">
                        ¡Bienvenido a la familia CotizaBelleza! 💖
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f5f5f5; padding: 25px; text-align: center; border-top: 1px solid #eee;">
                    <p style="margin: 0 0 15px 0; color: #666; font-size: 14px;">
                        <strong>CotizaBelleza</strong> - Tu plataforma de comparación de precios de belleza
                    </p>
                    <div style="margin-bottom: 15px;">
                        <a href="{{ dashboard_url }}" style="color: #e91e63; text-decoration: none; margin: 0 10px; font-size: 14px;">Dashboard</a>
                        <a href="{{ catalog_url }}" style="color: #e91e63; text-decoration: none; margin: 0 10px; font-size: 14px;">Catálogo</a>
                        <a href="{{ help_url }}" style="color: #e91e63; text-decoration: none; margin: 0 10px; font-size: 14px;">Ayuda</a>
                    </div>
                    <p style="margin: 0; color: #999; font-size: 12px;">
                        Este email fue enviado a {{ user_email }}<br>
                        Si no solicitaste esta cuenta, puedes ignorar este mensaje.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_welcome_text_template():
        """Plantilla de texto de bienvenida"""
        return """
¡Bienvenido a CotizaBelleza! 🎉

¡Hola {{ user_name }}!

Nos alegra mucho que te hayas unido a CotizaBelleza. Estamos aquí para ayudarte a encontrar los mejores precios en productos de belleza y cuidado personal.

✨ ¿Qué puedes hacer con CotizaBelleza?

1. COMPARAR PRECIOS
   Encuentra el mejor precio entre múltiples tiendas

2. ALERTAS DE PRECIO
   Recibe notificaciones cuando los precios bajen

3. HISTORIAL DE PRECIOS
   Monitorea cómo cambian los precios en el tiempo

4. PRODUCTOS DE CALIDAD
   Solo productos auténticos de marcas reconocidas

🚀 Comienza ahora mismo:

Paso 1: Explora nuestro catálogo de productos
Paso 2: Encuentra el producto que te interesa
Paso 3: Configura una alerta de precio
Paso 4: ¡Ahorra dinero en tus compras!

💡 Consejos para ahorrar más:

• Configura alertas de precio para productos que uses regularmente
• Compara precios antes de comprar
• Revisa el historial de precios para identificar patrones
• Suscríbete a nuestras notificaciones para ofertas especiales

Enlaces útiles:
Dashboard: {{ dashboard_url }}
Catálogo: {{ catalog_url }}
Ayuda: {{ help_url }}

Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos. ¡Estamos aquí para ayudarte a ahorrar en tus productos de belleza favoritos!

¡Bienvenido a la familia CotizaBelleza! 💖

---
CotizaBelleza - Tu plataforma de comparación de precios de belleza
Este email fue enviado a {{ user_email }}
        """
    
    @staticmethod
    def create_default_templates():
        """Crea plantillas por defecto si no existen"""
        templates_to_create = [
            {
                'name': 'price_alert',
                'subject': '¡Precio alcanzado! {product_name}',
                'html_content': EmailService._get_default_html_template(),
                'text_content': EmailService._get_default_text_template(),
            },
            {
                'name': 'price_alert_decreased',
                'subject': '¡Precio bajó! {product_name} 🎉',
                'html_content': EmailService._get_decreased_price_html_template(),
                'text_content': EmailService._get_decreased_price_text_template(),
            },
            {
                'name': 'price_alert_increased',
                'subject': 'Precio subió: {product_name} ⚠️',
                'html_content': EmailService._get_increased_price_html_template(),
                'text_content': EmailService._get_increased_price_text_template(),
            },
            {
                'name': 'price_alert_new_price',
                'subject': 'Nuevo precio disponible: {product_name} 📢',
                'html_content': EmailService._get_new_price_html_template(),
                'text_content': EmailService._get_new_price_text_template(),
            },
            {
                'name': 'welcome_email',
                'subject': '¡Bienvenido a CotizaBelleza! 🎉',
                'html_content': EmailService._get_welcome_html_template(),
                'text_content': EmailService._get_welcome_text_template(),
            }
        ]
        
        created_count = 0
        for template_data in templates_to_create:
            if not EmailTemplate.objects.filter(name=template_data['name']).exists():
                EmailTemplate.objects.create(
                    name=template_data['name'],
                    subject=template_data['subject'],
                    html_content=template_data['html_content'],
                    text_content=template_data['text_content'],
                    is_active=True
                )
                created_count += 1
        
        if created_count > 0:
            logger.info(f"Se crearon {created_count} plantillas de email por defecto")
        else:
            logger.info("Todas las plantillas de email ya existen")
    
    @staticmethod
    def send_welcome_email(user, dashboard_url=None, catalog_url=None, help_url=None):
        """
        Envía email de bienvenida a un nuevo usuario
        
        Args:
            user: Usuario que se registró
            dashboard_url: URL del dashboard (opcional)
            catalog_url: URL del catálogo (opcional)
            help_url: URL de ayuda (opcional)
        """
        try:
            # Preparar datos del email
            context = {
                'user_name': user.first_name or user.username,
                'user_email': user.email,
                'dashboard_url': dashboard_url or 'http://localhost:5173/dashboard',
                'catalog_url': catalog_url or 'http://localhost:5173/catalog',
                'help_url': help_url or 'http://localhost:5173/help',
            }
            
            # Obtener plantilla
            template = EmailTemplate.objects.filter(name='welcome_email', is_active=True).first()
            
            if template:
                subject = template.subject
                html_content = template.html_content
                text_content = template.text_content
            else:
                # Plantilla por defecto
                subject = '¡Bienvenido a CotizaBelleza! 🎉'
                html_content = EmailService._get_welcome_html_template()
                text_content = EmailService._get_welcome_text_template()
            
            # Renderizar contenido usando las plantillas del template
            from django.template import Template, Context
            html_template = Template(html_content)
            text_template = Template(text_content)
            
            html_message = html_template.render(Context(context))
            text_message = text_template.render(Context(context))
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            # Enviar
            email.send()
            
            logger.info(f"Email de bienvenida enviado exitosamente: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de bienvenida: {e}")
            return False

    @staticmethod
    def send_historical_alert_email(alerta, cambio, asunto, tipo_email, tienda_url=None):
        """
        Envía email de alerta histórica (subió/bajó/mantuvo)
        
        Args:
            alerta: AlertaPrecioProductoPersistente
            cambio: Diccionario con información del cambio
            asunto: Asunto del email
            tipo_email: Tipo de email (price_increased, price_decreased)
            tienda_url: URL de la tienda (opcional)
        """
        try:
            # Obtener email del usuario
            user_email = alerta.get_user_email()
            if not user_email:
                logger.error(f"No se pudo obtener email para alerta {alerta.id}")
                return False
            
            # Preparar contexto
            context = {
                'alerta': alerta,
                'producto': alerta.producto,
                'cambio': cambio,
                'dias_restantes': alerta.dias_restantes(),
                'notificaciones_enviadas': alerta.notificaciones_enviadas,
                'fecha_fin': alerta.fecha_fin.strftime('%d/%m/%Y') if alerta.fecha_fin else '',
                'tienda_url': tienda_url,
                'user_email': user_email,
            }
            
            # Obtener plantilla según tipo de cambio
            template_name = f'emails/historical_{tipo_email}.html'
            text_template_name = f'emails/historical_{tipo_email}.txt'
            
            try:
                # Renderizar contenido
                html_content = render_to_string(template_name, context)
                text_content = render_to_string(text_template_name, context)
            except:
                # Si no existe la plantilla, usar plantilla por defecto
                html_content = EmailService._get_default_historical_html_template(cambio)
                text_content = EmailService._get_default_historical_text_template(cambio)
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=asunto,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send()
            
            logger.info(f"Email histórico enviado a {user_email}: {cambio['tipo']}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email histórico: {e}")
            return False
    
    @staticmethod
    def send_alert_expired_email(alerta, precio_final=None):
        """
        Envía email cuando la alerta expira
        
        Args:
            alerta: AlertaPrecioProductoPersistente
            precio_final: Precio final del producto (opcional)
        """
        try:
            # Obtener email del usuario
            user_email = alerta.get_user_email()
            if not user_email:
                logger.error(f"No se pudo obtener email para alerta {alerta.id}")
                return False
            
            # Preparar contexto
            context = {
                'alerta': alerta,
                'producto': alerta.producto,
                'precio_final': precio_final,
                'precio_inicial': alerta.precio_inicial,
                'dias_monitoreados': 7,
                'user_email': user_email,
            }
            
            # Obtener plantilla
            template_name = 'emails/alert_expired.html'
            text_template_name = 'emails/alert_expired.txt'
            
            try:
                # Renderizar contenido
                html_content = render_to_string(template_name, context)
                text_content = render_to_string(text_template_name, context)
            except:
                # Si no existe la plantilla, usar plantilla por defecto
                html_content = EmailService._get_default_expired_html_template(context)
                text_content = EmailService._get_default_expired_text_template(context)
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=f"⏰ Alerta Expirada - {alerta.producto.nombre_original}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send()
            
            logger.info(f"Email de expiración enviado a {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de expiración: {e}")
            return False
    
    @staticmethod
    def _get_default_historical_html_template(cambio):
        """Plantilla HTML por defecto para alertas históricas"""
        if cambio['tipo'] == 'subio':
            return f"""
            <html>
            <body>
                <h2>📈 El precio ha subido</h2>
                <p>El precio de <strong>{cambio.get('producto', 'el producto')}</strong> ha subido desde que creaste tu alerta.</p>
                <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                    <h3>Resumen del Cambio:</h3>
                    <ul>
                        <li><strong>Precio inicial:</strong> ${cambio['precio_inicial']:,.0f} CLP</li>
                        <li><strong>Precio actual:</strong> ${cambio['precio_actual']:,.0f} CLP</li>
                        <li><strong>Subió:</strong> ${cambio['diferencia']:,.0f} CLP ({cambio['porcentaje']:.1f}%)</li>
                    </ul>
                </div>
                <p>Te seguiremos informando sobre los cambios de precio.</p>
                <p>Saludos,<br>Equipo CotizaBelleza</p>
            </body>
            </html>
            """
        else:  # bajó
            return f"""
            <html>
            <body>
                <h2>📉 ¡Buenas noticias! El precio bajó</h2>
                <p>¡Excelente! El precio de <strong>{cambio.get('producto', 'el producto')}</strong> ha bajado desde que creaste tu alerta.</p>
                <div style="background: #e8f5e8; padding: 15px; margin: 20px 0;">
                    <h3>Resumen del Cambio:</h3>
                    <ul>
                        <li><strong>Precio inicial:</strong> ${cambio['precio_inicial']:,.0f} CLP</li>
                        <li><strong>Precio actual:</strong> ${cambio['precio_actual']:,.0f} CLP</li>
                        <li><strong>Bajó:</strong> ${cambio['diferencia']:,.0f} CLP ({cambio['porcentaje']:.1f}%)</li>
                    </ul>
                </div>
                <p>¡Es un buen momento para comprar!</p>
                <p>Saludos,<br>Equipo CotizaBelleza</p>
            </body>
            </html>
            """
    
    @staticmethod
    def _get_default_historical_text_template(cambio):
        """Plantilla de texto por defecto para alertas históricas"""
        if cambio['tipo'] == 'subio':
            return f"""
            📈 El precio ha subido

            El precio de {cambio.get('producto', 'el producto')} ha subido desde que creaste tu alerta.

            Resumen del Cambio:
            - Precio inicial: ${cambio['precio_inicial']:,.0f} CLP
            - Precio actual: ${cambio['precio_actual']:,.0f} CLP
            - Subió: ${cambio['diferencia']:,.0f} CLP ({cambio['porcentaje']:.1f}%)

            Te seguiremos informando sobre los cambios de precio.

            Saludos,
            Equipo CotizaBelleza
            """
        else:  # bajó
            return f"""
            📉 ¡Buenas noticias! El precio bajó

            ¡Excelente! El precio de {cambio.get('producto', 'el producto')} ha bajado desde que creaste tu alerta.

            Resumen del Cambio:
            - Precio inicial: ${cambio['precio_inicial']:,.0f} CLP
            - Precio actual: ${cambio['precio_actual']:,.0f} CLP
            - Bajó: ${cambio['diferencia']:,.0f} CLP ({cambio['porcentaje']:.1f}%)

            ¡Es un buen momento para comprar!

            Saludos,
            Equipo CotizaBelleza
            """
    
    @staticmethod
    def _get_default_expired_html_template(context):
        """Plantilla HTML por defecto para alertas expiradas"""
        return f"""
        <html>
        <body>
            <h2>⏰ Tu alerta ha expirado</h2>
            <p>Hola,</p>
            <p>Tu alerta de precio para <strong>{context['producto'].nombre_original}</strong> ha expirado después de 7 días de monitoreo.</p>
            
            <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                <h3>Resumen del Período:</h3>
                <ul>
                    <li><strong>Producto:</strong> {context['producto'].nombre_original}</li>
                    <li><strong>Precio inicial:</strong> ${context['precio_inicial']:,.0f} CLP</li>
                    <li><strong>Precio final:</strong> ${context['precio_final']:,.0f} CLP</li>
                    <li><strong>Días monitoreados:</strong> {context['dias_monitoreados']}</li>
                </ul>
            </div>
            
            <p>Si quieres seguir monitoreando este producto, puedes crear una nueva alerta.</p>
            <p>Gracias por usar CotizaBelleza.</p>
            
            <p>Saludos,<br>Equipo CotizaBelleza</p>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_default_expired_text_template(context):
        """Plantilla de texto por defecto para alertas expiradas"""
        return f"""
        ⏰ Tu alerta ha expirado

        Hola,

        Tu alerta de precio para {context['producto'].nombre_original} ha expirado después de 7 días de monitoreo.

        Resumen del Período:
        - Producto: {context['producto'].nombre_original}
        - Precio inicial: ${context['precio_inicial']:,.0f} CLP
        - Precio final: ${context['precio_final']:,.0f} CLP
        - Días monitoreados: {context['dias_monitoreados']}

        Si quieres seguir monitoreando este producto, puedes crear una nueva alerta.

        Gracias por usar CotizaBelleza.

        Saludos,
        Equipo CotizaBelleza
        """
