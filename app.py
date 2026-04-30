from urllib import response

from flask import Flask, render_template, request, send_file
import os, uuid
from processor import process_pdfs
from flask import after_this_request
import threading
import time
from flask import send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB


@app.route('/googlef0a54c6b1326f751.html')
def google_verify():
    return send_from_directory('', 'googlef0a54c6b1326f751.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("pdfs")
    saved_files = []

    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            continue

        filename = str(uuid.uuid4()) + ".pdf"
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        saved_files.append(path)

    output_file = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".docx")

    process_pdfs(saved_files, output_file)

    # delay deletion in a separate thread
    def delayed_delete(path):
        time.sleep(10)

        try:
            if os.path.exists(path):
                os.remove(path)
                print("Deleted:", path)
        except Exception as e:
            print("Delete failed:", e)

    # Cleanup PDFs
    for f in saved_files:
        os.remove(f)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(output_file)
        except Exception as e:
            print("DOCX delete failed:", e)

        return response

    response = send_file(output_file, as_attachment=True)

    threading.Thread(target=delayed_delete, args=(output_file,)).start()

    return response


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/pvc-print-guide")
def pvc_print_guide():
    return render_template("blogs/pvc-print-guide.html")


@app.route("/id-card-print-settings")
def id_card_print_settings():
    return render_template("blogs/id-card-print-settings.html")


@app.route("/pdf-to-word-guide")
def pdf_to_word_guide():
    return render_template("blogs/pdf-to-word-guide.html")


@app.route("/common-pvc-printing-mistakes")
def common_pvc_printing_mistakes():
    return render_template("blogs/common-pvc-printing-mistakes.html")


if __name__ == "__main__":
    app.run()
