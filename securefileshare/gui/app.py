import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import base64
from core.secure_share import SecureShareSystem


class SecureShareApp:
    def __init__(self, root):
        self.root = root
<<<<<<< HEAD
        self.root.title("SecureShare")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg='#000000')

        # Theme colors - Classic green terminal
        self.bg_color = "#000000"
        self.fg_color = "#00ff00"          # Neon green
        self.accent_color = "#00ff00"
        self.panel_bg = "#0d0d0d"
        self.entry_bg = "#111111"
=======
        self.root.title("SecureShare - Secure File Sharing")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)

        # Modern color palette (dark mode inspired)
        self.bg_color = "#212121"          # Dark background
        self.fg_color = "#ffffff"          # Light text
        self.accent_color = "#00b0ff"      # Cyan accent for primary actions
        self.secondary_bg = "#2d2d2d"      # Slightly lighter panels
        self.entry_bg = "#333333"

        self.root.configure(bg=self.bg_color)
>>>>>>> 45b3eb458044a5abe802b50d53a909675ea262f6

        self.system = SecureShareSystem()
        self.current_password = None

        self.setup_styles()
<<<<<<< HEAD

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        self.show_welcome_screen()
=======
        self.main_container = ttk.Frame(root, padding="30")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.show_login_screen()
>>>>>>> 45b3eb458044a5abe802b50d53a909675ea262f6

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

<<<<<<< HEAD
        # Global terminal style
        style.configure('.', background=self.bg_color, foreground=self.fg_color,
                        font=('Courier New', 11))

        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe', background=self.panel_bg, foreground=self.fg_color)
        style.configure('TLabelframe.Label',
                        background=self.panel_bg,
                        foreground=self.fg_color,
                        font=('Courier New', 13, 'bold'))

        style.configure('TEntry',
                        fieldbackground=self.entry_bg,
                        foreground=self.fg_color,
                        insertcolor=self.fg_color,
                        font=('Courier New', 12))

        # Accent buttons (neon green glow)
        style.configure('Accent.TButton',
                        background='#002200',
                        foreground=self.accent_color,
                        font=('Courier New', 12, 'bold'),
                        padding=14,
                        borderwidth=1)
        style.map('Accent.TButton',
                  background=[('active', '#004400'), ('pressed', '#003300')],
                  foreground=[('active', '#00ff88')])

        # Titles
        style.configure('Title.TLabel', font=('Courier New', 32, 'bold'), foreground=self.accent_color)
        style.configure('Subtitle.TLabel', font=('Courier New', 14), foreground='#00cc00')

        # Treeview - terminal style
        style.configure('Treeview',
                        background=self.panel_bg,
                        foreground=self.fg_color,
                        fieldbackground=self.panel_bg,
                        rowheight=32,
                        font=('Courier New', 10))
        style.configure('Treeview.Heading',
                        font=('Courier New', 11, 'bold'),
                        background='#001100',
                        foreground=self.accent_color)
        style.map('Treeview', background=[('selected', '#004400')])
=======
        # Global configurations
        style.configure('.', background=self.bg_color, foreground=self.fg_color,
                        font=('Helvetica', 11), relief='flat')

        style.configure('TLabel', background=self.bg_color)
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabelframe', background=self.secondary_bg, foreground=self.fg_color)
        style.configure('TLabelframe.Label', background=self.secondary_bg, foreground=self.fg_color, font=('Helvetica', 12, 'bold'))

        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.fg_color,
                        insertcolor=self.fg_color)
        style.configure('TButton', font=('Helvetica', 11, 'bold'), padding=10)
        style.map('TButton',
                  background=[('active', self.accent_color)],
                  foreground=[('active', 'white')])

        # Accent button for primary actions
        style.configure('Accent.TButton',
                        background=self.accent_color,
                        foreground='white',
                        font=('Helvetica', 12, 'bold'),
                        padding=12)
        style.map('Accent.TButton',
                  background=[('active', '#009edc')],
                  foreground=[('active', 'white')])

        # Title style
        style.configure('Title.TLabel', font=('Helvetica', 28, 'bold'), foreground=self.accent_color)
        style.configure('Subtitle.TLabel', font=('Helvetica', 14), foreground='#b0b0b0')

        # Treeview (files list)
        style.configure('Treeview', background=self.secondary_bg, foreground=self.fg_color,
                        fieldbackground=self.secondary_bg, rowheight=30)
        style.configure('Treeview.Heading', font=('Helvetica', 11, 'bold'), background=self.accent_color, foreground='white')
        style.map('Treeview', background=[('selected', self.accent_color)])
>>>>>>> 45b3eb458044a5abe802b50d53a909675ea262f6

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

<<<<<<< HEAD
    # ==================== WELCOME SCREEN ====================
    def show_welcome_screen(self):
        self.clear_screen()

        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 20))
        ttk.Label(self.main_container,
                  text="Secure File Sharing with Hybrid Encryption\n& Digital Signatures",
                  style='Subtitle.TLabel',
                  justify=tk.CENTER).pack(pady=(0, 80))

        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack()

        ttk.Button(btn_frame,
                   text="Login",
                   style='Accent.TButton',
                   width=20,
                   command=self.show_login_screen).pack(pady=15)

        ttk.Button(btn_frame,
                   text="Register",
                   style='Accent.TButton',
                   width=20,
                   command=self.show_register_screen).pack(pady=15)

    # ==================== LOGIN SCREEN ====================
    def show_login_screen(self):
        self.clear_screen()

        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 30))
        ttk.Label(self.main_container, text="Login to Your Account", style='Subtitle.TLabel').pack(pady=(0, 50))

        frame = ttk.Labelframe(self.main_container, text=" Authentication ", padding=40)
        frame.pack(pady=20, ipadx=50, ipady=30)

        ttk.Label(frame, text="Username").grid(row=0, column=0, sticky=tk.W, pady=20)
        self.login_username = ttk.Entry(frame, width=40, font=('Courier New', 12))
        self.login_username.grid(row=0, column=1, pady=20, padx=(20, 0))

        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky=tk.W, pady=20)
        self.login_password = ttk.Entry(frame, width=40, show="*", font=('Courier New', 12))
        self.login_password.grid(row=1, column=1, pady=20, padx=(20, 0))

        ttk.Button(frame,
                   text="Login",
                   style='Accent.TButton',
                   command=self.do_login).grid(row=2, column=0, columnspan=2, pady=40)

        ttk.Button(self.main_container,
                   text="← Back",
                   command=self.show_welcome_screen).pack(pady=20)

    # ==================== REGISTER SCREEN ====================
    def show_register_screen(self):
        self.clear_screen()

        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 30))
        ttk.Label(self.main_container, text="Create New Account", style='Subtitle.TLabel').pack(pady=(0, 50))

        frame = ttk.Labelframe(self.main_container, text=" Registration ", padding=40)
        frame.pack(pady=20, ipadx=50, ipady=30)

        ttk.Label(frame, text="Username").grid(row=0, column=0, sticky=tk.W, pady=15)
        self.reg_username = ttk.Entry(frame, width=40, font=('Courier New', 12))
        self.reg_username.grid(row=0, column=1, pady=15, padx=(20, 0))

        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky=tk.W, pady=15)
        self.reg_password = ttk.Entry(frame, width=40, show="*", font=('Courier New', 12))
        self.reg_password.grid(row=1, column=1, pady=15, padx=(20, 0))

        ttk.Label(frame, text="Confirm Password").grid(row=2, column=0, sticky=tk.W, pady=15)
        self.reg_confirm = ttk.Entry(frame, width=40, show="*", font=('Courier New', 12))
        self.reg_confirm.grid(row=2, column=1, pady=15, padx=(20, 0))

        ttk.Button(frame,
                   text="Register",
                   style='Accent.TButton',
                   command=self.do_register).grid(row=3, column=0, columnspan=2, pady=40)

        ttk.Button(self.main_container,
                   text="← Back",
                   command=self.show_welcome_screen).pack(pady=20)

    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        if self.system.login_user(username, password):
            self.current_password = password
            self.show_main_dashboard()
            self.refresh_files_list()
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
            self.show_welcome_screen()
        else:
            messagebox.showerror("Error", "Username already exists")

    # ==================== MAIN DASHBOARD ====================
    def show_main_dashboard(self):
        self.clear_screen()

        header = ttk.Frame(self.main_container)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text=f"SecureShare > {self.system.current_user}", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(self.main_container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.create_share_tab(notebook)
        self.create_files_tab(notebook)
        self.create_users_tab(notebook)
        self.create_certificate_tab(notebook)

    def create_share_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Share File")

        file_frame = ttk.Labelframe(tab, text="Select File", padding=20)
        file_frame.pack(fill=tk.X, padx=20, pady=20)
        self.share_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.share_path_var, width=70).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        recip_frame = ttk.Labelframe(tab, text="Recipients", padding=20)
        recip_frame.pack(fill=tk.X, padx=20, pady=20)
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
            ttk.Label(recip_frame, text="No other users registered", foreground="#006600").pack(pady=10)

        ttk.Button(tab, text="Encrypt & Share", style='Accent.TButton', command=self.do_share_file).pack(pady=30)

    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Select file to share")
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
            messagebox.showinfo("Success", f"File shared successfully with: {', '.join(recipients)}")
            self.share_path_var.set("")
            for var in self.recip_vars.values():
                var.set(False)
            self.refresh_files_list()
        else:
            messagebox.showerror("Error", "Failed to share file")

    def create_files_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="My Files")

        top = ttk.Frame(tab)
        top.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(top, text="Refresh", command=self.refresh_files_list).pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        columns = ("ID", "Filename", "Owner", "Recipients", "Date")
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        for col, w in zip(columns, [150, 300, 120, 280, 120]):
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=w, anchor=tk.CENTER if col == "Date" else tk.W)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        actions = ttk.Frame(tab)
        actions.pack(fill=tk.X, padx=20, pady=20)
        ttk.Button(actions, text="Download", style='Accent.TButton', command=self.download_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(actions, text="Revoke Access", command=self.revoke_access).pack(side=tk.LEFT, padx=10)

        self.refresh_files_list()

    def refresh_files_list(self):
        for i in self.files_tree.get_children():
            self.files_tree.delete(i)
        for sf in self.system.get_shared_files():
            recips = [u for u in sf.encrypted_sym_key if u != sf.owner]
            recip_str = "(Only me)" if not recips else ", ".join(recips[:3]) + ("..." if len(recips) > 3 else "")
            self.files_tree.insert("", tk.END, iid=sf.file_id, values=(
                sf.file_id[:12] + "...",
                sf.filename,
                sf.owner,
                recip_str,
                sf.timestamp[:10]
            ))

    def download_file(self):
        sel = self.files_tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a file")
            return
        file_id = sel[0]
        sf = self.system.shared_files[file_id]
        path = filedialog.asksaveasfilename(initialfile=sf.filename)
        if not path:
            return
        if self.system.download_file(file_id, path, self.current_password):
            messagebox.showinfo("Success", f"'{sf.filename}' downloaded and decrypted\n\nIntegrity: Verified\nSignature: Valid")
        else:
            messagebox.showerror("Error", "Download failed (possibly revoked)")

    def revoke_access(self):
        sel = self.files_tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a file")
            return
        file_id = sel[0]
        sf = self.system.shared_files[file_id]
        if sf.owner != self.system.current_user:
            messagebox.showerror("Error", "Only owner can revoke access")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Revoke Access")
        dialog.configure(bg='#000000')
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Revoke access to '{sf.filename}' from:", font=('Courier New', 11, 'bold')).pack(pady=20)

        vars = {}
        for user in sf.encrypted_sym_key:
            if user == sf.owner: continue
            v = tk.BooleanVar()
            ttk.Checkbutton(dialog, text=user, variable=v).pack(anchor=tk.W, padx=50, pady=3)
            vars[user] = v

        def revoke():
            revoked = [u for u, v in vars.items() if v.get() and self.system.revoke_file_access(file_id, u)]
            if revoked:
                messagebox.showinfo("Success", f"Access revoked for: {', '.join(revoked)}")
            dialog.destroy()
            self.refresh_files_list()

        ttk.Button(dialog, text="Revoke Selected", style='Accent.TButton', command=revoke).pack(pady=30)

    def create_users_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Users")
        frame = ttk.Labelframe(tab, text="Registered Users", padding=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tree = ttk.Treeview(frame, columns=("Status", "Username"), show="headings")
        tree.heading("Status", text="")
        tree.heading("Username", text="Username")
        tree.column("Status", width=80, anchor=tk.CENTER)
        tree.column("Username", width=300)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for user in sorted(self.system.get_all_users()):
            status = "You" if user == self.system.current_user else ""
            tree.insert("", tk.END, values=(status, user))

    def create_certificate_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Certificate")
        user = self.system.users[self.system.current_user]
        cert = user.certificate
        info = (
            f"┌{'─' * 72}┐\n"
            f"│ {'YOUR DIGITAL CERTIFICATE':^70} │\n"
            f"├{'─' * 72}┤\n"
            f"│ Subject:     {str(cert.subject):<56} │\n"
            f"│ Serial:      {cert.serial:<56} │\n"
            f"│ Issuer:      {str(cert.issuer):<56} │\n"
            f"│ Valid from:  {cert.valid_from[:10]:<56} │\n"
            f"│ Valid to:    {cert.valid_to[:10]:<56} │\n"
            f"│ Status:      VALID (Self-Signed Demo) {' ':<32} │\n"
            f"└{'─' * 72}┘\n\n"
            f"Public Key (PEM preview):\n{cert.public_key_pem[:120]}...\n\n"
            f"Signature (base64 preview):\n{base64.b64encode(cert.signature).decode()[:80]}..."
        )
        ttk.Label(tab, text=info, font=('Courier New', 10), background='#000000',
                  foreground='#00ff00', justify=tk.LEFT, padding=30).pack(padx=40, pady=40, fill=tk.X)
=======
    # ==================== LOGIN / REGISTER ====================
    def show_login_screen(self):
        self.clear_screen()

        ttk.Label(self.main_container, text="🔐 SecureShare", style='Title.TLabel').pack(pady=(0, 10))
        ttk.Label(self.main_container,
                  text="Secure File Sharing with Hybrid Encryption & Digital Signatures",
                  style='Subtitle.TLabel').pack(pady=(0, 40))

        # Login Frame
        login_frame = ttk.Labelframe(self.main_container, text=" Login ", padding=30)
        login_frame.pack(fill=tk.X, pady=(0, 30), ipady=20)

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=15)
        self.login_username = ttk.Entry(login_frame, width=50, font=('Helvetica', 12))
        self.login_username.grid(row=0, column=1, pady=15, padx=(15, 0))

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=15)
        self.login_password = ttk.Entry(login_frame, width=50, show="*", font=('Helvetica', 12))
        self.login_password.grid(row=1, column=1, pady=15, padx=(15, 0))

        ttk.Button(login_frame, text="Login", style='Accent.TButton', command=self.do_login) \
            .grid(row=2, column=0, columnspan=2, pady=30)

        # Register Frame
        reg_frame = ttk.Labelframe(self.main_container, text=" Register New User ", padding=30)
        reg_frame.pack(fill=tk.X, ipady=20)

        ttk.Label(reg_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=15)
        self.reg_username = ttk.Entry(reg_frame, width=50, font=('Helvetica', 12))
        self.reg_username.grid(row=0, column=1, pady=15, padx=(15, 0))

        ttk.Label(reg_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=15)
        self.reg_password = ttk.Entry(reg_frame, width=50, show="*", font=('Helvetica', 12))
        self.reg_password.grid(row=1, column=1, pady=15, padx=(15, 0))

        ttk.Label(reg_frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=15)
        self.reg_confirm = ttk.Entry(reg_frame, width=50, show="*", font=('Helvetica', 12))
        self.reg_confirm.grid(row=2, column=1, pady=15, padx=(15, 0))

        ttk.Button(reg_frame, text="Register", style='Accent.TButton', command=self.do_register) \
            .grid(row=3, column=0, columnspan=2, pady=30)

    # The rest of your methods (do_login, do_register, show_main_dashboard, etc.)
    # remain unchanged, but benefit from the new styles automatically.
    # For example, buttons in the dashboard will use the Accent style if you add style='Accent.TButton'

    # Quick example updates for key buttons in other tabs:
    # In create_share_tab: ttk.Button(tab, text="🔒 Encrypt & Share File", style='Accent.TButton', command=self.do_share_file)
    # In create_files_tab: ttk.Button(action_frame, text="⬇️ Download Selected", style='Accent.TButton', command=self.download_file)

    # ... (paste the rest of your original methods here unchanged)
>>>>>>> 45b3eb458044a5abe802b50d53a909675ea262f6

    def logout(self):
        self.system.current_user = None
        self.current_password = None
<<<<<<< HEAD
        self.show_welcome_screen()
=======
        self.show_login_screen()
>>>>>>> 45b3eb458044a5abe802b50d53a909675ea262f6


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureShareApp(root)
    root.mainloop()