import os
import glob
import detect_scenes as ds
import audio_rendering as ar
import numpy as np
import matplotlib.pyplot as plt

from moviepy.editor import *
from moviepy.video.io.bindings import mplfig_to_npimage

if __name__ == '__main__':
    
    # Folder to find videos
    source_folder = '/media/unraid/Datasets/QuantitativeEditing'
    os.chdir(source_folder)
    
    # Some video constants to set
    include_audio = True
    render_audioplot = True  # Time intensive
    
    # Some scenedetect constants to set
    threshold = 40
    min_scene_len = 10
    
    # Resize video to 1920 wide before composing?
    resize = True
    
    # Build our list of files to analyze
    mp4_list = glob.glob(source_folder + '/*.mp4')
    mkv_list = glob.glob(source_folder + '/*.mkv')
    file_list = mp4_list + mkv_list
      
    # Loop over the videos making the annotated versions
    for video_file in file_list:
        
        # Analyze the video for scene transitions
        video_fps, frames_read, _, scene_list = ds.analyze_video(
            video_file, threshold=threshold, min_scene_len=min_scene_len,
            downscale_factor=1)
         
        # Convert the scene_list to milliseconds
        scene_list_msec = [(1000.0 * x) / float(video_fps) for x in scene_list]
         
        # Pull video file into moviepy
        video_clip = VideoFileClip(video_file)
        
        if resize:
            video_clip = video_clip.resize(width=1920)
        
        W, H = video_clip.size
         
        # Get rid of audio if set
        if not include_audio:
            video_clip = video_clip.set_audio(None)
         
        # Some constants for the text clip overlay
        scene = 0
        previous_scene_msec = 0
        textclip_list = []
         
        # Loop over list of scenes, creating TextClips for each scene
        for scene_idx in range(len(scene_list) + 1):
             
            # Each iteration is the same except for the final scene which is handled 
            # separately in the else statement
            if scene_idx != len(scene_list):
                 
                # Calculate duration of the scene in seconds
                duration = (scene_list_msec[scene_idx] - previous_scene_msec) / 1000
                 
                # Record ending time of scene for the next loop
                previous_scene_msec = scene_list_msec[scene_idx]
                 
                # Make the video clips of the numbers
                txtclip = (TextClip("%03d" % scene_idx, fontsize=288, color='white',
                                    font='FreeMono-Bold', stroke_color='black',
                                    stroke_width=5).set_pos('center').
                                    set_duration(duration).set_opacity(0.6))
                 
                # Add the clip to a list of all the TextClips
                textclip_list.append(txtclip)
             
            # Last scene needs special treatment
            else:
                 
                # Calculate the total duration of the video
                total_duration_msec = frames_read / float(video_fps) * 1000
                 
                # Calculate the duration of the final scene
                clip_duration = (total_duration_msec - previous_scene_msec) / 1000
                 
                # Create the TextClip for the final scene
                txtclip = (TextClip("%03d" % scene_idx, fontsize=288, color='white',
                                    font='FreeMono-Bold', stroke_color='black',
                                    stroke_width=5).set_pos('center').
                                    set_duration(clip_duration).set_opacity(0.6))
                 
                # Add it to the list of other TextClips
                textclip_list.append(txtclip)
         
        # Play the TextClips one after the other
        final_textclip = concatenate_videoclips(textclip_list).set_pos('center')
         
        # Play the TextClips over the original video
        annotated_video = CompositeVideoClip([video_clip, final_textclip])
         
        # Save resulting video to file
        outfile = video_file.split('/')[-1][:-4] + '_annotated.mp4'
    #    annotated_video.write_videofile(outfile, fps=video_fps, preset='medium')
         
        # Convert our scene lists to numpy arrays
        scene_list_array = np.array(scene_list)
        scene_list_array_msec = np.array(scene_list_msec)
         
        # Stack the scene data together
        scene_array = np.column_stack((scene_list_array, scene_list_array_msec))
         
        # Tack on the last row signifying the end of the video
        end_row = np.array([frames_read, total_duration_msec])
        end_row = end_row.reshape((1, 2))
        scene_array = np.vstack((scene_array, end_row))
         
        # Calculate the duration of each scene in msec
        scene_lens_msec = np.diff(np.insert(np.append(scene_list_array_msec,
                                                      total_duration_msec), 0, 0))
         
        # Tack on a column of the length of each scene in msec
        scene_array = np.column_stack((scene_array, scene_lens_msec))
         
        # Write this array to a .csv file columns are:
        # | scene break (frame) | scene break (msec) | scene duration (msec) |
        with open('video_scenelist.csv', 'wb') as f:
            np.savetxt(f, scene_array, delimiter=',', fmt=["%1d", "%1.1f", "%1.1f"])
         
        # Break these columns apart to make it a little easier to index later
        scene_frames = scene_array[:, 0]
        scene_times = scene_array[:, 1]
        scene_durs = scene_array[:, 2]
         
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
        avg_rate = scene_count[-2] / (scene_times[-1] / 1000.0)
         
        # Total duration of the video
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
        animation1 = VideoClip(make_frame1, duration=duration).resize(height=H / 2.0)
        animation1.write_videofile('animation1.mp4', fps=video_fps)
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
        animation2 = VideoClip(make_frame2, duration=duration).resize(height=H / 2.0)
        animation2.write_videofile('animation2.mp4', fps=video_fps)
         
        if render_audioplot:
            
            # Define our variables
            input_video = video_file
            audio_output = 'extracted_audio.mp3'
            graph_output = 'audio_animation.mp4'
             
            # Render the video
            audio_rendering = ar.animate_audio(input_video, audio_output,
                                               graph_output)
             
            # Create the video clip
            animation3 = VideoFileClip(audio_rendering)
    #        animation3 = VideoFileClip('audio_animation.mp4')
         
        # Reload saved videos of graphs as they cannot be composited together
        # until they are each rendered and saved independently
        animation1 = VideoFileClip('animation1.mp4')
        animation2 = VideoFileClip('animation2.mp4')
         
        # Stack the two graphs on top of each other
        animation_array = clips_array([[animation1], [animation2]])
    #    animation_array.write_videofile('stacked_animation.mp4', fps=video_fps)
         
        # Resize the main video
        resized_video = annotated_video.resize(width=(W - animation_array.w))
         
        # Stick the videos together
        final_array = clips_array([[resized_video, animation_array]])
         
        # Overlay audio rendering if set
        if render_audioplot:
             
            # Figure out positioning first
            sub_W, sub_H = final_array.resize(width=W - animation_array.w).size
            anim_W, anim_H = animation3.size
             
            # Composite the clip
            final_array = CompositeVideoClip([final_array,
                                              animation3.set_pos(
                                                  ((sub_W - anim_W) / 2,
                                                   final_array.h - 10 - anim_H))])
         
        # Write the output to file
    #    final_array.write_videofile('final_composition.mp4', fps=video_fps)
         
        # Calculate final stats to display after video ends
        sec_per_scene = duration / float(max(scene_count))
         
        # Format text to display
        result_string1 = "Results:                              \n"
        result_string2 = "%03d scenes in %03.1f seconds           " % (max(scene_count), duration)
        result_string3 = "Average of %0.2f transitions per second" % avg_rate
        result_string4 = "Average of %0.2f seconds per scene     " % sec_per_scene
         
        # String it together into a list
        result_text = [result_string1, result_string2,
                       result_string3, result_string4]
         
        # Add line breaks
        final_result_text = "\n".join(result_text)
         
        # Make the video clip from the text
        result_screen_text = TextClip(final_result_text, fontsize=72,
                                      font="FreeMono-Bold", color='white',
                                      size=(final_array.w, final_array.h)
                                      ).set_duration(7.5).set_pos('center')
         
        # Add the results onto the end of the analyzed video
        video_result = concatenate_videoclips([final_array, result_screen_text])
         
        # Find the longest scene
        scene_idx = np.argmax(scene_durs)
         
        # Figure out the timing of the longest scene
        scene_start = scene_times[scene_idx - 1] / 1000.0
        scene_end = (scene_times[scene_idx] - msec_per_frame) / 1000.0
        scene_duration = scene_end - scene_start
         
        # Make the text for the top of the screen
        scene_text = (TextClip("Longest Scene", fontsize=144, font="FreeMono-Bold",
                               stroke_color='black', stroke_width=3, color="white").
                               set_duration(scene_duration).set_opacity(0.6))
        scene_text = scene_text.set_pos("center").set_pos("top")
         
        # Make the text for the bottom of the screen
        dur_text = (TextClip("%0.3f seconds long" % scene_duration, fontsize=144,
                             font="FreeMono-Bold", stroke_color='black',
                             color='white', stroke_width=3).
                             set_duration(scene_duration).set_opacity(0.6))
        dur_text = dur_text.set_pos('center').set_pos('bottom')
         
        # Load the longest scene from the previously annotated video
        longest_scene = annotated_video.subclip(scene_start, scene_end)
         
        # Combine the text and the longest scene together
        final_scene = CompositeVideoClip([longest_scene, scene_text, dur_text])
         
        # Add the longest scene onto the end of the annotated video
        added_scene = concatenate_videoclips([video_result, final_scene])
        output_file = video_file.split('/')[-1][:-4] + '_analyzed.mp4'
        added_scene.write_videofile(output_file, fps=video_fps,
                                    preset='medium')