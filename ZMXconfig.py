# Configuration file for running automated Zemax tracing

from math import pi

class BaseConfig():
    def __init__(self):

        ########################
        ###### File paths ######
        ########################

        # Zemax file (recommended to use full path with r-string)
        self.zemax_file = r'C:\full\path\to\my_zemax_file.zmx'

        # Pupil coordinates to load for correcting wobble (comment if N/A)
        # self.wobble_file = 'pupil_coords.npy'

        # File to save raytracing output coordinates
        self.pupil_file = 'pupil_wobble_data.npy'

        ########################
        ### Zemax Parameters ###
        ########################

        # Lens surfaces for the tilt (coordinate break) for scanning mirrors
        self.x_galvo_sur = 20
        self.y_galvo_sur = 25
        self.fsm_sur = 40               # Will be ignored if no FSM present
        self.pupil_plane = 60
        self.pupil = True               # True for tracing at pupil plane, False for tracing at retina/image plane

        # Scan parameters (scan dimensions in mechanical angle)
        self.scan_type = 'radial'
        self.scan_dim = 5
        self.scan_range = [-self.scan_dim,self.scan_dim]
        self.radial_range = [0,pi]      # Range in polar coordinates for radial scans
        self.n_bscans = 16
        self.n_points = 21

        self.FSM = False                # True to apply FSM correction with wobble coordinates
        self.fsm_range = [0,pi]         # Range in polar coordinates
        self.fsm_slope = 1              # mm/deg calibration

        # Raytrace parameters
        self.waveNumber = 2             # Choose wavelength
        self.hx = 0                     # Leave normalized field coordinate 0
        self.hy = 0                     # Leave normalized field coordinate 0
        self.n_ring = 1                 # 1 for chief ray, n to trace n marginal rays (ring)
