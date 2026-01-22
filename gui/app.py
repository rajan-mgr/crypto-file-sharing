import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import os
import subprocess
import requests
from secure_share import SecureShareSystem


class SecureShareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SecureShare")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg='#000000')

        self.bg_color = "#000000"
        self.fg_color = "#00ff00"
        self.accent_color = "#00ff00"
        self.panel_bg = "#0d0d0d"
        self.entry_bg = "#111111"

        self.system = SecureShareSystem()
        self.current_password = None

        self.setup_styles()

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        self.show_welcome_screen()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=self.bg_color, foreground=self.fg_color, font=('Courier New', 11))
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe', background=self.panel_bg, foreground=self.fg_color)
        style.configure('TLabelframe.Label', background=self.panel_bg, foreground=self.fg_color, font=('Courier New', 13, 'bold'))

        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background='#002200', foreground=self.fg_color, padding=[15, 5])
        style.map('TNotebook.Tab',
                  background=[('selected', self.accent_color)],
                  foreground=[('selected', '#000000')])

        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.fg_color, insertcolor=self.fg_color, font=('Courier New', 12))
        style.configure('Accent.TButton', background='#002200', foreground=self.accent_color, font=('Courier New', 12, 'bold'), padding=14, borderwidth=1)
        style.map('Accent.TButton', background=[('active', '#004400'), ('pressed', '#003300')], foreground=[('active', '#00ff88')])

        style.configure('Title.TLabel', font=('Courier New', 32, 'bold'), foreground=self.accent_color)
        style.configure('Subtitle.TLabel', font=('Courier New', 14), foreground='#00cc00')

        style.configure('Treeview', background=self.panel_bg, foreground=self.fg_color, fieldbackground=self.panel_bg, rowheight=32, font=('Courier New', 10))
        style.configure('Treeview.Heading', font=('Courier New', 11, 'bold'), background='#001100', foreground=self.accent_color)
        style.map('Treeview', background=[('selected', '#004400')])

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_screen()
        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 20))
        ttk.Label(self.main_container, text="Secure File Sharing with Hybrid Encryption\n& Digital Signatures", style='Subtitle.TLabel', justify=tk.CENTER).pack(pady=(0, 80))
        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Login", style='Accent.TButton', width=20, command=self.show_login_screen).pack(pady=15)
        ttk.Button(btn_frame, text="Register", style='Accent.TButton', width=20, command=self.show_register_screen).pack(pady=15)

    def show_login_screen(self):
        self.clear_screen()
        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 30))
        ttk.Label(self.main_container, text="Login to Your Account", style='Subtitle.TLabel').pack(pady=(0, 50))
        frame = ttk.Labelframe(self.main_container, text=" Authentication ", padding=40)
        frame.pack(pady=20, ipadx=50, ipady=30)
        ttk.Label(frame, text="Username").grid(row=0, column=0, sticky=tk.W, pady=20)
        self.login_username = ttk.Entry(frame, width=40)
        self.login_username.grid(row=0, column=1, pady=20, padx=(20, 0))
        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky=tk.W, pady=20)
        self.login_password = ttk.Entry(frame, width=40, show="*")
        self.login_password.grid(row=1, column=1, pady=20, padx=(20, 0))
        ttk.Button(frame, text="Login", style='Accent.TButton', command=self.do_login).grid(row=2, column=0, columnspan=2, pady=40)
        ttk.Button(self.main_container, text="← Back", command=self.show_welcome_screen).pack(pady=20)

    def show_register_screen(self):
        self.clear_screen()
        ttk.Label(self.main_container, text="SecureShare", style='Title.TLabel').pack(pady=(50, 30))
        ttk.Label(self.main_container, text="Create New Account", style='Subtitle.TLabel').pack(pady=(0, 50))
        frame = ttk.Labelframe(self.main_container, text=" Registration ", padding=40)
        frame.pack(pady=20, ipadx=50, ipady=30)
        ttk.Label(frame, text="Username").grid(row=0, column=0, sticky=tk.W, pady=15)
        self.reg_username = ttk.Entry(frame, width=40)
        self.reg_username.grid(row=0, column=1, pady=15, padx=(20, 0))
        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky=tk.W, pady=15)
        self.reg_password = ttk.Entry(frame, width=40, show="*")
        self.reg_password.grid(row=1, column=1, pady=15, padx=(20, 0))
        ttk.Label(frame, text="Confirm Password").grid(row=2, column=0, sticky=tk.W, pady=15)
        self.reg_confirm = ttk.Entry(frame, width=40, show="*")
        self.reg_confirm.grid(row=2, column=1, pady=15, padx=(20, 0))
        ttk.Button(frame, text="Register", style='Accent.TButton', command=self.do_register).grid(row=3, column=0, columnspan=2, pady=40)
        ttk.Button(self.main_container, text="← Back", command=self.show_welcome_screen).pack(pady=20)

    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return

        if self.system.login(username, password):
            self.current_password = password
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def do_register(self):
        username = self.reg_username.get().strip()
        p1 = self.reg_password.get()
        p2 = self.reg_confirm.get()

        if not username or not p1 or not p2:
            messagebox.showerror("Error", "All fields are required")
            return

        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(p1) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return

        if self.system.register(username, p1):
            messagebox.showinfo("Success", "Account created! You can now login.")
            self.show_welcome_screen()
        else:
            messagebox.showerror("Error", "Registration failed (username may be taken or server error)")

    def show_main_dashboard(self):
        self.clear_screen()
        header = ttk.Frame(self.main_container)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text=f"SecureShare > {self.system.current_user}", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.create_share_tab()
        self.create_files_tab()
        self.create_users_tab()
        self.create_certificate_tab()

    def create_share_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Share File")

        file_frame = ttk.Labelframe(tab, text="Select File", padding=20)
        file_frame.pack(fill=tk.X, padx=20, pady=20)

        self.share_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.share_path_var).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        recip_frame = ttk.Labelframe(tab, text="Recipients", padding=20)
        recip_frame.pack(fill=tk.X, padx=20, pady=20)

        others = []
        try:
            r = requests.get(f"{self.system.api_base}/users", headers=self.system._headers(), timeout=8)
            r.raise_for_status()
            all_users = r.json()
            others = [u for u in all_users if u != self.system.current_user]
        except Exception as e:
            print("Failed to load users:", str(e))
            messagebox.showwarning("Warning", "Could not load other users. Sharing will be limited.")

        self.recip_vars = {}
        for i, user in enumerate(others):
            var = tk.BooleanVar()
            ttk.Checkbutton(recip_frame, text=user, variable=var).grid(row=i//4, column=i%4, sticky=tk.W, padx=15, pady=5)
            self.recip_vars[user] = var

        ttk.Button(tab, text="Encrypt & Share", style='Accent.TButton', command=self.do_share_file).pack(pady=30)

    def browse_file(self):
        path = filedialog.askopenfilename(initialdir=str(Path.home()))
        if path:
            self.share_path_var.set(path)

    def do_share_file(self):
        path = self.share_path_var.get()
        recipients = [u for u, v in self.recip_vars.items() if v.get()]

        if not path:
            messagebox.showerror("Error", "Please select a file")
            return
        if not recipients:
            messagebox.showerror("Error", "Select at least one recipient")
            return

        if self.system.share_file(path, recipients, self.current_password):
            messagebox.showinfo("Success", "File encrypted and shared successfully!")
            self.refresh_files_list()
        else:
            messagebox.showerror("Error", "Sharing failed - check console for details")

    def create_files_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="My Files")

        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols = ("ID", "Filename", "Owner", "Date")
        self.files_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols:
            self.files_tree.heading(c, text=c)
            self.files_tree.column(c, anchor=tk.CENTER if c in ["ID", "Date"] else tk.W)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.files_tree.bind('<<TreeviewSelect>>', self.on_file_select)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=10)

        self.btn_download = ttk.Button(btn_frame, text="Download", style='Accent.TButton', command=self.do_download)
        self.btn_refresh  = ttk.Button(btn_frame, text="Refresh",  command=self.refresh_files_list)
        self.btn_revoke   = ttk.Button(btn_frame, text="Revoke Access", style='Accent.TButton', command=self.do_revoke_access, state="disabled")
        self.btn_delete   = ttk.Button(btn_frame, text="Delete File",   style='Accent.TButton', command=self.do_delete_file,   state="disabled")

        self.btn_download.pack(side=tk.LEFT, padx=10)
        self.btn_refresh.pack(side=tk.LEFT, padx=10)
        self.btn_revoke.pack(side=tk.LEFT, padx=10)
        self.btn_delete.pack(side=tk.LEFT, padx=10)

        self.refresh_files_list()

    def on_file_select(self, event):
        sel = self.files_tree.selection()
        if not sel:
            self.btn_revoke.config(state="disabled")
            self.btn_delete.config(state="disabled")
            return

        item = self.files_tree.item(sel[0])
        owner = item["values"][2]  # Owner is third column

        if owner == self.system.current_user:
            self.btn_revoke.config(state="normal")
            self.btn_delete.config(state="normal")
        else:
            self.btn_revoke.config(state="disabled")
            self.btn_delete.config(state="disabled")

    def refresh_files_list(self):
        for i in self.files_tree.get_children():
            self.files_tree.delete(i)

        files = self.system.get_my_files()
        for f in files:
            date_str = f.timestamp[:10] if f.timestamp and len(f.timestamp) >= 10 else "N/A"
            self.files_tree.insert("", tk.END, iid=f.file_id, values=(
                f.file_id[:8] + "...",
                f.filename,
                f.owner,
                date_str
            ))

    def do_download(self):
        sel = self.files_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a file first")
            return

        file_id = sel[0]
        filename = self.files_tree.item(file_id)['values'][1]
        save_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".bin")
        if not save_path:
            return

        if self.system.download_file(file_id, save_path, self.current_password):
            messagebox.showinfo("Success", f"File decrypted and saved to:\n{save_path}")
        else:
            messagebox.showerror("Error", "Download or decryption failed")

    def do_revoke_access(self):
        sel = self.files_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a file first")
            return

        file_id = sel[0]
        filename = self.files_tree.item(file_id)["values"][1]

        target = simpledialog.askstring(
            title="Revoke Access",
            prompt=f"Enter username to revoke access from:\n{filename}",
            parent=self.root
        )

        if not target or not target.strip():
            return

        target = target.strip()

        if not messagebox.askyesno("Confirm Revoke", f"Revoke access for '{target}' from '{filename}'?"):
            return

        try:
            r = requests.delete(
                f"{self.system.api_base}/files/{file_id}/access/{target}",
                headers=self.system._headers(),
                timeout=10
            )
            r.raise_for_status()
            messagebox.showinfo("Success", f"Access revoked for {target}")
            self.refresh_files_list()
        except requests.HTTPError as e:
            detail = e.response.json().get("detail", "Unknown error") if e.response else str(e)
            messagebox.showerror("Revoke Failed", detail)
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed:\n{str(e)}")

    def do_delete_file(self):
        sel = self.files_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a file first")
            return

        file_id = sel[0]
        filename = self.files_tree.item(file_id)["values"][1]

        if not messagebox.askyesno("Confirm Delete", f"Delete file '{filename}' permanently?\nThis action cannot be undone."):
            return

        try:
            r = requests.delete(
                f"{self.system.api_base}/files/{file_id}",
                headers=self.system._headers(),
                timeout=12
            )
            r.raise_for_status()
            messagebox.showinfo("Success", f"File '{filename}' has been deleted")
            self.refresh_files_list()
        except requests.HTTPError as e:
            detail = e.response.json().get("detail", "Unknown error") if e.response else str(e)
            messagebox.showerror("Delete Failed", detail)
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed:\n{str(e)}")

    def create_users_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Users")

        tree = ttk.Treeview(tab, columns=("User",), show="headings")
        tree.heading("User", text="Username")
        tree.column("User", anchor=tk.W)
        tree.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        try:
            r = requests.get(f"{self.system.api_base}/users", headers=self.system._headers(), timeout=8)
            r.raise_for_status()
            users_list = r.json()
        except Exception as e:
            print("Failed to load users:", str(e))
            users_list = [self.system.current_user]

        for u in sorted(users_list):
            tree.insert("", tk.END, values=(u,))

    def create_certificate_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Certificate")

        # Create scrollable text widget for certificate info
        text_frame = ttk.Frame(tab)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        ttk.Label(text_frame, text=f"User Certificate: {self.system.current_user}", 
                  font=('Courier New', 14, 'bold'), 
                  foreground=self.accent_color).pack(pady=(0, 20))

        # Create text widget with scrollbar
        text_widget = tk.Text(text_frame, 
                              wrap=tk.WORD, 
                              font=('Courier New', 9),
                              bg=self.panel_bg,
                              fg=self.fg_color,
                              insertbackground=self.fg_color,
                              selectbackground='#004400',
                              selectforeground=self.accent_color,
                              relief=tk.FLAT,
                              padx=15,
                              pady=15)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fetch and display certificate info
        try:
            # Get certificate from PKI endpoint
            r = requests.get(
                f"{self.system.api_base}/users/me/certificate",
                headers=self.system._headers(),
                timeout=8
            )
            r.raise_for_status()
            cert_data = r.json()
            
            certificate_pem = cert_data.get("certificate_pem", "")
            cert_serial = cert_data.get("serial", "N/A")
            not_after = cert_data.get("not_after", "N/A")
            is_revoked = cert_data.get("is_revoked", False)
            details = cert_data.get("details", {})

            # Extract first and last few lines of certificate
            cert_lines = certificate_pem.strip().split('\n') if certificate_pem else []
            if len(cert_lines) > 10:
                # Show first 3 lines, ..., last 3 lines
                cert_preview = '\n'.join(cert_lines[:3]) + '\n... [certificate data truncated] ...\n' + '\n'.join(cert_lines[-3:])
            else:
                cert_preview = certificate_pem
            
            # Get certificate status and formatting
            status_emoji = "⚠️ REVOKED" if is_revoked else "✅ ACTIVE"
            status_color = "red" if is_revoked else "green"
            
            # Extract subject info from details
            subject_info = details.get("subject", {})
            cn = subject_info.get("commonName", self.system.current_user)
            org = subject_info.get("organizationName", "SecureShare")
            
            issuer = details.get("issuer", "CN=SecureShare Root CA")
            signature_algo = details.get("signature_algorithm", "sha256WithRSAEncryption")
            
            # Build certificate display
            cert_info = f"""╔═══════════════════════════════════════════════════════════════╗
║                  X.509 DIGITAL CERTIFICATE                    ║
╚═══════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────┐
│ CERTIFICATE STATUS                                              │
└───────────────────────────────────────────────────────────────┘

  Status:               {status_emoji}
  Serial Number:        {cert_serial}
  Expiry Date:          {not_after[:10] if not_after != "N/A" else "N/A"}

┌───────────────────────────────────────────────────────────────┐
│ SUBJECT INFORMATION                                             │
└───────────────────────────────────────────────────────────────┘

  Common Name (CN):     {cn}
  Organization (O):     {org}
  
┌───────────────────────────────────────────────────────────────┐
│ ISSUER INFORMATION                                              │
└───────────────────────────────────────────────────────────────┘

  Issuer:               {issuer}
  Signature Algorithm:  {signature_algo}
  
┌───────────────────────────────────────────────────────────────┐
│ CERTIFICATE (X.509 PEM FORMAT)                                  │
└───────────────────────────────────────────────────────────────┘

{cert_preview}

┌───────────────────────────────────────────────────────────────┐
│ PRIVATE KEY PROTECTION                                          │
└───────────────────────────────────────────────────────────────┘

  Status:               Encrypted with user password
  Encryption:           Fernet (AES-128-CBC)
  Key Derivation:       Scrypt (N=16384, r=8, p=1)
  Storage:              Secure database (encrypted)
  
┌───────────────────────────────────────────────────────────────┐
│ KEY USAGE                                                       │
└───────────────────────────────────────────────────────────────┘

  • Digital Signature    - Sign files and messages
  • Key Encipherment     - Encrypt symmetric keys
  • Non-Repudiation      - Prove file authorship
  
┌───────────────────────────────────────────────────────────────┐
│ SECURITY NOTES                                                  │
└───────────────────────────────────────────────────────────────┘

  • Certificate issued by trusted CA
  • Public key extracted from certificate
  • Private key never leaves server unencrypted
  • Certificate validated on every login
  • Revocation checked via CRL
  • Keep your password secure - it cannot be recovered

╔═══════════════════════════════════════════════════════════════╗
║                     END OF CERTIFICATE                        ║
╚═══════════════════════════════════════════════════════════════╝
"""
            
            text_widget.insert('1.0', cert_info)
            text_widget.config(state=tk.DISABLED)  # Make read-only

        except Exception as e:
            error_msg = f"""╔═══════════════════════════════════════════════════════════════╗
║                         ERROR                                 ║
╚═══════════════════════════════════════════════════════════════╝

Failed to load certificate information.

Error: {str(e)}

Please ensure you are logged in and the backend is running.
"""
            text_widget.insert('1.0', error_msg)
            text_widget.config(state=tk.DISABLED)

    def logout(self):
        self.system.logout()
        self.current_password = None
        self.show_welcome_screen()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureShareApp(root)
    root.mainloop()