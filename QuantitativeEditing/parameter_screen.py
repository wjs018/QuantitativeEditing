import scenedetect
import detect_scenes as ds
import gc
import scenedetect as sd

from moviepy.editor import *

if __name__ == '__main__':
    
    # Specify video location here
    video_file = '/media/unraid/Datasets/QuantitativeEditing/To Analyze/Norazo_2013_Wild Horse.mkv'
    outfile_dir = '/media/unraid/Datasets/QuantitativeEditing/Parameter Screen/'
    outfile_prefix = 'Norazo_2013_Wild Horse_'
    
    # First, load into a video manager
    video_mgr = sd.VideoManager([video_file])
    stats_mgr = sd.stats_manager.StatsManager()
    scene_mgr = sd.SceneManager(stats_mgr)
    
    # Specify range to vary for threshold value
    for threshold in range(22, 41):
        
        # Try a couple different minimum scene lengths for each threshold
        for min_scene_len in [5, 10, 15]:
            
            # Analyze the video for scene transitions
#             video_fps, frames_read, _, scene_list = ds.analyze_video(
#                 video_file, threshold=threshold,
#                 min_scene_len=min_scene_len, downscale_factor=1)
            
            # Add a content detector
            scene_mgr.add_detector(
                sd.ContentDetector(threshold=threshold,
                                   min_scene_len=min_scene_len))
            
            # Get the starting timecode
            base_timecode = video_mgr.get_base_timecode()
    
            # Start the video manager
            video_mgr.set_downscale_factor(1)
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
            
            # Convert detected scenes to time
            scene_list_msec = [(1000.0 * x) / float(video_fps)
                               for x in scene_list]
            
            # Reset the detector for next iteration
            video_mgr.release()
            video_mgr.reset()
            scene_mgr.clear_detectors()
            scene_mgr.clear()
            
            # Pull music video file into moviepy
            mv_clip = VideoFileClip(video_file)
            W, H = mv_clip.size
            
            # Initialize some variables
            scene = 0
            previous_scene_msec = 0
            textclip_list = []
            
            # Loop over list of scenes, creating TextClips for each scene
            for scene_idx in range(len(scene_list_msec) + 1):
                
                # Each iteration is the same except for the final scene which is
                # handled separately in the else statement
                if scene_idx != len(scene_list_msec):
                    
                    # Calculate duration of the scene in seconds
                    duration = (scene_list_msec[scene_idx] - 
                                previous_scene_msec) / 1000
                    
                    # Record ending time of scene for the next loop
                    previous_scene_msec = scene_list_msec[scene_idx]
                    
                    # Make the video clips of the numbers
                    txtclip = (TextClip("%03d" % scene_idx, fontsize=288,
                                        color='white', font='FreeMono-Bold',
                                        stroke_color='black', stroke_width=5).
                                        set_pos('center').
                                        set_duration(duration).set_opacity(0.6))
                    
                    # Add the clip to a list of all the TextClips
                    textclip_list.append(txtclip)
                
                # Last scene needs special treatment
                else:
                    
                    # Calculate the total duration of the video
                    total_duration_msec = frames_read / float(video_fps) * 1000
                    
                    # Calculate the duration of the final scene
                    clip_duration = (total_duration_msec - 
                                     previous_scene_msec) / 1000
                    
                    # Create the TextClip for the final scene
                    txtclip = (TextClip("%03d" % scene_idx, fontsize=288,
                                        color='white', font='FreeMono-Bold',
                                        stroke_color='black', stroke_width=5).
                                        set_pos('center').
                                        set_duration(clip_duration).
                                        set_opacity(0.6))
                    
                    # Add it to the list of other TextClips
                    textclip_list.append(txtclip)
            
            # Play the TextClips one after the other
            final_textclip = concatenate_videoclips(textclip_list).set_pos('center')
            
            # Play the TextClips over the original video
            final_video = CompositeVideoClip([mv_clip, final_textclip],
                                             size=(W, H))
            
            # Save resulting video to file, formatting name to avoid overwrites
            outfile_name = outfile_prefix + (str(threshold) + '_' + 
                                             str(min_scene_len) + '.mp4')
            outfile = os.path.join(outfile_dir, outfile_name)
            final_video.write_videofile(outfile,
                                        fps=video_fps,
                                        preset='ultrafast')
            
            # Having some memory overflow problems on my laptop, deleting some
            # variables and forcing garbage collection fixes that
            del txtclip
            del textclip_list
            del final_textclip
            del final_video
            gc.collect()
