import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import subprocess
from core.secure_share import SecureShareSystem


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
        if self.system.login_user(username, password):
            self.current_password = password
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def do_register(self):
        username = self.reg_username.get().strip()
        p1, p2 = self.reg_password.get(), self.reg_confirm.get()
        if p1 == p2 and len(p1) >= 8:
            if self.system.register_user(username, p1):
                messagebox.showinfo("Success", "Account created!")
                self.show_welcome_screen()
            else:
                messagebox.showerror("Error", "Username taken")
        else:
            messagebox.showerror("Error", "Passwords must match and be 8+ chars")

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
        others = [u for u in self.system.get_all_users() if u != self.system.current_user]
        self.recip_vars = {}
        for i, user in enumerate(others):
            var = tk.BooleanVar()
            ttk.Checkbutton(recip_frame, text=user, variable=var).grid(row=i//4, column=i%4, sticky=tk.W, padx=15, pady=5)
            self.recip_vars[user] = var
        ttk.Button(tab, text="Encrypt & Share", style='Accent.TButton', command=self.do_share_file).pack(pady=30)

    def browse_file(self):
        """Cross-platform file chooser: Windows Tk dialog, Linux Zenity fallback"""
        path = None
        if os.name == 'posix':  # Linux
            try:
                result = subprocess.run(
                    ["zenity", "--file-selection", "--title=Select a file", "--filename=" + str(Path.home()) + "/"],
                    capture_output=True, text=True
                )
                path = result.stdout.strip()
            except Exception:
                path = None
        if not path:
            # Windows or fallback
            path = filedialog.askopenfilename(initialdir=str(Path.home()))
        if path:
            self.share_path_var.set(path)

    def do_share_file(self):
        path = self.share_path_var.get()
        recipients = [u for u, v in self.recip_vars.items() if v.get()]
        if path and recipients:
            if self.system.share_file(path, recipients, self.current_password):
                messagebox.showinfo("Success", "File shared!")
                self.refresh_files_list()
            else:
                messagebox.showerror("Error", "Sharing failed")

    def create_files_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="My Files")
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        cols = ("ID", "Filename", "Owner", "Date")
        self.files_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols: self.files_tree.heading(c, text=c)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Download", style='Accent.TButton', command=self.do_download).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_files_list).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Revoke Access", command=self.do_revoke_access).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Delete File", command=self.do_delete_file).pack(side=tk.LEFT, padx=10)

        self.refresh_files_list()

    def do_revoke_access(self):
        sel = self.files_tree.selection()
        if not sel: return
        file_id = sel[0]
        if messagebox.askyesno("Revoke", "Revoke access for all other users?"):
            if self.system.db.revoke_all_except_owner(file_id, self.system.current_user):
                messagebox.showinfo("Success", "Access revoked.")
                self.refresh_files_list()

    def do_delete_file(self):
        sel = self.files_tree.selection()
        if not sel: return
        file_id = sel[0]
        if messagebox.askyesno("Delete", "Delete this file permanently?"):
            if self.system.db.delete_file(file_id, self.system.current_user):
                messagebox.showinfo("Success", "File deleted.")
                self.refresh_files_list()
            else:
                messagebox.showerror("Error", "Only the owner can delete this file.")

    def refresh_files_list(self):
        for i in self.files_tree.get_children(): self.files_tree.delete(i)
        for f in self.system.get_shared_files():
            self.files_tree.insert("", tk.END, iid=f.file_id, values=(f.file_id[:8], f.filename, f.owner, f.timestamp[:10]))

    def do_download(self):
        sel = self.files_tree.selection()
        if sel:
            file_id = sel[0]
            filename = self.files_tree.item(file_id)['values'][1]
            path = filedialog.asksaveasfilename(initialfile=filename)
            if path:
                if self.system.download_file(file_id, path, self.current_password):
                    messagebox.showinfo("Success", "File decrypted and saved!")
                else:
                    messagebox.showerror("Error", "Download/Decryption failed")

    def create_users_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Users")
        tree = ttk.Treeview(tab, columns=("User"), show="headings")
        tree.heading("User", text="Username")
        tree.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        for u in self.system.get_all_users():
            tree.insert("", tk.END, values=(u,))

    def create_certificate_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Certificate")
        user_data = self.system.db.get_user(self.system.current_user)
        info = f"SUBJECT: {user_data['username']}\nPUBLIC KEY PEM:\n{user_data['public_key_pem'][:200]}..."
        ttk.Label(tab, text=info, font=('Courier New', 10), padding=30, justify=tk.LEFT).pack()

    def logout(self):
        self.system.current_user = None
        self.current_password = None
        self.show_welcome_screen()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureShareApp(root)
    root.mainloop()
