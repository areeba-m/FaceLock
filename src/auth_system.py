"""
Main authentication system coordinating all components
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
    BLINK_DETECTION_FRAMES
)
from src.database import db_manager
from src.face_recognition_module import face_recognition_module
from src.anti_spoofing import anti_spoofing_module
from src.totp_handler import totp_handler


class AuthenticationSystem:
    """Main authentication system"""
    
    def __init__(self):
        self.current_user_id = None
        self.session_start_time = None
    
    def register_user(self, username: str, password: str, 
                     video_capture: cv2.VideoCapture) -> Dict:
        """
        Register a new user with facial data and TOTP
        Returns dict with status and information
        """
        result = {
            'success': False,
            'message': '',
            'qr_code': None,
            'secret': None
        }
        
        # Create user account
        user_id = db_manager.create_user(username, password)
        if user_id is None:
            result['message'] = "Username already exists"
            return result
        
        # Capture facial samples
        print(f"Capturing {REGISTRATION_SAMPLES} face samples...")
        face_encodings = []
        samples_captured = 0
        
        anti_spoofing_module.reset_counters()
        
        while samples_captured < REGISTRATION_SAMPLES:
            ret, frame = video_capture.read()
            if not ret:
                result['message'] = "Camera error"
                return result
            
            # Detect face
            face_locations = face_recognition_module.detect_faces(frame)
            
            if len(face_locations) != 1:
                # Show feedback
                cv2.putText(frame, "Position your face in frame", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow('Registration', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    result['message'] = "Registration cancelled"
                    return result
                continue
            
            face_location = face_locations[0]
            
            # Get landmarks for liveness check
            landmarks = face_recognition_module.get_face_landmarks(frame, face_location)
            
            if landmarks:
                # Perform liveness check
                liveness = anti_spoofing_module.perform_liveness_check(
                    frame, face_location, landmarks
                )
                
                # Check if we have enough frames for validation
                if anti_spoofing_module.frame_counter >= BLINK_DETECTION_FRAMES:
                    if liveness['overall_score'] < 0.4:
                        cv2.putText(frame, "Liveness check failed - please blink", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        cv2.imshow('Registration', frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            result['message'] = "Registration cancelled"
                            return result
                        continue
            
            # Get encoding
            encoding = face_recognition_module.get_face_encoding(frame, face_location)
            
            if encoding is not None:
                face_encodings.append(encoding)
                samples_captured += 1
                
                # Visual feedback
                progress = f"Sample {samples_captured}/{REGISTRATION_SAMPLES}"
                face_recognition_module.draw_face_box(frame, face_location, progress)
                cv2.imshow('Registration', frame)
                
                print(f"Captured sample {samples_captured}/{REGISTRATION_SAMPLES}")
                time.sleep(SAMPLE_DELAY)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                result['message'] = "Registration cancelled"
                return result
        
        cv2.destroyAllWindows()
        
        # Store face encodings
        if not db_manager.store_face_embeddings(user_id, face_encodings):
            result['message'] = "Failed to store facial data"
            return result
        
        # Generate TOTP secret
        secret = totp_handler.generate_secret()
        if not db_manager.store_totp_secret(user_id, secret):
            result['message'] = "Failed to store TOTP secret"
            return result
        
        # Generate QR code
        qr_image = totp_handler.generate_qr_code(secret, username)
        
        result['success'] = True
        result['message'] = "Registration successful"
        result['qr_code'] = qr_image
        result['secret'] = secret
        
        return result
    
    def authenticate_user(self, username: str, password: str, 
                         video_capture: cv2.VideoCapture) -> Dict:
        """
        Authenticate user with facial recognition, anti-spoofing, and TOTP
        Returns dict with authentication status
        """
        result = {
            'success': False,
            'message': '',
            'user_id': None,
            'requires_totp': False,
            'liveness_score': 0.0
        }
        
        # Verify password
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
        
        # Facial recognition with anti-spoofing
        print("Performing facial recognition with liveness detection...")
        face_verified = False
        liveness_passed = False
        attempts = 0
        max_attempts = 50  # About 5 seconds at 10 FPS
        
        anti_spoofing_module.reset_counters()
        
        while attempts < max_attempts:
            ret, frame = video_capture.read()
            if not ret:
                result['message'] = "Camera error"
                return result
            
            # Detect face
            face_locations = face_recognition_module.detect_faces(frame)
            
            if len(face_locations) != 1:
                cv2.putText(frame, "Position your face in frame", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow('Authentication', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    result['message'] = "Authentication cancelled"
                    return result
                attempts += 1
                continue
            
            face_location = face_locations[0]
            
            # Get encoding
            encoding = face_recognition_module.get_face_encoding(frame, face_location)
            
            if encoding is not None:
                # Compare with stored encodings
                match = face_recognition_module.compare_faces(known_encodings, encoding)
                
                if match:
                    # Get landmarks for liveness
                    landmarks = face_recognition_module.get_face_landmarks(frame, face_location)
                    
                    if landmarks:
                        # Perform liveness check
                        liveness = anti_spoofing_module.perform_liveness_check(
                            frame, face_location, landmarks
                        )
                        
                        result['liveness_score'] = liveness['overall_score']
                        
                        # Display liveness info
                        info_text = f"Blinks: {liveness['total_blinks']} | Score: {liveness['overall_score']:.2f}"
                        cv2.putText(frame, info_text, (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        # Check if liveness passed
                        if liveness['overall_score'] >= 0.6:
                            face_verified = True
                            liveness_passed = True
                            face_recognition_module.draw_face_box(
                                frame, face_location, "Verified", (0, 255, 0)
                            )
                            cv2.imshow('Authentication', frame)
                            cv2.waitKey(500)
                            break
                        else:
                            cv2.putText(frame, "Please blink and move your head", (10, 60),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    
                    face_recognition_module.draw_face_box(frame, face_location, "Face Match")
                else:
                    face_recognition_module.draw_face_box(
                        frame, face_location, "Unknown", (0, 0, 255)
                    )
            
            cv2.imshow('Authentication', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                result['message'] = "Authentication cancelled"
                return result
            
            attempts += 1
        
        cv2.destroyAllWindows()
        
        if not face_verified or not liveness_passed:
            result['message'] = "Facial verification failed or spoofing detected"
            db_manager.log_login_attempt(user_id, False, "face")
            
            # Check failed attempts
            user_info = db_manager.get_user_by_username(username)
            if user_info and user_info[2] >= MAX_LOGIN_ATTEMPTS:
                db_manager.lock_account(user_id, LOCKOUT_DURATION)
                result['message'] = "Too many failed attempts. Account locked."
            
            return result
        
        # Face verified - now require TOTP
        result['user_id'] = user_id
        result['requires_totp'] = True
        result['message'] = "Face verified. Enter TOTP code."
        
        return result
    
    def verify_totp(self, user_id: int, otp_code: str) -> Dict:
        """
        Verify TOTP code for two-factor authentication
        """
        result = {
            'success': False,
            'message': ''
        }
        
        # Get TOTP secret
        secret = db_manager.get_totp_secret(user_id)
        if not secret:
            result['message'] = "TOTP not configured for user"
            return result
        
        # Verify OTP
        if totp_handler.verify_otp(secret, otp_code):
            db_manager.log_login_attempt(user_id, True, "face+totp")
            self.current_user_id = user_id
            self.session_start_time = time.time()
            result['success'] = True
            result['message'] = "Authentication successful"
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