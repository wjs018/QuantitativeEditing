""" Experimental edge_detector module for PySceneDetect.

This module implements the EdgeDetector, which compares the difference
in edges between adjacent frames against a set threshold/score, which if
exceeded, triggers a scene cut.
"""

# Third-Party Library Imports
import numpy
import cv2

# New dependencies
from skvideo.motion.gme import globalEdgeMotion
from scipy.ndimage.morphology import binary_dilation

# PySceneDetect Library Imports
from scenedetect.scene_detector import SceneDetector


class EdgeDetector(SceneDetector):
    """Detects cuts using changes in edges found using the Canny operator.
    
    This detector uses edge information to detect scene transitions. The
    threshold sets the fraction of detected edge pixels that can change from one
    frame to the next in order to trigger a detected scene break. Images are 
    converted to grayscale in this detector, so color changes won't trigger
    a scene break like with the ContentDetector.
    
    Paper reference: http://www.cs.cornell.edu/~rdz/Papers/ZMM-MM95.pdf
    """

    def __init__(self, threshold=0.4, min_scene_len=10, r_dist=6):
        super(EdgeDetector, self).__init__()
        self.threshold = threshold
        self.min_scene_len = min_scene_len  # minimum length of any given scene, in frames
        self.r_dist = r_dist    # distance over which motion is estimate (on scaled-down image)
        self.last_frame = None
        self.last_scene_cut = None
        self._metric_keys = ['p_max', 'p_in', 'p_out']
#         self.cli_name = 'detect-content'

    def _percentage_distance(self, frame_in, frame_out, r):
        diamond = numpy.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        
        E_1 = binary_dilation(frame_in, structure=diamond, iterations=r)
        E_2 = binary_dilation(frame_out, structure=diamond, iterations=r)
        
        combo = numpy.float32(numpy.sum(E_1 & E_2))
        total_1 = numpy.float32(numpy.sum(E_1))
        
        return 1.0 - combo/total_1


    def process_frame(self, frame_num, frame_img):
        # type: (int, numpy.ndarray) -> List[int]
        """ Detects difference in edges between frames. Slow transitions or 
        transitions that happen in color space that won't show in grayscale
        won't trigger this detector.

        Arguments:
            frame_num (int): Frame number of frame that is being passed.

            frame_img (Optional[int]): Decoded frame image (numpy.ndarray) to perform scene
                detection on. Can be None *only* if the self.is_processing_required() method
                (inhereted from the base SceneDetector class) returns True.

        Returns:
            List[int]: List of frames where scene cuts have been detected. There may be 0
            or more frames in the list, and not necessarily the same as frame_num.
        """
        cut_list = []
        metric_keys = self._metric_keys
        _unused = ''

        if self.last_frame is not None:
            # Fraction of edge pixels changing in new frame, max, entering, and leaving
            p_max, p_in, p_out = 0.0, 0.0, 0.0
            
            if (self.stats_manager is not None and
                    self.stats_manager.metrics_exist(frame_num, metric_keys)):
                p_max, p_in, p_out = self.stats_manager.get_metrics(
                    frame_num, metric_keys)
            
            else:
                # Convert to grayscale
                curr_bw = cv2.cvtColor(frame_img, cv2.COLOR_BGR2GRAY)
                last_bw = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
                
                # Some calculation to determine canny thresholds
                curr_median = numpy.median(curr_bw)
                last_median = numpy.median(last_bw)
                sigma = 0.33
                curr_low = int(max(0, (1.0 - sigma) * curr_median))
                last_low = int(max(0, (1.0 - sigma) * last_median))
                curr_high = int(min(255, (1.0 + sigma) * curr_median))
                last_high = int(min(255, (1.0 + sigma) * last_median))
                
                # Do our Canny edge detection
                curr_edges = cv2.Canny(curr_bw, curr_low, curr_high)
                last_edges = cv2.Canny(last_bw, last_low, last_high)
                
                # Estimate the motion in the frame using skvideo
                r_dist = self.r_dist
                disp = globalEdgeMotion(numpy.array(last_edges, dtype=bool),
                                        numpy.array(curr_edges, dtype=bool),
                                        r=r_dist,
                                        method='hamming')
                
                # Translate our current frame to line it up with previous frame
                curr_edges = numpy.roll(curr_edges, disp[0], axis=0)
                curr_edges = numpy.roll(curr_edges, disp[1], axis=1)
                
                # Calculate fraction of edge pixels changing using scipy
                r_iter = 6      # Number of morphological operations performed
                p_in = self._percentage_distance(last_edges, curr_edges, r_iter)
                p_out = self._percentage_distance(curr_edges, last_edges, r_iter)
                p_max = numpy.max((p_in, p_out))
                
                if self.stats_manager is not None:
                    self.stats_manager.set_metrics(frame_num, {
                        metric_keys[0]: p_max,
                        metric_keys[1]: p_in,
                        metric_keys[2]: p_out})
                
            if p_max >= self.threshold:
                if self.last_scene_cut is None or (
                    (frame_num - self.last_scene_cut) >= self.min_scene_len):
                    cut_list.append(frame_num)
                    self.last_scene_cut = frame_num
                
            if self.last_frame is not None and self.last_frame is not _unused:
                del self.last_frame
                
        # If we have the next frame computed, don't copy the current frame
        # into last_frame since we won't use it on the next call anyways.
        if (self.stats_manager is not None and
                self.stats_manager.metrics_exist(frame_num+1, metric_keys)):
            self.last_frame = _unused
        else:
            self.last_frame = frame_img.copy()
            
        return cut_list


    #def post_process(self, frame_num):
    #    """ Not used for EdgeDetector, as unlike ThresholdDetector, cuts
    #    are always written as they are found.
    #    """
    #    return []
