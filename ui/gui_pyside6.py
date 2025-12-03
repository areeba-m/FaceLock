"""
PySide6-based Modern GUI for FaceLock authentication system
Minimal black and white design with embedded camera display
"""
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFrame, QStackedWidget, QTextEdit, QGraphicsDropShadowEffect,
                               QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QFont, QPixmap, QImage, QPalette, QColor, QIcon
import cv2
import numpy as np
from PIL import Image
import sys
import threading
from src.auth_system import auth_system
from src.totp_handler import totp_handler
from src.database import db_manager
from config.settings import CAMERA_INDEX


class AuthThread(QThread):
    """Thread for authentication operations"""
    finished = Signal(dict)
    
    def __init__(self, operation, *args):
        super().__init__()
        self.operation = operation
        self.args = args
    
    def run(self):
        result = self.operation(*self.args)
        self.finished.emit(result)


class CameraWidget(QLabel):
    """Widget to display camera feed"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self.setMaximumSize(640, 480)
        self.setScaledContents(True)
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #ffffff;
                border-radius: 8px;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Camera Initializing...")
        
    def update_frame(self, frame):
        """Update camera frame"""
        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


class ErrorLabel(QLabel):
    """Styled error label"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                color: #ff4444;
                background-color: rgba(255, 68, 68, 0.1);
                padding: 10px;
                border: 1px solid #ff4444;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.hide()
    
    def show_error(self, message):
        """Show error message"""
        self.setText(f"⚠ {message}")
        self.show()
    
    def clear_error(self):
        """Clear error message"""
        self.hide()


class InfoLabel(QLabel):
    """Styled info label"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                background-color: rgba(76, 175, 80, 0.1);
                padding: 10px;
                border: 1px solid #4CAF50;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.hide()
    
    def show_info(self, message):
        """Show info message"""
        self.setText(f"✓ {message}")
        self.show()
    
    def clear_info(self):
        """Clear info message"""
        self.hide()


class FaceLockMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FaceLock Authentication System")
        
        # Set reasonable default size that fits most screens
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        # State
        self.video_capture = None
        self.pending_user_id = None
        self.auth_thread = None
        self.camera_timer = None
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Setup main UI"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create screens
        self.create_login_screen()
        self.create_totp_screen()
        self.create_qr_screen()
        self.create_dashboard_screen()
        
        # Show login screen
        self.stacked_widget.setCurrentIndex(0)
    
    def apply_styles(self):
        """Apply global styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
            }
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px;
                color: #ffffff;
                font-family: 'Courier New', monospace;
            }
            QScrollArea {
                border: none;
                background-color: #000000;
            }
        """)
    
    def create_login_screen(self):
        """Create login screen"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo/Title
        title = QLabel("🔒 FaceLock")
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Secure Multi-Factor Authentication")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #888888;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Login form container
        form_container = QWidget()
        form_container.setMaximumWidth(380)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(12)
        
        # Username
        username_label = QLabel("Username")
        username_label.setFont(QFont("Arial", 11, QFont.Bold))
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)
        
        # Password
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 11, QFont.Bold))
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.password_input)
        
        form_layout.addSpacing(8)
        
        # Error display
        self.login_error = ErrorLabel()
        form_layout.addWidget(self.login_error)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.clicked.connect(self.handle_login)
        button_layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("Register")
        self.register_btn.setMinimumHeight(44)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)
        self.register_btn.clicked.connect(self.handle_registration)
        button_layout.addWidget(self.register_btn)
        
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_container, alignment=Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        # Info
        info = QLabel("Multi-layer security: Facial Recognition + Anti-Spoofing + 2FA")
        info.setFont(QFont("Arial", 9))
        info.setStyleSheet("color: #666666;")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.stacked_widget.addWidget(screen)
    
    def create_totp_screen(self):
        """Create TOTP verification screen"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icon
        icon = QLabel("🔑")
        icon.setFont(QFont("Arial", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Title
        title = QLabel("Two-Factor Authentication")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        self.totp_message = InfoLabel()
        self.totp_message.setMaximumWidth(450)
        layout.addWidget(self.totp_message, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        # Instructions
        instructions = QLabel("Enter the 6-digit code from your authenticator app")
        instructions.setFont(QFont("Arial", 12))
        instructions.setStyleSheet("color: #888888;")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # OTP Input
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("000000")
        self.otp_input.setMaxLength(6)
        self.otp_input.setAlignment(Qt.AlignCenter)
        self.otp_input.setFont(QFont("Courier New", 28, QFont.Bold))
        self.otp_input.setMaximumWidth(250)
        self.otp_input.setMinimumHeight(55)
        self.otp_input.returnPressed.connect(self.verify_totp)
        layout.addWidget(self.otp_input, alignment=Qt.AlignCenter)
        
        # Error display
        self.totp_error = ErrorLabel()
        self.totp_error.setMaximumWidth(450)
        layout.addWidget(self.totp_error, alignment=Qt.AlignCenter)
        
        layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        verify_btn = QPushButton("Verify")
        verify_btn.setMinimumSize(130, 44)
        verify_btn.clicked.connect(self.verify_totp)
        button_layout.addWidget(verify_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(130, 44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)
        cancel_btn.clicked.connect(self.back_to_login)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.stacked_widget.addWidget(screen)
    
    def create_qr_screen(self):
        """Create QR code display screen with side-by-side layout"""
        screen = QWidget()
        main_layout = QVBoxLayout(screen)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)
        
        # Success header
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("✓")
        icon.setFont(QFont("Arial", 36, QFont.Bold))
        icon.setStyleSheet("color: #4CAF50;")
        header_layout.addWidget(icon)
        
        title = QLabel("Registration Successful!")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #4CAF50;")
        header_layout.addWidget(title)
        
        main_layout.addLayout(header_layout)
        
        # Instructions
        instructions = QLabel("Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)")
        instructions.setFont(QFont("Arial", 11))
        instructions.setStyleSheet("color: #888888;")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        main_layout.addSpacing(10)
        
        # Side by side container for QR and Manual Key
        side_by_side_container = QWidget()
        side_by_side_layout = QHBoxLayout(side_by_side_container)
        side_by_side_layout.setSpacing(30)
        side_by_side_layout.setAlignment(Qt.AlignCenter)
        
        # Left side - QR Code
        qr_container = QWidget()
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setAlignment(Qt.AlignCenter)
        qr_layout.setSpacing(8)
        
        qr_title = QLabel("Scan QR Code")
        qr_title.setFont(QFont("Arial", 12, QFont.Bold))
        qr_title.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(qr_title)
        
        self.qr_label = QLabel()
        self.qr_label.setMinimumSize(200, 200)
        self.qr_label.setMaximumSize(220, 220)
        self.qr_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px solid #ffffff;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setScaledContents(True)
        qr_layout.addWidget(self.qr_label, alignment=Qt.AlignCenter)
        
        side_by_side_layout.addWidget(qr_container)
        
        # Divider
        divider = QLabel("OR")
        divider.setFont(QFont("Arial", 14, QFont.Bold))
        divider.setStyleSheet("color: #666666;")
        divider.setAlignment(Qt.AlignCenter)
        side_by_side_layout.addWidget(divider)
        
        # Right side - Manual Entry Key
        manual_container = QWidget()
        manual_layout = QVBoxLayout(manual_container)
        manual_layout.setAlignment(Qt.AlignCenter)
        manual_layout.setSpacing(8)
        
        manual_title = QLabel("Manual Entry Key")
        manual_title.setFont(QFont("Arial", 12, QFont.Bold))
        manual_title.setAlignment(Qt.AlignCenter)
        manual_layout.addWidget(manual_title)
        
        manual_desc = QLabel("If you can't scan the QR code,\nenter this key manually:")
        manual_desc.setFont(QFont("Arial", 10))
        manual_desc.setStyleSheet("color: #888888;")
        manual_desc.setAlignment(Qt.AlignCenter)
        manual_layout.addWidget(manual_desc)
        
        self.secret_display = QTextEdit()
        self.secret_display.setMinimumSize(280, 60)
        self.secret_display.setMaximumSize(300, 70)
        self.secret_display.setReadOnly(True)
        self.secret_display.setFont(QFont("Courier New", 12, QFont.Bold))
        self.secret_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                padding: 8px;
                color: #4CAF50;
            }
        """)
        manual_layout.addWidget(self.secret_display, alignment=Qt.AlignCenter)
        
        # Copy hint
        copy_hint = QLabel("Select and copy the key above")
        copy_hint.setFont(QFont("Arial", 9))
        copy_hint.setStyleSheet("color: #666666;")
        copy_hint.setAlignment(Qt.AlignCenter)
        manual_layout.addWidget(copy_hint)
        
        side_by_side_layout.addWidget(manual_container)
        
        main_layout.addWidget(side_by_side_container, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(15)
        
        # Important note
        note = QLabel("⚠ Save this key securely! You'll need it to log in.")
        note.setFont(QFont("Arial", 11, QFont.Bold))
        note.setStyleSheet("color: #FFA500;")
        note.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(note)
        
        main_layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setAlignment(Qt.AlignCenter)
        
        home_btn = QPushButton("🏠 Back to Home")
        home_btn.setMinimumSize(150, 44)
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)
        home_btn.clicked.connect(self.back_to_login)
        button_layout.addWidget(home_btn)
        
        done_btn = QPushButton("Done ✓")
        done_btn.setMinimumSize(150, 44)
        done_btn.clicked.connect(self.handle_qr_done)
        button_layout.addWidget(done_btn)
        
        main_layout.addLayout(button_layout)
        
        self.stacked_widget.addWidget(screen)
    
    def create_dashboard_screen(self):
        """Create dashboard screen"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Success icon
        icon = QLabel("🎉")
        icon.setFont(QFont("Arial", 56))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Title
        title = QLabel("Welcome to FaceLock!")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #4CAF50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Success message
        success_msg = QLabel("Authentication Successful")
        success_msg.setFont(QFont("Arial", 16))
        success_msg.setStyleSheet("color: #4CAF50;")
        success_msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(success_msg)
        
        layout.addSpacing(15)
        
        # Authentication methods container
        methods_container = QFrame()
        methods_container.setMaximumWidth(450)
        methods_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)
        methods_layout = QVBoxLayout(methods_container)
        methods_layout.setSpacing(10)
        methods_layout.setContentsMargins(25, 20, 25, 20)
        
        methods_title = QLabel("Authentication Methods Verified")
        methods_title.setFont(QFont("Arial", 14, QFont.Bold))
        methods_title.setAlignment(Qt.AlignCenter)
        methods_title.setStyleSheet("color: #ffffff; background-color: transparent;")
        methods_layout.addWidget(methods_title)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #333333;")
        methods_layout.addWidget(separator)
        
        methods_layout.addSpacing(5)
        
        methods = [
            ("✓", "Password Authentication"),
            ("✓", "Facial Recognition"),
            ("✓", "Anti-Spoofing Detection"),
            ("✓", "Time-based OTP (2FA)")
        ]
        
        for check, method_text in methods:
            method_row = QHBoxLayout()
            method_row.setSpacing(10)
            
            check_label = QLabel(check)
            check_label.setFont(QFont("Arial", 14, QFont.Bold))
            check_label.setStyleSheet("color: #4CAF50; background-color: transparent;")
            check_label.setFixedWidth(25)
            method_row.addWidget(check_label)
            
            method_label = QLabel(method_text)
            method_label.setFont(QFont("Arial", 13))
            method_label.setStyleSheet("color: #ffffff; background-color: transparent;")
            method_row.addWidget(method_label)
            
            method_row.addStretch()
            methods_layout.addLayout(method_row)
        
        layout.addWidget(methods_container, alignment=Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setMinimumSize(180, 48)
        logout_btn.clicked.connect(self.handle_logout)
        layout.addWidget(logout_btn, alignment=Qt.AlignCenter)
        
        self.stacked_widget.addWidget(screen)
    
    def handle_login(self):
        """Handle login action"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.login_error.show_error("Please enter username and password")
            return
        
        self.login_error.clear_error()
        self.login_btn.setEnabled(False)
        self.register_btn.setEnabled(False)
        self.login_btn.setText("Initializing Camera...")
        
        # Initialize camera
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            self.login_error.show_error("Cannot access camera")
            self.login_btn.setEnabled(True)
            self.register_btn.setEnabled(True)
            self.login_btn.setText("Login")
            return
        
        self.login_btn.setText("Authenticating...")
        
        # Start authentication in thread
        self.auth_thread = AuthThread(auth_system.authenticate_user, username, password, self.video_capture)
        self.auth_thread.finished.connect(self.handle_auth_result)
        self.auth_thread.start()
    
    def handle_auth_result(self, result):
        """Handle authentication result"""
        self.login_btn.setEnabled(True)
        self.register_btn.setEnabled(True)
        self.login_btn.setText("Login")
        
        if self.video_capture:
            self.video_capture.release()
            cv2.destroyAllWindows()
        
        if result.get('requires_totp', False):
            self.pending_user_id = result['user_id']
            self.totp_message.show_info(result['message'])
            self.totp_error.clear_error()
            self.otp_input.clear()
            self.stacked_widget.setCurrentIndex(1)
            self.otp_input.setFocus()
        elif result.get('success', False):
            self.stacked_widget.setCurrentIndex(3)
        else:
            # Check for spoofing timeout
            msg = result.get('message', '')
            if "timeout" in msg.lower() or "60" in msg:
                self.login_error.show_error("⚠ SPOOFING ATTEMPT DETECTED - Session Timeout\nThe system will close for security.")
                QTimer.singleShot(3000, self.close_application_security)
            else:
                self.login_error.show_error(msg)
    
    def close_application_security(self):
        """Close application due to security issue"""
        self.close()
    
    def handle_registration(self):
        """Handle registration action"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.login_error.show_error("Please enter username and password")
            return
        
        if len(password) < 8:
            self.login_error.show_error("Password must be at least 8 characters")
            return
        
        # Simple password confirmation dialog alternative
        from PySide6.QtWidgets import QInputDialog
        confirm_password, ok = QInputDialog.getText(
            self, "Confirm Password", "Re-enter password:",
            QLineEdit.Password
        )
        
        if not ok:
            return
        
        if password != confirm_password:
            self.login_error.show_error("Passwords do not match")
            return
        
        self.login_error.clear_error()
        self.login_btn.setEnabled(False)
        self.register_btn.setEnabled(False)
        self.register_btn.setText("Initializing Camera...")
        
        # Initialize camera
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            self.login_error.show_error("Cannot access camera")
            self.login_btn.setEnabled(True)
            self.register_btn.setEnabled(True)
            self.register_btn.setText("Register")
            return
        
        self.register_btn.setText("Registering...")
        
        # Start registration in thread
        self.auth_thread = AuthThread(auth_system.register_user, username, password, self.video_capture)
        self.auth_thread.finished.connect(self.handle_register_result)
        self.auth_thread.start()
    
    def handle_register_result(self, result):
        """Handle registration result"""
        self.login_btn.setEnabled(True)
        self.register_btn.setEnabled(True)
        self.register_btn.setText("Register")
        
        if self.video_capture:
            self.video_capture.release()
            cv2.destroyAllWindows()
        
        if result.get('success', False):
            # Display QR code
            qr_image = result['qr_code']
            qr_image_resized = qr_image.resize((200, 200))
            qr_image_resized = qr_image_resized.convert("RGB")
            
            # Convert PIL to QPixmap
            data = qr_image_resized.tobytes("raw", "RGB")
            qimage = QImage(data, qr_image_resized.width, qr_image_resized.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.qr_label.setPixmap(pixmap)
            
            # Display secret
            self.secret_display.setText(result['secret'])
            
            # Show QR screen
            self.stacked_widget.setCurrentIndex(2)
        else:
            # Check for spoofing timeout
            msg = result.get('message', '')
            if "timeout" in msg.lower() or "60" in msg:
                self.login_error.show_error("⚠ SPOOFING ATTEMPT DETECTED - Registration Timeout\nThe system will close for security.")
                QTimer.singleShot(3000, self.close_application_security)
            else:
                self.login_error.show_error(msg)
    
    def verify_totp(self):
        """Verify TOTP code"""
        otp_code = self.otp_input.text().strip()
        
        if len(otp_code) != 6 or not otp_code.isdigit():
            self.totp_error.show_error("Please enter a valid 6-digit code")
            return
        
        self.totp_error.clear_error()
        
        result = auth_system.verify_totp(self.pending_user_id, otp_code)
        
        if result['success']:
            self.stacked_widget.setCurrentIndex(3)
        else:
            self.totp_error.show_error(result['message'])
            self.otp_input.clear()
    
    def handle_qr_done(self):
        """Handle done button on QR screen"""
        auth_system.logout()
        self.pending_user_id = None
        self.back_to_login()
    
    def back_to_login(self):
        """Go back to login screen"""
        auth_system.logout()
        self.pending_user_id = None
        self.username_input.clear()
        self.password_input.clear()
        self.login_error.clear_error()
        self.stacked_widget.setCurrentIndex(0)
        self.username_input.setFocus()
    
    def handle_logout(self):
        """Handle logout"""
        auth_system.logout()
        self.pending_user_id = None
        self.back_to_login()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.video_capture:
            self.video_capture.release()
        cv2.destroyAllWindows()
        event.accept()


def run_gui():
    """Run the PySide6 GUI application"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(0, 0, 0))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(26, 26, 26))
    palette.setColor(QPalette.AlternateBase, QColor(51, 51, 51))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    window = FaceLockMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()