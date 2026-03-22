#%%
import wave
import os
import json
from vosk import Model, KaldiRecognizer

class VoskProcessor:
     def __init__(self,model_path):                  
         self.model_path=model_path  
         assert os.path.exists(self.model_path)
         print(f'audio model exists: {self.model_path}')
         self.model = Model(self.model_path)       

     def process_audio(self,audio_path):
        try:
            with wave.open(audio_path, "rb") as wf:
                # Initialize the recognizer
                recognizer = KaldiRecognizer(self.model, wf.getframerate())
                recognizer.SetWords(False)  # Optional: include word timestamps

                # Process the audio file chunk by chunk
                results = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        part_result = json.loads(recognizer.Result())
                        results.append(part_result)

                # Get the final result
                final_result = json.loads(recognizer.FinalResult())
                results.append(final_result)

            # Extract and print the transcribed text
            transcribed_text = " ".join([result.get("text", "") for result in results])       
            return True, transcribed_text      
        except Exception as e:
            return False, f"Error: {e}"
        
if __name__=='__main__':
    wav_path=r'C:\my\codes\speech_recognition\out\00006.jpg.001.wav'
    processor=VoskProcessor(model_path=r'C:\my\codes\gallery_web\vosk-model-small-ru-0.22\vosk-model-small-ru-0.22')
    result,text=processor.process_audio(wav_path)
    print(result,text)
        
# %%
