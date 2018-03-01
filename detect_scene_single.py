import scenedetect
import numpy as np
import csv

from moviepy.editor import *


class PySceneDetectArgs(object):

    def __init__(self, input, threshold=40, min_scene_len=15, type='content',
                 stats_file=None):
        self.input = input
        self.detection_method = type
        self.threshold = threshold
        self.min_scene_len = min_scene_len
        self.min_percent = 95
        self.block_size = 8
        self.downscale_factor = 1
        self.frame_skip = 0
        self.save_images = False
        self.save_image_prefix = ''
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.quiet_mode = True
        self.stats_file = stats_file


if __name__ == '__main__':
    
    video_file = '/home/walter/Videos/Music Videos/BTS_2017_DNA.mkv'
    threshold = 33
    min_scene_len = 10
    
    detector = scenedetect.detectors.get_available()
    
    with open('MV_stats.csv', 'wb') as csvfile:
        
        manager = scenedetect.manager.SceneManager(
            PySceneDetectArgs(input=video_file, threshold=threshold,
                              min_scene_len=min_scene_len, stats_file=csvfile), detector)
        
        video_fps, frames_read, frames_processed = scenedetect.detect_scenes_file(video_file, manager)
    
    scene_list = manager.scene_list
    scene_list_msec = [(1000.0 * x) / float(video_fps) for x in scene_list]
    scene_list_tc = [scenedetect.timecodes.get_string(x) for x in scene_list_msec]
    
    mv_clip = VideoFileClip(video_file)
    W, H = mv_clip.size
    
    scene = 0
    previous_scene_msec = 0
    textclip_list = []
    
    for scene_idx in range(len(scene_list_tc) + 1):
         
        if scene_idx != len(scene_list_tc):
             
            duration = (scene_list_msec[scene_idx] - previous_scene_msec) / 1000
            previous_scene_msec = scene_list_msec[scene_idx]
             
            txtclip = TextClip("%03d" % scene_idx, fontsize=288, color='white',
                               font='Ubuntu Mono', stroke_color='black',
                               stroke_width=5).set_pos('center').\
                               set_duration(duration).set_opacity(0.6)
             
            textclip_list.append(txtclip)
         
        else:
             
            total_duration_msec = frames_read / float(video_fps) * 1000
            clip_duration = (total_duration_msec - previous_scene_msec) / 1000
             
            txtclip = TextClip("%03d" % scene_idx, fontsize=288, color='white',
                               font='Ubuntu Mono', stroke_color='black',
                               stroke_width=5).set_pos('center').\
                               set_duration(clip_duration).set_opacity(0.6)
             
            textclip_list.append(txtclip)
     
    final_textclip = concatenate_videoclips(textclip_list).set_pos('center')
    
    final_video = CompositeVideoClip([mv_clip, final_textclip], size=(W, H))
    final_video.write_videofile('BTS_2017_DNA_Annotated_' + str(threshold) + 
                                '_' + str(min_scene_len) + '.mp4',
                                fps=video_fps, preset='medium')
    
    scene_list_array = np.array(scene_list)
    scene_list_array_msec = np.array(scene_list_msec)
    scene_list_tc_array = np.array(scene_list_tc)
    
    scene_array = np.column_stack((scene_list_array, scene_list_array_msec))
    
    end_row = np.array([frames_read, total_duration_msec])
    end_row = end_row.reshape((1,2))
    
    scene_array = np.vstack((scene_array, end_row))
    
    scene_lens_msec = np.diff(np.insert(np.append(scene_list_array_msec,
                                                  total_duration_msec), 0, 0))
     
    scene_array = np.column_stack((scene_array, scene_lens_msec))
    
    with open('MV_scenelist.csv', 'wb') as f:
        np.savetxt(f, scene_array, delimiter=',', fmt=["%1d", "%1.1f", "%1.1f"])
