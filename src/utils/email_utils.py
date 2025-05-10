import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

def send_email(subject: str, body: str, to_email: str = ADMIN_EMAIL):
    """Envía un email al destinatario especificado usando Mailtrap."""
    try:
        if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, to_email]):
            logger.error("Faltan configuraciones SMTP. Verifica las variables de entorno:")
            logger.error(f"SMTP_SERVER: {'✓' if SMTP_SERVER else '✗'}")
            logger.error(f"SMTP_PORT: {'✓' if SMTP_PORT else '✗'}")
            logger.error(f"SMTP_USERNAME: {'✓' if SMTP_USERNAME else '✗'}")
            logger.error(f"SMTP_PASSWORD: {'✓' if SMTP_PASSWORD else '✗'}")
            logger.error(f"ADMIN_EMAIL: {'✓' if ADMIN_EMAIL else '✗'}")
            return False

        msg = MIMEMultipart()
        msg['From'] = f"Sistema de Farmacia <{SMTP_USERNAME}>"
        msg['To'] = to_email
        msg['Subject'] = f"[UTCUBAMBA] {subject}"

        # Agregar un estilo básico al HTML
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">{subject}</h2>
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                        {body}
                    </div>
                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                        Este es un mensaje automático del Sistema de Farmacia UTCUBAMBA.
                        Por favor no responda a este correo.
                    </p>
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
            
        logger.info(f"Email enviado exitosamente a {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar email a {to_email}: {str(e)}")
        return False