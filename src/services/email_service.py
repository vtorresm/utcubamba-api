import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks
from typing import Optional, Dict, Any
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.core.config import settings

logger = logging.getLogger(__name__)

# Configurar entorno de plantillas
template_dir = Path(__file__).parent.parent / "templates"
if not template_dir.exists():
    template_dir.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(template_dir))

class EmailService:
    @staticmethod
    def render_template(template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza una plantilla de correo electrónico.
        """
        try:
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error al renderizar plantilla {template_name}: {str(e)}")
            raise

    @staticmethod
    async def send_email_async(
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico de forma asíncrona.
        """
        try:
            # Renderizar plantilla HTML
            html_content = EmailService.render_template(template_name, context)
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Adjuntar versiones HTML y texto plano
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
                
            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Configurar y enviar el correo
            async with aiosmtplib.SMTP(
                hostname=settings.MAILTRAP_HOST,
                port=settings.MAILTRAP_PORT,
                use_tls=True,
            ) as smtp:
                await smtp.connect()
                await smtp.login(settings.MAILTRAP_USERNAME, settings.MAILTRAP_PASSWORD)
                await smtp.send_message(message)
                
            logger.info(f"Correo enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar correo a {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_email_background(
        background_tasks: BackgroundTasks,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        text_content: Optional[str] = None
    ) -> None:
        """
        Programa el envío de un correo electrónico en segundo plano.
        """
        background_tasks.add_task(
            EmailService.send_email_async,
            to_email,
            subject,
            template_name,
            context,
            text_content
        )

    @staticmethod
    async def send_password_reset_email(
        background_tasks: BackgroundTasks,
        to_email: str,
        token: str,
        username: str
    ) -> None:
        """
        Envía un correo de restablecimiento de contraseña.
        """
        subject = "Restablecer contraseña - UTCubamba"
        template_name = "emails/password_reset.html"
        frontend_url = settings.FRONTEND_URL
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        context = {
            "username": username,
            "reset_url": reset_url,
            "token": token,
            "support_email": "soporte@utcubamba.edu.pe"
        }
        
        text_content = f"""
        Hola {username},
        
        Para restablecer tu contraseña, haz clic en el siguiente enlace:
        {reset_url}
        
        Si no solicitaste este restablecimiento, puedes ignorar este mensaje.
        
        Saludos,
        El equipo de UTCubamba
        """
        
        EmailService.send_email_background(
            background_tasks=background_tasks,
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            context=context,
            text_content=text_content
        )
