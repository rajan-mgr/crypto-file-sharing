import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import base64
import hashlib
import datetime
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import hashlib

# ============ DATACLASSES ============

@dataclass
class Certificate:
    """Digital certificate structure"""
    version: str = "1.0"
    serial: str = ""
    subject: str = ""
    issuer: str = "SecureShare CA"
    valid_from: str = ""
    valid_to: str = ""
    public_key: str = ""
    signature: str = ""

@dataclass
class User:
    """User account"""
    username: str
    password_hash: str
    private_key: str = ""  # Encrypted
    certificate: Certificate = None
    shared_files: list = None
    
    def __post_init__(self):
        if self.shared_files is None:
            self.shared_files = []

@dataclass
class SharedFile:
    """Shared file metadata"""
    file_id: str
    filename: str
    owner: str
    encrypted_key: str  # File key encrypted with recipient's public key
    file_hash: str
    timestamp: str
    recipients: list

# ============ SECURE SHARE SYSTEM ============

class SecureShareSystem:
    """Core system for secure file sharing"""
    
    def __init__(self, data_dir="data"):
        self.users = {}
        self.shared_files = {}
        self.ca_private_key = None
        self.ca_certificate = None
        self.revoked_certs = set()
        self.data_dir = Path(data_dir)
        self.current_user = None
        
        # Create data directory
        self.data_dir.mkdir(exist_ok=True)
        
        # Setup CA
        self._setup_ca()
        
        # Load existing data
        self._load_data()
    
    # ============ USER MANAGEMENT ============
    
    def register_user(self, username: str, password: str) -> bool:
        """Register a new user"""
        if username in self.users:
            return False
        
        # Generate key pair
        private_key, public_key = self._generate_key_pair()
        
        # Encrypt private key with password
        encrypted_private_key = self._encrypt_with_password(
            private_key, password
        )
        
        # Create user
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            private_key=encrypted_private_key
        )
        
        # Issue certificate
        user.certificate = self._issue_certificate(username, public_key)
        
        # Save user
        self.users[username] = user
        self._save_data()
        
        return True
    
    def login_user(self, username: str, password: str) -> bool:
        """Authenticate user"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Check password
        if not self._verify_password(password, user.password_hash):
            return False
        
        # Decrypt private key (this verifies password is correct)
        try:
            private_key = self._decrypt_with_password(
                user.private_key, password
            )
            self.current_user = username
            return True
        except:
            return False
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
    
    def get_current_user(self):
        """Get current user info"""
        if self.current_user:
            return self.users[self.current_user]
        return None
    
    # ============ FILE OPERATIONS ============
    
    def share_file(self, filepath: str, recipients: list) -> bool:
        """Share a file with encryption"""
        if not self.current_user:
            return False
        
        try:
            # Generate random encryption key for the file
            file_key = Fernet.generate_key()
            cipher = Fernet(file_key)
            
            # Read and encrypt file
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = cipher.encrypt(file_data)
            
            # Create file hash for integrity
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Create file ID
            file_id = f"file_{datetime.datetime.now().timestamp()}_{hashlib.md5(file_data).hexdigest()[:8]}"
            
            # Save encrypted file
            encrypted_filename = f"{file_id}.encrypted"
            encrypted_path = self.data_dir / "files" / encrypted_filename
            encrypted_path.parent.mkdir(exist_ok=True)
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Encrypt file key for each recipient
            shared_file = SharedFile(
                file_id=file_id,
                filename=Path(filepath).name,
                owner=self.current_user,
                encrypted_key=base64.b64encode(file_key).decode(),  # For owner
                file_hash=file_hash,
                timestamp=datetime.datetime.now().isoformat(),
                recipients=recipients
            )
            
            # Store metadata
            self.shared_files[file_id] = shared_file
            
            # Add to user's shared files
            self.users[self.current_user].shared_files.append(file_id)
            
            self._save_data()
            return True
            
        except Exception as e:
            print(f"Error sharing file: {e}")
            return False
    
    def get_shared_files(self):
        """Get files shared with current user"""
        if not self.current_user:
            return []
        
        user_files = []
        for file_id, shared_file in self.shared_files.items():
            if (shared_file.owner == self.current_user or 
                self.current_user in shared_file.recipients):
                user_files.append(shared_file)
        
        return user_files
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """Download and decrypt a shared file"""
        if not self.current_user:
            return False
        
        if file_id not in self.shared_files:
            return False
        
        shared_file = self.shared_files[file_id]
        
        # Check if user has access
        if (shared_file.owner != self.current_user and 
            self.current_user not in shared_file.recipients):
            return False
        
        try:
            # Load encrypted file
            encrypted_path = self.data_dir / "files" / f"{file_id}.encrypted"
            
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Get file key
            file_key = base64.b64decode(shared_file.encrypted_key)
            cipher = Fernet(file_key)
            
            # Decrypt file
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Verify integrity
            if hashlib.sha256(decrypted_data).hexdigest() != shared_file.file_hash:
                messagebox.showerror("Error", "File integrity check failed!")
                return False
            
            # Save decrypted file
            with open(save_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    def revoke_file_access(self, file_id: str, username: str) -> bool:
        """Revoke user's access to a file"""
        if not self.current_user:
            return False
        
        if file_id not in self.shared_files:
            return False
        
        shared_file = self.shared_files[file_id]
        
        # Only owner can revoke access
        if shared_file.owner != self.current_user:
            return False
        
        if username in shared_file.recipients:
            shared_file.recipients.remove(username)
            self._save_data()
            return True
        
        return False
    
    # ============ USER LIST ============
    
    def get_all_users(self):
        """Get list of all registered users"""
        return list(self.users.keys())
    
    # ============ HELPER METHODS ============
    
    def _setup_ca(self):
        """Setup Certificate Authority"""
        self.ca_private_key = "CA_PRIVATE_KEY_" + os.urandom(16).hex()
        
        # Create CA certificate
        now = datetime.datetime.now()
        self.ca_certificate = Certificate(
            serial="CA_ROOT_001",
            subject="SecureShare Root CA",
            issuer="Self-Signed",
            valid_from=now.isoformat(),
            valid_to=(now + datetime.timedelta(days=3650)).isoformat(),
            public_key=self.ca_private_key.replace("PRIVATE", "PUBLIC"),
            signature=self._sign_data("CA_CERT", self.ca_private_key)
        )
    
    def _generate_key_pair(self):
        """Generate simulated key pair"""
        private_key = f"PRIV_{os.urandom(32).hex()}"
        public_key = f"PUB_{private_key[5:]}"
        return private_key, public_key
    
    def _issue_certificate(self, username, public_key):
        """Issue a digital certificate"""
        now = datetime.datetime.now()
        serial = f"CERT_{now.strftime('%Y%m%d')}_{len(self.users)+1:04d}"
        
        cert = Certificate(
            serial=serial,
            subject=username,
            valid_from=now.isoformat(),
            valid_to=(now + datetime.timedelta(days=365)).isoformat(),
            public_key=public_key
        )
        
        # Sign certificate
        cert_data = f"{serial}{username}{public_key}"
        cert.signature = self._sign_data(cert_data, self.ca_private_key)
        
        return cert
    
    def _hash_password(self, password):
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password, stored_hash):
        """Verify password"""
        return self._hash_password(password) == stored_hash
    
    def _encrypt_with_password(self, data, password):
        """Encrypt data with password"""
        # Simple XOR for demo (use proper encryption in production)
        key = self._hash_password(password)[:32]
        encoded = ''.join(chr(ord(c) ^ ord(k)) 
                         for c, k in zip(data, key * (len(data)//len(key) + 1)))
        return base64.b64encode(encoded.encode()).decode()
    
    def _decrypt_with_password(self, encrypted, password):
        """Decrypt data with password"""
        key = self._hash_password(password)[:32]
        decoded = base64.b64decode(encrypted).decode()
        data = ''.join(chr(ord(c) ^ ord(k)) 
                      for c, k in zip(decoded, key * (len(decoded)//len(key) + 1)))
        return data
    
    def _sign_data(self, data, private_key):
        """Create digital signature"""
        return f"SIG_{hashlib.sha256((data + private_key).encode()).hexdigest()}"
    
    def _save_data(self):
        """Save all data to files"""
        # Save users
        users_data = {}
        for username, user in self.users.items():
            users_data[username] = {
                "username": user.username,
                "password_hash": user.password_hash,
                "private_key": user.private_key,
                "certificate": asdict(user.certificate) if user.certificate else None,
                "shared_files": user.shared_files
            }
        
        with open(self.data_dir / "users.json", "w") as f:
            json.dump(users_data, f, indent=2)
        
        # Save shared files
        files_data = {}
        for file_id, shared_file in self.shared_files.items():
            files_data[file_id] = asdict(shared_file)
        
        with open(self.data_dir / "shared_files.json", "w") as f:
            json.dump(files_data, f, indent=2)
    
    def _load_data(self):
        """Load data from files"""
        # Load users
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            with open(users_file, "r") as f:
                users_data = json.load(f)
            
            for username, data in users_data.items():
                cert_data = data.get("certificate")
                certificate = Certificate(**cert_data) if cert_data else None
                
                user = User(
                    username=data["username"],
                    password_hash=data["password_hash"],
                    private_key=data["private_key"],
                    certificate=certificate,
                    shared_files=data.get("shared_files", [])
                )
                self.users[username] = user
        
        # Load shared files
        files_file = self.data_dir / "shared_files.json"
        if files_file.exists():
            with open(files_file, "r") as f:
                files_data = json.load(f)
            
            for file_id, data in files_data.items():
                shared_file = SharedFile(**data)
                self.shared_files[file_id] = shared_file

# ============ GUI APPLICATION ============

class SecureShareApp:
    """Main GUI application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SecureShare - Secure File Sharing")
        self.root.geometry("900x700")
        
        # Initialize system
        self.system = SecureShareSystem()
        
        # Set style
        self.setup_styles()
        
        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show login screen initially
        self.show_login_screen()
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
    def clear_screen(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    # ============ LOGIN/REGISTER SCREENS ============
    
    def show_login_screen(self):
        """Show login screen"""
        self.clear_screen()
        
        # Title
        title = ttk.Label(self.main_container, text="🔐 SecureShare", 
                         style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        subtitle = ttk.Label(self.main_container, 
                           text="Secure File Sharing with PKI")
        subtitle.pack(pady=(0, 30))
        
        # Login frame
        login_frame = ttk.LabelFrame(self.main_container, text="Login", 
                                    padding=20)
        login_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Username
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, 
                                                     sticky=tk.W, pady=5)
        self.login_username = ttk.Entry(login_frame, width=30)
        self.login_username.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Password
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, 
                                                     sticky=tk.W, pady=5)
        self.login_password = ttk.Entry(login_frame, width=30, show="*")
        self.login_password.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Login button
        login_btn = ttk.Button(login_frame, text="Login", 
                              command=self.do_login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=(15, 5))
        
        # Separator
        separator = ttk.Separator(self.main_container, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)
        
        # Register frame
        register_frame = ttk.LabelFrame(self.main_container, text="Register", 
                                       padding=20)
        register_frame.pack(fill=tk.X)
        
        # Register username
        ttk.Label(register_frame, text="Username:").grid(row=0, column=0, 
                                                        sticky=tk.W, pady=5)
        self.register_username = ttk.Entry(register_frame, width=30)
        self.register_username.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Register password
        ttk.Label(register_frame, text="Password:").grid(row=1, column=0, 
                                                        sticky=tk.W, pady=5)
        self.register_password = ttk.Entry(register_frame, width=30, show="*")
        self.register_password.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Confirm password
        ttk.Label(register_frame, text="Confirm Password:").grid(row=2, column=0, 
                                                               sticky=tk.W, pady=5)
        self.register_confirm = ttk.Entry(register_frame, width=30, show="*")
        self.register_confirm.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Register button
        register_btn = ttk.Button(register_frame, text="Register", 
                                 command=self.do_register)
        register_btn.grid(row=3, column=0, columnspan=2, pady=(15, 5))
    
    def do_login(self):
        """Handle login"""
        username = self.login_username.get()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        if self.system.login_user(username, password):
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def do_register(self):
        """Handle registration"""
        username = self.register_username.get()
        password = self.register_password.get()
        confirm = self.register_confirm.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        if self.system.register_user(username, password):
            messagebox.showinfo("Success", 
                              f"User '{username}' registered successfully!\n"
                              f"Please login with your credentials.")
            self.login_username.delete(0, tk.END)
            self.login_password.delete(0, tk.END)
            self.login_username.insert(0, username)
        else:
            messagebox.showerror("Error", "Username already exists")
    
    # ============ MAIN DASHBOARD ============
    
    def show_main_dashboard(self):
        """Show main dashboard after login"""
        self.clear_screen()
        
        # Header
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        user = self.system.get_current_user()
        welcome_text = f"Welcome, {user.username}!"
        
        ttk.Label(header_frame, text=welcome_text, 
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        # Logout button
        logout_btn = ttk.Button(header_frame, text="Logout", 
                               command=self.logout)
        logout_btn.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_share_tab()
        self.create_files_tab()
        self.create_users_tab()
        self.create_certificate_tab()
    
    def create_share_tab(self):
        """Create tab for sharing files"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📤 Share File")
        
        # File selection
        file_frame = ttk.LabelFrame(tab, text="Select File", padding=15)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.share_file_path = tk.StringVar()
        
        ttk.Entry(file_frame, textvariable=self.share_file_path, 
                 width=50).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(file_frame, text="Browse...", 
                  command=self.browse_share_file).pack(side=tk.LEFT)
        
        # Recipients selection
        recipients_frame = ttk.LabelFrame(tab, text="Select Recipients", 
                                        padding=15)
        recipients_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Get all users except current
        all_users = self.system.get_all_users()
        current_user = self.system.current_user
        other_users = [u for u in all_users if u != current_user]
        
        self.recipient_vars = {}
        
        if other_users:
            for i, user in enumerate(other_users):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(recipients_frame, text=user, 
                                     variable=var)
                chk.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
                self.recipient_vars[user] = var
        else:
            ttk.Label(recipients_frame, text="No other users registered", 
                     foreground="gray").pack()
        
        # Share button
        share_btn = ttk.Button(tab, text="🔒 Encrypt & Share File", 
                              command=self.share_file, style='Accent.TButton')
        share_btn.pack(pady=20)
    
    def create_files_tab(self):
        """Create tab for viewing shared files"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📁 My Files")
        
        # Refresh button
        refresh_frame = ttk.Frame(tab)
        refresh_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Button(refresh_frame, text="🔄 Refresh", 
                  command=self.refresh_files).pack(side=tk.RIGHT)
        
        # Files list
        files_frame = ttk.LabelFrame(tab, text="Shared Files", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for files
        columns = ("ID", "Filename", "Owner", "Recipients", "Date")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, 
                                      show="headings", height=10)
        
        # Define headings
        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=100)
        
        # Adjust column widths
        self.files_tree.column("Filename", width=150)
        self.files_tree.column("Recipients", width=150)
        self.files_tree.column("Date", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, 
                                 command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="⬇️ Download Selected", 
                  command=self.download_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Revoke Access", 
                  command=self.revoke_access).pack(side=tk.LEFT, padx=5)
        
        # Load files
        self.refresh_files()
    
    def create_users_tab(self):
        """Create tab for viewing users"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="👥 Users")
        
        # Users list
        users_frame = ttk.LabelFrame(tab, text="Registered Users", padding=10)
        users_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text widget for display
        self.users_text = scrolledtext.ScrolledText(users_frame, height=15)
        self.users_text.pack(fill=tk.BOTH, expand=True)
        
        # Load users
        self.refresh_users()
    
    def create_certificate_tab(self):
        """Create tab for certificate info"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📜 Certificate")
        
        user = self.system.get_current_user()
        if not user or not user.certificate:
            ttk.Label(tab, text="No certificate found").pack(pady=50)
            return
        
        cert = user.certificate
        
        # Certificate info frame
        cert_frame = ttk.LabelFrame(tab, text="Your Digital Certificate", 
                                   padding=20)
        cert_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info_text = f"""
        ┌─────────────────────────────────────┐
        │        DIGITAL CERTIFICATE          │
        ├─────────────────────────────────────┤
        │ Subject:    {cert.subject:30} │
        │ Serial:     {cert.serial:30} │
        │ Issuer:     {cert.issuer:30} │
        │ Valid From: {cert.valid_from[:10]:30} │
        │ Valid To:   {cert.valid_to[:10]:30} │
        │ Status:     {'✅ VALID':30} │
        └─────────────────────────────────────┘
        
        Public Key (truncated):
        {cert.public_key[:50]}...
        
        Signature (truncated):
        {cert.signature[:50]}...
        """
        
        cert_label = ttk.Label(cert_frame, text=info_text, 
                              font=('Courier', 10), justify=tk.LEFT)
        cert_label.pack()
        
        # Export button
        ttk.Button(cert_frame, text="Export Certificate", 
                  command=self.export_certificate).pack(pady=20)
    
    # ============ FILE OPERATIONS ============
    
    def browse_share_file(self):
        """Browse for file to share"""
        filename = filedialog.askopenfilename(
            title="Select file to share"
        )
        if filename:
            self.share_file_path.set(filename)
    
    def share_file(self):
        """Share selected file"""
        filepath = self.share_file_path.get()
        
        if not filepath or not Path(filepath).exists():
            messagebox.showerror("Error", "Please select a valid file")
            return
        
        # Get selected recipients
        recipients = []
        for user, var in self.recipient_vars.items():
            if var.get():
                recipients.append(user)
        
        if not recipients:
            messagebox.showerror("Error", "Please select at least one recipient")
            return
        
        # Share file
        if self.system.share_file(filepath, recipients):
            messagebox.showinfo("Success", 
                              f"File '{Path(filepath).name}' shared successfully!\n"
                              f"Recipients: {', '.join(recipients)}")
            self.share_file_path.set("")
            # Clear checkboxes
            for var in self.recipient_vars.values():
                var.set(False)
            self.refresh_files()
        else:
            messagebox.showerror("Error", "Failed to share file")
    
    def refresh_files(self):
        """Refresh files list"""
        # Clear tree
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Get shared files
        files = self.system.get_shared_files()
        
        # Add to tree
        for i, file in enumerate(files):
            self.files_tree.insert("", tk.END, iid=file.file_id,
                                  values=(file.file_id[:10] + "...",
                                          file.filename,
                                          file.owner,
                                          ", ".join(file.recipients[:3]) + 
                                          ("..." if len(file.recipients) > 3 else ""),
                                          file.timestamp[:10]))
    
    def download_selected(self):
        """Download selected file"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a file")
            return
        
        file_id = selection[0]
        
        # Ask for save location
        save_path = filedialog.asksaveasfilename(
            title="Save file as",
            defaultextension=".*"
        )
        
        if save_path:
            if self.system.download_file(file_id, save_path):
                messagebox.showinfo("Success", 
                                  "File downloaded and decrypted successfully!")
            else:
                messagebox.showerror("Error", "Failed to download file")
    
    def revoke_access(self):
        """Revoke access for selected file"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a file")
            return
        
        file_id = selection[0]
        
        if file_id not in self.system.shared_files:
            messagebox.showerror("Error", "File not found")
            return
        
        shared_file = self.system.shared_files[file_id]
        
        # Check if current user is owner
        if shared_file.owner != self.system.current_user:
            messagebox.showerror("Error", "Only the file owner can revoke access")
            return
        
        # Show recipient selection dialog
        self.show_revoke_dialog(file_id, shared_file.recipients)
    
    def show_revoke_dialog(self, file_id, recipients):
        """Show dialog to select recipients to revoke"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Revoke Access")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select users to revoke access:").pack(pady=10)
        
        revoke_vars = {}
        
        for user in recipients:
            var = tk.BooleanVar()
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=20, pady=2)
            
            ttk.Checkbutton(frame, text=user, variable=var).pack(side=tk.LEFT)
            revoke_vars[user] = var
        
        def do_revoke():
            users_to_revoke = [u for u, var in revoke_vars.items() if var.get()]
            
            for user in users_to_revoke:
                self.system.revoke_file_access(file_id, user)
            
            self.refresh_files()
            dialog.destroy()
            messagebox.showinfo("Success", 
                              f"Access revoked for {len(users_to_revoke)} user(s)")
        
        ttk.Button(dialog, text="Revoke Access", command=do_revoke).pack(pady=20)
    
    def refresh_users(self):
        """Refresh users list"""
        self.users_text.delete(1.0, tk.END)
        
        users = self.system.get_all_users()
        current_user = self.system.current_user
        
        for user in users:
            if user == current_user:
                self.users_text.insert(tk.END, f"✓ {user} (you)\n")
            else:
                self.users_text.insert(tk.END, f"• {user}\n")
    
    def export_certificate(self):
        """Export certificate to file"""
        user = self.system.get_current_user()
        if not user or not user.certificate:
            return
        
        cert = user.certificate
        
        # Create certificate text
        cert_text = f"""SECURESHARE DIGITAL CERTIFICATE
===============================
Subject: {cert.subject}
Serial: {cert.serial}
Issuer: {cert.issuer}
Valid From: {cert.valid_from}
Valid To: {cert.valid_to}
Public Key: {cert.public_key}
Signature: {cert.signature}

Exported: {datetime.datetime.now().isoformat()}
"""
        
        # Ask for save location
        save_path = filedialog.asksaveasfilename(
            title="Save certificate",
            defaultextension=".txt",
            initialfile=f"certificate_{cert.subject}.txt"
        )
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(cert_text)
            messagebox.showinfo("Success", "Certificate exported successfully!")
    
    def logout(self):
        """Logout user"""
        self.system.logout()
        self.show_login_screen()

# ============ MAIN ENTRY POINT ============

def main():
    """Main entry point"""
    root = tk.Tk()
    app = SecureShareApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()