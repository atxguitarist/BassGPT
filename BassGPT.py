
################################################################
# Nick Bild
# January 2023
# https://github.com/nickbild/voice_chatgpt
#
# Voice-controlled ChatGPT prompt
################################################################
# Jessie Carabajal
# June 2023
# Edits made to add Official OpenAI API calls and to add 
# animatronic movement.
#  
# -Create a Google Cloud Service account key and name it
# service_account.json and place in same directory as this script
# 
# -Add OpenAI API Key on line 181
################################################################



import os
import io
import sys
import openai
import asyncio
import argparse
import pyaudio
import wave
import time
import subprocess
import threading
import RPi.GPIO as GPIO
from google.cloud import speech
from google.cloud import texttospeech
from ChatGPT_lite.ChatGPT import Chatbot
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

gpt_response = ""


def speech_to_text(speech_file):
    client = speech.SpeechClient()

    with io.open(speech_file, "rb") as audio_file:
            content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    stt = ""
    for result in response.results:
        stt += result.alternatives[0].transcript
    return stt


    gpt_response = response['answer']



def text_to_speech(tts):
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=tts)

    # Build the voice request, select the language code ("en-US") and the ssml
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("result.wav", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    return


def record_wav():
    form_1 = pyaudio.paInt16
    chans = 1
    samp_rate = 48000
    chunk = 4096
    record_secs = 4
    dev_index = 1
    wav_output_filename = 'input.wav'

    audio = pyaudio.PyAudio()

    # Create pyaudio stream.
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)
    print("recording")
    frames = []

    # Loop through stream and append audio chunks to frame array.
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data = stream.read(chunk)
        frames.append(data)

    print("finished recording")

    # Stop the stream, close it, and terminate the pyaudio instantiation.
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the audio frames as .wav file.
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()

    return

def mouth_move():
    mouth_pin = 27
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(mouth_pin, GPIO.OUT)
    while True:
        GPIO.output(mouth_pin, GPIO.HIGH)
        time.sleep(0.4)
        GPIO.output(mouth_pin, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(mouth_pin, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(mouth_pin, GPIO.LOW)
        time.sleep(0.4)
    return
    
def head_move():
    head_pin = 17
    tail_pin = 22
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(head_pin, GPIO.OUT)
    GPIO.setup(tail_pin, GPIO.OUT)
    while True:
        GPIO.output(head_pin, GPIO.HIGH)
        time.sleep(30)
        GPIO.output(head_pin, GPIO.LOW)
        time.sleep(2)
        GPIO.setup(tail_pin, GPIO.HIGH)
        time.sleep(2)
        GPIO.setup(tail_pin, GPIO.LOW)
        time.sleep(6)
    return

def play_audio():
    subprocess.call(["aplay", "result.wav"])
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_token_file', type=str, default="openai_session.txt")
    parser.add_argument('--bypass_node', type=str, default="https://gpt.pawan.krd")
    args = parser.parse_args()
    openai.api_key = "<*********OpenAI_API_Key_Here*********>"

    # Get WAV from microphone.
    thread = threading.Thread(target=head_move)
    thread.start()
    os.system("aplay RecordBeep.wav")
    record_wav()

    # Convert audio into text.
    os.system("aplay RecordBeep.wav")
    question = speech_to_text("input.wav")

    # Send text to ChatGPT.
    print("Asking: {0}".format(question))
    completion = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[
         {"role": "user", "content": question}
       ]
    )
    print(completion.choices[0].message.content)

    # Convert ChatGPT response into audio. 
    text_to_speech(completion.choices[0].message.content)

    # Play audio of reponse.
    print("Playing Audio")
    thread = threading.Thread(target=mouth_move)
    thread.start()
    play_audio()
    print("Done Playing Audio")
    # Cleanup GPIO
    GPIO.cleanup()

if __name__ == "__main__":
    main()
