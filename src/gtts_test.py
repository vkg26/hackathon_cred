from gtts import gTTS

# Hindi text you want to convert to speech
hindi_text = "मैं अपना HDFC का क्रेडिट कार्ड बिल पे करना चाहता हूँ"
marathi_text = "मी माझ्या HDFC च्या क्रेडिट कार्डचा बिल भरायचं आहे"
bengali_text = "আমি আমার HDFC ক্রেডিট কার্ডের বিল পরিশোধ করতে চাই"

# Create a gTTS object
tts = gTTS(text=hindi_text, lang='hi')
# Save the audio file
tts.save("hindi_audio.mp3")
print("Hindi audio file has been saved as 'hindi_audio.mp3'")

tts = gTTS(text=marathi_text, lang='mr')
# Save the audio file
tts.save("marathi_audio.mp3")
print("Marathi audio file has been saved as 'marathi_audio.mp3'")

tts = gTTS(text=bengali_text, lang='bn')
# Save the audio file
tts.save("bengali_audio.mp3")
print("Bengali audio file has been saved as 'bengali_audio.mp3'")


