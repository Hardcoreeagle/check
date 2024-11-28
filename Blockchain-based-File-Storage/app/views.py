import json
import os
import requests
from flask import render_template, redirect, request, send_file
from werkzeug.utils import secure_filename
from app import app
from timeit import default_timer as timer

# Stores all the post transaction in the node
request_tx = []
# store filename
files = {}
# destination for upload files
UPLOAD_FOLDER = "app/static/Uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# store address (change to use environment variable for Render deployment)
ADDR = os.environ.get("ADDR", "http://127.0.0.1:8800")  # Default to 127.0.0.1 if not set

# create a list of requests that peers have sent to upload files
def get_tx_req():
    global request_tx
    chain_addr = "{0}/chain".format(ADDR)
    resp = requests.get(chain_addr)
    if resp.status_code == 200:
        content = []
        chain = json.loads(resp.content.decode())
        for block in chain["chain"]:
            for trans in block["transactions"]:
                trans["index"] = block["index"]
                trans["hash"] = block["prev_hash"]
                content.append(trans)
        request_tx = sorted(content, key=lambda k: k["hash"], reverse=True)


# Loads and runs the home page
@app.route("/")
def index():
    get_tx_req()
    return render_template("index.html", title="FileStorage", subtitle="A Decentralized Network for File Storage/Sharing", node_address=ADDR, request_tx=request_tx)


@app.route("/submit", methods=["POST"])
def submit():
    start = timer()
    user = request.form["user"]
    up_file = request.files["v_file"]
    
    # Ensure the uploads directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Save the uploaded file in the correct directory
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(up_file.filename))
    up_file.save(file_path)

    # Add the file to the list to create a download link
    files[up_file.filename] = file_path

    # Determine the size of the file uploaded in bytes 
    file_size = os.stat(file_path).st_size

    # Create a transaction object
    post_object = {
        "user": user,  # User name
        "v_file": up_file.filename,  # Filename
        "file_data": str(up_file.stream.read()),  # File data
        "file_size": file_size  # File size
    }

    # Submit a new transaction
    address = f"{ADDR}/new_transaction"
    requests.post(address, json=post_object)
    
    end = timer()
    print(end - start)
    return redirect("/")



# creates a download link for the file
@app.route("/submit/<string:variable>", methods=["GET"])
def download_file(variable):
    p = files[variable]
    return send_file(p, as_attachment=True)
