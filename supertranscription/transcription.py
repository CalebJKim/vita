import os
import pyaudio
import wave
import speech_recognition as sr
import threading
from dotenv import load_dotenv
from groq import Groq
import json
import time
from listener import Listener

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    listener = Listener()
    listener.start()