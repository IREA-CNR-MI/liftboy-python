import os
from flask import Flask, flash, request, redirect, url_for, Response
from werkzeug.utils import secure_filename

# LATER TRY TO MAKE THIS PATH RELATIVE
UPLOAD_FOLDER = '/home/cristiano/devel/liftboy-python/input'
ALLOWED_EXTENSIONS = set(['xml', 'xsl'])

app = Flask(__name__)   #create the Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/form-example', methods=['GET', 'POST']) #allow both GET and POST requests
def form_example():
    #header("Content-type: text/html")
    if request.method == 'POST':
        # check if the post request has the file part
        if 'input' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['metadata']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = '''
            <!doctype html>
            <html>
                <head>
                    <meta content="text/html;charset=utf-8" http-equiv="Content-Type" />
                    <meta content="utf-8" http-equiv="encoding" />
                    <meta charset="utf-8" />
                </head>
                <body>
                    File uploaded
                </body>
            </html>
            '''
        #res = Response(data, mimetype='text/html')
        #res.headers["Content-Type"] = "text/html; charset=utf-8"
        #return res

    data = '''
            <!doctype html>
            <html>
                <head>
                    <meta content="text/html;charset=utf-8" http-equiv="Content-Type" />
                    <meta content="utf-8" http-equiv="encoding" />
                    <meta charset="utf-8" />
                </head>
                <body>
                    <form method="POST" enctype="multipart/form-data">
                        Metadata:<br/>
                        <input type="file" id="metadata" name="metadata" accept="text/xml, application/xml"><br/>
                        Template: (optional)<br/>
                        <input type="file" id="template" name="template" accept="text/xml, application/xml"><br/>
                        <input type="submit" value="Submit"><br>
                    </form>
                </body>
            </html>
            '''
    res = Response(data, mimetype='text/html')
    res.headers["Content-Type"] = "text/html; charset=utf-8"
    return res


if __name__ == "__main__":
    app.run()