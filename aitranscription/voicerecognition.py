import speech_recognition as sr

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    async def listen_until_quit(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Listening continuously... Press 'q' to stop.")
            full_transcript = ""
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio)
                    print(f"Recognized Text: {text}")
                    full_transcript += text + " "
                except sr.UnknownValueError:
                    print("Sorry, I could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                except sr.WaitTimeoutError:
                    pass

                if self._is_quit_pressed():
                    break

            return full_transcript

    def _is_quit_pressed(self):
        import sys
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            ch = sys.stdin.read(1)
            if ch == 'q':
                return True
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return False
