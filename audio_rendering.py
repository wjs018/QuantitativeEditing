import librosa
import matplotlib.pyplot as plt
import numpy as np

from moviepy.editor import *
from librosa.display import waveplot
from moviepy.video.io.bindings import mplfig_to_npimage


def animate_audio(video, audio, output):
    """
    Renders a waveform of a video's audio and progresses it every 0.5s as the
    video plays.
    
    Parameters
    -----------
    
    video
      filepath to a video that has audio
    
    audio
      filepath to save the extracted audio from video as an .mp3
    
    output
      filepath to save the animated audio to as a .mp4
    
    Returns
    --------
    
    output
      Simply returns the filepath to the saved output video
    """
    
    # Load video and extract audio to file
    video_file = VideoFileClip(video)
    extracted_audio = video_file.audio
    extracted_audio.write_audiofile(audio)
    
    # Load the saved audio into librosa
    y, sr = librosa.load(audio, mono=False)
    
    # Make a waveplot figure
    fig, ax = plt.subplots(1, figsize=(12, 2), facecolor='white')
    waveplot(y, sr=sr, color='b', alpha=0.25)
    
    # Initialize some variables
    last_t = 0
    tempgraph = mplfig_to_npimage(fig)
    
    # Function to animate our graph
    def animate(t):
        
        # Access our initialized variables from outside the function
        global last_t
        global tempgraph
        
        # Round time to nearest 0.5 second. This limits the number of times we
        # update the graph. Each graph update costs 10-20 seconds to draw, so by
        # limiting this, we can render the graph an order of magnitude faster
        temp_t = np.round(t * 2) / 2.0
        
        # Only update the graph if we are at the next 0.5 seconds
        if t > 0 and temp_t != last_t:
            
            # Update our timekeeping variable
            last_t = temp_t
            
            # Delete the previous graph, otherwise we will keep plotting over
            # the same graphs again and again
            for coll in (ax.collections):
                ax.collections.remove(coll)
            
            # Load only the played portion of the mp3 and plot them
            y2, sr2 = librosa.load('extracted_audio.mp3', mono=False,
                                   duration=t)
            waveplot(y2, sr=sr2, color='b', alpha=0.8)
            waveplot(y, sr=sr, color='b', alpha=0.25)
            
            # Update the output graph
            tempgraph = mplfig_to_npimage(fig)
        
        return tempgraph
    
    # Make a video of the animated graph and save it
    animation1 = VideoClip(animate, duration=video.duration)
    animation1.write_videofile(output, fps=video.fps)
    
    return output


if __name__ == '__main__':
    
    # Import source video and extract the audio to an mp3
    video = VideoFileClip('BTS_2016_Fire.mkv')
    audio = video.audio
    audio.write_audiofile('extracted_audio.mp3')
    
    # Load the mp3 into librosa
    y, sr = librosa.load('extracted_audio.mp3', mono=False)
    
    # Make a waveplot figure
    fig, ax = plt.subplots(1, figsize=(12, 2), facecolor='white')
    waveplot(y, sr=sr, color='b', alpha=0.25)
    
    # Initialize some variables
    last_t = 0
    tempgraph = mplfig_to_npimage(fig)
    
    # Function to animate our graph
    def animate1(t):
        
        # Access our initialized variables from outside the function
        global last_t
        global tempgraph
        
        # Round time to nearest 0.5 second. This limits the number of times we
        # update the graph. Each graph update costs 10-20 seconds to draw, so by
        # limiting this, we can render the graph an order of magnitude faster
        temp_t = np.round(t * 2) / 2.0
        
        # Only update the graph if we are at the next 0.5 seconds
        if t > 0 and temp_t != last_t:
            
            # Update our timekeeping variable
            last_t = temp_t
            
            # Delete the previous graph, otherwise we will keep plotting over
            # the same graphs again and again
            for coll in (ax.collections):
                ax.collections.remove(coll)
            
            # Load only the played portion of the mp3 and plot them
            y2, sr2 = librosa.load('extracted_audio.mp3', mono=False,
                                   duration=t)
            waveplot(y2, sr=sr2, color='b', alpha=0.8)
            waveplot(y, sr=sr, color='b', alpha=0.25)
            
            # Update the output graph
            tempgraph = mplfig_to_npimage(fig)
        
        return tempgraph
    
    # Make a video of the animated graph and save it
    animation1 = VideoClip(animate1, duration=video.duration)
    animation1.write_videofile('audio_animation1.mp4', fps=video.fps)
