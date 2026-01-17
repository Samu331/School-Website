from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask_cors import CORS 

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

SENDER_EMAIL = "masekosamkelo828@gmail.com"
SENDER_PASSWORD = "cttxqiaolkunsoxt"   # Gmail App Password
ADMIN_EMAIL = "zamandulo.tshabalala@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# Branding
LOGO_URL = "https://yourwebsite.com/images/ydela-logo.png" 
WHATSAPP_NUMBER = "27768515992"
GOOGLE_MAPS_URL = "https://maps.google.com/?q=Young+Dream+Early+Learning+Academy"



if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
CORS(app)  # Enable CORS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/submit_application', methods=['POST'])
def submit_application():
    try:
        name = request.form.get('full_name')
        parent_email = request.form.get('email')
        message_text = request.form.get('message', '')

        if not name or not parent_email:
            return jsonify({"success": False, "message": "Name and Email are required!"})

        files = request.files.getlist('application_file') + \
                request.files.getlist('id_documents') + \
                request.files.getlist('other_documents')

        attachments = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                attachments.append(path)

        year = str(datetime.now().year)

        # ================= ADMIN EMAIL =================
        admin_msg = MIMEMultipart()
        admin_msg['Subject'] = 'New Application – Young Dream Early Learning Academy'
        admin_msg['From'] = SENDER_EMAIL
        admin_msg['To'] = ADMIN_EMAIL

        admin_body = f"""
        <html>
        <body style="background:#FFF7ED;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center">
        <table width="600" cellpadding="20" style="background:#ffffff;border-radius:12px;">

        <tr>
        <td align="center" style="background:#2A9D8F;color:white;border-radius:12px 12px 0 0;">
        <img src="{LOGO_URL}" width="120"><br>
        <h2>New Application Received</h2>
        </td>
        </tr>

        <tr><td>
        <p><strong>Parent Name:</strong> {name}</p>
        <p><strong>Email:</strong> {parent_email}</p>

        <p><strong>Message:</strong></p>
        <div style="background:#FFF7ED;padding:15px;border-radius:8px;">
        {message_text}
        </div>

        <p>📎 Documents attached</p>
        </td></tr>

        <tr>
        <td align="center" style="font-size:12px;color:#777;">
        <a href="{GOOGLE_MAPS_URL}" style="color:#2A9D8F;text-decoration:none;">
        📍 View Location on Google Maps
        </a><br><br>
        © {year} Young Dream Early Learning Academy
        </td>
        </tr>

        </table>
        </td></tr>
        </table>
        </body>
        </html>
        """

        admin_msg.attach(MIMEText(admin_body, 'html'))

        for file_path in attachments:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                admin_msg.attach(part)

        # ================= AUTO-REPLY EMAIL =================
        reply_msg = MIMEMultipart()
        reply_msg['Subject'] = 'Application Received – Young Dream Early Learning Academy'
        reply_msg['From'] = SENDER_EMAIL
        reply_msg['To'] = parent_email

        reply_body = f"""
        <html>
        <body style="background:#FFF7ED;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center">
        <table width="600" cellpadding="20" style="background:#ffffff;border-radius:12px;">

        <tr>
        <td align="center" style="background:#F4A261;color:white;border-radius:12px 12px 0 0;">
        <img src="{LOGO_URL}" width="120"><br>
        <h2>Application Received 🎉</h2>
        </td>
        </tr>

        <tr><td>
        <p>Dear <strong>{name}</strong>,</p>

        <p>
        Thank you for submitting your application to
        <strong>Young Dream Early Learning Academy</strong>.Our admin team will get back to you regarding the next step </p>

        <div style="text-align:center;margin:25px 0;">
        <a href="https://wa.me/{WHATSAPP_NUMBER}"
        style="background:#25D366;color:white;padding:14px 26px;
        border-radius:30px;text-decoration:none;font-weight:bold;">
        💬 Chat with us on WhatsApp
        </a>
        </div>

        <p>
        Warm regards,<br>
        <strong>Young Dream Early Learning Academy</strong><br>
        <span style="color:#2A9D8F;">Nurturing young minds</span>
        </p>
        </td></tr>

        <tr>
        <td align="center" style="font-size:12px;color:#777;">
        <a href="{GOOGLE_MAPS_URL}" style="color:#2A9D8F;text-decoration:none;">
        📍 Open in Google Maps
        </a><br><br>
        © {year} Young Dream Early Learning Academy
        </td>
        </tr>

        </table>
        </td></tr>
        </table>
        </body>
        </html>
        """

        reply_msg.attach(MIMEText(reply_body, 'html'))

        # ================= SEND EMAILS =================
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, admin_msg.as_string())
            server.sendmail(SENDER_EMAIL, parent_email, reply_msg.as_string())

        return jsonify({"success": True, "message": "Application submitted successfully!"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True)





