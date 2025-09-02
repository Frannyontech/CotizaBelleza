"""
Módulo de seguridad para protección de datos sensibles
"""
import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Variable global para el cipher
_cipher = None

def _get_cipher():
    """
    Obtiene o crea el cipher de Fernet usando la clave secreta
    """
    global _cipher
    
    if _cipher is None:
        try:
            # Obtener la clave secreta desde settings
            secret_key = getattr(settings, 'EMAIL_SECRET_KEY', None)
            
            if not secret_key:
                raise ValueError("EMAIL_SECRET_KEY no está configurada en settings")
            
            # Asegurar que la clave tenga el formato correcto (32 bytes base64)
            if len(secret_key) != 44:  # Fernet requiere 32 bytes en base64
                # Si la clave no tiene el formato correcto, generar una nueva
                logger.warning("EMAIL_SECRET_KEY no tiene el formato correcto. Generando nueva clave...")
                secret_key = Fernet.generate_key()
            
            _cipher = Fernet(secret_key)
            
        except Exception as e:
            logger.error(f"Error inicializando cipher: {e}")
            raise
    
    return _cipher

def encrypt_email(email: str) -> str:
    """
    Encripta un email usando Fernet
    
    Args:
        email (str): Email a encriptar
        
    Returns:
        str: Email encriptado en formato base64
        
    Raises:
        ValueError: Si el email está vacío
        Exception: Si hay error en la encriptación
    """
    if not email or not email.strip():
        raise ValueError("Email no puede estar vacío")
    
    try:
        cipher = _get_cipher()
        email_bytes = email.strip().encode('utf-8')
        encrypted_bytes = cipher.encrypt(email_bytes)
        encrypted_string = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        
        logger.debug(f"Email encriptado exitosamente: {mask_email(email)}")
        return encrypted_string
        
    except Exception as e:
        logger.error(f"Error encriptando email {mask_email(email)}: {e}")
        raise

def decrypt_email(encrypted_email: str) -> str:
    """
    Desencripta un email usando Fernet
    
    Args:
        encrypted_email (str): Email encriptado en formato base64
        
    Returns:
        str: Email desencriptado
        
    Raises:
        ValueError: Si el email encriptado está vacío
        Exception: Si hay error en la desencriptación
    """
    if not encrypted_email or not encrypted_email.strip():
        raise ValueError("Email encriptado no puede estar vacío")
    
    try:
        cipher = _get_cipher()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_email.encode('utf-8'))
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        decrypted_email = decrypted_bytes.decode('utf-8')
        
        logger.debug(f"Email desencriptado exitosamente: {mask_email(decrypted_email)}")
        return decrypted_email
        
    except Exception as e:
        logger.error(f"Error desencriptando email: {e}")
        raise

def mask_email(email: str) -> str:
    """
    Enmascara un email para mostrar en logs y APIs
    
    Args:
        email (str): Email a enmascarar
        
    Returns:
        str: Email enmascarado (ej: f*****@gmail.com)
    """
    if not email or not email.strip():
        return "***@***"
    
    email = email.strip()
    
    try:
        # Separar usuario y dominio
        if '@' not in email:
            return "***@***"
        
        username, domain = email.split('@', 1)
        
        # Enmascarar username (mostrar solo primera letra)
        if len(username) <= 1:
            masked_username = "*"
        else:
            masked_username = username[0] + "*" * (len(username) - 1)
        
        # Enmascarar dominio (mostrar solo primera letra de cada parte)
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            masked_domain = domain_parts[0][0] + "*" * (len(domain_parts[0]) - 1)
            masked_domain += "." + domain_parts[-1]  # Mostrar TLD completo
        else:
            masked_domain = domain[0] + "*" * (len(domain) - 1)
        
        return f"{masked_username}@{masked_domain}"
        
    except Exception as e:
        logger.error(f"Error enmascarando email: {e}")
        return "***@***"

def generate_secret_key() -> str:
    """
    Genera una nueva clave secreta para Fernet
    
    Returns:
        str: Clave secreta en formato base64
    """
    return Fernet.generate_key().decode('utf-8')

def is_valid_encrypted_email(encrypted_email: str) -> bool:
    """
    Verifica si un email encriptado es válido
    
    Args:
        encrypted_email (str): Email encriptado a verificar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not encrypted_email or not encrypted_email.strip():
        return False
    
    try:
        # Intentar desencriptar para verificar que es válido
        decrypt_email(encrypted_email)
        return True
    except Exception:
        return False







