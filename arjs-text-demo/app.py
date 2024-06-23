from flask import Flask, render_template, Response
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import threading
import time
import os

app = Flask(__name__)

# Adjust the paths
text_file_path = os.path.join('..', 'supertranscription', 'summary.txt')
fixed_text_file_path = "fixed_text.txt"
latest_text = ""
fixed_text = ""

# Track the last read position
last_read_position = 0

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def read_text_file():
    global latest_text, last_read_position
    try:
        with open(text_file_path, "r") as file:
            # Move the file pointer to the last read position
            file.seek(last_read_position)
            new_content = file.read()
            if new_content:
                latest_text += new_content.replace("\n", "<br>")
                last_read_position = file.tell()
                logging.info(f'Latest text updated: {latest_text}')
    except Exception as e:
        logging.error(f'Error reading {text_file_path}: {e}')

def read_fixed_text_file():
    global fixed_text
    try:
        with open(fixed_text_file_path, "r") as file:
            fixed_text = file.read().replace("\n", "<br>")
            logging.info(f'Fixed text loaded: {fixed_text}')
    except Exception as e:
        logging.error(f'Error reading {fixed_text_file_path}: {e}')

class TextFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('summary.txt'):
            logging.info(f'{text_file_path} has been modified.')
            read_text_file()

@app.route('/')
def index():
    global fixed_text  # Ensure fixed_text is updated before rendering
    read_fixed_text_file()
    return render_template('index.html', initial_text=latest_text, fixed_text=fixed_text)

@app.route('/stream')
def stream():
    def generate():
        global latest_text
        while True:
            time.sleep(1)
            if latest_text:
                yield f"data: {latest_text}\n\n"
                latest_text = ""
    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    # Read the initial and fixed texts
    read_text_file()
    read_fixed_text_file()

    # Set up the observer
    event_handler = TextFileHandler()
    observer = Observer()
    # Use the directory of the text_file_path
    observer.schedule(event_handler, path=os.path.dirname(text_file_path), recursive=False)
    observer_thread = threading.Thread(target=observer.start)
    observer_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

    # Stop the observer
    observer.stop()
    observer.join()
