"""
Database operations for FaceLock system
Handles user registration, authentication, and secure data storage
"""
import sqlite3
import json
import pickle
from datetime import datetime
from typing import Optional, List, Tuple
from config.settings import DATABASE_PATH
from src.encryption import encryption_manager


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            ''')
            
            # Face embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    embedding_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # TOTP secrets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS totp_secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    encrypted_secret BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Login history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    method TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def create_user(self, username: str, password: str) -> Optional[int]:
        """Create a new user account"""
        try:
            password_hash = encryption_manager.hash_password(password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (username, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def verify_user_password(self, username: str, password: str) -> Optional[int]:
        """Verify user credentials and return user ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, password_hash FROM users WHERE username = ?',
                (username,)
            )
            result = cursor.fetchone()
            
            if result and encryption_manager.verify_password(result[1], password):
                return result[0]
            return None
    
    def store_face_embeddings(self, user_id: int, embeddings: List) -> bool:
        """Store encrypted facial embeddings for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for embedding in embeddings:
                    # Serialize and encrypt embedding
                    serialized = pickle.dumps(embedding)
                    encrypted = encryption_manager.encrypt(serialized)
                    
                    cursor.execute(
                        'INSERT INTO face_embeddings (user_id, embedding_data) VALUES (?, ?)',
                        (user_id, encrypted)
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing face embeddings: {e}")
            return False
    
    def get_face_embeddings(self, user_id: int) -> List:
        """Retrieve and decrypt facial embeddings for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT embedding_data FROM face_embeddings WHERE user_id = ?',
                (user_id,)
            )
            results = cursor.fetchall()
            
            embeddings = []
            for row in results:
                try:
                    decrypted = encryption_manager.decrypt(row[0])
                    embedding = pickle.loads(decrypted)
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Error decrypting embedding: {e}")
            
            return embeddings
    
    def store_totp_secret(self, user_id: int, secret: str) -> bool:
        """Store encrypted TOTP secret for a user"""
        try:
            encrypted_secret = encryption_manager.encrypt(secret.encode())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO totp_secrets (user_id, encrypted_secret) VALUES (?, ?)',
                    (user_id, encrypted_secret)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing TOTP secret: {e}")
            return False
    
    def get_totp_secret(self, user_id: int) -> Optional[str]:
        """Retrieve and decrypt TOTP secret for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT encrypted_secret FROM totp_secrets WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                try:
                    decrypted = encryption_manager.decrypt(result[0])
                    return decrypted.decode()
                except Exception as e:
                    print(f"Error decrypting TOTP secret: {e}")
            
            return None
    
    def log_login_attempt(self, user_id: int, success: bool, method: str = "face+totp"):
        """Log a login attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO login_history (user_id, success, method) VALUES (?, ?, ?)',
                (user_id, success, method)
            )
            
            if success:
                cursor.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP, failed_attempts = 0 WHERE id = ?',
                    (user_id,)
                )
            else:
                cursor.execute(
                    'UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = ?',
                    (user_id,)
                )
            
            conn.commit()
    
    def get_user_by_username(self, username: str) -> Optional[Tuple]:
        """Get user information by username"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username, failed_attempts, locked_until FROM users WHERE username = ?',
                (username,)
            )
            return cursor.fetchone()
    
    def check_account_locked(self, user_id: int) -> bool:
        """Check if account is locked due to failed attempts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT locked_until FROM users WHERE id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result and result[0]:
                locked_until = datetime.fromisoformat(result[0])
                if datetime.now() < locked_until:
                    return True
                else:
                    # Unlock account
                    cursor.execute(
                        'UPDATE users SET locked_until = NULL, failed_attempts = 0 WHERE id = ?',
                        (user_id,)
                    )
                    conn.commit()
            
            return False
    
    def lock_account(self, user_id: int, duration_seconds: int):
        """Lock account for specified duration"""
        from datetime import timedelta
        lock_until = datetime.now() + timedelta(seconds=duration_seconds)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET locked_until = ? WHERE id = ?',
                (lock_until.isoformat(), user_id)
            )
            conn.commit()


# Singleton instance
db_manager = DatabaseManager()