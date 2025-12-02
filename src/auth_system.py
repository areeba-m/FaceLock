"""
Main authentication system with camera display during registration/login
"""
import cv2
import time
import numpy as np
from typing import Optional, Dict, List, Tuple
from config.settings import (
    REGISTRATION_SAMPLES,
    SAMPLE_DELAY,
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION,
    CAMERA_INDEX
)
from src.database import db_manager
from src.face_recognition_module import face_recognition_module
from src.anti_spoofing import anti_spoofing_module
from src.totp_handler import totp_handler
from src.encryption import encryption_manager


class AuthenticationSystem:
    """Main authentication system"""
    
    def __init__(self):
        self.current_user_id = None
        self.session_start_time = None
    
    def register_user(self, username: str, password: str, 
                     video_capture: cv2.VideoCapture) -> Dict:
        """
        Register a new user with facial data and TOTP
        Shows camera window during face capture
        """
        result = {
            'success': False,
            'message': '',
            'qr_code': None,
            'secret': None,
            'user_id': None
        }
        
        try:
            # Check if username exists
            if db_manager.get_user_by_username(username):
                result['message'] = "Username already exists"
                return result
            
            # Reinitialize camera with DirectShow
            video_capture.release()
            time.sleep(0.5)
            video_capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            
            if not video_capture.isOpened():
                result['message'] = "Failed to open camera"
                return result
            
            # Set camera properties
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            video_capture.set(cv2.CAP_PROP_FPS, 30)
            
            # Warm up camera
            print("Warming up camera...")
            for _ in range(10):
                video_capture.read()
                time.sleep(0.05)
            
            # Reset anti-spoofing
            anti_spoofing_module.reset_counters()
            
            # Create window for camera display
            cv2.namedWindow('Registration - Face Capture', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Registration - Face Capture', 640, 480)
            
            face_encodings = []
            samples_captured = 0
            required_samples = REGISTRATION_SAMPLES
            last_capture_time = 0
            max_time = 60  # 60 seconds timeout
            start_time = time.time()
            
            print(f"Starting face capture. Need {required_samples} samples...")
            print("Please blink naturally and move your head slightly.")
            
            while samples_captured < required_samples:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_time:
                    result['message'] = f"Registration timeout. Captured {samples_captured}/{required_samples} samples."
                    break
                
                ret, frame = video_capture.read()
                if not ret or frame is None:
                    continue
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                display_frame = frame.copy()
                
                # Detect faces
                face_locations = face_recognition_module.detect_faces(frame)
                
                if len(face_locations) == 1:
                    face_location = face_locations[0]
                    top, right, bottom, left = face_location
                    
                    # Get landmarks
                    landmarks = face_recognition_module.get_face_landmarks(frame, face_location)
                    
                    # Perform liveness check
                    liveness = anti_spoofing_module.perform_liveness_check(
                        frame, face_location, landmarks
                    )
                    
                    # Draw face box
                    color = (0, 255, 0) if liveness['is_live'] else (0, 165, 255)
                    cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                    
                    # Show liveness status
                    cv2.putText(display_frame, f"Blinks: {liveness['total_blinks']}/2", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Movement: {liveness['total_movement']:.0f}px", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Samples: {samples_captured}/{required_samples}", 
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Capture sample if enough time passed
                    current_time = time.time()
                    can_capture = current_time - last_capture_time >= SAMPLE_DELAY
                    
                    # For first few samples, don't require full liveness
                    # After that, require at least 1 blink
                    liveness_ok = (samples_captured < 2) or (liveness['total_blinks'] >= 1)
                    
                    if can_capture and liveness_ok:
                        encoding = face_recognition_module.get_face_encoding(frame, face_location)
                        
                        if encoding is not None:
                            face_encodings.append(encoding)
                            samples_captured += 1
                            last_capture_time = current_time
                            print(f"✓ Sample {samples_captured}/{required_samples} captured")
                            
                            # Flash green to indicate capture
                            cv2.rectangle(display_frame, (left-5, top-5), (right+5, bottom+5), 
                                        (0, 255, 0), 4)
                    
                    # Show instruction
                    if liveness['total_blinks'] < 2:
                        cv2.putText(display_frame, "Please blink naturally", 
                                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                elif len(face_locations) == 0:
                    cv2.putText(display_frame, "No face detected - look at camera", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    cv2.putText(display_frame, "Multiple faces - only one person please", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Show time remaining
                remaining = int(max_time - elapsed)
                cv2.putText(display_frame, f"Time: {remaining}s", 
                           (display_frame.shape[1] - 100, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Display frame
                cv2.imshow('Registration - Face Capture', display_frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q or ESC
                    result['message'] = "Registration cancelled"
                    break
            
            # Clean up
            cv2.destroyAllWindows()
            video_capture.release()
            
            # Check if enough samples
            if samples_captured < required_samples:
                if not result['message']:
                    result['message'] = f"Not enough samples. Got {samples_captured}/{required_samples}"
                return result
            
            # Create user in database
            user_id = db_manager.create_user(username, password)
            if user_id is None:
                result['message'] = "Failed to create user account"
                return result
            
            # Store face embeddings
            if not db_manager.store_face_embeddings(user_id, face_encodings):
                result['message'] = "Failed to store facial data"
                return result
            
            # Generate and store TOTP secret
            secret = totp_handler.generate_secret()
            if not db_manager.store_totp_secret(user_id, secret):
                result['message'] = "Failed to store TOTP secret"
                return result
            
            # Generate QR code
            qr_image = totp_handler.generate_qr_code(secret, username)
            
            result['success'] = True
            result['message'] = "Registration successful!"
            result['qr_code'] = qr_image
            result['secret'] = secret
            result['user_id'] = user_id
            
            print(f"✓ User '{username}' registered successfully!")
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            result['message'] = f"Registration error: {str(e)}"
            return result
    
    def authenticate_user(self, username: str, password: str, 
                         video_capture: cv2.VideoCapture) -> Dict:
        """
        Authenticate user with facial recognition and liveness detection
        Requires 2 blinks and head movement within 60 seconds
        """
        result = {
            'success': False,
            'message': '',
            'user_id': None,
            'requires_totp': False,
            'liveness_score': 0.0
        }
        
        try:
            # Verify password first
            user_id = db_manager.verify_user_password(username, password)
            if user_id is None:
                result['message'] = "Invalid username or password"
                return result
            
            # Check if account is locked
            if db_manager.check_account_locked(user_id):
                result['message'] = "Account locked due to failed attempts. Try again later."
                return result
            
            # Get stored face encodings
            known_encodings = db_manager.get_face_embeddings(user_id)
            if not known_encodings:
                result['message'] = "No facial data found for user"
                return result
            
            print(f"\n=== AUTHENTICATING: {username} ===")
            print(f"Found {len(known_encodings)} stored face encodings")
            
            # Reinitialize camera
            video_capture.release()
            time.sleep(0.3)
            video_capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            
            if not video_capture.isOpened():
                result['message'] = "Failed to open camera"
                return result
            
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Warm up
            for _ in range(10):
                video_capture.read()
            
            # Reset anti-spoofing
            anti_spoofing_module.reset_counters()
            
            # Create window
            cv2.namedWindow('Authentication', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Authentication', 640, 480)
            
            # State tracking
            face_verified = False
            face_match_count = 0
            face_match_threshold = 3
            liveness_passed = False
            
            max_time = 60  # 60 seconds
            start_time = time.time()
            
            print("Please look at the camera, blink 2 times, and move your head slightly.")
            
            while time.time() - start_time < max_time:
                ret, frame = video_capture.read()
                if not ret or frame is None:
                    continue
                
                frame = cv2.flip(frame, 1)
                display_frame = frame.copy()
                
                # Detect faces
                face_locations = face_recognition_module.detect_faces(frame)
                
                if len(face_locations) == 1:
                    face_location = face_locations[0]
                    top, right, bottom, left = face_location
                    
                    # Get landmarks
                    landmarks = face_recognition_module.get_face_landmarks(frame, face_location)
                    
                    # Face matching
                    encoding = face_recognition_module.get_face_encoding(frame, face_location)
                    face_match = False
                    
                    if encoding is not None:
                        match = face_recognition_module.compare_faces(known_encodings, encoding)
                        if match:
                            face_match = True
                            face_match_count += 1
                            if face_match_count >= face_match_threshold:
                                face_verified = True
                        else:
                            face_match_count = max(0, face_match_count - 1)
                    
                    # Liveness check
                    liveness = anti_spoofing_module.perform_liveness_check(
                        frame, face_location, landmarks
                    )
                    
                    if liveness['is_live']:
                        liveness_passed = True
                    
                    result['liveness_score'] = liveness['overall_score']
                    
                    # UI Colors
                    if face_verified and liveness_passed:
                        color = (0, 255, 0)  # Green - all good
                    elif face_match:
                        color = (0, 255, 255)  # Yellow - face matches
                    else:
                        color = (0, 0, 255)  # Red - no match
                    
                    cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                    
                    # Show status
                    cv2.putText(display_frame, "BLINK 2 TIMES & MOVE HEAD", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Blink status
                    blink_text = f"Blinks: {liveness['total_blinks']}/2"
                    blink_color = (0, 255, 0) if liveness['total_blinks'] >= 2 else (255, 255, 255)
                    cv2.putText(display_frame, blink_text, (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, blink_color, 2)
                    
                    # Movement status
                    move_text = f"Movement: {liveness['total_movement']:.0f}/{liveness['movement_threshold']}px"
                    move_color = (0, 255, 0) if liveness['has_movement'] else (255, 255, 255)
                    cv2.putText(display_frame, move_text, (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, move_color, 2)
                    
                    # Face match status
                    match_text = "Face: MATCHED" if face_verified else f"Face: Verifying... {face_match_count}/{face_match_threshold}"
                    match_color = (0, 255, 0) if face_verified else (0, 165, 255)
                    cv2.putText(display_frame, match_text, (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, match_color, 2)
                    
                    # Check success: Face verified + Liveness passed
                    if face_verified and liveness_passed:
                        cv2.putText(display_frame, "SUCCESS! Proceeding to OTP...", 
                                   (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        cv2.imshow('Authentication', display_frame)
                        cv2.waitKey(1500)
                        
                        result['success'] = True
                        result['user_id'] = user_id
                        result['requires_totp'] = True
                        result['message'] = "Face and liveness verified. Enter TOTP code."
                        break
                
                else:
                    msg = "No face detected" if len(face_locations) == 0 else "Multiple faces"
                    cv2.putText(display_frame, msg, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Time remaining
                remaining = int(max_time - (time.time() - start_time))
                cv2.putText(display_frame, f"Time: {remaining}s", 
                           (display_frame.shape[1] - 100, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow('Authentication', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    result['message'] = "Authentication cancelled"
                    break
            
            cv2.destroyAllWindows()
            video_capture.release()
            
            # Handle failure
            if not result['success']:
                reasons = []
                if not face_verified:
                    reasons.append("Face not recognized")
                if not liveness_passed:
                    blinks = anti_spoofing_module.total_blinks
                    movement = anti_spoofing_module.total_movement
                    reasons.append(f"Liveness failed (blinks: {blinks}/2, movement: {movement:.0f}px)")
                
                if not reasons:
                    reasons.append("Authentication timeout")
                
                result['message'] = " | ".join(reasons)
                db_manager.log_login_attempt(user_id, False, "face")
                
                # Check failed attempts
                user_info = db_manager.get_user_by_username(username)
                if user_info and user_info[2] >= MAX_LOGIN_ATTEMPTS:
                    db_manager.lock_account(user_id, LOCKOUT_DURATION)
                    result['message'] = "Too many failed attempts. Account locked."
                
                print(f"✗ Authentication failed: {result['message']}")
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            result['message'] = f"Authentication error: {str(e)}"
            return result
    
    def verify_totp(self, user_id: int, otp_code: str) -> Dict:
        """Verify TOTP code for two-factor authentication"""
        result = {
            'success': False,
            'message': ''
        }
        
        secret = db_manager.get_totp_secret(user_id)
        if secret:
            secret = secret.strip()
        
        if not secret:
            result['message'] = "TOTP not configured for user"
            return result
        
        if totp_handler.verify_otp(secret, otp_code):
            db_manager.log_login_attempt(user_id, True, "face+totp")
            self.current_user_id = user_id
            self.session_start_time = time.time()
            result['success'] = True
            result['message'] = "Authentication successful"
            print(f"✓ TOTP verified for user {user_id}")
        else:
            db_manager.log_login_attempt(user_id, False, "totp")
            result['message'] = "Invalid TOTP code"
        
        return result
    
    def logout(self):
        """Logout current user"""
        self.current_user_id = None
        self.session_start_time = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user_id is not None


# Singleton instance
auth_system = AuthenticationSystem()
