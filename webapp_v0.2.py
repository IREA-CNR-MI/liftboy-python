import os
from flask import Flask, flash, request, redirect, url_for, Response, send_file, send_from_directory, render_template
from werkzeug.utils import secure_filename
from app import liftboy
#from redis import Redis
#import rq

# LATER TRY TO MAKE THIS PATH RELATIVE
UPLOAD_FOLDER = './input'
OUTPUT_FOLDER = './output'
TEMPLATES_FOLDER = './templates'
ALLOWED_EXTENSIONS = set(['xml'])

app = Flask(__name__)   #create the Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['TEMPLATES_FOLDER'] = TEMPLATES_FOLDER
app.secret_key = "super secret key"

#job = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/liftboy-form', methods=['GET', 'POST'])
def form_example():
    #global job
    # if the request is a POST
    if request.method == 'POST':
        # metadata file
        # check if the post request has the metadata part
        if 'metadata' not in request.files:
            flash('No metadata part')
            return redirect(request.url)
        metadata = request.files['metadata']
        # if user does not select file, browser also
        # submit an empty part without filename
        if metadata.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if metadata and allowed_file(metadata.filename):
            metadata_filename = secure_filename(metadata.filename)
            metadata.save(os.path.join(app.config['UPLOAD_FOLDER'], metadata_filename))
        # template file
        template_filename = ''
        # check if the post request has the template part
        if 'template' in request.files:
            template = request.files['template']
            if template and allowed_file(template.filename):
                template_filename = secure_filename(template.filename)
                template.save(os.path.join(app.config['TEMPLATES_FOLDER'], template_filename))

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
        return redirect('/liftboy-form?metadata=' + metadata_filename + '&template=' + template_filename, code=302)

    # if the request is a GET one but contains the job ID
    #if request.args.get('jID'):
    # if the request is a GET one but contains the input file name
    elif request.args.get('metadata'):
        metadata = request.args.get('metadata')
        template = request.args.get('template')
        # execute liftboy
        liftboy.do_lift(metadata, template)
        #ediml_id = liftboy.do_lift(metadata,template)
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
        return send_from_directory(app.config['OUTPUT_FOLDER'], metadata[:metadata.rfind('.')] + '_transformed.ediml', as_attachment=True)
        #return redirect('file:///media/cristiano/MyData/home/cristiano/Documents/debug_EDI/EDI-NG_client-master/dist/ISO1936_template_edi_v1.00.html?edit=' + ediml_id, code=302)

    # request is GET and no parameters are contained in the URL
    return render_template('input.html')


@app.route('/liftboy-api', methods=['POST'])
def api_example():
    # if the request is a POST
    if request.method == 'POST':
        # metadata file
        # check if the post request has the metadata part
        if 'metadata' not in request.files:
            flash('No metadata part')
            return redirect(request.url)
        metadata = request.files['metadata']
        # if user does not select file, browser also
        # submit an empty part without filename
        if metadata.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if metadata and allowed_file(metadata.filename):
            metadata_filename = secure_filename(metadata.filename)
            metadata.save(os.path.join(app.config['UPLOAD_FOLDER'], metadata_filename))
        # template file
        template_filename = ''
        # check if the post request has the template part
        if 'template' in request.files:
            template = request.files['template']
            if template and allowed_file(template.filename):
                template_filename = secure_filename(template.filename)
                template.save(os.path.join(app.config['TEMPLATES_FOLDER'], template_filename))

        return redirect('/liftboy-form?metadata=' + metadata_filename + '&template=' + template_filename, code=302)

    # if the request is a GET one but contains the job ID
    #if request.args.get('jID'):
    # if the request is a GET one but contains the input file name
    elif request.args.get('metadata'):
        metadata = request.args.get('metadata')
        template = request.args.get('template')
        # execute liftboy
        liftboy.do_lift(metadata,template)
        #ediml_id = liftboy.do_lift(metadata,template)
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
        return send_from_directory(app.config['OUTPUT_FOLDER'], metadata[:metadata.rfind('.')] + '_transformed.ediml', as_attachment=True)
        #return redirect('file:///media/cristiano/MyData/home/cristiano/Documents/debug_EDI/EDI-NG_client-master/dist/ISO1936_template_edi_v1.00.html?edit=' + ediml_id, code=302)
    # request is GET and no parameters are contained in the URL
    return render_template('input.html')


if __name__ == "__main__":
    app.run()