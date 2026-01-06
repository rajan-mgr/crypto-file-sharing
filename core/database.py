import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    def __init__(self, host=None, dbname=None, user=None, password=None):
        # Prioritize .env variables, fallback to arguments or hardcoded defaults
        self.conn_params = {
            "host": os.getenv("DB_HOST", host ),
            "database": os.getenv("DB_NAME", dbname),
            "user": os.getenv("DB_USER", user),
            "password": os.getenv("DB_PASS", password),
            "port": os.getenv("DB_PORT")
        }

    def get_conn(self):
        """Creates a fresh connection to the PostgreSQL database."""
        return psycopg2.connect(**self.conn_params)

    # --- User Methods ---
    def save_user(self, username, pwd_hash, salt, priv_key_enc, pub_key_pem):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, salt, private_key_enc, public_key_pem)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, pwd_hash, salt, priv_key_enc, pub_key_pem))
            conn.commit()

    def get_user(self, username):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                return cur.fetchone()

    def get_all_usernames(self):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users")
                return [row[0] for row in cur.fetchall()]

    # --- File Methods ---
    def save_file(self, file_id, filename, owner, file_data, signature, file_hash, permissions):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                # 1. Save main encrypted file data
                cur.execute("""
                    INSERT INTO shared_files (file_id, filename, owner, file_data, signature, file_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (file_id, filename, owner, file_data, signature, file_hash))
                
                # 2. Save recipient permissions (RSA-encrypted symmetric keys)
                for recipient, enc_sym_key in permissions.items():
                    cur.execute("""
                        INSERT INTO file_permissions (file_id, recipient, encrypted_sym_key)
                        VALUES (%s, %s, %s)
                    """, (file_id, recipient, enc_sym_key))
            conn.commit()

    def get_user_files(self, username):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Retrieve files where user is the owner OR has been granted permission
                cur.execute("""
                    SELECT f.file_id, f.filename, f.owner, f.signature, f.file_hash, f.timestamp
                    FROM shared_files f
                    LEFT JOIN file_permissions p ON f.file_id = p.file_id
                    WHERE f.owner = %s OR p.recipient = %s
                    GROUP BY f.file_id, f.filename, f.owner, f.signature, f.file_hash, f.timestamp
                    ORDER BY f.timestamp DESC
                """, (username, username))
                return cur.fetchall()

    def get_file_for_download(self, file_id, username):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT f.*, p.encrypted_sym_key 
                    FROM shared_files f
                    JOIN file_permissions p ON f.file_id = p.file_id
                    WHERE f.file_id = %s AND (f.owner = %s OR p.recipient = %s)
                """, (file_id, username, username))
                return cur.fetchone()

    # --- Management & Deletion ---

    def delete_file(self, file_id, owner):
        """Permanently removes file and all associated access rights."""
        try:
            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    # Clear permissions first (Foreign Key constraint)
                    cur.execute("DELETE FROM file_permissions WHERE file_id = %s", (file_id,))
                    # Delete the file itself only if the requestor is the owner
                    cur.execute("DELETE FROM shared_files WHERE file_id = %s AND owner = %s", (file_id, owner))
                conn.commit()
                return True
        except Exception as e:
            print(f"DB Delete Error: {e}")
            return False

    def revoke_all_except_owner(self, file_id, owner):
        """Locks the file so only the owner can access it."""
        try:
            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM file_permissions 
                        WHERE file_id = %s AND recipient != %s
                    """, (file_id, owner))
                conn.commit()
                return True
        except Exception as e:
            print(f"DB Revoke Error: {e}")
            return False

    def delete_permission(self, file_id, recipient):
        """Specific removal of one user's access."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM file_permissions 
                    WHERE file_id = %s AND recipient = %s
                """, (file_id, recipient))
            conn.commit()