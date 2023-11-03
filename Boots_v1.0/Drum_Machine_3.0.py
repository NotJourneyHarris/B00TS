import tkinter as tk
from tkinter import filedialog
import librosa
import soundfile as sf
from pyrubberband import time_stretch
from pydub import AudioSegment
import pygame
import RPi.GPIO as GPIO
import time

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)

# Declare global variables
user_song = ""
output_file = ""
selected_drum_loop = ""

# Function to time-stretch an audio track to match the reference song's tempo
def inputAudio():
    global user_song, output_file, selected_drum_loop

    user_song = entry_path.get()
    output_file = '/home/boobo/Desktop/Boots_v1.0/Your_Song.wav'
    selected_drum_loop = drum_loop_var.get()

    # Define the drum loop file based on the selection
    if selected_drum_loop == "Drum Loop 1":
        drum_loop_file = '/home/boobo/Desktop/Boots_v1.0/drum_loop.wav'
    elif selected_drum_loop == "Drum Loop 2":
        drum_loop_file = '/home/boobo/Desktop/Boots_v1.0/drum_loop2.wav'
    else:
        result_label.config(text="Error: Invalid drum loop selection.")
        return

    # Calculate the BPM of the input song
    y_ref, sr_ref = librosa.load(user_song, sr=None)
    onset_env_ref = librosa.onset.onset_strength(y=y_ref, sr=sr_ref)
    input_tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env_ref, sr=sr_ref)

    if input_tempo is None:
        result_label.config(text="Error extracting reference song's tempo. Stopping.")
        return

    # Calculate the initial BPM of the selected drum loop
    y, sr = librosa.load(drum_loop_file, sr=None)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    loop_tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    if loop_tempo is None:
        result_label.config(text="Error extracting drum loop's tempo. Stopping.")
        return

    # Print the initial tempo of the drum loop and the new song's tempo
    initial_tempo_label.config(text=f"Initial Tempo (Selected Drum Loop): {loop_tempo} BPM")
    user_song_label.config(text=f"Your Song's Tempo: {input_tempo} BPM")

    # Calculate the time-stretching factor to match the reference song's tempo
    stretch_factor = input_tempo / loop_tempo

    # If stretch_factor is greater than 1, speed up using Pydub
    if stretch_factor > 1.0:
        result_label.config(text=f"Speeding up by a factor of {stretch_factor:.2f}")
        audio = AudioSegment.from_file(drum_loop_file)
        stretched_audio = audio.speedup(playback_speed=stretch_factor)
        stretched_audio.export(output_file, format="wav")
    # If stretch_factor is less than 1, slow down using pyrubberband
    elif stretch_factor < 1.0:
        result_label.config(text=f"Slowing down by a factor of {1/stretch_factor:.2f}")
        y_stretched = time_stretch(y, sr, stretch_factor)
        sf.write(output_file, y_stretched, sr)
    else:
        result_label.config(text="No time-stretching needed.")
        return

    # Export the output
    result_label.config(text="Audio stretched successfully.")

    # Show the "Mix Audio" button
    mix_audio_button.pack(pady=20)

    # Show the "Play Output" button
    play_output_button.pack(pady=20)

# Function to mix the audio
def mixAudio():
    global user_song, output_file

    # Load the user's song and the stretched drum loop
    user_audio = AudioSegment.from_file(user_song)
    stretched_audio = AudioSegment.from_file(output_file)

    mixed_audio = user_audio.overlay(stretched_audio)

    # Export the mixed audio
    mixed_audio.export(output_file, format="wav")

    # Export the output
    result_label.config(text="Audio stretched and mixed successfully.")

    # Show the "Play Output" button
    play_output_button.pack(pady=20)

# Function to play the output file
def playOutput():
    output_file = '/home/boobo/Desktop/Boots_v1.0/Your_Song.wav'

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        # Analyze beats using librosa
        y, sr = librosa.load(output_file, sr=None)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

        beat_duration = 60 / tempo  # Duration of one beat in seconds

        # Wait for the music to start
        time.sleep(beat_duration)

        while pygame.mixer.music.get_busy():
            # Get the current beat
            beat_start_time = pygame.mixer.music.get_pos() / 1000.0
            current_beat = int(beat_start_time / beat_duration)

            # Turn off all LEDs
            GPIO.output(17, GPIO.LOW)
            GPIO.output(18, GPIO.LOW)
            GPIO.output(19, GPIO.LOW)
            GPIO.output(20, GPIO.LOW)

            # Turn on one LED based on the current beat
            if current_beat % 4 == 0:
                GPIO.output(17, GPIO.HIGH)
            elif current_beat % 4 == 1:
                GPIO.output(18, GPIO.HIGH)
            elif current_beat % 4 == 2:
                GPIO.output(19, GPIO.HIGH)
            elif current_beat % 4 == 3:
                GPIO.output(20, GPIO.HIGH)

            # Adjust sleep time to control the LED flashing speed
            time.sleep(0.05)  # Adjust as needed

        # Stop flashing LEDs after playback
        GPIO.output(17, GPIO.LOW)
        GPIO.output(18, GPIO.LOW)
        GPIO.output(19, GPIO.LOW)
        GPIO.output(20, GPIO.LOW)

    except Exception as e:
        result_label.config(text=f"Error playing output: {e}")
        return

# Function to reset the system
def resetSystem():
    global user_song, output_file, selected_drum_loop

    # Clear entry widget
    entry_path.delete(0, tk.END)

    # Reset dropdown menu
    drum_loop_var.set(drum_loops[0])

    # Clear labels
    initial_tempo_label.config(text="")
    user_song_label.config(text="")
    result_label.config(text="")

    # Turn off LEDs
    GPIO.output(17, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
    GPIO.output(19, GPIO.LOW)
    GPIO.output(20, GPIO.LOW)

    # Stop music playback
    pygame.mixer.music.stop()

# Create the main window
root = tk.Tk()
'''window_width = 1024
window_height = 600
root.geometry(f"{window_width}x{window_height}")'''
root.attributes('-fullscreen', True)
root.title("BOOTS v1.0")

# Set the background color and font
root.configure(bg='black')
root.option_add('*Font', 'Courier 24')

# Set text color to white
text_color = 'white'

# Create a label
label = tk.Label(root, text="Select a reference song:", fg=text_color, bg='black')
label.pack(pady=20)

# Create an entry widget to display the selected file path
entry_path = tk.Entry(root, width=50)
entry_path.pack()

# Create a button to browse for an input song file
browse_button = tk.Button(root, text="Browse", fg="white", bg='black', command=lambda: entry_path.insert(0, filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])))
browse_button.pack(pady=20)

# Create a dropdown menu to select the drum loop
drum_loops = ["Drum Loop 1", "Drum Loop 2"]
drum_loop_var = tk.StringVar()
drum_loop_var.set(drum_loops[0])  # Set the initial selection
drum_loop_menu = tk.OptionMenu(root, drum_loop_var, *drum_loops)
drum_loop_menu.config(fg='black', bg='white')
drum_loop_menu.pack(pady=20)

# Create a button to start time-stretching
stretch_button = tk.Button(root, text="Stretch Audio", fg='white', bg='black', command=inputAudio)
stretch_button.pack(pady=20)

# Labels to display drum loop and input track's tempo
initial_tempo_label = tk.Label(root, text="", fg='white', bg='black')
initial_tempo_label.pack()
user_song_label = tk.Label(root, text="", fg='white', bg='black')
user_song_label.pack()

# Create a button to play the output file
play_output_button = tk.Button(root, text="Play Output", fg="white", bg='black', command=playOutput)

# Create a button to reset the system
reset_button = tk.Button(root, text="Reset", fg="white", bg='black', command=resetSystem)

# Create the Mix Audio button, but initially, it should be hidden
mix_audio_button = tk.Button(root, text="Mix Audio", fg="white", bg='black', command=mixAudio)
mix_audio_button.pack_forget()
# Label to reset loop
reset_button = tk.Button(root, text="Reset", fg="white", bg='black', command=resetSystem)
reset_button.pack(pady=20)

play_output_button.pack_forget()
# Label to display results
result_label = tk.Label(root, text="", fg='white', bg='black')
result_label.pack()

# Run the main event loop
root.mainloop()

# Cleanup GPIO on program exit
GPIO.cleanup()
