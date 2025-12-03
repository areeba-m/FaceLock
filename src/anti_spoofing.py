"""
Anti-spoofing module with improved blink detection using dlib landmarks
1. Blink Detection (minimum 2 blinks required) - using EAR method
2. Head Movement Detection
"""
import cv2
import numpy as np
import dlib
from scipy.spatial import distance
from typing import Optional, Tuple, List, Dict
from collections import deque
from imutils import face_utils


class AntiSpoofingModule:
    """Anti-spoofing with improved blink and movement detection"""
    
    def __init__(self):
        # Initialize dlib's face detector and landmark predictor
        self.detector = dlib.get_frontal_face_detector()
        try:
            # Try to load the shape predictor model
            self.landmark_predict = dlib.shape_predictor(
                'models/shape_predictor_68_face_landmarks.dat'
            )
            self.use_dlib = True
            print("✓ Dlib landmark predictor loaded successfully")
        except:
            print("⚠ Dlib shape predictor not found. Fallback mode enabled.")
            print("  Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
            self.use_dlib = False
        
        # Eye landmark indices for dlib 68-point model
        (self.L_start, self.L_end) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.R_start, self.R_end) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']
        
        # Blink detection parameters - based on research papers
        self.blink_thresh = 0.18  # EAR threshold (research suggests 0.2-0.25)
        self.succ_frame = 2  # Consecutive frames below threshold to count as blink
        self.count_frame = 0  # Current consecutive frames below threshold
        self.total_blinks = 0
        self.required_blinks = 2
        
        # EAR history for analysis
        self.ear_history = deque(maxlen=30)
        
        # Head movement tracking
        self.face_center_history = deque(maxlen=30)
        self.total_movement = 0
        self.movement_threshold = 30  # Pixels of movement required
        
        # Frame counter
        self.frame_counter = 0
    
    def reset_counters(self):
        """Reset all counters for new session"""
        self.count_frame = 0
        self.total_blinks = 0
        self.ear_history.clear()
        self.face_center_history.clear()
        self.total_movement = 0
        self.frame_counter = 0
    
    @staticmethod
    def calculate_EAR(eye):
        """
        Calculate Eye Aspect Ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        # Calculate the vertical distances
        y1 = distance.euclidean(eye[1], eye[5])
        y2 = distance.euclidean(eye[2], eye[4])
        
        # Calculate the horizontal distance
        x1 = distance.euclidean(eye[0], eye[3])
        
        # Avoid division by zero
        if x1 < 1e-6:
            return 0.3
        
        # Calculate the EAR
        EAR = (y1 + y2) / (2.0 * x1)
        return EAR
    
    def detect_blink_dlib(self, frame: np.ndarray, gray_frame: np.ndarray) -> Tuple[bool, int, float]:
        """
        Detect blinks using dlib landmarks and EAR method
        Returns (blink_detected, total_blinks, avg_EAR)
        """
        blink_detected = False
        avg_EAR = 0.3
        
        try:
            # Detect faces
            faces = self.detector(gray_frame)
            
            if len(faces) == 0:
                # No face detected - reset counter
                self.count_frame = 0
                return False, self.total_blinks, 0.3
            
            # Use first face
            face = faces[0]
            
            # Get facial landmarks
            shape = self.landmark_predict(gray_frame, face)
            shape = face_utils.shape_to_np(shape)
            
            # Extract left and right eye landmarks
            lefteye = shape[self.L_start:self.L_end]
            righteye = shape[self.R_start:self.R_end]
            
            # Calculate EAR for both eyes
            left_EAR = self.calculate_EAR(lefteye)
            right_EAR = self.calculate_EAR(righteye)
            
            # Average EAR
            avg_EAR = (left_EAR + right_EAR) / 2.0
            
            # Store in history
            self.ear_history.append(avg_EAR)
            
            # Check if EAR is below threshold
            if avg_EAR < self.blink_thresh:
                self.count_frame += 1
            else:
                # EAR is above threshold - check if we had a blink
                if self.count_frame >= self.succ_frame:
                    self.total_blinks += 1
                    blink_detected = True
                    print(f"✓ BLINK DETECTED! Total: {self.total_blinks}/{self.required_blinks} (EAR: {avg_EAR:.3f})")
                
                # Reset counter
                self.count_frame = 0
            
            return blink_detected, self.total_blinks, avg_EAR
            
        except Exception as e:
            print(f"Error in blink detection: {e}")
            return False, self.total_blinks, 0.3
    
    def detect_blink_fallback(self, landmarks: dict) -> Tuple[bool, int]:
        """
        Fallback blink detection using face_recognition landmarks
        (Less accurate but works without dlib shape predictor)
        """
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            self.count_frame = 0
            return False, self.total_blinks
        
        try:
            left_ear = self.calculate_EAR(landmarks['left_eye'])
            right_ear = self.calculate_EAR(landmarks['right_eye'])
            avg_ear = (left_ear + right_ear) / 2.0
            
            self.ear_history.append(avg_ear)
            
            blink_detected = False
            
            if avg_ear < self.blink_thresh:
                self.count_frame += 1
            else:
                if self.count_frame >= self.succ_frame:
                    self.total_blinks += 1
                    blink_detected = True
                    print(f"✓ BLINK DETECTED (fallback)! Total: {self.total_blinks}/{self.required_blinks}")
                self.count_frame = 0
            
            return blink_detected, self.total_blinks
            
        except Exception as e:
            print(f"Error in fallback blink detection: {e}")
            self.count_frame = 0
            return False, self.total_blinks
    
    def track_head_movement(self, face_location: Tuple) -> Tuple[bool, float]:
        """
        Track head movement based on face center position
        Returns (has_enough_movement, total_movement)
        """
        try:
            top, right, bottom, left = face_location
            center_x = (left + right) / 2
            center_y = (top + bottom) / 2
            current_center = (center_x, center_y)
            
            if len(self.face_center_history) > 0:
                prev_center = self.face_center_history[-1]
                movement = np.sqrt(
                    (current_center[0] - prev_center[0])**2 + 
                    (current_center[1] - prev_center[1])**2
                )
                self.total_movement += movement
            
            self.face_center_history.append(current_center)
            
            has_enough = self.total_movement >= self.movement_threshold
            
            if has_enough and self.total_movement > self.movement_threshold:
                print(f"✓ HEAD MOVEMENT DETECTED! Total: {self.total_movement:.1f}px")
            
            return has_enough, self.total_movement
            
        except Exception as e:
            print(f"Movement tracking error: {e}")
            return False, 0
    
    def perform_liveness_check(self, frame: np.ndarray, face_location: Tuple, 
                               landmarks: dict = None) -> Dict:
        """
        Perform liveness check with blink and movement detection
        Returns dict with results
        """
        self.frame_counter += 1
        
        results = {
            'blink_detected': False,
            'total_blinks': self.total_blinks,
            'required_blinks': self.required_blinks,
            'has_movement': False,
            'total_movement': self.total_movement,
            'movement_threshold': self.movement_threshold,
            'overall_score': 0.0,
            'is_live': False,
            'status': '',
            'ear': 0.3
        }
        
        # Convert to grayscale for dlib
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect blinks using dlib if available, otherwise fallback
        if self.use_dlib:
            blink_detected, total_blinks, avg_ear = self.detect_blink_dlib(frame, gray_frame)
            results['ear'] = avg_ear
        else:
            blink_detected, total_blinks = self.detect_blink_fallback(landmarks)
        
        results['blink_detected'] = blink_detected
        results['total_blinks'] = total_blinks
        
        # Track head movement
        has_movement, total_movement = self.track_head_movement(face_location)
        results['has_movement'] = has_movement
        results['total_movement'] = total_movement
        
        # Calculate overall score
        blink_score = min(total_blinks / self.required_blinks, 1.0) * 0.6
        movement_score = min(total_movement / self.movement_threshold, 1.0) * 0.4
        results['overall_score'] = blink_score + movement_score
        
        # Check if liveness passed
        blinks_ok = total_blinks >= self.required_blinks
        movement_ok = total_movement >= (self.movement_threshold * 0.5)
        
        results['is_live'] = blinks_ok and movement_ok
        
        # Status message
        if results['is_live']:
            results['status'] = "✓ Liveness verified!"
        else:
            status_parts = []
            if not blinks_ok:
                status_parts.append(f"Blink {total_blinks}/{self.required_blinks}")
            if not movement_ok:
                status_parts.append(f"Move head ({total_movement:.0f}/{self.movement_threshold}px)")
            results['status'] = " | ".join(status_parts)
        
        return results
    
    def get_status_text(self) -> str:
        """Get current status text for display"""
        blink_status = f"Blinks: {self.total_blinks}/{self.required_blinks}"
        movement_status = f"Movement: {self.total_movement:.0f}/{self.movement_threshold}px"
        return f"{blink_status} | {movement_status}"


# Singleton instance
anti_spoofing_module = AntiSpoofingModule()