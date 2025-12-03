"""
FaceLock - Facial Recognition and TOTP Authentication System
Main entry point for the application
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from ui.gui import run_gui
from ui.gui_pyside6 import run_gui

def main():
    """Main application entry point"""
    print("=" * 60)
    print("FaceLock Authentication System")
    print("Facial Recognition + Anti-Spoofing + TOTP 2FA")
    print("=" * 60)
    print()
    print("Starting application...")
    print()
    print("Features:")
    print("  - Facial recognition using deep learning")
    print("  - Multi-layer anti-spoofing detection")
    print("  - TOTP-based two-factor authentication")
    print("  - Encrypted local data storage")
    print()
    print("=" * 60)
    
    try:
        run_gui()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()