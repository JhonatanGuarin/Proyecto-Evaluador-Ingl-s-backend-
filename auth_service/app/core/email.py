from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_reset_password_email(email_to: str, reset_code: str):
    """
    Envía el correo con el código para resetear la contraseña.
    """
    html_content = f"""
    <html>
        <body>
            <h2>Reseteo de Contraseña</h2>
            <p>Hola,</p>
            <p>Has solicitado resetear tu contraseña. Usa el siguiente código para continuar:</p>
            <h3 style="font-size: 24px; letter-spacing: 2px;"><b>{reset_code}</b></h3>
            <p>Este código expirará en 10 minutos.</p>
            <p>Si no solicitaste esto, por favor ignora este correo.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Tu código para resetear la contraseña",
        recipients=[email_to],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)