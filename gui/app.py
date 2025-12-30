import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import base64

from core.secure_share import SecureShareSystem


class SecureShareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SecureShare - Secure File Sharing")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.system = SecureShareSystem()
        self.current_password = None  # Stored temporarily for crypto operations

        self.setup_styles()

        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.show_login_screen()

    # ==================== STYLES ====================
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel', font=('Arial', 20, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # ==================== LOGIN / REGISTER ====================
    def show_login_screen(self):
        self.clear_screen()

        ttk.Label(self.main_container, text="🔐 SecureShare", style='Title.TLabel').pack(pady=(0, 10))
        ttk.Label(
            self.main_container,
            text="Secure File Sharing with Hybrid Encryption & Digital Signatures"
        ).pack(pady=(0, 30))

        # Login Frame
        login_frame = ttk.LabelFrame(self.main_container, text=" Login ", padding=20)
        login_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.login_username = ttk.Entry(login_frame, width=40, font=('Arial', 11))
        self.login_username.grid(row=0, column=1, pady=10, padx=(10, 0))

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.login_password = ttk.Entry(login_frame, width=40, show="*", font=('Arial', 11))
        self.login_password.grid(row=1, column=1, pady=10, padx=(10, 0))

        ttk.Button(login_frame, text="Login", command=self.do_login).grid(row=2, column=0, columnspan=2, pady=20)

        # Register Frame
        reg_frame = ttk.LabelFrame(self.main_container, text=" Register New User ", padding=20)
        reg_frame.pack(fill=tk.X)

        ttk.Label(reg_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.reg_username = ttk.Entry(reg_frame, width=40, font=('Arial', 11))
        self.reg_username.grid(row=0, column=1, pady=10, padx=(10, 0))

        ttk.Label(reg_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.reg_password = ttk.Entry(reg_frame, width=40, show="*", font=('Arial', 11))
        self.reg_password.grid(row=1, column=1, pady=10, padx=(10, 0))

        ttk.Label(reg_frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.reg_confirm = ttk.Entry(reg_frame, width=40, show="*", font=('Arial', 11))
        self.reg_confirm.grid(row=2, column=1, pady=10, padx=(10, 0))

        ttk.Button(reg_frame, text="Register", command=self.do_register).grid(row=3, column=0, columnspan=2, pady=20)

    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return

        if self.system.login_user(username, password):
            self.current_password = password
            self.show_main_dashboard()
            self.refresh_files_list()  # Auto-refresh on login
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def do_register(self):
        username = self.reg_username.get().strip()
        pwd1 = self.reg_password.get()
        pwd2 = self.reg_confirm.get()

        if not username or not pwd1:
            messagebox.showerror("Error", "All fields are required")
            return
        if pwd1 != pwd2:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if len(pwd1) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return

        if self.system.register_user(username, pwd1):
            messagebox.showinfo("Success", f"User '{username}' registered successfully!\nYou can now log in.")
            self.reg_username.delete(0, tk.END)
            self.reg_password.delete(0, tk.END)
            self.reg_confirm.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Username already exists")

    # ==================== MAIN DASHBOARD ====================
    def show_main_dashboard(self):
        self.clear_screen()

        # Header
        header = ttk.Frame(self.main_container)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text=f"Welcome, {self.system.current_user}!", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        # Notebook with tabs
        notebook = ttk.Notebook(self.main_container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.create_share_tab(notebook)
        self.create_files_tab(notebook)
        self.create_users_tab(notebook)
        self.create_certificate_tab(notebook)

    # ==================== SHARE FILE TAB ====================
    def create_share_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📤 Share File")

        # File selection
        file_frame = ttk.LabelFrame(tab, text="Select File to Share", padding=15)
        file_frame.pack(fill=tk.X, padx=20, pady=15)
        self.share_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.share_path_var, width=70).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        # Recipients
        recip_frame = ttk.LabelFrame(tab, text="Select Recipients", padding=15)
        recip_frame.pack(fill=tk.X, padx=20, pady=15)

        all_users = self.system.get_all_users()
        others = [u for u in all_users if u != self.system.current_user]
        self.recip_vars = {}

        if others:
            for i, user in enumerate(others):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(recip_frame, text=user, variable=var)
                chk.grid(row=i // 4, column=i % 4, sticky=tk.W, padx=15, pady=5)
                self.recip_vars[user] = var
        else:
            ttk.Label(recip_frame, text="No other registered users", foreground="gray").pack(pady=10)

        # Share button
        ttk.Button(tab, text="🔒 Encrypt & Share File", command=self.do_share_file).pack(pady=25)

    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Choose a file to share")
        if filepath:
            self.share_path_var.set(filepath)

    def do_share_file(self):
        filepath = self.share_path_var.get()
        if not filepath or not Path(filepath).exists():
            messagebox.showerror("Error", "Please select a valid file")
            return

        recipients = [user for user, var in self.recip_vars.items() if var.get()]
        if not recipients:
            messagebox.showerror("Error", "Please select at least one recipient")
            return

        if self.system.share_file(filepath, recipients, self.current_password):
            messagebox.showinfo(
                "Success",
                f"File '{Path(filepath).name}' shared successfully with:\n{', '.join(recipients)}"
            )
            self.share_path_var.set("")
            for var in self.recip_vars.values():
                var.set(False)
            self.refresh_files_list()
        else:
            messagebox.showerror("Error", "Failed to share file. Check console for details.")

    # ==================== FILES TAB ====================
    def create_files_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📁 My Files")

        # Controls
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(top_frame, text="🔄 Refresh", command=self.refresh_files_list).pack(side=tk.RIGHT)

        # Treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("ID", "Filename", "Owner", "Recipients", "Date")
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, [120, 250, 120, 250, 130]):
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=width, anchor=tk.W if col != "Date" else tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Actions
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, padx=20, pady=15)
        ttk.Button(action_frame, text="⬇️ Download Selected", command=self.download_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="🚫 Revoke Access", command=self.revoke_access).pack(side=tk.LEFT, padx=10)

        self.refresh_files_list()

    def refresh_files_list(self):
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        files = self.system.get_shared_files()
        for sf in files:
            recipients = [u for u in sf.encrypted_sym_key.keys() if u != sf.owner]
            recip_str = "(Only me)" if not recipients else ", ".join(recipients[:4])
            if len(recipients) > 4:
                recip_str += "..."

            self.files_tree.insert("", tk.END, iid=sf.file_id, values=(
                sf.file_id[:15] + "...",
                sf.filename,
                sf.owner,
                recip_str,
                sf.timestamp[:10]
            ))

    def download_file(self):
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a file to download")
            return
        file_id = selection[0]
        sf = self.system.shared_files[file_id]

        save_path = filedialog.asksaveasfilename(
            title="Save decrypted file as",
            initialfile=sf.filename
        )
        if not save_path:
            return

        if self.system.download_file(file_id, save_path, self.current_password):
            messagebox.showinfo(
                "Success",
                f"File '{sf.filename}' downloaded and decrypted successfully!\n\n"
                "✓ Integrity verified\n"
                "✓ Digital signature verified"
            )
        else:
            messagebox.showerror(
                "Error",
                "Download failed.\nPossible causes:\n"
                "• Access was revoked\n"
                "• File is corrupted\n"
                "• Internal error (check console)"
            )

    def revoke_access(self):
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a file")
            return
        file_id = selection[0]
        sf = self.system.shared_files[file_id]

        if sf.owner != self.system.current_user:
            messagebox.showerror("Error", "Only the file owner can revoke access")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Revoke Access")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text=f"Revoke access to '{sf.filename}' from:",
            font=('Arial', 11, 'bold')
        ).pack(pady=15)

        revoke_vars = {}
        for user in sf.encrypted_sym_key:
            if user == sf.owner:
                continue
            var = tk.BooleanVar()
            ttk.Checkbutton(dialog, text=user, variable=var).pack(anchor=tk.W, padx=40, pady=4)
            revoke_vars[user] = var

        def perform_revoke():
            revoked = []
            for user, var in revoke_vars.items():
                if var.get() and self.system.revoke_file_access(file_id, user):
                    revoked.append(user)

            if revoked:
                messagebox.showinfo("Success", f"Access revoked for: {', '.join(revoked)}")
            else:
                messagebox.showinfo("Info", "No users selected for revocation")
            dialog.destroy()
            self.refresh_files_list()

        ttk.Button(dialog, text="Revoke Selected", command=perform_revoke).pack(pady=20)

    # ==================== USERS TAB ====================
    def create_users_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="👥 Users")

        frame = ttk.LabelFrame(tab, text="Registered Users", padding=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        columns = ("Status", "Username")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        tree.heading("Status", text="")
        tree.heading("Username", text="Username")
        tree.column("Status", width=60, anchor=tk.CENTER)
        tree.column("Username", width=200, anchor=tk.W)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for user in sorted(self.system.get_all_users()):
            status = "✓ You" if user == self.system.current_user else "•"
            tree.insert("", tk.END, values=(status, user))

    # ==================== CERTIFICATE TAB ====================
    def create_certificate_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📜 Your Certificate")

        user = self.system.users[self.system.current_user]
        cert = user.certificate

        info = (
            f"┌{'─' * 70}┐\n"
            f"│                    YOUR DIGITAL CERTIFICATE                     │\n"
            f"├{'─' * 70}┤\n"
            f"│ Subject:        {cert.subject.ljust(48)} │\n"
            f"│ Serial:         {cert.serial.ljust(48)} │\n"
            f"│ Issuer:         {cert.issuer.ljust(48)} │\n"
            f"│ Valid From:     {cert.valid_from[:10].ljust(48)} │\n"
            f"│ Valid To:       {cert.valid_to[:10].ljust(48)} │\n"
            f"│ Status:         ✅ VALID (Demo Self-Signed)                     │\n"
            f"└{'─' * 70}┘\n"
            f"\nPublic Key (first 120 chars):\n{cert.public_key_pem[:120]}...\n"
            f"\nSignature (first 80 chars of base64):\n"
            f"{base64.b64encode(cert.signature).decode()[:80]}..."
        )

        label = ttk.Label(tab, text=info, font=('Courier', 10), background="#f0f0f0", relief="groove", padding=30)
        label.pack(padx=40, pady=40, fill=tk.X)

    # ==================== LOGOUT ====================
    def logout(self):
        self.system.current_user = None
        self.current_password = None
        self.show_login_screen()
