import subprocess
import threading
import time
import webbrowser
import os
import signal

# Function to run a script in a specified directory
def run_script(script_path, script_name):
    subprocess.run(['python3', script_name], cwd=script_path)

# Run main.py in facecv for 20 seconds
facecv_process = subprocess.Popen(['python3', 'main.py'], cwd='facecv')
time.sleep(26)
facecv_process.terminate()

# Function to terminate a process group
def terminate_process_group(process):
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)

# Run transcription.py
transcription_thread = threading.Thread(target=run_script, args=('supertranscription', 'tester.py'))

# Run app.py and open browser tab
def run_app_and_open_browser():
    run_script('arjs-text-demo', 'app.py')
    webbrowser.open_new_tab('http://127.0.0.1:5000/')

app_thread = threading.Thread(target=run_app_and_open_browser)

transcription_thread.start()
app_thread.start()

# Wait for both scripts to finish
transcription_thread.join()
app_thread.join()
