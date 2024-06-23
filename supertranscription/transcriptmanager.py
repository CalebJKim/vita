class TranscriptManager:
    def __init__(self):
        self.transcript = ""

    def add_to_transcript(self, text):
        self.transcript += text + " "

    def get_transcript(self):
        return self.transcript

    def save_transcript(self, filename="transcript.txt"):
        with open(filename, "w") as f:
            f.write(self.transcript)

    def load_transcript(self, filename="transcript.txt"):
        with open(filename, "r") as f:
            self.transcript = f.read()