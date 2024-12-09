import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_DOMAIN, FRONT_DOMAIN

smtp_server = SMTP_SERVER
smtp_port = SMTP_PORT
username = SMTP_USERNAME
password = SMTP_PASSWORD

async def send_new_pass(email, token):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = email
    msg["Subject"] = "Сброс пароля"

    html = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Сброс пароля</title>
<style>
    body {{
        font-family: 'Arial', sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
    }}
    .container {{
        max-width: 600px;
        margin: 20px auto;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    h1 {{
        color: #333;
        text-align: center;
        margin-bottom: 20px;
    }}
    p {{
        color: #666;
        text-align: center;
        margin: 10px 0;
    }}
    .btn {{
        display: inline-block;
        padding: 15px 25px;
        margin: 20px 0;
        background-color: #4CAF50;
        font-size: 18px;
        border-radius: 5px;
        text-decoration: none;
        color: white;
        font-weight: bold;
    }}
    .footer {{
        text-align: center;
        color: #999;
        font-size: 12px;
        margin-top: 20px;
    }}
</style>
</head>
<body>
<div class="container">
    <h1>Сброс пароля</h1>
    <p>Вы получили это письмо, потому что вы или кто-то другой запросили сброс пароля для вашего аккаунта.</p>
    <p>Нажмите на кнопку ниже, чтобы изменить пароль:</p>
    <center>
        <a href="{FRONT_DOMAIN}/auth/reset-password/{token}" class='btn'>Изменить пароль</a>
    </center>
    <p>Если вы не запрашивали сброс пароля или считаете, что это ошибка, пожалуйста, проигнорируйте это сообщение.</p>
    <div class="footer">
        <p>С уважением, команда поддержки.</p>
    </div>
</div>
</body>
</html>
    """

    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        print(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("Logging in to the SMTP server...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            print(f"Sending email to {email}...")
            server.sendmail(SMTP_USERNAME, email, text)
            print("Email sent successfully")
            return True
    except Exception as e:
        print("Ошибка отправки электронной почты:", e)
        return False

async def send_pass(email:str, password:str, chair_number:int, user_first_name:str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = email
    msg["Subject"] = "Ваш аккаунт"

    html = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ваш аккаунт</title>
<style>
    body {{
        font-family: 'Arial', sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
    }}
    .container {{
        max-width: 600px;
        margin: 20px auto;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    h1 {{
        color: #333;
        text-align: center;
        margin-bottom: 20px;
    }}
    p {{
        color: #666;
        text-align: center;
        margin: 10px 0;
    }}
    .btn {{
        display: inline-block;
        padding: 15px 25px;
        margin: 20px 0;
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
    }}
    .footer {{
        text-align: center;
        color: #999;
        font-size: 12px;
        margin-top: 20px;
    }}
</style>
</head>
<body>
<div class="container">
    <h1>Создан новый аккаунт</h1>
        <p>Дорогой {user_first_name}, вы получили это письмо, потому что вам создали аккаунт на сайте {FRONT_DOMAIN}.</p>
        <center><h2>Ваши данные для входа в личный кабинет</h2></center>
        <p>
            <span>Электронная почта: {email} </span><br>
            <span>Пароль: {password} </span>
        </p>
        <p>Ваш номер окна: {chair_number}</p>
        <p>Нажмите на <a href="{FRONT_DOMAIN}/auth/sign-in">ссылку</a>, чтобы перейти на страницу входа.</p>
        <div class="footer">
            <p>С уважением, команда поддержки.</p>
        </div>
    </div>
</body>
</html>
    """

    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        print(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("Logging in to the SMTP server...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            print(f"Sending email to {email}...")
            server.sendmail(SMTP_USERNAME, email, text)
            print("Email sent successfully")
            return True
    except Exception as e:
        print("Ошибка отправки электронной почты:", e)
        return False