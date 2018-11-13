"""This code provides an example of how scenedetection can fail for videos that 
use vp9 video encoding rather than avc.
"""

import os
import scenedetect as sd
import youtube_dl


def analyze_video(video_file, threshold=30, min_scene_len=10, downscale_factor=1):
    
    # First, load into a video manager
    video_mgr = sd.VideoManager([video_file])
    stats_mgr = sd.stats_manager.StatsManager()
    scene_mgr = sd.SceneManager(stats_mgr)
    
    # Add a content detector
    scene_mgr.add_detector(
        sd.ContentDetector(threshold=threshold, min_scene_len=min_scene_len))
    
    # Get the starting timecode
    base_timecode = video_mgr.get_base_timecode()
    
    # Start the video manager
    video_mgr.set_downscale_factor(downscale_factor)
    video_mgr.start()
    
    # Detect the scenes
    scene_mgr.detect_scenes(frame_source=video_mgr, start_time=base_timecode,
                            show_progress=True)
    
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
    
    return (video_fps, frames_read, scene_list)


if __name__ == '__main__':
    
    # URL of the video to be downloaded and analyzed
    video_url = 'https://www.youtube.com/watch?v=hfXZ6ydgZyo'
    
    # Define some options for youtube_dl
    ydl_opts1 = {}
    ydl_opts1['outtmpl'] = 'EXID_2014_Up and Down_VP9'
    ydl_opts1['merge_output_format'] = 'mkv'
    
    # Download video using youtube_dl
    with youtube_dl.YoutubeDL(ydl_opts1) as ydl:
        ydl.download([video_url])
    
    # Analyze the video using function above
    video1 = ydl_opts1['outtmpl'] + '.mkv'
    video1_fps, frames_read1, scene_list1 = analyze_video(video1)
    
    # Define some options for youtube_dl
    ydl_opts2 = {}
    ydl_opts2['outtmpl'] = 'EXID_2014_Up and Down_AVC'
    ydl_opts2['merge_output_format'] = 'mkv'
    ydl_opts2['format'] = 'bestvideo[ext=mp4]+bestaudio'
    
    # Download video using youtube_dl
    with youtube_dl.YoutubeDL(ydl_opts2) as ydl:
        ydl.download([video_url])
    
    # Analyze the video using the function above
    video2 = ydl_opts2['outtmpl'] + '.mkv'
    video2_fps, frames_read2, scene_list2 = analyze_video(video2)
    
    print('.mkv file with vp9 codec:')
    print(f"fps: {video1_fps}")
    print(f"frames read: {frames_read1}")
    print(f"Number of scenes: {len(scene_list1)}")
    
    print('.mkv file with avc codec:')
    print(f"fps: {video2_fps}")
    print(f"frames read: {frames_read2}")
    print(f"Number of scenes: {len(scene_list2)}")