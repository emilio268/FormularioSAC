from flask import Flask, request, render_template
import psycopg2
import re
from flask_cors import CORS
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment

app = Flask(__name__)
CORS(app)

# Configuración de la conexión de la base de datos
def get_db_connection():
    connection = psycopg2.connect(
        host="localhost",
        database="prueba12344",
        user="postgres",
        password="PRUEBA2023",
        port="5432"
    )
    return connection

# Validación de datos
def validar_email(email):
    patron = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(patron, email)

def validar_numero_documento(documento):
    return re.match(r'^[0-9]+$', documento)

TIPOS_DOCUMENTO_VALIDOS = ['Cédula', 'Pasaporte', 'NIT']

def create_assessment(project_id: str, recaptcha_key: str, token: str, recaptcha_action: str) -> Assessment:
    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()
    event = recaptchaenterprise_v1.Event(site_key=recaptcha_key, token=token)
    assessment = recaptchaenterprise_v1.Assessment(event=event)
    project_name = f"projects/{project_id}"

    request = recaptchaenterprise_v1.CreateAssessmentRequest(
        parent=project_name,
        assessment=assessment
    )
    response = client.create_assessment(request)

    if not response.token_properties.valid:
        print("Token inválido:", response.token_properties.invalid_reason)
        return None

    if response.token_properties.action != recaptcha_action:
        print("Acción del token no coincide.")
        return None

    print("Score del reCAPTCHA:", response.risk_analysis.score)
    return response

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/insertar-datos', methods=['POST'])
def insertar_datos():
    # Verificación del reCAPTCHA
    captcha_response = request.form.get('g-recaptcha-response')
    project_id = '6Lcv6W0qAAAAALVJQ-84jp7j6Xo4nzxLsCFDUKZC'
    recaptcha_key = '6Lcv6W0qAAAAALVJQ-84jp7j6Xo4nzxLsCFDUKZC'

    assessment = create_assessment(project_id, recaptcha_key, captcha_response, 'LOGIN')
    if not assessment:
        return render_template('error.html', message='Error de captcha. Intenta nuevamente.')

    # Procesar los datos del formulario si el captcha es válido
    data = request.form
    hora_registro = datetime.now()
    tipo_documento = data.get('tipo_documento')
    numero_documento = data.get('numero_documento')
    nombres = data.get('nombres')
    apellidos = data.get('apellidos')
    correo_electronico = data.get('correo_electronico')
    telefono_celular = data.get('telefono_celular')
    fecha_nacimiento = data.get('fecha_nacimiento')

    if not all([tipo_documento, numero_documento, nombres, apellidos, correo_electronico, telefono_celular, fecha_nacimiento]):
        return render_template('error.html', message='Faltan datos')

    if tipo_documento not in TIPOS_DOCUMENTO_VALIDOS:
        return render_template('error.html', message='Tipo de documento no válido')

    if not validar_numero_documento(numero_documento):
        return render_template('error.html', message='Número de documento no válido')

    if not validar_email(correo_electronico):
        return render_template('error.html', message='Correo electrónico no válido')

    if not re.match(r'^[0-9]{10}$', telefono_celular):
        return render_template('error.html', message='Número de teléfono no válido')

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = '''
        INSERT INTO Registro (hora_registro, tipo_documento, numero_documento, nombres, apellidos, correo_electronico, telefono_celular, fecha_nacimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (hora_registro, tipo_documento, numero_documento, nombres,
                               apellidos, correo_electronico, telefono_celular, fecha_nacimiento))

        connection.commit()
        cursor.close()
        connection.close()

        send_email(correo_electronico)

        return render_template('success.html', message='Datos insertados correctamente')
    except Exception as e:
        return render_template('error.html', message=str(e))

def send_email(to_email):
    sender_email = "clientes@berlinasdelfonce.com"
    sender_password = "Cl13nt35**"
    subject = "Actualización de Datos Exitosa"
    body = "Tus datos han sido actualizados con éxito."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('mail.berlinasdelfonce.com', 25) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8087, debug=True)
