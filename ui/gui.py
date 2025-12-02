# """
# Tkinter-based GUI for FaceLock authentication system
# """
# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext, simpledialog
# import cv2
# from PIL import Image, ImageTk
# import threading
# from src.auth_system import auth_system
# from src.totp_handler import totp_handler
# from src.database import db_manager
# from config.settings import CAMERA_INDEX


# class FaceLockGUI:
#     """Main GUI application"""
    
#     def __init__(self, root):
#         self.root = root
#         self.root.title("FaceLock Authentication System")
#         self.root.geometry("800x600")
#         self.root.resizable(False, False)
        
#         self.video_capture = None
#         self.current_frame = None
#         self.pending_user_id = None
        
#         # Style
#         style = ttk.Style()
#         style.theme_use('clam')
        
#         # Create main container
#         self.main_container = ttk.Frame(root, padding="10")
#         self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
#         # Show login screen
#         self.show_login_screen()
    
#     def clear_screen(self):
#         """Clear all widgets from main container"""
#         for widget in self.main_container.winfo_children():
#             widget.destroy()
    
#     def show_login_screen(self):
#         """Display login screen"""
#         self.clear_screen()
        
#         # Title
#         title = ttk.Label(self.main_container, text="FaceLock Authentication",
#                          font=('Helvetica', 24, 'bold'))
#         title.grid(row=0, column=0, columnspan=2, pady=20)
        
#         # Subtitle
#         subtitle = ttk.Label(self.main_container, 
#                             text="Secure facial recognition with anti-spoofing & 2FA",
#                             font=('Helvetica', 10))
#         subtitle.grid(row=1, column=0, columnspan=2, pady=5)
        
#         # Username
#         ttk.Label(self.main_container, text="Username:", 
#                  font=('Helvetica', 12)).grid(row=2, column=0, sticky=tk.E, pady=10, padx=5)
#         self.username_entry = ttk.Entry(self.main_container, width=30, font=('Helvetica', 11))
#         self.username_entry.grid(row=2, column=1, pady=10, padx=5)
        
#         # Password
#         ttk.Label(self.main_container, text="Password:", 
#                  font=('Helvetica', 12)).grid(row=3, column=0, sticky=tk.E, pady=10, padx=5)
#         self.password_entry = ttk.Entry(self.main_container, width=30, show="*", 
#                                        font=('Helvetica', 11))
#         self.password_entry.grid(row=3, column=1, pady=10, padx=5)
        
#         # Buttons
#         button_frame = ttk.Frame(self.main_container)
#         button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
#         login_btn = ttk.Button(button_frame, text="Login", command=self.handle_login,
#                               width=15)
#         login_btn.grid(row=0, column=0, padx=5)
        
#         register_btn = ttk.Button(button_frame, text="Register", 
#                                  command=self.handle_registration, width=15)
#         register_btn.grid(row=0, column=1, padx=5)
        
#         # Status
#         self.status_label = ttk.Label(self.main_container, text="", 
#                                      font=('Helvetica', 10), foreground='blue')
#         self.status_label.grid(row=5, column=0, columnspan=2, pady=10)
        
#         # Info
#         info_text = ("FaceLock uses facial recognition with anti-spoofing detection\n"
#                     "and Time-based One-Time Passwords (TOTP) for secure authentication.")
#         info_label = ttk.Label(self.main_container, text=info_text, 
#                               font=('Helvetica', 9), foreground='gray')
#         info_label.grid(row=6, column=0, columnspan=2, pady=20)
    
#     def handle_login(self):
#         """Handle login button click"""
#         username = self.username_entry.get().strip()
#         password = self.password_entry.get()
        
#         if not username or not password:
#             messagebox.showerror("Error", "Please enter username and password")
#             return
        
#         self.status_label.config(text="Initializing camera...")
#         self.root.update()
        
#         # Initialize camera
#         self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
#         if not self.video_capture.isOpened():
#             messagebox.showerror("Error", "Cannot access camera")
#             return

#         # Perform authentication in thread
#         self.status_label.config(text="Authenticating...")
#         thread = threading.Thread(target=self._authenticate_thread, 
#                                  args=(username, password))
#         thread.start()
    
#     def _authenticate_thread(self, username, password):
#         """Authentication in separate thread"""
#         result = auth_system.authenticate_user(username, password, self.video_capture)
        
#         self.video_capture.release()
#         cv2.destroyAllWindows()
        
#         # Update GUI in main thread
#         self.root.after(0, self._handle_auth_result, result)
    
#     def _handle_auth_result(self, result):
#         """Handle authentication result"""
#         if result['requires_totp']:
#             self.pending_user_id = result['user_id']
#             self.show_totp_screen(result['message'])
#         elif result['success']:
#             self.show_dashboard()
#         else:
#             self.status_label.config(text=result['message'], foreground='red')
#             messagebox.showerror("Authentication Failed", result['message'])
    
#     def handle_registration(self):
#         """Handle registration button click"""
#         username = self.username_entry.get().strip()
#         password = self.password_entry.get()
        
#         if not username or not password:
#             messagebox.showerror("Error", "Please enter username and password")
#             return
        
#         if len(password) < 8:
#             messagebox.showerror("Error", "Password must be at least 8 characters")
#             return
        
#         # Confirm password
#         confirm_password = simpledialog.askstring("Confirm Password", 
#                                                      "Re-enter password:", 
#                                                      show='*')
#         if password != confirm_password:
#             messagebox.showerror("Error", "Passwords do not match")
#             return
        
#         self.status_label.config(text="Initializing camera...")
#         self.root.update()
        
#         # Initialize camera
#         self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
#         if not self.video_capture.isOpened():
#             messagebox.showerror("Error", "Cannot access camera")
#             return
        
#         # Set camera properties for stability
#         self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#         self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#         self.video_capture.set(cv2.CAP_PROP_FPS, 30)
#         self.video_capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)


#         # Perform registration in thread
#         self.status_label.config(text="Starting registration...")
#         thread = threading.Thread(target=self._register_thread, 
#                                  args=(username, password))
#         thread.start()
    
#     def _register_thread(self, username, password):
#         """Registration in separate thread"""
#         result = auth_system.register_user(username, password, self.video_capture)
        
#         self.video_capture.release()
#         cv2.destroyAllWindows()
        
#         # Update GUI in main thread
#         self.root.after(0, self._handle_register_result, result)
    
#     def _handle_register_result(self, result):
#         """Handle registration result"""
#         if result['success']:
#             self.show_qr_code_screen(result['qr_code'], result['secret'])
#         else:
#             self.status_label.config(text=result['message'], foreground='red')
#             messagebox.showerror("Registration Failed", result['message'])
    
#     # def show_qr_code_screen(self, qr_image, secret):
#     #     """Display QR code for TOTP setup"""
#     #     self.clear_screen()
        
#     #     # Title
#     #     title = ttk.Label(self.main_container, text="Registration Successful!",
#     #                      font=('Helvetica', 20, 'bold'), foreground='green')
#     #     title.grid(row=0, column=0, pady=20)
        
#     #     # Instructions
#     #     instructions = ttk.Label(self.main_container, 
#     #                             text="Scan this QR code with your authenticator app\n"
#     #                                  "(Google Authenticator, Authy, etc.)",
#     #                             font=('Helvetica', 11))
#     #     instructions.grid(row=1, column=0, pady=10)
        
#     #     # QR Code
#     #     qr_photo = ImageTk.PhotoImage(qr_image.resize((300, 300)))
#     #     qr_label = ttk.Label(self.main_container, image=qr_photo)
#     #     qr_label.image = qr_photo  # Keep reference
#     #     qr_label.grid(row=2, column=0, pady=10)
        
#     #     # Secret key
#     #     secret_frame = ttk.LabelFrame(self.main_container, text="Manual Entry Key", 
#     #                                  padding="10")
#     #     secret_frame.grid(row=3, column=0, pady=10, padx=20, sticky=(tk.W, tk.E))
        
#     #     secret_text = scrolledtext.ScrolledText(secret_frame, height=2, width=40, 
#     #                                             font=('Courier', 10))
#     #     secret_text.insert(tk.END, secret)
#     #     secret_text.config(state=tk.DISABLED)
#     #     secret_text.pack()
        
#     #     # Continue button
#     #     continue_btn = ttk.Button(self.main_container, text="Continue to Login",
#     #                              command=self.show_login_screen, width=20)
#     #     continue_btn.grid(row=4, column=0, pady=20)
    
#     def show_totp_screen(self, message):
#         """Display TOTP verification screen"""
#         self.clear_screen()
        
#         # Title
#         title = ttk.Label(self.main_container, text="Two-Factor Authentication",
#                          font=('Helvetica', 20, 'bold'))
#         title.grid(row=0, column=0, pady=20)
        
#         # Message
#         msg_label = ttk.Label(self.main_container, text=message,
#                              font=('Helvetica', 11), foreground='green')
#         msg_label.grid(row=1, column=0, pady=10)
        
#         # Instructions
#         instructions = ttk.Label(self.main_container,
#                                 text="Enter the 6-digit code from your authenticator app:",
#                                 font=('Helvetica', 11))
#         instructions.grid(row=2, column=0, pady=10)
        
#         # OTP Entry
#         self.otp_entry = ttk.Entry(self.main_container, width=15, 
#                                    font=('Helvetica', 18, 'bold'), 
#                                    justify='center')
#         self.otp_entry.grid(row=3, column=0, pady=20)
#         self.otp_entry.focus()
        
#         # Verify button
#         verify_btn = ttk.Button(self.main_container, text="Verify",
#                                command=self.verify_totp_code, width=15)
#         verify_btn.grid(row=4, column=0, pady=10)
        
#         # Cancel button
#         cancel_btn = ttk.Button(self.main_container, text="Cancel",
#                                command=self.show_login_screen, width=15)
#         cancel_btn.grid(row=5, column=0, pady=5)
        
#         # Bind Enter key
#         self.otp_entry.bind('<Return>', lambda e: self.verify_totp_code())
    
#     def verify_totp_code(self):
#         """Verify entered TOTP code"""
#         otp_code = self.otp_entry.get().strip()
        
#         if len(otp_code) != 6 or not otp_code.isdigit():
#             messagebox.showerror("Error", "Please enter a valid 6-digit code")
#             return
        
#         result = auth_system.verify_totp(self.pending_user_id, otp_code)
        
#         if result['success']:
#             messagebox.showinfo("Success", "Authentication successful!")
#             self.show_dashboard()
#         else:
#             messagebox.showerror("Error", result['message'])
#             self.otp_entry.delete(0, tk.END)
    
#     def show_dashboard(self):
#         """Display main dashboard after successful authentication"""
#         self.clear_screen()
        
#         # Title
#         title = ttk.Label(self.main_container, text="Welcome to FaceLock!",
#                          font=('Helvetica', 24, 'bold'), foreground='green')
#         title.grid(row=0, column=0, pady=30)
        
#         # Success message
#         success_msg = ttk.Label(self.main_container,
#                                text="✓ Authentication Successful",
#                                font=('Helvetica', 16), foreground='green')
#         success_msg.grid(row=1, column=0, pady=20)
        
#         # Info
#         info_frame = ttk.LabelFrame(self.main_container, 
#                                    text="Authentication Methods Used", 
#                                    padding="20")
#         info_frame.grid(row=2, column=0, pady=20, padx=40, sticky=(tk.W, tk.E))
        
#         methods = [
#             "✓ Password Authentication",
#             "✓ Facial Recognition",
#             "✓ Anti-Spoofing Detection (Blink, Movement, Texture)",
#             "✓ Time-based One-Time Password (TOTP)"
#         ]
        
#         for i, method in enumerate(methods):
#             ttk.Label(info_frame, text=method, font=('Helvetica', 11)).grid(
#                 row=i, column=0, sticky=tk.W, pady=5
#             )
        
#         # Logout button
#         logout_btn = ttk.Button(self.main_container, text="Logout",
#                                command=self.handle_logout, width=15)
#         logout_btn.grid(row=3, column=0, pady=30)
    
#     def handle_logout(self):
#         """Handle logout"""
#         auth_system.logout()
#         self.pending_user_id = None
#         messagebox.showinfo("Logged Out", "You have been logged out successfully")
#         self.show_login_screen()
    
#     def on_closing(self):
#         """Handle window closing"""
#         if self.video_capture is not None:
#             self.video_capture.release()
#         cv2.destroyAllWindows()
#         self.root.destroy()


#     def show_qr_code_screen(self, qr_image, secret):
#         """Display QR code for TOTP setup"""
#         self.clear_screen()
    
#         # Configure column weight for centering
#         self.main_container.columnconfigure(0, weight=1)
    
#         # Title
#         title = ttk.Label(self.main_container, text="Registration Successful!",
#                      font=('Helvetica', 20, 'bold'), foreground='green')
#         title.grid(row=0, column=0, pady=20)
    
#         # Instructions
#         instructions = ttk.Label(self.main_container, 
#                             text="Scan this QR code with your authenticator app\n"
#                                  "(Google Authenticator, Authy, etc.)",
#                             font=('Helvetica', 11))
#         instructions.grid(row=1, column=0, pady=10)
    
#         # QR Code
#         qr_photo = ImageTk.PhotoImage(qr_image.resize((300, 300)))
#         qr_label = ttk.Label(self.main_container, image=qr_photo)
#         qr_label.image = qr_photo  # Keep reference
#         qr_label.grid(row=2, column=0, pady=10)
    
#         # Secret key
#         secret_frame = ttk.LabelFrame(self.main_container, text="Manual Entry Key", 
#                                  padding="10")
#         secret_frame.grid(row=3, column=0, pady=10, padx=20, sticky=(tk.W, tk.E))
    
#         secret_text = scrolledtext.ScrolledText(secret_frame, height=2, width=40, 
#                                             font=('Courier', 10))
#         secret_text.insert(tk.END, secret)
#         secret_text.config(state=tk.DISABLED)
#         secret_text.pack()
    
#         # Button frame for better layout
#         button_frame = ttk.Frame(self.main_container)
#         button_frame.grid(row=4, column=0, pady=20)
    
#         # Continue to Login button
#         continue_btn = ttk.Button(button_frame, text="Continue to Login",
#                              command=self.show_login_screen, width=20)
#         continue_btn.pack(side=tk.LEFT, padx=5)
    
#         # Done button (logout and return to home)
#         done_btn = ttk.Button(button_frame, text="Done",
#                          command=self.handle_qr_done, width=15)
#         done_btn.pack(side=tk.LEFT, padx=5)

#     def handle_qr_done(self):
#         """Handle Done button on QR code screen"""
#         # Logout if user is authenticated
#         auth_system.logout()
#         self.pending_user_id = None
    
#         # Show confirmation message
#         messagebox.showinfo("Setup Complete", 
#                        "Registration complete! Please login with your credentials.")
    
#         # Return to login screen
#         self.show_login_screen()


# def run_gui():
#     """Run the GUI application"""
#     root = tk.Tk()
#     app = FaceLockGUI(root)
#     root.protocol("WM_DELETE_WINDOW", app.on_closing)
#     root.mainloop()

"""
Tkinter-based GUI for FaceLock authentication system - Enhanced UI
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
    """Main GUI application with enhanced UI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("FaceLock Authentication System")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        # Set background color
        self.root.configure(bg='#f0f0f0')
        
        self.video_capture = None
        self.current_frame = None
        self.pending_user_id = None
        
        # Enhanced Style Configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', 
                       font=('Helvetica', 28, 'bold'),
                       foreground='#2c3e50',
                       background='#f0f0f0')
        
        style.configure('Subtitle.TLabel',
                       font=('Helvetica', 11),
                       foreground='#7f8c8d',
                       background='#f0f0f0')
        
        style.configure('Header.TLabel',
                       font=('Helvetica', 20, 'bold'),
                       foreground='#2c3e50',
                       background='#f0f0f0')
        
        style.configure('Success.TLabel',
                       font=('Helvetica', 20, 'bold'),
                       foreground='#27ae60',
                       background='#f0f0f0')
        
        style.configure('Info.TLabel',
                       font=('Helvetica', 10),
                       foreground='#34495e',
                       background='#f0f0f0')
        
        style.configure('Primary.TButton',
                       font=('Helvetica', 11, 'bold'),
                       padding=10)
        
        style.configure('Secondary.TButton',
                       font=('Helvetica', 10),
                       padding=8)
        
        style.map('Primary.TButton',
                 background=[('active', '#3498db')],
                 foreground=[('active', 'white')])
        
        # Create main container with gradient-like effect
        self.main_container = tk.Frame(root, bg='#f0f0f0', padx=30, pady=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Show login screen
        self.show_login_screen()
    
    def clear_screen(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    def create_card_frame(self, parent):
        """Create a card-like frame with shadow effect"""
        card = tk.Frame(parent, bg='white', relief=tk.RAISED, borderwidth=2)
        return card
    
    def show_login_screen(self):
        """Display enhanced login screen"""
        self.clear_screen()
        
        # Center frame
        center_frame = tk.Frame(self.main_container, bg='#f0f0f0')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Logo/Icon area (you can add an icon here)
        icon_frame = tk.Frame(center_frame, bg='#3498db', width=100, height=100, relief=tk.RAISED, borderwidth=3)
        icon_frame.pack(pady=(0, 20))
        
        icon_label = tk.Label(icon_frame, text="🔐", font=('Arial', 50), bg='#3498db', fg='white')
        icon_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title = ttk.Label(center_frame, text="FaceLock", style='Title.TLabel')
        title.pack(pady=(0, 5))
        
        # Subtitle
        subtitle = ttk.Label(center_frame, 
                            text="Secure Multi-Factor Authentication",
                            style='Subtitle.TLabel')
        subtitle.pack(pady=(0, 30))
        
        # Login card
        login_card = self.create_card_frame(center_frame)
        login_card.pack(pady=10, padx=40, fill=tk.BOTH)
        
        # Card content
        card_content = tk.Frame(login_card, bg='white', padx=40, pady=30)
        card_content.pack(fill=tk.BOTH, expand=True)
        
        # Username
        username_label = tk.Label(card_content, text="Username", 
                                  font=('Helvetica', 11, 'bold'),
                                  bg='white', fg='#2c3e50')
        username_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.username_entry = tk.Entry(card_content, width=35, 
                                       font=('Helvetica', 12),
                                       relief=tk.SOLID, borderwidth=1)
        self.username_entry.pack(pady=(0, 20), ipady=8)
        
        # Password
        password_label = tk.Label(card_content, text="Password", 
                                 font=('Helvetica', 11, 'bold'),
                                 bg='white', fg='#2c3e50')
        password_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.password_entry = tk.Entry(card_content, width=35, show="●",
                                       font=('Helvetica', 12),
                                       relief=tk.SOLID, borderwidth=1)
        self.password_entry.pack(pady=(0, 25), ipady=8)
        
        # Buttons
        button_frame = tk.Frame(card_content, bg='white')
        button_frame.pack(pady=(10, 0))
        
        login_btn = tk.Button(button_frame, text="Login", 
                             command=self.handle_login,
                             font=('Helvetica', 11, 'bold'),
                             bg='#3498db', fg='white',
                             width=15, height=2,
                             relief=tk.FLAT,
                             cursor='hand2',
                             activebackground='#2980b9',
                             activeforeground='white')
        login_btn.grid(row=0, column=0, padx=5)
        
        register_btn = tk.Button(button_frame, text="Register", 
                                command=self.handle_registration,
                                font=('Helvetica', 11, 'bold'),
                                bg='#2ecc71', fg='white',
                                width=15, height=2,
                                relief=tk.FLAT,
                                cursor='hand2',
                                activebackground='#27ae60',
                                activeforeground='white')
        register_btn.grid(row=0, column=1, padx=5)
        
        # Status
        self.status_label = tk.Label(center_frame, text="", 
                                     font=('Helvetica', 10),
                                     bg='#f0f0f0', fg='#e74c3c')
        self.status_label.pack(pady=15)
        
        # Info box
        info_frame = self.create_card_frame(center_frame)
        info_frame.pack(pady=(20, 0), fill=tk.X)
        
        info_content = tk.Frame(info_frame, bg='white', padx=20, pady=15)
        info_content.pack(fill=tk.BOTH)
        
        info_icon = tk.Label(info_content, text="ℹ️", font=('Arial', 16), bg='white')
        info_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        info_text = ("Multi-layer security: Facial Recognition + Anti-Spoofing + 2FA")
        info_label = tk.Label(info_content, text=info_text, 
                             font=('Helvetica', 9), bg='white', fg='#7f8c8d',
                             wraplength=450)
        info_label.pack(side=tk.LEFT)
    
    def show_qr_code_screen(self, qr_image, secret):
        """Display enhanced QR code screen"""
        self.clear_screen()
        
        # Center frame
        center_frame = tk.Frame(self.main_container, bg='#f0f0f0')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Success icon
        success_icon = tk.Label(center_frame, text="✓", 
                               font=('Arial', 60, 'bold'),
                               bg='#f0f0f0', fg='#27ae60')
        success_icon.pack(pady=(0, 10))
        
        # Title
        title = ttk.Label(center_frame, text="Registration Successful!",
                         style='Success.TLabel')
        title.pack(pady=(0, 10))
        
        # Instructions card
        instruction_card = self.create_card_frame(center_frame)
        instruction_card.pack(pady=15, fill=tk.X)
        
        instruction_content = tk.Frame(instruction_card, bg='white', padx=30, pady=20)
        instruction_content.pack(fill=tk.BOTH)
        
        instructions = tk.Label(instruction_content,
                               text="Scan this QR code with your authenticator app\n"
                                    "(Google Authenticator, Authy, Microsoft Authenticator, etc.)",
                               font=('Helvetica', 11),
                               bg='white', fg='#34495e')
        instructions.pack()
        
        # QR Code card
        qr_card = self.create_card_frame(center_frame)
        qr_card.pack(pady=15)
        
        qr_content = tk.Frame(qr_card, bg='white', padx=30, pady=30)
        qr_content.pack()
        
        qr_photo = ImageTk.PhotoImage(qr_image.resize((280, 280)))
        qr_label = tk.Label(qr_content, image=qr_photo, bg='white')
        qr_label.image = qr_photo
        qr_label.pack()
        
        # Secret key card
        secret_card = self.create_card_frame(center_frame)
        secret_card.pack(pady=15, fill=tk.X)
        
        secret_content = tk.Frame(secret_card, bg='white', padx=25, pady=20)
        secret_content.pack(fill=tk.BOTH)
        
        secret_label = tk.Label(secret_content, text="Manual Entry Key:",
                               font=('Helvetica', 10, 'bold'),
                               bg='white', fg='#2c3e50')
        secret_label.pack(anchor=tk.W, pady=(0, 8))
        
        secret_display = tk.Text(secret_content, height=2, width=45,
                                font=('Courier', 10),
                                bg='#ecf0f1', relief=tk.FLAT,
                                wrap=tk.WORD)
        secret_display.insert('1.0', secret)
        secret_display.config(state=tk.DISABLED)
        secret_display.pack()
        
        # Buttons
        button_frame = tk.Frame(center_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        home_btn = tk.Button(button_frame, text="🏠 Back to Home",
                            command=self.show_login_screen,
                            font=('Helvetica', 11, 'bold'),
                            bg='#95a5a6', fg='white',
                            width=18, height=2,
                            relief=tk.FLAT,
                            cursor='hand2',
                            activebackground='#7f8c8d',
                            activeforeground='white')
        home_btn.grid(row=0, column=0, padx=5)
        
        done_btn = tk.Button(button_frame, text="Done ✓",
                            command=self.handle_qr_done,
                            font=('Helvetica', 11, 'bold'),
                            bg='#3498db', fg='white',
                            width=18, height=2,
                            relief=tk.FLAT,
                            cursor='hand2',
                            activebackground='#2980b9',
                            activeforeground='white')
        done_btn.grid(row=0, column=1, padx=5)
    
    def handle_qr_done(self):
        """Handle Done button on QR code screen"""
        auth_system.logout()
        self.pending_user_id = None
        messagebox.showinfo("Setup Complete", 
                           "Registration complete! Please login with your credentials.")
        self.show_login_screen()
    
    # Keep all other methods (handle_login, handle_registration, etc.) the same
    # Just add these enhanced UI methods
    
    def show_totp_screen(self, message):
        """Display enhanced TOTP verification screen"""
        self.clear_screen()
        
        # Center frame
        center_frame = tk.Frame(self.main_container, bg='#f0f0f0')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Icon
        icon_label = tk.Label(center_frame, text="🔑", 
                             font=('Arial', 50),
                             bg='#f0f0f0')
        icon_label.pack(pady=(0, 15))
        
        # Title
        title = ttk.Label(center_frame, text="Two-Factor Authentication",
                         style='Header.TLabel')
        title.pack(pady=(0, 10))
        
        # Success message
        msg_card = self.create_card_frame(center_frame)
        msg_card.pack(pady=10, fill=tk.X)
        
        msg_content = tk.Frame(msg_card, bg='white', padx=30, pady=15)
        msg_content.pack()
        
        msg_label = tk.Label(msg_content, text=message,
                            font=('Helvetica', 11),
                            bg='white', fg='#27ae60')
        msg_label.pack()
        
        # Instructions
        instructions = tk.Label(center_frame,
                               text="Enter the 6-digit code from your authenticator app:",
                               font=('Helvetica', 11),
                               bg='#f0f0f0', fg='#34495e')
        instructions.pack(pady=(20, 10))
        
        # OTP Entry card
        otp_card = self.create_card_frame(center_frame)
        otp_card.pack(pady=10)
        
        otp_content = tk.Frame(otp_card, bg='white', padx=50, pady=30)
        otp_content.pack()
        
        self.otp_entry = tk.Entry(otp_content, width=12,
                                  font=('Courier', 28, 'bold'),
                                  justify='center',
                                  relief=tk.SOLID, borderwidth=2)
        self.otp_entry.pack(ipady=10)
        self.otp_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(center_frame, bg='#f0f0f0')
        button_frame.pack(pady=25)
        
        verify_btn = tk.Button(button_frame, text="Verify",
                              command=self.verify_totp_code,
                              font=('Helvetica', 11, 'bold'),
                              bg='#2ecc71', fg='white',
                              width=15, height=2,
                              relief=tk.FLAT,
                              cursor='hand2',
                              activebackground='#27ae60',
                              activeforeground='white')
        verify_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel",
                              command=self.show_login_screen,
                              font=('Helvetica', 11),
                              bg='#95a5a6', fg='white',
                              width=15, height=2,
                              relief=tk.FLAT,
                              cursor='hand2',
                              activebackground='#7f8c8d',
                              activeforeground='white')
        cancel_btn.grid(row=0, column=1, padx=5)
        
        # Bind Enter key
        self.otp_entry.bind('<Return>', lambda e: self.verify_totp_code())
    
    def show_dashboard(self):
        """Display enhanced dashboard"""
        self.clear_screen()
        
        # Center frame
        center_frame = tk.Frame(self.main_container, bg='#f0f0f0')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Success animation/icon
        success_icon = tk.Label(center_frame, text="🎉", 
                               font=('Arial', 60),
                               bg='#f0f0f0')
        success_icon.pack(pady=(0, 15))
        
        # Title
        title = ttk.Label(center_frame, text="Welcome to FaceLock!",
                         style='Success.TLabel')
        title.pack(pady=(0, 10))
        
        # Success message
        success_msg = tk.Label(center_frame,
                              text="✓ Authentication Successful",
                              font=('Helvetica', 16, 'bold'),
                              fg='#27ae60', bg='#f0f0f0')
        success_msg.pack(pady=(0, 25))
        
        # Info card
        info_card = self.create_card_frame(center_frame)
        info_card.pack(pady=15, fill=tk.BOTH)
        
        info_content = tk.Frame(info_card, bg='white', padx=40, pady=30)
        info_content.pack(fill=tk.BOTH)
        
        info_title = tk.Label(info_content, 
                             text="Authentication Methods Verified",
                             font=('Helvetica', 13, 'bold'),
                             bg='white', fg='#2c3e50')
        info_title.pack(pady=(0, 20))
        
        methods = [
            ("✓", "Password Authentication", "#27ae60"),
            ("✓", "Facial Recognition", "#27ae60"),
            ("✓", "Anti-Spoofing Detection", "#27ae60"),
            ("✓", "Time-based OTP (2FA)", "#27ae60")
        ]
        
        for icon, method, color in methods:
            method_frame = tk.Frame(info_content, bg='white')
            method_frame.pack(fill=tk.X, pady=5)
            
            icon_label = tk.Label(method_frame, text=icon,
                                 font=('Arial', 16, 'bold'),
                                 bg='white', fg=color)
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
            
            method_label = tk.Label(method_frame, text=method,
                                   font=('Helvetica', 11),
                                   bg='white', fg='#34495e')
            method_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Logout button
        logout_btn = tk.Button(center_frame, text="🚪 Logout",
                              command=self.handle_logout,
                              font=('Helvetica', 11, 'bold'),
                              bg='#e74c3c', fg='white',
                              width=20, height=2,
                              relief=tk.FLAT,
                              cursor='hand2',
                              activebackground='#c0392b',
                              activeforeground='white')
        logout_btn.pack(pady=30)
    
    # Keep all the existing handler methods
    def handle_login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        self.status_label.config(text="Initializing camera...", fg='#3498db')
        self.root.update()
        
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return

        self.status_label.config(text="Authenticating...", fg='#3498db')
        thread = threading.Thread(target=self._authenticate_thread, 
                                 args=(username, password))
        thread.start()
    
    def _authenticate_thread(self, username, password):
        """Authentication in separate thread"""
        result = auth_system.authenticate_user(username, password, self.video_capture)
        
        self.video_capture.release()
        cv2.destroyAllWindows()
        
        self.root.after(0, self._handle_auth_result, result)
    
    def _handle_auth_result(self, result):
        """Handle authentication result"""
        if result['requires_totp']:
            self.pending_user_id = result['user_id']
            self.show_totp_screen(result['message'])
        elif result['success']:
            self.show_dashboard()
        else:
            self.status_label.config(text=result['message'], fg='#e74c3c')
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
        
        confirm_password = simpledialog.askstring("Confirm Password", 
                                                  "Re-enter password:", 
                                                  show='*')
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        self.status_label.config(text="Initializing camera...", fg='#3498db')
        self.root.update()
        
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return
        
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video_capture.set(cv2.CAP_PROP_FPS, 30)
        self.video_capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)

        self.status_label.config(text="Starting registration...", fg='#3498db')
        thread = threading.Thread(target=self._register_thread, 
                                 args=(username, password))
        thread.start()
    
    def _register_thread(self, username, password):
        """Registration in separate thread"""
        result = auth_system.register_user(username, password, self.video_capture)
        
        self.video_capture.release()
        cv2.destroyAllWindows()
        
        self.root.after(0, self._handle_register_result, result)
    
    def _handle_register_result(self, result):
        """Handle registration result"""
        if result['success']:
            self.show_qr_code_screen(result['qr_code'], result['secret'])
        else:
            self.status_label.config(text=result['message'], fg='#e74c3c')
            messagebox.showerror("Registration Failed", result['message'])
    
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