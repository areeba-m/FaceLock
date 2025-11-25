"""
Configuration settings for FaceLock system
"""
import os

# Project directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Database
DATABASE_PATH = os.path.join(DATA_DIR, 'facelock.db')

# Face Recognition Settings
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower is more strict
FACE_ENCODING_MODEL = 'large'  # 'large' or 'small'
MIN_FACE_SIZE = (100, 100)

# Anti-Spoofing Settings
BLINK_DETECTION_FRAMES = 30  # Frames to check for blink
EYE_AR_THRESH = 0.21  # Eye aspect ratio threshold
EYE_AR_CONSEC_FRAMES = 3  # Consecutive frames for blink
HEAD_MOVEMENT_THRESHOLD = 15  # Degrees for head movement
LBP_THRESHOLD = 0.65  # Texture analysis threshold

# TOTP Settings
TOTP_INTERVAL = 30  # seconds
TOTP_DIGITS = 6
TOTP_ISSUER = "FaceLock"

# Session Settings
SESSION_TIMEOUT = 300  # seconds (5 minutes)
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # seconds (5 minutes)

# Camera Settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Registration Settings
REGISTRATION_SAMPLES = 5  # Number of face samples to capture
SAMPLE_DELAY = 1  # Seconds between samples

# Security
ENCRYPTION_KEY_FILE = os.path.join(DATA_DIR, '.key')
PASSWORD_MIN_LENGTH = 8