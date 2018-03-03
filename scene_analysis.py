import numpy as np
import matplotlib.pyplot as plt

from moviepy.editor import *
from moviepy.video.io.bindings import mplfig_to_npimage
from scipy.signal import savgol_filter

if __name__ == '__main__':
    
    #Read in data generated from previous video analysis
    scenes = np.loadtxt('MV_scenelist.csv', delimiter=',')
    
    #Break these columns apart to make it a little easier to index later
    scene_frames = scenes[:,0]
    scene_times = scenes[:,1]
    
    #Calculate the time that passes each frame
    msec_per_frame = scene_times[-1] / scene_frames[-1]
    
    #Initialize a list to keep track of edits/sec
    rolling_average = []
    
    #Size of the rolling window to average over
    window_sec = 5.0
    
    #Keep track of number of scenes to have passed
    scene_count = []
    
    for i in range(int(np.max(scene_frames))+1):
        
        #First frame, starts with 0 edits per second
        if i == 0:
            rolling_average.append(0)
            scene_count.append(1)
            continue
        
        #Find current time in msec
        current_time = i * msec_per_frame
        
        #Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(current_time >= scene_times)]
        
        #Keep track of total number of scenes to have passed
        scene_count.append(len(in_window_scenes) + 1)
        
        #Then filter that down to scenes that have happened within the rolling
        #window prior to current frame
        in_window_scenes = len(in_window_scenes[np.where(
            current_time - window_sec * 1000. <= in_window_scenes)])
        
        #Find the rate from number of scenes
        scenes_per_sec = in_window_scenes / window_sec
        
        #Add this frame's rate to the list
        rolling_average.append(scenes_per_sec)
    
    #Calculate the average rate at which edits are made
    avg_rate = scene_count[-1] / (scene_times[-1] / 1000.0)
    
#     plt.plot(range(len(rolling_average)), rolling_average, 'k-')
#     plt.plot(range(len(rolling_average)), savgol_filter(rolling_average, int(2000*window_sec/msec_per_frame), 3), 'r-')
#     plt.plot([0, len(rolling_average)], [avg_rate, avg_rate], 'b-')
#     plt.show()
#     
#     plt.plot(range(len(rolling_average)), scene_count, 'k-')
#     plt.plot([0, len(rolling_average)], [1, scene_count[-1]], 'r-')
#     plt.show()
    
    #duration = 30
    duration = scene_times[-1] / 1000.0
    
    fig1, ax = plt.subplots(1, figsize=(4,4), facecolor='white')
    ax.set_title("Rate of Scene Transitions \n (%0d sec Rolling Average)" % window_sec)
    ax.set_ylim(0, max(rolling_average))
    ax.set_xlim(0, duration)
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Detected Rate of Transitions (changes/sec)')
    line, = ax.plot(0,0,'k-')
    line2, = ax.plot(0, avg_rate, 'b-')
    plt.tight_layout()
    
    times = []
    rates = []
    
    def make_frame1(t):
        
        times.append(t)
        
        #Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(t*1000.0 >= scene_times)]
        
        #Then filter that down to scenes that have happened within the rolling
        #window prior to current frame
        in_window_scenes = len(in_window_scenes[np.where(
            t*1000.0 - window_sec*1000.0 <= in_window_scenes)])
        
        #Find the rate from number of scenes
        scenes_per_sec = in_window_scenes / window_sec
        
        rates.append(scenes_per_sec)
        
        line.set_xdata(times)
        line2.set_xdata([0,t])
        
        line.set_ydata(rates)
        line2.set_ydata([avg_rate, avg_rate])
        
        return mplfig_to_npimage(fig1)
    
    animation1 = VideoClip(make_frame1, duration=duration).resize(height=540)
    animation1.write_videofile('rate_animation.mp4', fps=23.976)
    
    plt.close()
    
    #Animate plot of total scene transitions detected
    
    fig2, ax = plt.subplots(1, figsize=(4,4), facecolor='white')
    ax.set_title("Number of Scene Transitions")
    ax.set_ylim(0, max(scene_count))
    ax.set_xlim(0, duration)
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Total Number of Detected Scenes')
    line, = ax.plot(0,1,'k-')
    line2, = ax.plot([0, duration], [1, max(scene_count)], 'b-')
    plt.tight_layout()
    
    times = []
    scenes = []
    
    def make_frame2(t):
        
        times.append(t)
        
        #Find all scenes that have happened prior to current frame
        in_window_scenes = scene_times[np.where(t*1000.0 >= scene_times)]
        
        #Keep track of total number of scenes to have passed
        scenes.append(len(in_window_scenes) + 1)
        
        line.set_xdata(times)
        line.set_ydata(scenes)
        
        return mplfig_to_npimage(fig2)
    
    animation2 = VideoClip(make_frame2, duration=duration).resize(height=540)
    animation2.write_videofile('total_animation.mp4', fps=23.976)
    
    animation1 = VideoFileClip('rate_animation.mp4')
    animation2 = VideoFileClip('total_animation.mp4')
    
    animation_array = clips_array([[animation1], [animation2]])
    animation_array.write_videofile('stacked_animation.mp4', fps=23.976)
    
    mv_video = VideoFileClip('BTS_2017_DNA_Annotated_33_10.mp4').resize(width=1920-animation_array.w)
    
    final_array = clips_array([[mv_video, animation_array]])
    final_array.write_videofile('final_composition.mp4', fps=23.976)