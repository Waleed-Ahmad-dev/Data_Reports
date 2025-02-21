from flask import Flask, request, send_file, render_template
import os
import pandas as pd
from ydata_profiling import ProfileReport
from threading import Thread
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to generate profile report in a separate thread
def generate_report(file_path, report_html_path, report_json_path):
     try:
          # Read CSV data in chunks (use low_memory=True for better memory efficiency)
          df = pd.read_csv(file_path, low_memory=True)
          profile = ProfileReport(df, title="Data Report", explorative=True)

          # Save the profile report as HTML
          profile.to_file(report_html_path)

          # Save the profile report as JSON
          profile_json = profile.to_json()
          with open(report_json_path, 'w') as json_file:
               json_file.write(profile_json)

          print(f"Reports generated: {report_html_path}, {report_json_path}")
     except Exception as e:
          print(f"Error processing file: {e}")

@app.route('/')
def index():
     return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
     if 'csv_file' not in request.files:
          return "No file part", 400

     file = request.files['csv_file']

     if file.filename == '':
          return "No selected file", 400

     if file and allowed_file(file.filename):
          # Secure the filename to prevent any malicious paths
          filename = secure_filename(file.filename)

          # Save the uploaded file
          file_path = os.path.join(UPLOAD_FOLDER, filename)
          file.save(file_path)

          print(f"File saved to {file_path}")

          # Paths for the report files
          html_report_path = os.path.join(UPLOAD_FOLDER, f'{filename}_report.html')
          json_report_path = os.path.join(UPLOAD_FOLDER, f'{filename}_report.json')

          # Start report generation in a separate thread
          thread = Thread(target=generate_report, args=(file_path, html_report_path, json_report_path))
          thread.start()

          # Return the result page with links to the generated reports
          return render_template('result.html', html_report=html_report_path, json_report=json_report_path)

     return "Invalid file type", 400

@app.route('/download/<filename>')
def download_file(filename):
     # Serve the file as a download
     file_path = os.path.join(UPLOAD_FOLDER, filename)
     if os.path.exists(file_path):
          return send_file(file_path, as_attachment=True)
     else:
          return f"File {filename} not found", 404


if __name__ == '__main__':
     port = int(os.environ.get('PORT', 5000))  # Default to 5000 if no PORT is set
     app.run(host='0.0.0.0', port=port)
