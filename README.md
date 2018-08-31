# Quantitative Editing

This repository consists of code written to support a hobby project of mine, quantifying scene transitions in videos. This project was originally borne from my noticing that different genres of music videos that I watched had a very different feel. After watching some videos by [Every Frame a Painting](https://www.youtube.com/user/everyframeapainting) about movie editing, I thought that those same lessons could be applied to music video editing as well. It wasn't until I happened across [this video](https://www.youtube.com/watch?v=Q9v1UikfewA) on YouTube that I had seen a way to quantify this and show it visually.

Unlike the creator of that video linked above, I have no experience actually editing video, nor the time to exhaustively go frame by frame through a video to analyze it. Instead, I have put together some code in this repository to both analyze a video and attempt to automatically detect scene transitions as well as create a video visualizing those transitions. Below I will walk through my methodology and outline the workflow I use to analyze and create a video.

To see some of the results of the code in this repository, feel free to check out the [YouTube channel](https://www.youtube.com/channel/UCoOUknptLNANAOldpk-27RQ) I created to place videos after analysis.

## Outline of Methodology

The basic workflow I use when analyzing a video is as follows:

* The video is downloaded using the `youtube_dl` library within python and saved to a `.mkv` file
* The saved video is loaded into the `pyscenedetect` library in which I use the `content` scene detector built into the library. 
* Once the scenes are detected, I use the `moviepy` library to create the text to overlay on the original video and save the resulting video.
* After screening a large number of settings for the scene detection and determining the best combination of threshold level and minimum scene length, I do a full analysis video with those settings. 
* This final video includes animated graphs to go alongside the annotated original video, an animated audio waveform, a final results screen at the end, and finally the addition of the longest single scene to the end of the video. These visualizations use the `librosa` library for the audio visualization, but otherwise use `moviepy` features.

## Shortcomings of methodology

There are certainly shortcomings to the methods implemented in `pyscenedetect` when it comes to scene detection. There are situations in which transition points are erroneously detected. The most common situation in which this arises is when there is something like a strobe light in the video. Bright flashes of light that only last a single or a handful of frames are detected as scene transitions. See the [Growl music video](https://www.youtube.com/watch?v=I3dezFzsNss) by EXO for an example. This video is done in a single take with no edits, but the code will detect a large number of transitions even with a high threshold value due to the fact that there are many instances in which an incredibly bright strobe light flashes at the screen for just one or two frames. A way to possibly improve this in the future would be to skip forward a couple frames after a detected scene transition and see if the scene transition would still be true. Alternatively, implementing some kind of edge detection comparison between frames in addition to the HSV and intensity comparison that `pyscenedetect` uses currently could help alleviate this problem.

On the other end of the scale, there are also cases in which scene transitions are not detected. A simple case in which this happens is with slow screen wipes. For an example to see this, you can look to [Star Wars](https://www.youtube.com/watch?v=hF50y9FAY-0), which heavily uses screen wipes. These change the screen slowly enough that it is difficult to detect as a transition unless it is an incredibly fast wipe. Another case in which edit points are undercounted is when there are very smooth transitions done with the aid of CGI or a slow fade. For an example of this, check out this video about scene transitions in [Sherlock](https://www.youtube.com/watch?v=1IDBZ5AsUuk).

## Requirements

These libraries are required to run the code in this repository:

* `youtube_dl` is used to download videos from youtube for analysis
* `pyscenedetect` is used to detect transitions in videos (v0.5-beta-1, master branch from github, some older versions won't work, if you run into scenedetect problems, try updating this from github)
* `moviepy` is used to create data visualizations and compose resulting videos (version 0.2.3.5)
* `librosa` is used for audio analysis to visualize the audio waveform (version 0.6.2)

Other Requirements:

* `matplotlib` for graphs
* `numpy` for some number manipulation
* `pandas` for some data manipulation

I am running this code using Python 3.6.6 in Ubuntu 18.04. Video downloading with `youtube_dl` won't work correctly in Python 2 without decoding the function arguments in to utf-8. 

## Running the Code

To see the start to end process of how I analyze a single video, you can look at `complete_process.py`. Once you have decided on your scene detection settings, just change some of the variables near the beginning of this file to suit your needs and run it to end up with a fully analyzed and annotated video. This process can take a long time (about 4 hours on my laptop, a large chunk of that is the audio waveform animation).

In order to settle on the parameters used in scene detection, I use `parameter_screen.py` to analyze and create videos with a large number of different settings. This process can take a long time. With my current settings, it usually takes about 4-8 hours on my laptop depending on how many conditions I am screening.

If you want to analyze a folder full of `.mp4` and `.mkv` videos, you can use `analyze_folder.py`, making sure to specify the folder in the beginning of the script. All the videos will be analyzed using the same settings for threshold and minimum scene length.

## Contact

Feel free to reach out with questions/issues or make pull requests with optimizations and compatibility fixes. I can be reached at quantitative.editing@gmail.com
