import os
from flask import Flask, flash, request, redirect, url_for, Response, send_file, send_from_directory
from werkzeug.utils import secure_filename
from app import liftboy
#from redis import Redis
#import rq

# LATER TRY TO MAKE THIS PATH RELATIVE
UPLOAD_FOLDER = '/home/cristiano/devel/liftboy-python/input'
ALLOWED_EXTENSIONS = set(['xml'])

app = Flask(__name__)   #create the Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key"

#job = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/liftboy-form', methods=['GET', 'POST'])
def form_example():
    #global job
    # if the request is a POST
    if request.method == 'POST':
        # check if the post request has the file part
        if 'metadata' not in request.files:
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

        # connect to the 'liftboy-tasks' queue
        #queue = rq.Queue('liftboy-tasks', connection=Redis.from_url('redis://'))
        # istantiate the liftboy task
        #job = queue.enqueue_call(func='app.liftboy_v0.10.do_lift', args=(filename,))
        # get the job ID
        #jID = job.get_id()
        # add job metadata containing filename and progress status
        #job.meta['filename'] = filename
        #job.meta['progress'] = 0
        #job.save_meta()
        # redirect to URL containing the jID
        #return redirect('/liftboy-form?jID='+jID, code=302)
        return redirect('/liftboy-form?metadata=' + filename, code=302)

    # if the request is a GET one but contains the job ID
    #if request.args.get('jID'):
    # if the request is a GET one but contains the input file name
    if request.args.get('metadata'):
        metadata = request.args.get('metadata')
        # execute liftboy
        liftboy.do_lift(metadata)
        # connect to the 'liftboy-tasks' queue
        #queue = rq.Queue('liftboy-tasks', connection=Redis.from_url('redis://'))
        #task = queue.fetch_job(request.args.get('jID'))
        #filename = job.meta.get('filename')
        #progress = job.meta.get('progress')
        # if execution of liftboy still in progress
        #if not os.path.isfile('output/' + metadata + '_transformed.ediml'):
        data = '''
                     <!doctype html>
                     <html>
                         <head>
                             <meta content="text/html;charset=utf-8" http-equiv="Content-Type" />
                             <!-- <meta http-equiv="refresh" content="2" /> -->
                             <title>Test liftboy-python interface</title>
                         </head>
                         <body>
                            <div>Processing file ''' + metadata + '''</div>
                         </body>
                     </html>
                 '''
        #return data
        #else:
        #return send_file(data, attachment_filename='output/' + metadata + '_transformed.ediml')
        #return send_file('output/' + metadata[:metadata.rfind('.')] + '_transformed.ediml', attachment_filename=metadata[:metadata.rfind('.')] + '_transformed.ediml')
        return send_from_directory('output', metadata[:metadata.rfind('.')] + '_transformed.ediml', as_attachment=True)

    # request is GET and no parameters are contained in the URL
    data = '''
        <!doctype html>
        <html>
            <head>
                <meta content="text/html;charset=utf-8" http-equiv="Content-Type" />
                <script>
                    var uID = Math.floor((Math.random()*100)+1);
                    function doSubmit() {
                        document.forms.liftboy_input.submit();
                    }
                </script>
                <title>Test liftboy-python interface</title>
            </head>
            <body>
                <form method="POST" enctype="multipart/form-data" id="liftboy_input" name="liftboy_input">
                    Metadata:<br/>
                    <input type="file" id="metadata" name="metadata" accept="text/xml, application/xml"><br/>
                    Template: (optional)<br/>
                    <input type="file" id="template" name="template" accept="text/xml, application/xml"><br/>
                    <input type="submit" onClick="doSubmit()"><br>
                </form>
            </body>
        </html>
    '''
    #res = Response(data, mimetype='text/html')
    #res.headers["Content-Type"] = "text/html; charset=utf-8"
    #return render_template('static/input.html')
    return data


if __name__ == "__main__":
    app.run()