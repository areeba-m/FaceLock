"""
Anti-spoofing module implementing multiple liveness detection techniques:
1. Blink Detection - Eye Aspect Ratio (EAR)
2. Head Movement Detection - Pose estimation
3. Texture Analysis - Local Binary Patterns (LBP)
"""
import cv2
import numpy as np
from scipy.spatial import distance
from typing import Optional, Tuple, List
from collections import deque
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import pickle
import os
from config.settings import (
    EYE_AR_THRESH,
    EYE_AR_CONSEC_FRAMES,
    HEAD_MOVEMENT_THRESHOLD,
    LBP_THRESHOLD,
    MODELS_DIR
)


class AntiSpoofingModule:
    """Implements multiple anti-spoofing techniques"""
    
    def __init__(self):
        self.eye_ar_history = deque(maxlen=EYE_AR_CONSEC_FRAMES)
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        
        # Head pose history
        self.pose_history = deque(maxlen=30)
        
        # LBP model
        self.lbp_model_path = os.path.join(MODELS_DIR, 'lbp_model.pkl')
        self.lbp_scaler_path = os.path.join(MODELS_DIR, 'lbp_scaler.pkl')
        self._init_lbp_model()
    
    def _init_lbp_model(self):
        """Initialize or load LBP classifier"""
        if os.path.exists(self.lbp_model_path) and os.path.exists(self.lbp_scaler_path):
            with open(self.lbp_model_path, 'rb') as f:
                self.lbp_classifier = pickle.load(f)
            with open(self.lbp_scaler_path, 'rb') as f:
                self.lbp_scaler = pickle.load(f)
        else:
            # Create simple model (will improve with training)
            self.lbp_classifier = SVC(kernel='linear', probability=True)
            self.lbp_scaler = StandardScaler()
            self._create_initial_lbp_model()
    
    def _create_initial_lbp_model(self):
        """Create initial LBP model with synthetic data"""
        # Create synthetic training data
        n_samples = 100
        
        # Simulate real face features (higher variance)
        real_features = np.random.randn(n_samples, 59) * 30 + 50
        real_labels = np.ones(n_samples)
        
        # Simulate fake face features (lower variance, different mean)
        fake_features = np.random.randn(n_samples, 59) * 15 + 70
        fake_labels = np.zeros(n_samples)
        
        X = np.vstack([real_features, fake_features])
        y = np.hstack([real_labels, fake_labels])
        
        # Train model
        X_scaled = self.lbp_scaler.fit_transform(X)
        self.lbp_classifier.fit(X_scaled, y)
        
        # Save model
        with open(self.lbp_model_path, 'wb') as f:
            pickle.dump(self.lbp_classifier, f)
        with open(self.lbp_scaler_path, 'wb') as f:
            pickle.dump(self.lbp_scaler, f)
    
    @staticmethod
    def eye_aspect_ratio(eye_landmarks: List) -> float:
        """
        Calculate Eye Aspect Ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        # Vertical eye distances
        A = distance.euclidean(eye_landmarks[1], eye_landmarks[5])
        B = distance.euclidean(eye_landmarks[2], eye_landmarks[4])
        
        # Horizontal eye distance
        C = distance.euclidean(eye_landmarks[0], eye_landmarks[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, landmarks: dict) -> Tuple[bool, int]:
        """
        Detect blinks using Eye Aspect Ratio
        Returns (blink_detected, total_blinks)
        """
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return False, self.total_blinks
        
        # Calculate EAR for both eyes
        left_ear = self.eye_aspect_ratio(landmarks['left_eye'])
        right_ear = self.eye_aspect_ratio(landmarks['right_eye'])
        
        # Average EAR
        ear = (left_ear + right_ear) / 2.0
        
        # Add to history
        self.eye_ar_history.append(ear)
        
        # Check for blink
        blink_detected = False
        if ear < EYE_AR_THRESH:
            self.blink_counter += 1
        else:
            if self.blink_counter >= EYE_AR_CONSEC_FRAMES:
                self.total_blinks += 1
                blink_detected = True
            self.blink_counter = 0
        
        self.frame_counter += 1
        
        return blink_detected, self.total_blinks
    
    def estimate_head_pose(self, landmarks: dict, frame_shape: Tuple) -> Optional[Tuple[float, float, float]]:
        """
        Estimate head pose (yaw, pitch, roll) from facial landmarks
        """
        if not landmarks or 'nose_tip' not in landmarks or 'chin' not in landmarks:
            return None
        
        try:
            # Image dimensions
            size = frame_shape
            
            # 2D image points from landmarks
            image_points = np.array([
                landmarks['nose_tip'][2],      # Nose tip
                landmarks['chin'][8],           # Chin
                landmarks['left_eye'][0],       # Left eye left corner
                landmarks['right_eye'][3],      # Right eye right corner
                landmarks['top_lip'][0],        # Left mouth corner
                landmarks['bottom_lip'][0]      # Right mouth corner
            ], dtype="double")
            
            # 3D model points (approximate)
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip
                (0.0, -330.0, -65.0),        # Chin
                (-225.0, 170.0, -135.0),     # Left eye left corner
                (225.0, 170.0, -135.0),      # Right eye right corner
                (-150.0, -150.0, -125.0),    # Left mouth corner
                (150.0, -150.0, -125.0)      # Right mouth corner
            ])
            
            # Camera internals
            focal_length = size[1]
            center = (size[1] / 2, size[0] / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            
            dist_coeffs = np.zeros((4, 1))
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points,
                image_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if success:
                # Convert rotation vector to Euler angles
                rotation_mat, _ = cv2.Rodrigues(rotation_vector)
                pose_mat = cv2.hconcat((rotation_mat, translation_vector))
                _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
                
                pitch, yaw, roll = euler_angles.flatten()[:3]
                return (pitch, yaw, roll)
            
        except Exception as e:
            print(f"Error in pose estimation: {e}")
        
        return None
    
    def check_head_movement(self, landmarks: dict, frame_shape: Tuple) -> bool:
        """
        Check if sufficient head movement detected (anti-spoofing)
        """
        pose = self.estimate_head_pose(landmarks, frame_shape)
        
        if pose is None:
            return False
        
        self.pose_history.append(pose)
        
        if len(self.pose_history) < 2:
            return False
        
        # Calculate movement range
        poses = np.array(self.pose_history)
        pitch_range = np.ptp(poses[:, 0])
        yaw_range = np.ptp(poses[:, 1])
        
        # Check if movement exceeds threshold
        return (pitch_range > HEAD_MOVEMENT_THRESHOLD or 
                yaw_range > HEAD_MOVEMENT_THRESHOLD)
    
    def extract_lbp_features(self, frame: np.ndarray, face_location: Tuple) -> np.ndarray:
        """
        Extract Local Binary Pattern features for texture analysis
        """
        top, right, bottom, left = face_location
        
        # Extract face region
        face = frame[top:bottom, left:right]
        
        if face.size == 0:
            return np.zeros(59)
        
        # Convert to grayscale
        if len(face.shape) == 3:
            gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        else:
            gray = face
        
        # Resize to standard size
        gray = cv2.resize(gray, (64, 64))
        
        # Calculate LBP
        lbp = self._calculate_lbp(gray)
        
        # Calculate histogram
        hist, _ = np.histogram(lbp.ravel(), bins=59, range=(0, 59))
        
        # Normalize
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        
        return hist
    
    @staticmethod
    def _calculate_lbp(image: np.ndarray, radius: int = 1, n_points: int = 8) -> np.ndarray:
        """
        Calculate Local Binary Pattern
        """
        rows, cols = image.shape
        lbp = np.zeros((rows, cols), dtype=np.uint8)
        
        for i in range(radius, rows - radius):
            for j in range(radius, cols - radius):
                center = image[i, j]
                binary_string = ''
                
                for p in range(n_points):
                    # Calculate coordinates
                    x = i + int(radius * np.cos(2 * np.pi * p / n_points))
                    y = j - int(radius * np.sin(2 * np.pi * p / n_points))
                    
                    # Compare with center
                    if image[x, y] >= center:
                        binary_string += '1'
                    else:
                        binary_string += '0'
                
                lbp[i, j] = int(binary_string, 2)
        
        return lbp
    
    def check_texture_liveness(self, frame: np.ndarray, face_location: Tuple) -> Tuple[bool, float]:
        """
        Check if face is real using texture analysis
        Returns (is_real, confidence)
        """
        features = self.extract_lbp_features(frame, face_location)
        features_scaled = self.lbp_scaler.transform([features])
        
        prediction = self.lbp_classifier.predict(features_scaled)[0]
        probability = self.lbp_classifier.predict_proba(features_scaled)[0]
        
        confidence = probability[int(prediction)]
        is_real = prediction == 1 and confidence > LBP_THRESHOLD
        
        return is_real, confidence
    
    def reset_counters(self):
        """Reset all counters for new authentication session"""
        self.eye_ar_history.clear()
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        self.pose_history.clear()
    
    def perform_liveness_check(self, frame: np.ndarray, face_location: Tuple, 
                              landmarks: dict) -> dict:
        """
        Perform comprehensive liveness check
        Returns dict with results from all methods
        """
        results = {
            'blink_detected': False,
            'total_blinks': 0,
            'head_movement': False,
            'texture_real': False,
            'texture_confidence': 0.0,
            'overall_score': 0.0
        }
        
        # Blink detection
        blink_detected, total_blinks = self.detect_blink(landmarks)
        results['blink_detected'] = blink_detected
        results['total_blinks'] = total_blinks
        
        # Head movement
        results['head_movement'] = self.check_head_movement(landmarks, frame.shape)
        
        # Texture analysis
        texture_real, texture_conf = self.check_texture_liveness(frame, face_location)
        results['texture_real'] = texture_real
        results['texture_confidence'] = texture_conf
        
        # Calculate overall score
        score = 0.0
        if total_blinks >= 1:
            score += 0.3
        if results['head_movement']:
            score += 0.3
        if texture_real:
            score += 0.4
        
        results['overall_score'] = score
        
        return results


# Singleton instance
anti_spoofing_module = AntiSpoofingModule()