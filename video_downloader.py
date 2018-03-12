from __future__ import unicode_literals

import pandas as pd
import os
import youtube_dl


def download_video(url, output=u'video'):
    """
    Download a video from youtube with a given url and destination filepath.
    
    Both input arguments must be utf-8 encoded.
    """
    
    ydl_opts = {}
    ydl_opts['outtmpl'] = output
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == '__main__':
    
    # Read in csv file containing MV information
    # Formatted in five columns with a header row of column titles
    # | Artist | Song Title | Genre | Year | YouTube Link |
    video_list = pd.read_csv('video_list.csv')
    
    # Specify folder to save MVs to
    video_folder = "/home/walter/Videos/Music Videos/"
    
    # Dictionary to put output filenames into
    ydl_opts = {}
    
    for idx, row in video_list.iterrows():
        
        # Build output filename from MV data
        cols = [0, 3, 1]
        outfile = '_'.join(str(i) for i in row[cols].tolist())
        
        # Check to see if MV already exists
        if os.path.isfile(os.path.join(video_folder, outfile + '.mkv')):
            continue
        
        # Set output filename for MV to pass to youtube_dl
        ydl_opts['outtmpl'] = os.path.join(video_folder, outfile)
        
        # Download the video
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([row[4]])
