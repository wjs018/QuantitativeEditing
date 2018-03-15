import numpy as np
import matplotlib.pyplot as plt

from moviepy.editor import *
from moviepy.video.io.bindings import mplfig_to_npimage

if __name__ == '__main__':
    
    #Boolean to set whether to include audio or not in final product
    include_audio = False
    
    # Read in data generated from previous video analysis
    scenes = np.loadtxt('MV_scenelist.csv', delimiter=',')
    
    # Break these columns apart to make it a little easier to index later
    scene_frames = scenes[:, 0]
    scene_times = scenes[:, 1]
    scene_durs = scenes[:, 2]
    
    # Calculate the time that passes each frame
    msec_per_frame = scene_times[-1] / scene_frames[-1]
    
    # Initialize a list to keep track of edits/sec
    rolling_average = []
    
    # Size of the rolling window to average over
    window_sec = 5.0
    
    # Keep track of number of scenes to have passed
    scene_count = []
    
    for i in range(int(np.max(scene_frames)) + 1):
        
        # First frame, starts with 0 edits per second
        if i == 0:
            rolling_average.append(0)
            scene_count.append(1)
            continue
        
        # Find current time in msec
        current_time = i * msec_per_frame
        
        # Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(current_time >= scene_times)]
        
        # Keep track of total number of scenes to have passed
        scene_count.append(len(in_window_scenes))
        
        # Then filter that down to scenes that have happened within the rolling
        # window prior to current frame
        in_window_scenes = len(in_window_scenes[np.where(
            current_time - window_sec * 1000. <= in_window_scenes)])
        
        # Find the rate from number of scenes
        scenes_per_sec = in_window_scenes / window_sec
        
        # Add this frame's rate to the list
        rolling_average.append(scenes_per_sec)
    
    # Calculate the average rate at which edits are made
    avg_rate = scene_count[-1] / (scene_times[-1] / 1000.0)
    
    # duration = 30
    duration = scene_times[-1] / 1000.0
    
    # Make the first figure that will keep track of the rate of transitions
    fig1, ax = plt.subplots(1, figsize=(4, 4), facecolor='white')
    ax.set_title("Rate of Scene Transitions \n (%0d sec Rolling Average)" % window_sec)
    ax.set_ylim(0, max(rolling_average))
    ax.set_xlim(0, duration)
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Detected Rate of Transitions (changes/sec)')
    line, = ax.plot(0, 0, 'k-')
    line2, = ax.plot([0, duration], [avg_rate, avg_rate], 'b-')
    plt.tight_layout()
    
    # Initialize lists to keep track of things
    times = []
    rates = []
    
    def make_frame1(t):
        """Function to make a graph of the rate of scene transitions."""
        
        times.append(t)
        
        # Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(t * 1000.0 >= scene_times)]
        
        # Then filter that down to scenes that have happened within the rolling
        # window prior to current frame
        in_window_scenes = len(in_window_scenes[np.where(
            t * 1000.0 - window_sec * 1000.0 <= in_window_scenes)])
        
        # Find the rate from number of scenes
        scenes_per_sec = in_window_scenes / window_sec
        
        # Add the rate to the list
        rates.append(scenes_per_sec)
        
        # Update the graph
        line.set_xdata(times)
        line.set_ydata(rates)
        
        return mplfig_to_npimage(fig1)
    
    # Use our function to animate a video and save it to file
    animation1 = VideoClip(make_frame1, duration=duration).resize(height=540)
    # animation1.write_videofile('rate_animation.mp4', fps=23.976)
    plt.close()
    
    # Animate plot of total scene transitions detected
    fig2, ax = plt.subplots(1, figsize=(4, 4), facecolor='white')
    ax.set_title("Number of Scene Transitions")
    ax.set_ylim(0, max(scene_count))
    ax.set_xlim(0, duration)
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Total Number of Detected Scenes')
    line, = ax.plot(0, 1, 'k-')
    line2, = ax.plot([0, duration], [1, max(scene_count)], 'b-')
    plt.tight_layout()
    
    # Initialize lists
    times = []
    scenes = []
    
    def make_frame2(t):
        """Function to graph the total number of scene transitions over time."""
        
        # Keep track of the time
        times.append(t)
        
        # Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(t * 1000.0 >= scene_times)]
        
        # Keep track of total number of scenes to have passed
        scenes.append(len(in_window_scenes) + 1)
        
        # Update the graph
        line.set_xdata(times)
        line.set_ydata(scenes)
        
        return mplfig_to_npimage(fig2)
    
    # Animate the graph and save it to file
    animation2 = VideoClip(make_frame2, duration=duration).resize(height=540)
    # animation2.write_videofile('total_animation.mp4', fps=23.976)
    
    # Reload saved videos of graphs as they cannot be composited together
    # until they are each rendered and saved independently
    animation1 = VideoFileClip('rate_animation.mp4')
    animation2 = VideoFileClip('total_animation.mp4')
    
    # Stack the two graphs on top of each other
    animation_array = clips_array([[animation1], [animation2]])
    # animation_array.write_videofile('stacked_animation.mp4', fps=23.976)
    
    # Load the main video
    mv_video = (VideoFileClip('BTS_2017_DNA_Annotated_33_10.mp4').
                resize(width=1920 - animation_array.w))
    
    #Get rid of audio if set
    if not include_audio:
        mv_video = mv_video.set_audio(None)
    
    # Stick the videos together and save the result
    final_array = clips_array([[mv_video, animation_array]])
    # final_array.write_videofile('final_composition.mp4', fps=23.976)
    
    # Make a final results screen
    
    # Calculate final stats
    sec_per_scene = duration / float(max(scene_count))
    
    result_string1 = "Results:                              \n"
    result_string2 = "%03d scenes in %03.1f seconds           " % (max(scene_count), duration)
    result_string3 = "Average of %0.2f transitions per second" % avg_rate
    result_string4 = "Average of %0.2f seconds per scene     " % sec_per_scene
    
    result_text = [result_string1, result_string2,
                   result_string3, result_string4]
    
    final_result_text = "\n".join(result_text)
    
    result_screen_text = TextClip(final_result_text, fontsize=72,
                                  font="FreeMono-Bold", color='white',
                                  size=(final_array.w, final_array.h)
                                  ).set_duration(7.5).set_pos('center')
    
    video_result = concatenate_videoclips([final_array, result_screen_text])
    
    # Tack on the longest scene at the end
    
    # Find the longest scene
    scene_idx = np.argmax(scene_durs)
    
    # Figure out the timing of the longest scene
    scene_start = scene_times[scene_idx - 1] / 1000.0
    scene_end = (scene_times[scene_idx] - msec_per_frame) / 1000.0
    scene_duration = scene_end - scene_start
    
    # Make the text for the top of the screen
    scene_text = (TextClip("Longest Scene", fontsize=144, font="FreeMono-Bold",
                           stroke_color='black', stroke_width=3, color='white').
                           set_duration(scene_duration).set_opacity(0.6))
    scene_text = scene_text.set_pos("center").set_pos('top')
    
    # Make the text for the bottom of the screen
    dur_text = (TextClip("%0.3f seconds long" % scene_duration, fontsize=144,
                         font="FreeMono-Bold", stroke_color='black',
                         color='white', stroke_width=3).
                         set_duration(scene_duration).set_opacity(0.6))
    dur_text = dur_text.set_pos('center').set_pos('bottom')
    
    # Load the longest scene from the previously annotated video
    video_file = '/home/walter/Videos/Music Videos/BTS_2017_DNA.mkv'
    longest_scene = (VideoFileClip(video_file).
                     subclip(scene_start, scene_end))
    
    #Get rid of audio if set
    if not include_audio:
        longest_scene = longest_scene.set_audio(None)
    
    # Combine the text and the longest scene together
    final_scene = CompositeVideoClip([longest_scene, scene_text, dur_text])
    
    # Add the longest scene onto the end of the annotated video
    added_scene = concatenate_videoclips([video_result, final_scene])
    added_scene.write_videofile('added_scene.mp4', fps=23.976, preset='medium')