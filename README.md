# FaceLock: Facial Recognition and TOTP Authentication System

A secure, offline authentication system combining facial recognition, multi-layer anti-spoofing detection, and Time-based One-Time Passwords (TOTP) for two-factor authentication.

## Features

- **Facial Recognition**: Deep learning-based face detection and recognition using dlib's ResNet model
- **Multi-Layer Anti-Spoofing**:
  - **Blink Detection**: Eye Aspect Ratio (EAR) algorithm
  - **Head Movement**: 3D pose estimation tracking
  - **Texture Analysis**: Local Binary Patterns (LBP) for liveness detection
- **TOTP 2FA**: RFC 6238 compliant time-based one-time passwords
- **Encrypted Storage**: AES-256 encryption for facial embeddings and secrets
- **Local-Only**: All data stored locally in SQLite database
- **Account Security**: Failed attempt tracking and account lockout

## Technology Stack

- **Language**: Python 3.8+
- **Computer Vision**: OpenCV, dlib, face_recognition
- **Machine Learning**: scikit-learn, scipy
- **Cryptography**: cryptography library (Fernet)
- **2FA**: PyOTP
- **Database**: SQLite3
- **GUI**: Tkinter

## Project Structure

```
FaceLock/
├── src/
│   ├── __init__.py
│   ├── database.py                 # Database operations
│   ├── encryption.py               # Encryption utilities
│   ├── face_recognition_module.py  # Face detection & recognition
│   ├── anti_spoofing.py           # Liveness detection
│   ├── totp_handler.py            # TOTP management
│   └── auth_system.py             # Authentication coordinator
├── ui/
│   ├── __init__.py
│   └── gui.py                     # Tkinter GUI
├── config/
│   └── settings.py                # Configuration
├── models/
│   └── lbp_model.pkl             # LBP classifier (auto-generated)
├── data/
│   └── facelock.db               # SQLite database (auto-created)
├── main.py                        # Application entry point
├── requirements.txt               # Dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Webcam
- CMake (for dlib compilation)
- C++ compiler (Visual Studio Build Tools on Windows, gcc on Linux)

### Step 1: Install System Dependencies

**Windows:**
```bash
# Install Visual Studio Build Tools with C++ support
# Download from: https://visualstudio.microsoft.com/downloads/

# Install CMake
# Download from: https://cmake.org/download/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libopencv-dev python3-opencv
```

**macOS:**
```bash
brew install cmake
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installing dlib may take several minutes as it compiles from source.

### Step 4: Run the Application

```bash
python main.py
```

## Usage

### Registration

1. Launch the application
2. Enter a username and password (minimum 8 characters)
3. Click "Register"
4. Position your face in front of the camera
5. Follow on-screen instructions (blink, move head slightly)
6. System captures 5 face samples with liveness detection
7. Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)
8. Save the backup key securely

### Login

1. Enter your username and password
2. Click "Login"
3. Position your face in front of the camera
4. System performs:
   - Face recognition
   - Blink detection
   - Head movement verification
   - Texture analysis (LBP)
5. Enter the 6-digit TOTP code from your authenticator app
6. Access granted upon successful verification

## Security Features

### Encryption
- **Facial Embeddings**: Encrypted with Fernet (AES-256)
- **TOTP Secrets**: Encrypted with Fernet (AES-256)
- **Passwords**: PBKDF2-HMAC-SHA256 with 100,000 iterations

### Anti-Spoofing Detection

1. **Blink Detection**
   - Eye Aspect Ratio (EAR) < 0.21 indicates closed eyes
   - Requires at least 1 blink during authentication
   - Detects printed photos and static images

2. **Head Movement Detection**
   - 3D pose estimation (pitch, yaw, roll)
   - Requires >15° movement
   - Detects video replays

3. **Texture Analysis**
   - Local Binary Patterns (LBP) feature extraction
   - SVM classifier distinguishes live faces from spoofs
   - Detects screen displays and masks

### Account Protection
- Maximum 3 failed login attempts
- 5-minute account lockout after failed attempts
- Login history tracking

## Configuration

Edit `config/settings.py` to customize:

```python
# Face Recognition
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower = more strict

# Anti-Spoofing
EYE_AR_THRESH = 0.21              # Eye aspect ratio threshold
HEAD_MOVEMENT_THRESHOLD = 15       # Degrees

# Security
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300             # seconds
SESSION_TIMEOUT = 300              # seconds

# Camera
CAMERA_INDEX = 0                   # Change if using external webcam
```

## Logic & Algorithms

### Face Recognition
- **Model**: dlib's ResNet-based face recognition model
- **Encoding**: 128-dimensional face embeddings
- **Matching**: Euclidean distance < tolerance threshold

### Blink Detection
```
EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
```
Where p1-p6 are eye landmark points. EAR drops significantly when eyes close.

### Head Pose Estimation
- **Method**: Perspective-n-Point (PnP) algorithm
- **Input**: 2D facial landmarks + 3D model points
- **Output**: Rotation angles (pitch, yaw, roll)

### Local Binary Patterns (LBP)
```
LBP(x,y) = Σ(p=0 to 7) s(neighbor_p - center) * 2^p
where s(x) = 1 if x >= 0, else 0
```
Creates texture histogram for SVM classification.

### TOTP
```
TOTP = HOTP(K, T)
where T = floor((current_time - T0) / X)
```
- K: Secret key
- T0: Unix epoch (0)
- X: Time step (30 seconds)

## Best Practices Used

1. **Separation of Concerns**: Modular architecture with dedicated modules
2. **Singleton Pattern**: Single instances for managers (database, encryption)
3. **Error Handling**: Try-catch blocks with informative error messages
4. **Security by Design**: Encryption at rest, secure password hashing
5. **Type Hints**: Python type annotations for code clarity
6. **Documentation**: Comprehensive docstrings and comments
7. **Configuration Management**: Centralized settings file
8. **Thread Safety**: GUI operations in main thread, processing in background
9. **Resource Management**: Proper cleanup of camera and database connections
10. **User Feedback**: Clear status messages and progress indicators

## Troubleshooting

### Camera not detected
- Check camera permissions in system settings
- Try different CAMERA_INDEX values in settings.py
- Ensure no other application is using the camera

### dlib installation fails
- Install Visual Studio Build Tools (Windows)
- Install cmake and build-essential (Linux)
- Update pip: `pip install --upgrade pip`

### Face detection fails
- Ensure good lighting
- Position face 1-2 feet from camera
- Remove glasses if causing issues
- Adjust FACE_RECOGNITION_TOLERANCE in settings

### Authentication consistently fails
- Re-register with better lighting conditions
- Ensure face is clearly visible during registration
- Check that anti-spoofing isn't too strict

## Limitations

- Requires webcam
- Single-user authentication per session
- No cloud backup
- Limited to offline use
- Requires good lighting conditions

## Future Enhancements

- Multi-user session support
- Backup and restore functionality
- Mobile app integration
- Advanced anti-spoofing (IR sensors, depth cameras)
- Biometric template protection (cancelable biometrics)
- Audit logging and reporting
- API for integration with other systems

## Security Considerations

- Keep the encryption key file (`.key`) secure
- Use strong passwords (>12 characters recommended)
- Store backup codes in a secure location
- Regularly update dependencies for security patches
- Do not share TOTP secrets or QR codes
- Consider additional physical security for the device

## License

Educational project for Information Security coursework.

## Authors

CS3002 Information Security Project

## Acknowledgments

- dlib library by Davis King
- face_recognition library by Adam Geitgey
- OpenCV community
- PyOTP developers