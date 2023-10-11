import tkinter as tk
from tkinter import filedialog
import librosa
import soundfile as sf
from pyrubberband import time_stretch
from pydub import AudioSegment
import os
import paramiko

def send_audio_to_pi(file_path, raspberry_pi_ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(raspberry_pi_ip, username='pi@raspberry', password="raspberry")

        # Use scp to copy the audio file to the Raspberry Pi
        scp_command = f'scp {file_path} pi@{raspberry_pi_ip}:received_audio.wav'
        os.system(scp_command)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

# Function to time-stretch an audio track to match the reference song's tempo
def inputAudio():
    user_song = entry_path.get()
    selected_drum_loop = drum_loop_var.get()  # Get the selected drum loop
    output_file = 'Boots_v1.0/Your_Song.wav'

    # Define the drum loop file based on the selection
    if selected_drum_loop == "Drum Loop 1":
        drum_loop_file = 'Boots_v1.0/drum_loop.wav'
    elif selected_drum_loop == "Drum Loop 2":
        drum_loop_file = 'Boots_v1.0/drum_loop2.wav'
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
    # If stretch_factor is less than 1, slow down using pyrubberband
    elif stretch_factor < 1.0:
        result_label.config(text=f"Slowing down by a factor of {1/stretch_factor:.2f}")
        y_stretched = time_stretch(y, sr, stretch_factor)
        sf.write(output_file, y_stretched, sr)
    else:
        result_label.config(text="No time-stretching needed.")
        return

    # Export the output
    if stretch_factor > 1.0:
        stretched_audio.export(output_file, format="wav")
        result_label.config(text="Audio stretched and saved successfully.")
        send_audio_to_pi(output_file, raspberry_pi_ip, username, password)
        play_audio_on_pi()
        
        # Show the "Play Output" button
        play_output_button.pack(pady=10)

# Function to play the output file
def playOutput():
    output_file = 'Boots_v1.0/Your_Song.wav'    
    os.system(f'afplay {output_file}')

# Create the main window
root = tk.Tk()
root.title("BOOTS v1.0")

# Set the background color and font
root.configure(bg='black')
root.option_add('*Font', 'Courier 12')

# Set text color to white
text_color = 'white'

# Create a label
label = tk.Label(root, text="Select a reference song:", fg=text_color, bg='black')
label.pack(pady=10)

# Create an entry widget to display the selected file path
entry_path = tk.Entry(root, width=50)
entry_path.pack()

# Create a button to browse for an input song file
browse_button = tk.Button(root, text="Browse", fg="black", bg='black', command=lambda: entry_path.insert(0, filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])))
browse_button.pack(pady=10)

# Create a dropdown menu to select the drum loop
drum_loops = ["Drum Loop 1", "Drum Loop 2"]
drum_loop_var = tk.StringVar()
drum_loop_var.set(drum_loops[0])  # Set the initial selection
drum_loop_menu = tk.OptionMenu(root, drum_loop_var, *drum_loops)
drum_loop_menu.config(fg=text_color, bg='black')
drum_loop_menu.pack(pady=10)

# Create a button to start time-stretching
stretch_button = tk.Button(root, text="Stretch Audio", fg='black', bg='black', command=inputAudio)
stretch_button.pack(pady=10)

# Labels to display drum loop and input track's tempo
initial_tempo_label = tk.Label(root, text="", fg=text_color, bg='black')
initial_tempo_label.pack()
user_song_label = tk.Label(root, text="", fg=text_color, bg='black')
user_song_label.pack()

# Create a button to play the output file
play_output_button = tk.Button(root, text="Play Output", fg="black", bg='black', command=playOutput)

play_output_button.pack(pady=10)

# Label to display results
result_label = tk.Label(root, text="", fg=text_color, bg='black')
result_label.pack()

# Run the main event loop
root.mainloop()