"""
Tkinter-based GUI for FaceLock authentication system
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import cv2
from PIL import Image, ImageTk
import threading
from src.auth_system import auth_system
from src.totp_handler import totp_handler
from src.database import db_manager
from config.settings import CAMERA_INDEX


class FaceLockGUI:
    """Main GUI application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("FaceLock Authentication System")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        self.video_capture = None
        self.current_frame = None
        self.pending_user_id = None
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main container
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Show login screen
        self.show_login_screen()
    
    def clear_screen(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Display login screen"""
        self.clear_screen()
        
        # Title
        title = ttk.Label(self.main_container, text="FaceLock Authentication",
                         font=('Helvetica', 24, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Subtitle
        subtitle = ttk.Label(self.main_container, 
                            text="Secure facial recognition with anti-spoofing & 2FA",
                            font=('Helvetica', 10))
        subtitle.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Username
        ttk.Label(self.main_container, text="Username:", 
                 font=('Helvetica', 12)).grid(row=2, column=0, sticky=tk.E, pady=10, padx=5)
        self.username_entry = ttk.Entry(self.main_container, width=30, font=('Helvetica', 11))
        self.username_entry.grid(row=2, column=1, pady=10, padx=5)
        
        # Password
        ttk.Label(self.main_container, text="Password:", 
                 font=('Helvetica', 12)).grid(row=3, column=0, sticky=tk.E, pady=10, padx=5)
        self.password_entry = ttk.Entry(self.main_container, width=30, show="*", 
                                       font=('Helvetica', 11))
        self.password_entry.grid(row=3, column=1, pady=10, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.main_container)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        login_btn = ttk.Button(button_frame, text="Login", command=self.handle_login,
                              width=15)
        login_btn.grid(row=0, column=0, padx=5)
        
        register_btn = ttk.Button(button_frame, text="Register", 
                                 command=self.handle_registration, width=15)
        register_btn.grid(row=0, column=1, padx=5)
        
        # Status
        self.status_label = ttk.Label(self.main_container, text="", 
                                     font=('Helvetica', 10), foreground='blue')
        self.status_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Info
        info_text = ("FaceLock uses facial recognition with anti-spoofing detection\n"
                    "and Time-based One-Time Passwords (TOTP) for secure authentication.")
        info_label = ttk.Label(self.main_container, text=info_text, 
                              font=('Helvetica', 9), foreground='gray')
        info_label.grid(row=6, column=0, columnspan=2, pady=20)
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        self.status_label.config(text="Initializing camera...")
        self.root.update()
        
        # Initialize camera
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return
        
        # Perform authentication in thread
        self.status_label.config(text="Authenticating...")
        thread = threading.Thread(target=self._authenticate_thread, 
                                 args=(username, password))
        thread.start()
    
    def _authenticate_thread(self, username, password):
        """Authentication in separate thread"""
        result = auth_system.authenticate_user(username, password, self.video_capture)
        
        self.video_capture.release()
        cv2.destroyAllWindows()
        
        # Update GUI in main thread
        self.root.after(0, self._handle_auth_result, result)
    
    def _handle_auth_result(self, result):
        """Handle authentication result"""
        if result['requires_totp']:
            self.pending_user_id = result['user_id']
            self.show_totp_screen(result['message'])
        elif result['success']:
            self.show_dashboard()
        else:
            self.status_label.config(text=result['message'], foreground='red')
            messagebox.showerror("Authentication Failed", result['message'])
    
    def handle_registration(self):
        """Handle registration button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return
        
        # Confirm password
        confirm_password = simpledialog.askstring("Confirm Password", 
                                                     "Re-enter password:", 
                                                     show='*')
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        self.status_label.config(text="Initializing camera...")
        self.root.update()
        
        # Initialize camera
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return
        
        # Perform registration in thread
        self.status_label.config(text="Starting registration...")
        thread = threading.Thread(target=self._register_thread, 
                                 args=(username, password))
        thread.start()
    
    def _register_thread(self, username, password):
        """Registration in separate thread"""
        result = auth_system.register_user(username, password, self.video_capture)
        
        self.video_capture.release()
        cv2.destroyAllWindows()
        
        # Update GUI in main thread
        self.root.after(0, self._handle_register_result, result)
    
    def _handle_register_result(self, result):
        """Handle registration result"""
        if result['success']:
            self.show_qr_code_screen(result['qr_code'], result['secret'])
        else:
            self.status_label.config(text=result['message'], foreground='red')
            messagebox.showerror("Registration Failed", result['message'])
    
    def show_qr_code_screen(self, qr_image, secret):
        """Display QR code for TOTP setup"""
        self.clear_screen()
        
        # Title
        title = ttk.Label(self.main_container, text="Registration Successful!",
                         font=('Helvetica', 20, 'bold'), foreground='green')
        title.grid(row=0, column=0, pady=20)
        
        # Instructions
        instructions = ttk.Label(self.main_container, 
                                text="Scan this QR code with your authenticator app\n"
                                     "(Google Authenticator, Authy, etc.)",
                                font=('Helvetica', 11))
        instructions.grid(row=1, column=0, pady=10)
        
        # QR Code
        qr_photo = ImageTk.PhotoImage(qr_image.resize((300, 300)))
        qr_label = ttk.Label(self.main_container, image=qr_photo)
        qr_label.image = qr_photo  # Keep reference
        qr_label.grid(row=2, column=0, pady=10)
        
        # Secret key
        secret_frame = ttk.LabelFrame(self.main_container, text="Manual Entry Key", 
                                     padding="10")
        secret_frame.grid(row=3, column=0, pady=10, padx=20, sticky=(tk.W, tk.E))
        
        secret_text = scrolledtext.ScrolledText(secret_frame, height=2, width=40, 
                                                font=('Courier', 10))
        secret_text.insert(tk.END, secret)
        secret_text.config(state=tk.DISABLED)
        secret_text.pack()
        
        # Continue button
        continue_btn = ttk.Button(self.main_container, text="Continue to Login",
                                 command=self.show_login_screen, width=20)
        continue_btn.grid(row=4, column=0, pady=20)
    
    def show_totp_screen(self, message):
        """Display TOTP verification screen"""
        self.clear_screen()
        
        # Title
        title = ttk.Label(self.main_container, text="Two-Factor Authentication",
                         font=('Helvetica', 20, 'bold'))
        title.grid(row=0, column=0, pady=20)
        
        # Message
        msg_label = ttk.Label(self.main_container, text=message,
                             font=('Helvetica', 11), foreground='green')
        msg_label.grid(row=1, column=0, pady=10)
        
        # Instructions
        instructions = ttk.Label(self.main_container,
                                text="Enter the 6-digit code from your authenticator app:",
                                font=('Helvetica', 11))
        instructions.grid(row=2, column=0, pady=10)
        
        # OTP Entry
        self.otp_entry = ttk.Entry(self.main_container, width=15, 
                                   font=('Helvetica', 18, 'bold'), 
                                   justify='center')
        self.otp_entry.grid(row=3, column=0, pady=20)
        self.otp_entry.focus()
        
        # Verify button
        verify_btn = ttk.Button(self.main_container, text="Verify",
                               command=self.verify_totp_code, width=15)
        verify_btn.grid(row=4, column=0, pady=10)
        
        # Cancel button
        cancel_btn = ttk.Button(self.main_container, text="Cancel",
                               command=self.show_login_screen, width=15)
        cancel_btn.grid(row=5, column=0, pady=5)
        
        # Bind Enter key
        self.otp_entry.bind('<Return>', lambda e: self.verify_totp_code())
    
    def verify_totp_code(self):
        """Verify entered TOTP code"""
        otp_code = self.otp_entry.get().strip()
        
        if len(otp_code) != 6 or not otp_code.isdigit():
            messagebox.showerror("Error", "Please enter a valid 6-digit code")
            return
        
        result = auth_system.verify_totp(self.pending_user_id, otp_code)
        
        if result['success']:
            messagebox.showinfo("Success", "Authentication successful!")
            self.show_dashboard()
        else:
            messagebox.showerror("Error", result['message'])
            self.otp_entry.delete(0, tk.END)
    
    def show_dashboard(self):
        """Display main dashboard after successful authentication"""
        self.clear_screen()
        
        # Title
        title = ttk.Label(self.main_container, text="Welcome to FaceLock!",
                         font=('Helvetica', 24, 'bold'), foreground='green')
        title.grid(row=0, column=0, pady=30)
        
        # Success message
        success_msg = ttk.Label(self.main_container,
                               text="✓ Authentication Successful",
                               font=('Helvetica', 16), foreground='green')
        success_msg.grid(row=1, column=0, pady=20)
        
        # Info
        info_frame = ttk.LabelFrame(self.main_container, 
                                   text="Authentication Methods Used", 
                                   padding="20")
        info_frame.grid(row=2, column=0, pady=20, padx=40, sticky=(tk.W, tk.E))
        
        methods = [
            "✓ Password Authentication",
            "✓ Facial Recognition",
            "✓ Anti-Spoofing Detection (Blink, Movement, Texture)",
            "✓ Time-based One-Time Password (TOTP)"
        ]
        
        for i, method in enumerate(methods):
            ttk.Label(info_frame, text=method, font=('Helvetica', 11)).grid(
                row=i, column=0, sticky=tk.W, pady=5
            )
        
        # Logout button
        logout_btn = ttk.Button(self.main_container, text="Logout",
                               command=self.handle_logout, width=15)
        logout_btn.grid(row=3, column=0, pady=30)
    
    def handle_logout(self):
        """Handle logout"""
        auth_system.logout()
        self.pending_user_id = None
        messagebox.showinfo("Logged Out", "You have been logged out successfully")
        self.show_login_screen()
    
    def on_closing(self):
        """Handle window closing"""
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()
        self.root.destroy()


def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app = FaceLockGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()