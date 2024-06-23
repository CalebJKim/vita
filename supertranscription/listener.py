from audiorecorder import AudioRecorder
from groqclient import GroqClient
from realtimeprocessor import RealTimeProcessor
import threading

class Listener:
    def __init__(self):
        self.audio_recorder = AudioRecorder()
        self.groq_client = GroqClient()
        self.real_time_processor = RealTimeProcessor(self.audio_recorder, self.groq_client)
        self.recording_thread = threading.Thread(target=self.audio_recorder.start_recording)

    def start(self):
        print("Recording started. Press 'q' and then Enter to stop.")
        self.recording_thread.start()
        self.real_time_processor.start()
        while True:
            key = input()
            if key == 'q':
                break
        self.audio_recorder.stop_recording()
        self.real_time_processor.stop()
        print("Recording stopped.")

        # Post-processing after recording stops
        transcript = self.real_time_processor.transcript_manager.get_transcript()
        print("Transcript:", transcript)

        bullets_path = "summary.txt"
        
        with open(bullets_path, 'r') as file:
            bullet_points = file.read()

        # Generate paragraph summary from transcript
        print("Summarizing the entire conversation...")
        paragraph_summary = self.groq_client.summarize_bullets(bullet_points)
        print("Paragraph Summary:", paragraph_summary)

        # Process the paragraph summary to create appointments and prescriptions
        print("Processing paragraph summary to create appointments and prescriptions...")
        self.groq_client.process_summary(paragraph_summary)

        self.audio_recorder.terminate()
        print("Summary saved to summary.txt")