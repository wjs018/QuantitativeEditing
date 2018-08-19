import scenedetect
import numpy as np
import csv

from moviepy.editor import *
from scenedetect.stats_manager import StatsManager


def analyze_video(video_file, threshold=40, min_scene_len=15, stats_file=None,
                  downscale_factor=1):
    """
    Analyzes a given video filepath for scene transitions.
    
    Parameters
    -----------
    
    video_file
      filepath of the video to be analyzed
    
    threshold
      threshold to use for scene detection
    
    min_scene_len
      minimum length of a scene to be counted as an independent scene in frames
    
    stats_file
      csv file to dump frame by frame stats of the video to
    
    downscale_factor
      factor to downscale the resolution of the video by before analyzing. Has a
      roughly linear effect on processing speed (having a downscale_facter of 2
      roughly double the speed of video analysis).
    
    Returns
    --------
    
    video_fps
      detected frames per second of the video
    
    frames_read
      number of frames analyzed of the video for scene transitions
    
    frames_processed
      number of frames of the video that were processed by the analyzer
    
    scene_list
      list of detected scenes from input video with given settings 
    """
    
    # First, load into a video manager
    video_mgr = scenedetect.VideoManager([video_file])
    stats_mgr = StatsManager()
    scene_mgr = scenedetect.SceneManager(stats_mgr)
    
    # Add a content detector
    scene_mgr.add_detector(
        scenedetect.ContentDetector(threshold=threshold,
                                    min_scene_len=min_scene_len))
    
    # Get the starting timecode
    base_timecode = video_mgr.get_base_timecode()
    
    # Start the video manager
    video_mgr.set_downscale_factor(downscale_factor)
    video_mgr.start()
    
    # Detect the scenes
    scene_mgr.detect_scenes(frame_source=video_mgr, start_time=base_timecode)
    
    # Retrieve scene list
    scene_mgr_list = scene_mgr.get_scene_list(base_timecode)
    
    # Initialize scene list for analysis
    scene_list = []
    
    # Build our list from the frame_timecode objects
    for scene in scene_mgr_list:
        start_frame, end_frame = scene
        start_frame = start_frame.frame_num
        scene_list.append(start_frame)
    
    # Extract some info
    video_fps = end_frame.framerate
    frames_read = end_frame.frame_num
    frames_processed = frames_read
    
    if stats_file:
        with open(stats_file, 'wb') as stats_csv:
            stats_mgr.save_to_csv(stats_csv, base_timecode)
    
    # Release the video manager
    video_mgr.release()
    
    return (video_fps, frames_read, frames_processed, scene_list)


if __name__ == '__main__':
    
    # Specify video file and constants here
    video_file = 'BTS_2017_DNA.mkv'
    threshold = 21
    min_scene_len = 15
     
    # First, load into a video manager
    video_mgr = scenedetect.VideoManager([video_file])
    stats_mgr = StatsManager()
    scene_mgr = scenedetect.SceneManager(stats_mgr)
    
    # Add a content detector
    scene_mgr.add_detector(
        scenedetect.ContentDetector(threshold=threshold,
                                    min_scene_len=min_scene_len))
    base_timecode = video_mgr.get_base_timecode()
    
    # Start the video manager
    video_mgr.start()
    
    # Detect the scenes
    scene_mgr.detect_scenes(frame_source=video_mgr, start_time=base_timecode)
    
    # Retrieve scene list
    scene_mgr_list = scene_mgr.get_scene_list(base_timecode)
    
    # Initialize scene list for analysis
    scene_list = []
    
    # Build our list from the frame_timecode objects
    for scene in scene_mgr_list:
        start_frame, end_frame = scene
        start_frame = start_frame.frame_num
        scene_list.append(start_frame)
    
    # Extract some info
    video_fps = end_frame.framerate
    frames_read = end_frame.frame_num
    
    # Release the video manager
    video_mgr.release()
    
    # Extract scene info from the manager
    scene_list_msec = [(1000.0 * x) / float(video_fps) for x in scene_list]
    
    # Pull music video file into moviepy
    mv_clip = VideoFileClip(video_file)
    W, H = mv_clip.size
    
    scene = 0
    previous_scene_msec = 0
    textclip_list = []
    
    # Loop over list of scenes, creating TextClips for each scene
    for scene_idx in range(len(scene_list_msec) + 1):
        
        # Each iteration is the same except for the final scene which is
        # handled separately in the else statement
        if scene_idx != len(scene_list_msec):
            
            # Calculate duration of the scene in seconds
            duration = (scene_list_msec[scene_idx] - previous_scene_msec) / 1000
            
            # Record ending time of scene for the next loop
            previous_scene_msec = scene_list_msec[scene_idx]
            
            # Make the video clips of the numbers
            txtclip = TextClip("%03d" % scene_idx, fontsize=288, color='white',
                               font='FreeMono-Bold', stroke_color='black',
                               stroke_width=5).set_pos('center').\
                               set_duration(duration).set_opacity(0.6)
            
            # Add the clip to a list of all the TextClips
            textclip_list.append(txtclip)
        
        # Last scene needs special treatment
        else:
            
            # Calculate the total duration of the video
            total_duration_msec = frames_read / float(video_fps) * 1000
            
            # Calculate the duration of the final scene
            clip_duration = (total_duration_msec - previous_scene_msec) / 1000
            
            # Create the TextClip for the final scene
            txtclip = TextClip("%03d" % scene_idx, fontsize=288, color='white',
                               font='FreeMono-Bold', stroke_color='black',
                               stroke_width=5).set_pos('center').\
                               set_duration(clip_duration).set_opacity(0.6)
            
            # Add it to the list of other TextClips
            textclip_list.append(txtclip)
    
    # Play the TextClips one after the other
    final_textclip = concatenate_videoclips(textclip_list).set_pos('center')
    
    # Play the TextClips over the original video
    final_video = CompositeVideoClip([mv_clip, final_textclip])
    
    # Save resulting video to file
    final_video.write_videofile('BTS_2017_DNA_Annotated_' + str(threshold) + 
                                '_' + str(min_scene_len) + '.mp4',
                                fps=video_fps, preset='medium')
    
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
    with open('MV_scenelist.csv', 'wb') as f:
        np.savetxt(f, scene_array, delimiter=',', fmt=["%1d", "%1.1f", "%1.1f"])
