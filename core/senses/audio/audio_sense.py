# ./brainbot/core/senses/audio/audio_sense.py
# Created by: David Kistner (Unconditional Love)



#system imports
import os, pyttsx3, librosa, pygame, speech_recognition as sr
from datetime import datetime



# =======================
# AUDIO CONTROLLER CLASS
# =======================
class AudioController:
    # ------------
    # Initialize
    # ------------
    def __init__(self, log_function=None): #AudioController initialization
        self.log = log_function or (lambda msg: print(msg))
    # ----------------------
    # Listen and Transcribe
    # ----------------------
    def listen_and_transcribe(self, timeout=5, phrase_time_limit=10): #listener and transcriber
        recognizer = sr.Recognizer()
        try:

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("🎙️ Listening...")
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            transcript = recognizer.recognize_google(audio)
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            return {
                "timestamp": timestamp,
                "text": transcript.strip()
            }

        except sr.WaitTimeoutError:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "text": "(No speech detected — silence)"
            }

        except sr.UnknownValueError:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "text": "(Speech unintelligible)"
            }

        except sr.RequestError as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "text": f"(Recognition error: {e})"
            }
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "text": f"(Unexpected error: {e})"
            }
    # ------------
    # Play Audio
    # ------------
    def play_audio(self, filepath): #audio player
        try:

            if not os.path.exists(filepath):
                self.log(f"⚠️ Audio file not found: {filepath}")
                return False

            pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                continue

            self.log(f"🔊 Played audio: {filepath}")
            return True

        except Exception as e:
            self.log(f"⚠️ Failed to play audio: {e}")
            return False
    # -------------------
    # Synthesize Speech
    # -------------------
    def synthesize_speech(self, text, agent=None):

        try:
            engine = pyttsx3.init()

            if agent and "voice_profile" in agent and agent["voice_profile"]:
                vp = agent["voice_profile"]
                tempo = vp.get("tempo", 150)
                engine.setProperty("rate", int(tempo))
                # pitch is best‑effort; some engines ignore it
                pitch = vp.get("pitch", 150)

                try:
                    engine.setProperty("pitch", int(pitch))

                except Exception:
                    pass

            engine.say(text)
            engine.runAndWait()
            self.log(f"🗣️ Synthesized speech for {agent.get('name','?') if agent else 'BrainBot'}: {text[:60]}...")
            return True

        except Exception as e:
            self.log(f"⚠️ Speech synthesis failed: {e}")
            return False
    # -------------------
    # Load Voice Profile
    # -------------------
    def load_voice_profile(self, filepath): #voice profile loader (converts voice from .mp3)

        try:
        
            if not os.path.exists(filepath):
                self.log(f"⚠️ Voice file not found: {filepath}")
                return False

            # Extract pitch, tempo, and timbre features
            y, sr = librosa.load(filepath)
            pitch = librosa.yin(y, fmin=50, sr=sr).mean()
            tempo = librosa.beat.tempo(y, sr=sr)[0]
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
            self.voice_profile = {
                "pitch": pitch,
                "tempo": tempo,
                "mfcc": mfcc.tolist()
            }
            self.log(f"🎙️ Voice profile loaded from {filepath}")
            return True

        except Exception as e:
            self.log(f"⚠️ Failed to load voice profile: {e}")
            return False

        return 
        self.voice_profile
    # ------------
    # Voice Loop
    # ------------
    def voice_loop(self, cognition, timeout=5, phrase_time_limit=10):

        while True:
            transcript_data = self.listen_and_transcribe(timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = transcript_data.get("text", "")

            if not text or text.startswith("("):
                continue

            self.log(f"🎧 Heard: {text}")
            response = cognition.respond(text, source="voice")
            self.synthesize_speech(response)

