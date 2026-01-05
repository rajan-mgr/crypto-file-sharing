import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import base64
from core.secure_share import SecureShareSystem


class SecureShareApp:
    def __init__(self, root):
        self.root = root
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

        self.system = SecureShareSystem()
        self.current_password = None

        self.setup_styles()
        self.main_container = ttk.Frame(root, padding="30")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.show_login_screen()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

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

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

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

    def logout(self):
        self.system.current_user = None
        self.current_password = None
        self.show_login_screen()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureShareApp(root)
    root.mainloop()