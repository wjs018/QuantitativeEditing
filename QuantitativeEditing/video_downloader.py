import pandas as pd
import os
import youtube_dl


def download_video(url, output='video', quiet=True):
    """
    Download a video from youtube with a given url and destination filepath.
    
    url and output must be utf-8 encoded.
    
    If quiet is true, stdout will be suppressed.
    """
    
    ydl_opts = {}
    ydl_opts['outtmpl'] = output
    ydl_opts['quiet'] = quiet
    ydl_opts['merge_output_format'] = 'mkv'
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        result = ydl.extract_info(url, download=False)
        outfile = ydl.prepare_filename(result) + '.' + result['ext']
    
    return outfile


if __name__ == '__main__':
    
    # Read in csv file containing MV information
    # Formatted in five columns with a header row of column titles
    # | Artist | Song Title | Genre | Year | YouTube Link |
    video_list = pd.read_csv('video_list.csv')
    
    # Specify folder to save MVs to
    video_folder = "/media/unraid/Datasets/QuantitativeEditing/To Analyze/"
    
    for idx, row in video_list.iterrows():
        
        # Build output filename from MV data
        cols = [0, 3, 1]
        outfile = '_'.join(str(i) for i in row[cols].tolist())
        
        video_file = download_video(row[4],
                                    output=os.path.join(video_folder, outfile),
                                    quiet=False)
        
        print(video_file)
