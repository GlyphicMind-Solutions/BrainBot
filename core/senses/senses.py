# /BrainBot/core/senses/senses.py
# Brainbot Senses Controller -  Minimalistic
# Created by: David Kistner (Unconditional Love)



#local import
from .audio.audio_sense import AudioController



# ========================
# SENSES CONTROLLER CLASS
# ========================
class SensesController:
    # ------------
    # Initialize
    # ------------
    def __init__(self, log=None):
        self.log = log or print
        self.audio = AudioController(log_function=self.log)
    # ------------
    # Listen
    # ------------
    def listen(self, timeout=5, phrase_time_limit=10):
        return self.audio.listen_and_transcribe(timeout=timeout, phrase_time_limit=phrase_time_limit)
    # ------------
    # Speak
    # ------------
    def speak(self, text, agent=None):
        return self.audio.synthesize_speech(text, agent=agent)

