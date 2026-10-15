"""APEX GARAGE PRO — dashboard desktop untuk manajemen bengkel."""
import csv
import sqlite3
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from database import Database
from effects import (GradientText, Hero, Palette, Splash, animate, confetti, count_up, curtain, donut, fade_in, hover, lerp,
                     toast as show_toast)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg": "#0A101A", "sidebar": "#0D1522", "panel": "#111C2B",
    "panel2": "#162438", "line": "#26364B", "text": "#F3F7FC",
    "muted": "#9BAEC4", "blue": "#2878FF", "blue_hover": "#1D64DF",
    "cyan": "#42D9F5", "green": "#2DD4A7", "yellow": "#F6BE4F",
    "red": "#FF6878", "purple": "#A78BFA", "white": "#FFFFFF",
}
STATUSES = ["Menunggu", "Sedang Dikerjakan", "Menunggu Suku Cadang", "Selesai", "Diambil Pelanggan"]
PAYMENT_METHODS = ["Tunai", "Transfer", "QRIS", "Kartu Debit"]


def rupiah(value):
    try:
        return "Rp " + f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"


def make_id(prefix):
    return f"{prefix}-{datetime.now().strftime('%y%m%d-%H%M%S-%f')}"


class ApexGarageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # disembunyikan sampai loading screen selesai
        self.db = Database()
        self.title("APEX GARAGE PRO | Workshop Management")
        self.geometry("1440x900")
        self.minsize(1120, 720)
        self.configure(fg_color=C["bg"])
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._setup_tree_style()
        self._build_shell()
        self.after(40, lambda: Splash(self, self._reveal))

    def _reveal(self):
        try:
            self.attributes("-alpha", 0)
        except tk.TclError:
            pass
        self.deiconify()
        fade_in(self)
        self.show_page("Dashboard")
        self._tick()
        self._pulse()
        for key in ("<Control-k>", "<Control-K>"):
            self.bind_all(key, lambda _e: self.open_palette())
        for i, nm in enumerate(self.nav_buttons, 1):
            self.bind_all(f"<Control-Key-{i}>", lambda _e, n=nm: self.show_page(n))

    def open_palette(self):
        if getattr(self, "_pal", None) is not None and self._pal.winfo_exists():
            self._pal.destroy()
            return
        cmds = [(f"Buka {n}", "Navigasi", lambda n=n: self.show_page(n)) for n in self.nav_buttons]
        cmds += [("Registrasi kendaraan baru", "Aksi", self.dialog_vehicle), ("Tambah pelanggan", "Aksi", self.dialog_customer),
                 ("Buat order servis", "Aksi", self.dialog_service)]
        self._pal = Palette(self, cmds)

    def toast(self, message, color=None):
        show_toast(self, message, color or C["green"])

    def _tick(self):
        self.clock_lbl.configure(text=datetime.now().strftime("◷  %d %b %Y  ·  %H:%M:%S"))
        self.after(1000, self._tick)

    def _pulse(self, t=0):
        self.online_lbl.configure(text_color=lerp(C["panel"], C["green"], .45 + .55 * abs(((t % 40) - 20) / 20)))
        self.after(60, lambda: self._pulse(t + 1))

    def _setup_tree_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Apex.Treeview", background=C["panel"], foreground=C["text"],
                        fieldbackground=C["panel"], borderwidth=0, rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Apex.Treeview.Heading", background=C["panel2"], foreground=C["muted"],
                        relief="flat", borderwidth=0, font=("Segoe UI Semibold", 9))
        style.map("Apex.Treeview", background=[("selected", C["blue"])], foreground=[("selected", C["white"])])
        style.map("Apex.Treeview.Heading", background=[("active", C["panel2"])])

    def _build_shell(self):
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=C["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(25, 28))
        ctk.CTkLabel(brand, text="◆", font=("Segoe UI Symbol", 26, "bold"), text_color=C["cyan"]).pack(anchor="w")
        GradientText(brand, "APEX GARAGE", size=14, bg=C["sidebar"], animated=True).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(brand, text="PRO  /  WORKSHOP OS", font=("Segoe UI", 9, "bold"), text_color=C["muted"]).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(self.sidebar, text="WORKSPACE", font=("Segoe UI", 9, "bold"), text_color="#61758F").pack(anchor="w", padx=23, pady=(0, 9))
        nav_items = [
            ("Dashboard", "⌂"), ("Kendaraan", "▣"), ("Pelanggan", "♙"),
            ("Servis & Perbaikan", "⚙"), ("Pembayaran", "＄"), ("Laporan", "▤"),
        ]
        self.nav_buttons = {}
        for label, icon in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=f"{icon}     {label}", anchor="w", height=44,
                                corner_radius=10, font=("Segoe UI", 12, "bold"),
                                fg_color="transparent", hover_color=C["panel2"], text_color=C["muted"],
                                command=lambda page=label: self.show_page(page))
            btn.pack(fill="x", padx=13, pady=3)
            self.nav_buttons[label] = btn

        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        status_card = ctk.CTkFrame(self.sidebar, fg_color=C["panel"], corner_radius=12, border_width=1, border_color=C["line"])
        status_card.pack(fill="x", padx=14, pady=(12, 18))
        self.online_lbl = ctk.CTkLabel(status_card, text="●  SYSTEM ONLINE", text_color=C["green"], font=("Segoe UI", 10, "bold"))
        self.online_lbl.pack(anchor="w", padx=13, pady=(13, 2))
        ctk.CTkLabel(status_card, text="Local database · SQLite", text_color=C["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=13, pady=(0, 13))
        ctk.CTkLabel(self.sidebar, text="APEX GARAGE PRO  •  v1.2", text_color="#61758F", font=("Segoe UI", 9)).pack(pady=(0, 17))

        self.workspace = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.workspace.pack(side="left", fill="both", expand=True)
        self.topbar = ctk.CTkFrame(self.workspace, height=76, corner_radius=0, fg_color=C["bg"])
        self.topbar.pack(fill="x", padx=28, pady=(14, 3))
        self.topbar.pack_propagate(False)
        self.top_title = ctk.CTkLabel(self.topbar, text="Dashboard", font=("Segoe UI", 22, "bold"), text_color=C["text"])
        self.top_title.pack(side="left", anchor="center")
        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.pack(side="right", anchor="center")
        today = date.today().strftime("%d %b %Y")
        ctk.CTkButton(right, text="⌕  Cari cepat   Ctrl+K", width=150, height=32, corner_radius=9, fg_color=C["panel"], hover_color=C["panel2"],
                      border_width=1, border_color=C["line"], text_color=C["muted"], font=("Segoe UI", 10),
                      command=lambda: self.open_palette()).pack(side="left", padx=(0, 14))
        self.clock_lbl = ctk.CTkLabel(right, text=f"◷  {today}", text_color=C["muted"], font=("Segoe UI", 11))
        self.clock_lbl.pack(side="left", padx=(0, 16))
        profile = ctk.CTkFrame(right, fg_color=C["panel"], corner_radius=12, border_width=1, border_color=C["line"])
        profile.pack(side="left")
        ctk.CTkLabel(profile, text="A", width=34, height=34, corner_radius=10, fg_color=C["blue"], text_color="white", font=("Segoe UI", 13, "bold")).pack(side="left", padx=6, pady=5)
        ctk.CTkLabel(profile, text="Administrator", text_color=C["text"], font=("Segoe UI", 10, "bold")).pack(side="left", padx=(3, 12))
        self.page = ctk.CTkScrollableFrame(self.workspace, fg_color=C["bg"], corner_radius=0)
        self.page.pack(fill="both", expand=True, padx=28, pady=(0, 18))

    def show_page(self, name):
        self.current_page = name
        animate(self.top_title, lambda pr: self.top_title.configure(text=name[:max(1, int(len(name) * pr + .5))]), 14)
        for label, button in self.nav_buttons.items():
            active = label == name
            button.configure(fg_color=C["blue"] if active else "transparent",
                             text_color=C["white"] if active else C["muted"],
                             hover_color=C["blue_hover"] if active else C["panel2"])
        self.update_idletasks()
        btn = self.nav_buttons[name]
        y1 = btn.winfo_y() + (btn.winfo_height() - 26) // 2
        if not hasattr(self, "nav_ind"):
            self.nav_ind = ctk.CTkFrame(self.sidebar, width=4, height=26, corner_radius=2, fg_color=C["cyan"])
            self._ind_y = y1
        y0, self._ind_y = self._ind_y, y1
        animate(self.nav_ind, lambda pr: (self.nav_ind.place(x=0, y=int(y0 + (y1 - y0) * pr)), self.nav_ind.lift()), 16)
        for child in self.page.winfo_children():
            child.destroy()
        page_methods = {
            "Dashboard": self.page_dashboard, "Kendaraan": self.page_vehicles,
            "Pelanggan": self.page_customers, "Servis & Perbaikan": self.page_services,
            "Pembayaran": self.page_payments, "Laporan": self.page_reports,
        }
        page_methods[name]()
        curtain(self.page, self.workspace, C["bg"])

    def _heading(self, title, subtitle, button_text=None, command=None):
        row = ctk.CTkFrame(self.page, fg_color="transparent")
        row.pack(fill="x", pady=(8, 19))
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        GradientText(left, title, size=15, bg=C["bg"]).pack(anchor="w")
        ctk.CTkLabel(left, text=subtitle, font=("Segoe UI", 11), text_color=C["muted"]).pack(anchor="w", pady=(4, 0))
        if button_text:
            self._button(row, button_text, command, primary=True).pack(side="right", padx=(10, 0), pady=3)
        return row

    def _button(self, parent, text, command, primary=False, danger=False, width=None):
        color = C["red"] if danger else C["blue"] if primary else C["panel2"]
        hover = "#E24F63" if danger else C["blue_hover"] if primary else "#20334C"
        return ctk.CTkButton(parent, text=text, command=command, height=38, width=width or 120,
                             corner_radius=9, fg_color=color, hover_color=hover,
                             text_color=C["white"], font=("Segoe UI", 11, "bold"))

    def _card(self, parent, title=None, subtitle=None):
        card = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=14, border_width=1, border_color=C["line"])
        if title:
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(anchor="w", padx=17, pady=(15, 0))
        if subtitle:
            ctk.CTkLabel(card, text=subtitle, font=("Segoe UI", 10), text_color=C["muted"]).pack(anchor="w", padx=17, pady=(3, 0))
        return card

    def _stat_card(self, parent, title, value, hint, accent, icon):
        card = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=14, border_width=1, border_color=C["line"])
        ctk.CTkFrame(card, height=3, fg_color=accent, corner_radius=3).pack(fill="x", padx=15, pady=(13, 0))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(top, text=title, text_color=C["muted"], font=("Segoe UI", 10, "bold")).pack(side="left")
        ctk.CTkLabel(top, text=icon, text_color=accent, font=("Segoe UI Symbol", 19, "bold")).pack(side="right")
        value_lbl = ctk.CTkLabel(card, text=value, text_color=C["text"], font=("Segoe UI", 24, "bold"))
        value_lbl.pack(anchor="w", padx=16, pady=(7, 0))
        count_up(value_lbl, value)
        ctk.CTkLabel(card, text=hint, text_color=accent, font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(3, 15))
        hover(card, {"border_color": accent}, {"border_color": C["line"]})
        return card

    def _tree(self, parent, columns, headings, widths=None, height=9):
        wrapper = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=11)
        wrapper.pack(fill="both", expand=True, padx=12, pady=(12, 13))
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", style="Apex.Treeview", height=height, selectmode="browse")
        for i, (col, heading) in enumerate(zip(columns, headings)):
            tree.heading(col, text=heading)
            tree.column(col, width=(widths[i] if widths else 130), minwidth=70, anchor="w", stretch=True)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=7)
        scrollbar.pack(side="right", fill="y", padx=(0, 7), pady=7)
        tree.tag_configure("waiting", foreground=C["yellow"])
        tree.tag_configure("active", foreground=C["cyan"])
        tree.tag_configure("done", foreground=C["green"])
        tree.tag_configure("danger", foreground=C["red"])
        tree.tag_configure("hover", background="#1A2B44")
        hov = {"row": None}

        def on_move(e):
            row = tree.identify_row(e.y)
            if row == hov["row"]:
                return
            if hov["row"] and tree.exists(hov["row"]):
                tree.item(hov["row"], tags=tuple(t for t in tree.item(hov["row"], "tags") if t != "hover"))
            hov["row"] = row or None
            if row:
                tree.item(row, tags=tuple(tree.item(row, "tags")) + ("hover",))
        tree.bind("<Motion>", on_move)
        tree.bind("<Leave>", lambda _e: on_move(type("E", (), {"y": -1})()))
        return tree

    def _select_id(self, tree, label="data"):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Pilih data", f"Pilih {label} pada tabel terlebih dahulu.", parent=self)
            return None
        return tree.item(selection[0], "values")[0]

    # DASHBOARD
    def page_dashboard(self):
        stats = self.db.dashboard_stats()
        self._heading("Overview", "Pantau performa bengkel dan aktivitas servis hari ini.", "+ Buat Servis", self.dialog_service)
        hr = datetime.now().hour
        sap = "Selamat pagi" if hr < 11 else "Selamat siang" if hr < 15 else "Selamat sore" if hr < 19 else "Selamat malam"
        Hero(self.page, f"{sap}, Administrator 👋",
             f"{stats['active']} servis berjalan  ·  {stats['today_services']} order masuk hari ini  ·  pendapatan {rupiah(stats['revenue'])}",
             stats["active"]).pack(fill="x", pady=(0, 16))
        grid = ctk.CTkFrame(self.page, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1, uniform="stats")
        cards = [
            ("Total Kendaraan", str(stats["vehicles"]), "Data terdaftar", C["cyan"], "▣"),
            ("Pelanggan", str(stats["customers"]), "Pelanggan tersimpan", C["purple"], "♙"),
            ("Servis Berjalan", str(stats["active"]), "Perlu ditindaklanjuti", C["yellow"], "⚙"),
            ("Pendapatan Hari Ini", rupiah(stats["revenue"]), f"{stats['today_services']} order masuk hari ini", C["green"], "↗"),
        ]
        for i, args in enumerate(cards):
            self._stat_card(grid, *args).grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 7 if i < 3 else 0), pady=(0, 16))

        mid = ctk.CTkFrame(self.page, fg_color="transparent")
        mid.pack(fill="both", expand=True)
        mid.grid_columnconfigure(0, weight=4, uniform="mid")
        mid.grid_columnconfigure(1, weight=2, uniform="mid")
        mid.grid_columnconfigure(2, weight=3, uniform="mid")
        chart_card = self._card(mid, "Pendapatan 7 Hari", "Total pembayaran yang tercatat per hari")
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 15))
        self._draw_chart(chart_card, self.db.revenue_last_seven_days())
        quick_card = self._card(mid, "Aksi Cepat", "Pintasan aktivitas operasional")
        quick_card.grid(row=0, column=1, sticky="nsew", padx=(8, 8), pady=(0, 15))
        with self.db.connect() as conn:
            counts = {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM servis GROUP BY status")}
        donut_card = self._card(mid, "Status Servis", "Distribusi order saat ini")
        donut_card.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=(0, 15))
        donut(donut_card, [("Menunggu", counts.get("Menunggu", 0), C["yellow"]), ("Dikerjakan", counts.get("Sedang Dikerjakan", 0), C["cyan"]),
                           ("Tunggu Part", counts.get("Menunggu Suku Cadang", 0), C["purple"]), ("Selesai", counts.get("Selesai", 0), C["green"]),
                           ("Diambil", counts.get("Diambil Pelanggan", 0), "#5B7BA6")]).pack(fill="x", expand=True, padx=15, pady=(12, 10))
        for text, subtitle, color, fn in [
            ("＋  Registrasi Kendaraan", "Tambahkan kendaraan ke sistem", C["cyan"], self.dialog_vehicle),
            ("♙  Tambah Pelanggan", "Simpan informasi pelanggan", C["purple"], self.dialog_customer),
            ("⚙  Order Servis Baru", "Catat keluhan dan pekerjaan", C["green"], self.dialog_service),
        ]:
            item = ctk.CTkFrame(quick_card, fg_color=C["panel2"], corner_radius=10)
            item.pack(fill="x", padx=13, pady=(12, 0))
            hover(item, {"fg_color": "#1E3350"}, {"fg_color": C["panel2"]})
            ctk.CTkLabel(item, text=text, text_color=color, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=13, pady=(10, 0))
            ctk.CTkLabel(item, text=subtitle, text_color=C["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=13, pady=(2, 10))
            item.bind("<Button-1>", lambda _e, f=fn: f())
            for child in item.winfo_children():
                child.bind("<Button-1>", lambda _e, f=fn: f())

        recent_card = self._card(self.page, "Servis Terbaru", "Order servis paling baru yang tercatat")
        recent_card.pack(fill="both", expand=True, pady=(0, 15))
        tree = self._tree(recent_card, ("id", "tanggal", "pelanggan", "kendaraan", "status", "total"),
                          ("ID SERVIS", "TANGGAL", "PELANGGAN", "KENDARAAN / PLAT", "STATUS", "TOTAL"),
                          (150, 100, 170, 180, 160, 130), height=4)
        for row in self.db.list_services()[:5]:
            tag = "done" if row["status"] in ("Selesai", "Diambil Pelanggan") else "waiting" if row["status"] == "Menunggu" else "active"
            tree.insert("", "end", values=(row["id_servis"], row["tanggal_masuk"], row["nama_pelanggan"], f"{row['merk']} {row['model']} · {row['plat_nomor']}", row["status"], rupiah(row["total_biaya"])), tags=(tag,))
        if not tree.get_children():
            ctk.CTkLabel(recent_card, text="Belum ada order servis. Mulai dari tombol + Buat Servis.", text_color=C["muted"]).pack(pady=10)

    def _draw_chart(self, parent, values):
        canvas = tk.Canvas(parent, height=235, bg=C["panel"], highlightthickness=0, bd=0)
        canvas.pack(fill="x", expand=True, padx=15, pady=(12, 10))

        state = {"p": 0.0}

        def draw(_event=None):
            canvas.delete("all")
            w = max(canvas.winfo_width(), 300)
            h = max(canvas.winfo_height(), 200)
            left, right, top, bottom = 54, w - 20, 20, h - 34
            max_value = max([v for _, v in values] + [1])
            for j in range(4):
                y = top + (bottom - top) * j / 3
                canvas.create_line(left, y, right, y, fill=C["line"], dash=(3, 5))
            gap = (right - left) / max(len(values), 1)
            for i, (day, amount) in enumerate(values):
                x_center = left + gap * (i + 0.5)
                bar_h = max(3, (bottom - top) * (amount / max_value) * state["p"]) if amount else 3
                canvas.create_rectangle(x_center - min(18, gap * .28), bottom - bar_h, x_center + min(18, gap * .28), bottom,
                                        fill=C["blue"] if i < len(values)-1 else C["cyan"], outline="")
                if amount:
                    short = f"{amount/1_000_000:.1f}jt" if amount >= 1_000_000 else f"{amount/1000:.0f}k" if amount >= 1000 else str(amount)
                    canvas.create_text(x_center, max(top + 4, bottom - bar_h - 12), text=short, fill=C["muted"], font=("Segoe UI", 8))
                canvas.create_text(x_center, bottom + 16, text=day, fill=C["muted"], font=("Segoe UI", 9))
            canvas.create_text(3, top + 4, text="IDR", fill=C["muted"], anchor="nw", font=("Segoe UI", 8))
        canvas.bind("<Configure>", draw)
        self.after(60, lambda: animate(canvas, lambda pr: (state.update(p=pr), draw()), 24))

    # KENDARAAN
    def page_vehicles(self):
        self._heading("Data Kendaraan", "Kelola registrasi kendaraan pelanggan.", "+ Kendaraan Baru", self.dialog_vehicle)
        controls = ctk.CTkFrame(self.page, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        search = ctk.CTkEntry(controls, placeholder_text="Cari ID, merek, model, atau plat nomor…", width=340, height=38,
                              fg_color=C["panel"], border_color=C["line"], text_color=C["text"])
        search.pack(side="left")
        kind = ctk.CTkOptionMenu(controls, values=["Semua", "Mobil", "Motor"], width=135, height=38,
                                 fg_color=C["panel2"], button_color=C["blue"], command=lambda _v: refresh())
        kind.set("Semua")
        kind.pack(side="left", padx=9)
        count_label = ctk.CTkLabel(controls, text="", text_color=C["muted"], font=("Segoe UI", 10))
        count_label.pack(side="right")
        card = self._card(self.page, "Registrasi Kendaraan", "Pilih baris untuk mengedit atau menghapus data")
        card.pack(fill="both", expand=True)
        tree = self._tree(card, ("id", "merk", "model", "tahun", "plat", "jenis", "status"),
                          ("ID KENDARAAN", "MEREK", "MODEL", "TAHUN", "PLAT NOMOR", "JENIS", "STATUS"),
                          (155, 120, 150, 75, 130, 90, 130), height=12)
        action = ctk.CTkFrame(card, fg_color="transparent")
        action.pack(fill="x", padx=13, pady=(0, 13))
        self._button(action, "Edit Data", lambda: self._edit_selected_vehicle(tree)).pack(side="left", padx=(0, 7))
        self._button(action, "Hapus", lambda: self._delete_selected_vehicle(tree), danger=True).pack(side="left")

        def refresh(*_):
            tree.delete(*tree.get_children())
            rows = self.db.list_vehicles(search.get().strip(), kind.get())
            for r in rows:
                tree.insert("", "end", values=(r["id_kendaraan"], r["merk"], r["model"], r["tahun"], r["plat_nomor"], r["jenis"], r["status"]))
            count_label.configure(text=f"{len(rows)} kendaraan")
        search.bind("<KeyRelease>", refresh)
        refresh()
        self._vehicles_refresh = refresh

    def _edit_selected_vehicle(self, tree):
        vid = self._select_id(tree, "kendaraan")
        if vid:
            row = next((r for r in self.db.list_vehicles() if r["id_kendaraan"] == vid), None)
            if row:
                self.dialog_vehicle(row)

    def _delete_selected_vehicle(self, tree):
        vid = self._select_id(tree, "kendaraan")
        if not vid:
            return
        if messagebox.askyesno("Konfirmasi", f"Hapus kendaraan {vid}?", parent=self):
            try:
                self.db.delete_vehicle(vid)
                self.show_page("Kendaraan")
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror("Tidak bisa menghapus", str(exc), parent=self)

    def dialog_vehicle(self, row=None):
        edit = row is not None
        win = self._dialog("Edit Kendaraan" if edit else "Registrasi Kendaraan", "Lengkapi informasi kendaraan di bawah.")
        fields = [
            ("ID Kendaraan", row["id_kendaraan"] if edit else make_id("KDR")),
            ("Merek", row["merk"] if edit else ""), ("Model", row["model"] if edit else ""),
            ("Tahun", row["tahun"] if edit else ""), ("Plat Nomor", row["plat_nomor"] if edit else ""),
            ("Nomor Rangka (opsional)", row["nomor_rangka"] if edit else ""),
        ]
        entries = {}
        grid = ctk.CTkFrame(win, fg_color="transparent")
        grid.pack(fill="x", padx=22, pady=(4, 8))
        for i, (label, value) in enumerate(fields):
            ctk.CTkLabel(grid, text=label, text_color=C["muted"], font=("Segoe UI", 10, "bold")).grid(row=i//2*2, column=i%2, sticky="w", padx=(0 if i%2==0 else 10, 0), pady=(8, 4))
            entry = ctk.CTkEntry(grid, height=37, width=220, fg_color=C["panel2"], border_color=C["line"])
            entry.insert(0, str(value))
            entry.grid(row=i//2*2+1, column=i%2, sticky="ew", padx=(0 if i%2==0 else 10, 0), pady=(0, 4))
            entries[label] = entry
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(grid, text="Jenis Kendaraan", text_color=C["muted"], font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="w", pady=(8, 4))
        jenis = ctk.CTkOptionMenu(grid, values=["Mobil", "Motor"], fg_color=C["panel2"], button_color=C["blue"])
        jenis.set(row["jenis"] if edit else "Mobil")
        jenis.grid(row=7, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(grid, text="Status", text_color=C["muted"], font=("Segoe UI", 10, "bold")).grid(row=6, column=1, sticky="w", padx=(10, 0), pady=(8, 4))
        status = ctk.CTkOptionMenu(grid, values=["Tersedia", "Dalam Servis", "Tidak Aktif"], fg_color=C["panel2"], button_color=C["blue"])
        status.set(row["status"] if edit else "Tersedia")
        status.grid(row=7, column=1, sticky="ew", padx=(10, 0))

        def save():
            vals = [entries[k].get().strip() for k, _ in fields]
            if not all(vals[i] for i in range(5)):
                messagebox.showwarning("Input belum lengkap", "ID, merek, model, tahun, dan plat nomor wajib diisi.", parent=win)
                return
            data = [vals[0], vals[1], vals[2], vals[3], vals[4], jenis.get(), status.get(), vals[5]]
            try:
                self.db.save_vehicle(data, row["id_kendaraan"] if edit else None)
            except sqlite3.IntegrityError:
                messagebox.showerror("ID sudah digunakan", "ID kendaraan tersebut sudah terdaftar. Gunakan ID yang berbeda.", parent=win)
                return
            except sqlite3.Error as exc:
                messagebox.showerror("Database error", str(exc), parent=win)
                return
            win.destroy()
            self.show_page("Kendaraan")
            self.toast("Data kendaraan tersimpan")
        self._dialog_actions(win, save)

    # PELANGGAN
    def page_customers(self):
        self._heading("Data Pelanggan", "Simpan kontak pelanggan agar proses servis lebih tertata.", "+ Pelanggan Baru", self.dialog_customer)
        controls = ctk.CTkFrame(self.page, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        search = ctk.CTkEntry(controls, placeholder_text="Cari nama, ID, atau nomor telepon…", width=360, height=38, fg_color=C["panel"], border_color=C["line"])
        search.pack(side="left")
        card = self._card(self.page, "Database Pelanggan", "Informasi pelanggan yang telah didaftarkan")
        card.pack(fill="both", expand=True)
        tree = self._tree(card, ("id", "nama", "hp", "alamat", "kendaraan"), ("ID PELANGGAN", "NAMA", "NO. TELEPON", "ALAMAT", "KENDARAAN"), (170, 190, 150, 280, 100), height=12)
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=13, pady=(0, 13))
        self._button(actions, "Edit Data", lambda: self._edit_selected_customer(tree)).pack(side="left", padx=(0, 7))
        self._button(actions, "Hapus", lambda: self._delete_selected_customer(tree), danger=True).pack(side="left")

        def refresh(*_):
            tree.delete(*tree.get_children())
            for r in self.db.list_customers(search.get().strip()):
                tree.insert("", "end", values=(r["id_pelanggan"], r["nama"], r["no_hp"], r["alamat"] or "—", r["jumlah_kendaraan"]))
        search.bind("<KeyRelease>", refresh)
        refresh()

    def _edit_selected_customer(self, tree):
        cid = self._select_id(tree, "pelanggan")
        if cid:
            row = next((r for r in self.db.list_customers() if r["id_pelanggan"] == cid), None)
            if row:
                self.dialog_customer(row)

    def _delete_selected_customer(self, tree):
        cid = self._select_id(tree, "pelanggan")
        if cid and messagebox.askyesno("Konfirmasi", f"Hapus pelanggan {cid}?", parent=self):
            try:
                self.db.delete_customer(cid)
                self.show_page("Pelanggan")
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror("Tidak bisa menghapus", str(exc), parent=self)

    def dialog_customer(self, row=None):
        edit = row is not None
        win = self._dialog("Edit Pelanggan" if edit else "Pelanggan Baru", "Masukkan kontak pelanggan dengan benar.")
        data = [("ID Pelanggan", row["id_pelanggan"] if edit else make_id("PLG")),
                ("Nama Lengkap", row["nama"] if edit else ""),
                ("Nomor Telepon", row["no_hp"] if edit else ""),
                ("Alamat (opsional)", row["alamat"] if edit else "")]
        entries = {}
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=6)
        for i, (label, value) in enumerate(data):
            ctk.CTkLabel(body, text=label, text_color=C["muted"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(7, 3))
            e = ctk.CTkEntry(body, height=38, fg_color=C["panel2"], border_color=C["line"])
            e.insert(0, str(value))
            e.pack(fill="x")
            entries[label] = e
        def save():
            values = [entries[k].get().strip() for k, _ in data]
            if not all(values[:3]):
                messagebox.showwarning("Input belum lengkap", "ID, nama, dan nomor telepon wajib diisi.", parent=win)
                return
            try:
                self.db.save_customer(values, row["id_pelanggan"] if edit else None)
            except sqlite3.IntegrityError:
                messagebox.showerror("ID sudah digunakan", "ID pelanggan sudah terdaftar.", parent=win)
                return
            except sqlite3.Error as exc:
                messagebox.showerror("Database error", str(exc), parent=win)
                return
            win.destroy()
            self.show_page("Pelanggan")
            self.toast("Data pelanggan tersimpan")
        self._dialog_actions(win, save)

    # SERVIS
    def page_services(self):
        self._heading("Servis & Perbaikan", "Pantau order, status pengerjaan, dan estimasi biaya.", "+ Buat Servis", self.dialog_service)
        controls = ctk.CTkFrame(self.page, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        search = ctk.CTkEntry(controls, placeholder_text="Cari ID servis, pelanggan, plat, keluhan…", width=330, height=38, fg_color=C["panel"], border_color=C["line"])
        search.pack(side="left")
        status_filter = ctk.CTkOptionMenu(controls, values=["Semua"] + STATUSES, width=200, height=38, fg_color=C["panel2"], button_color=C["blue"], command=lambda _v: refresh())
        status_filter.set("Semua")
        status_filter.pack(side="left", padx=9)
        card = self._card(self.page, "Workshop Board", "Pilih order untuk mengubah statusnya")
        card.pack(fill="both", expand=True)
        tree = self._tree(card, ("id", "tanggal", "pelanggan", "kendaraan", "keluhan", "mekanik", "status", "total"),
                          ("ID SERVIS", "MASUK", "PELANGGAN", "KENDARAAN / PLAT", "KELUHAN", "MEKANIK", "STATUS", "TOTAL"),
                          (155, 90, 145, 170, 180, 120, 160, 130), height=11)
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=13, pady=(0, 13))
        self._button(actions, "Ubah Status", lambda: self.dialog_status(tree), primary=True).pack(side="left", padx=(0, 7))
        self._button(actions, "Refresh", lambda: refresh()).pack(side="left")

        def refresh(*_):
            tree.delete(*tree.get_children())
            for r in self.db.list_services(search.get().strip(), status_filter.get()):
                tag = "done" if r["status"] in ("Selesai", "Diambil Pelanggan") else "waiting" if r["status"] == "Menunggu" else "active"
                tree.insert("", "end", values=(r["id_servis"], r["tanggal_masuk"], r["nama_pelanggan"], f"{r['merk']} {r['model']} · {r['plat_nomor']}", r["keluhan"], r["mekanik"], r["status"], rupiah(r["total_biaya"])), tags=(tag,))
        search.bind("<KeyRelease>", refresh)
        refresh()

    def dialog_service(self):
        customers = self.db.customers_for_combo()
        vehicles = self.db.vehicles_for_combo()
        if not customers:
            messagebox.showinfo("Pelanggan dibutuhkan", "Tambahkan data pelanggan terlebih dahulu sebelum membuat order servis.", parent=self)
            self.show_page("Pelanggan")
            return
        if not vehicles:
            messagebox.showinfo("Kendaraan dibutuhkan", "Tambahkan data kendaraan terlebih dahulu sebelum membuat order servis.", parent=self)
            self.show_page("Kendaraan")
            return
        win = self._dialog("Buat Order Servis", "Buat tiket pekerjaan baru untuk pelanggan.", width=710)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=(2, 4))
        body.grid_columnconfigure(0, weight=1, uniform="forms")
        body.grid_columnconfigure(1, weight=1, uniform="forms")
        customer_map = {f"{r['id_pelanggan']}  ·  {r['nama']}": r["id_pelanggan"] for r in customers}
        vehicle_map = {f"{r['id_kendaraan']}  ·  {r['merk']} {r['model']} / {r['plat_nomor']}": r["id_kendaraan"] for r in vehicles}
        fields = {}
        def label_field(text, row, col, kind="entry", values=None, default=""):
            ctk.CTkLabel(body, text=text, text_color=C["muted"], font=("Segoe UI", 10, "bold")).grid(row=row*2, column=col, sticky="w", padx=(0, 10), pady=(8, 4))
            if kind == "combo":
                widget = ctk.CTkComboBox(body, values=values or [], height=37, fg_color=C["panel2"], border_color=C["line"], button_color=C["blue"])
                widget.set(default or (values[0] if values else ""))
            else:
                widget = ctk.CTkEntry(body, height=37, fg_color=C["panel2"], border_color=C["line"])
                widget.insert(0, default)
            widget.grid(row=row*2+1, column=col, sticky="ew", padx=(0, 10), pady=(0, 3))
            fields[text] = widget
            return widget
        label_field("Pelanggan", 0, 0, "combo", list(customer_map))
        label_field("Kendaraan", 0, 1, "combo", list(vehicle_map))
        label_field("Tanggal Masuk (YYYY-MM-DD)", 1, 0, default=date.today().isoformat())
        label_field("Estimasi Selesai (opsional)", 1, 1, default="")
        label_field("Keluhan Pelanggan", 2, 0)
        label_field("Jenis Servis", 2, 1, "combo", ["Servis Berkala", "Ganti Oli", "Perbaikan Mesin", "Rem", "Ban & Kaki-kaki", "Kelistrikan", "AC", "Lainnya"])
        label_field("Mekanik", 3, 0, default="Teknisi 1")
        label_field("Status Awal", 3, 1, "combo", STATUSES, "Menunggu")
        label_field("Biaya Jasa (Rp)", 4, 0, default="0")
        label_field("Biaya Suku Cadang (Rp)", 4, 1, default="0")
        label_field("Catatan Tambahan (opsional)", 5, 0)
        def save():
            customer_key = fields["Pelanggan"].get()
            vehicle_key = fields["Kendaraan"].get()
            complaint = fields["Keluhan Pelanggan"].get().strip()
            mechanic = fields["Mekanik"].get().strip()
            try:
                tanggal = fields["Tanggal Masuk (YYYY-MM-DD)"].get().strip()
                datetime.strptime(tanggal, "%Y-%m-%d")
                estimate = fields["Estimasi Selesai (opsional)"].get().strip()
                if estimate:
                    datetime.strptime(estimate, "%Y-%m-%d")
                labor = int(fields["Biaya Jasa (Rp)"].get().strip() or "0")
                parts = int(fields["Biaya Suku Cadang (Rp)"].get().strip() or "0")
                if labor < 0 or parts < 0:
                    raise ValueError("Biaya tidak boleh negatif.")
            except ValueError as exc:
                messagebox.showwarning("Periksa input", f"Tanggal harus berformat YYYY-MM-DD dan biaya harus bilangan bulat non-negatif.\n\nDetail: {exc}", parent=win)
                return
            if not complaint or not mechanic:
                messagebox.showwarning("Input belum lengkap", "Keluhan dan nama mekanik wajib diisi.", parent=win)
                return
            data = (make_id("SRV"), vehicle_map[vehicle_key], customer_map[customer_key], tanggal, complaint,
                    fields["Jenis Servis"].get(), mechanic, estimate, labor, parts, fields["Status Awal"].get(), fields["Catatan Tambahan (opsional)"].get().strip())
            try:
                self.db.create_service(data)
            except (sqlite3.Error, KeyError) as exc:
                messagebox.showerror("Gagal menyimpan order", str(exc), parent=win)
                return
            win.destroy()
            self.show_page("Servis & Perbaikan")
            self.toast("Order servis dibuat")
        self._dialog_actions(win, save)

    def dialog_status(self, tree):
        service_id = self._select_id(tree, "order servis")
        if not service_id:
            return
        row = next((r for r in self.db.list_services() if r["id_servis"] == service_id), None)
        if not row:
            return
        win = self._dialog("Perbarui Status Servis", f"Order {service_id}")
        ctk.CTkLabel(win, text=f"{row['nama_pelanggan']}  ·  {row['plat_nomor']}", text_color=C["muted"]).pack(anchor="w", padx=22, pady=(4, 12))
        status = ctk.CTkOptionMenu(win, values=STATUSES, height=38, fg_color=C["panel2"], button_color=C["blue"])
        status.set(row["status"])
        status.pack(fill="x", padx=22, pady=(0, 15))
        def save():
            self.db.update_service_status(service_id, status.get())
            win.destroy()
            self.show_page("Servis & Perbaikan")
            self.toast("Status servis diperbarui", C["cyan"])
        self._dialog_actions(win, save)

    # PEMBAYARAN
    def page_payments(self):
        self._heading("Pembayaran", "Catat pembayaran dan pantau sisa tagihan setiap order.")
        rows = self.db.list_services()
        total_due = sum(max(0, int(r["total_biaya"]) - int(r["sudah_dibayar"])) for r in rows)
        total_paid = sum(int(r["sudah_dibayar"]) for r in rows)
        stats = ctk.CTkFrame(self.page, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 15))
        for i in range(3): stats.grid_columnconfigure(i, weight=1, uniform="paystats")
        self._stat_card(stats, "Total Tagihan", rupiah(sum(int(r["total_biaya"]) for r in rows)), "Seluruh order servis", C["cyan"], "▤").grid(row=0, column=0, sticky="ew", padx=(0, 7))
        self._stat_card(stats, "Sudah Dibayar", rupiah(total_paid), "Akumulasi transaksi", C["green"], "✓").grid(row=0, column=1, sticky="ew", padx=7)
        self._stat_card(stats, "Sisa Tagihan", rupiah(total_due), "Belum diterima bengkel", C["yellow"], "◷").grid(row=0, column=2, sticky="ew", padx=(7, 0))
        card = self._card(self.page, "Tagihan Servis", "Pilih order yang masih memiliki sisa tagihan")
        card.pack(fill="both", expand=True, pady=(0, 15))
        tree = self._tree(card, ("id", "pelanggan", "plat", "status", "total", "paid", "due"),
                          ("ID SERVIS", "PELANGGAN", "PLAT NOMOR", "STATUS SERVIS", "TOTAL", "DIBAYAR", "SISA"),
                          (165, 180, 140, 155, 130, 130, 130), height=7)
        for r in rows:
            due = int(r["total_biaya"]) - int(r["sudah_dibayar"])
            tag = "done" if due <= 0 else "waiting"
            tree.insert("", "end", values=(r["id_servis"], r["nama_pelanggan"], r["plat_nomor"], r["status"], rupiah(r["total_biaya"]), rupiah(r["sudah_dibayar"]), rupiah(due)), tags=(tag,))
        action = ctk.CTkFrame(card, fg_color="transparent")
        action.pack(fill="x", padx=13, pady=(0, 13))
        self._button(action, "+ Catat Pembayaran", lambda: self.dialog_payment(tree), primary=True).pack(side="left")
        history = self._card(self.page, "Riwayat Transaksi", "Pembayaran yang sudah tersimpan di database")
        history.pack(fill="both", expand=True)
        pay_tree = self._tree(history, ("tanggal", "id", "pelanggan", "plat", "jumlah", "metode"),
                              ("TANGGAL", "ID SERVIS", "PELANGGAN", "PLAT NOMOR", "NOMINAL", "METODE"),
                              (120, 165, 190, 140, 150, 130), height=5)
        for p in self.db.list_payments():
            pay_tree.insert("", "end", values=(p["tanggal"], p["id_servis"], p["nama_pelanggan"], p["plat_nomor"], rupiah(p["jumlah"]), p["metode"]))

    def dialog_payment(self, tree):
        service_id = self._select_id(tree, "tagihan")
        if not service_id:
            return
        row = next((r for r in self.db.list_services() if r["id_servis"] == service_id), None)
        if not row:
            return
        due = int(row["total_biaya"]) - int(row["sudah_dibayar"])
        if due <= 0:
            messagebox.showinfo("Tagihan lunas", "Order ini sudah lunas.", parent=self)
            return
        win = self._dialog("Catat Pembayaran", f"{service_id}  ·  Sisa {rupiah(due)}")
        amount = self._form_entry(win, "Nominal pembayaran (Rp)", str(due))
        method = self._form_combo(win, "Metode pembayaran", PAYMENT_METHODS, "Tunai")
        note = self._form_entry(win, "Catatan (opsional)", "")
        def save():
            try:
                value = int(amount.get().strip())
                self.db.add_payment(service_id, value, method.get(), note.get().strip())
            except ValueError as exc:
                messagebox.showwarning("Nominal tidak valid", str(exc), parent=win)
                return
            except sqlite3.Error as exc:
                messagebox.showerror("Database error", str(exc), parent=win)
                return
            win.destroy()
            self.show_page("Pembayaran")
            self.toast("Pembayaran tercatat")
            confetti(self)
        self._dialog_actions(win, save)

    # LAPORAN
    def page_reports(self):
        self._heading("Laporan Bengkel", "Ringkasan aktivitas order, omzet, dan ekspor data.")
        stats = self.db.dashboard_stats()
        rows = self.db.report_rows()
        paid = sum(int(r["dibayar"]) for r in rows)
        total = sum(int(r["total"]) for r in rows)
        grid = ctk.CTkFrame(self.page, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 15))
        for i in range(3): grid.grid_columnconfigure(i, weight=1, uniform="reports")
        self._stat_card(grid, "Total Order Servis", str(len(rows)), "Seluruh waktu", C["cyan"], "▤").grid(row=0, column=0, sticky="ew", padx=(0, 7))
        self._stat_card(grid, "Nilai Seluruh Servis", rupiah(total), "Total nilai order", C["purple"], "↗").grid(row=0, column=1, sticky="ew", padx=7)
        self._stat_card(grid, "Pembayaran Diterima", rupiah(paid), "Akumulasi pembayaran", C["green"], "✓").grid(row=0, column=2, sticky="ew", padx=(7, 0))
        card = self._card(self.page, "Rincian Order", "Ekspor laporan akan menghasilkan file CSV yang dapat dibuka di Excel")
        card.pack(fill="both", expand=True)
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=(12, 0))
        self._button(actions, "⇩  Ekspor CSV", lambda: self.export_report(rows), primary=True).pack(side="left")
        tree = self._tree(card, ("id", "tanggal", "pelanggan", "plat", "jenis", "mekanik", "status", "total", "dibayar"),
                          ("ID SERVIS", "TANGGAL", "PELANGGAN", "PLAT NOMOR", "JENIS SERVIS", "MEKANIK", "STATUS", "TOTAL", "DIBAYAR"),
                          (155, 100, 160, 130, 150, 120, 150, 125, 125), height=10)
        for r in rows:
            tree.insert("", "end", values=(r["id_servis"], r["tanggal_masuk"], r["pelanggan"], r["plat_nomor"], r["jenis_servis"], r["mekanik"], r["status"], rupiah(r["total"]), rupiah(r["dibayar"])))

    def export_report(self, rows):
        path = filedialog.asksaveasfilename(parent=self, title="Simpan laporan", defaultextension=".csv",
                                            filetypes=[("CSV file", "*.csv")], initialfile="laporan_apex_garage.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["ID Servis", "Tanggal", "Pelanggan", "Plat Nomor", "Jenis Servis", "Mekanik", "Status", "Total Biaya", "Sudah Dibayar"])
                for r in rows:
                    writer.writerow([r["id_servis"], r["tanggal_masuk"], r["pelanggan"], r["plat_nomor"], r["jenis_servis"], r["mekanik"], r["status"], r["total"], r["dibayar"]])
            messagebox.showinfo("Ekspor berhasil", f"Laporan tersimpan di:\n{path}", parent=self)
        except OSError as exc:
            messagebox.showerror("Gagal mengekspor", str(exc), parent=self)

    # Dialog helper
    def _dialog(self, title, subtitle="", width=560):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry(f"{width}x720" if width > 600 else f"{width}x620")
        win.resizable(False, False)
        win.configure(fg_color=C["bg"])
        win.transient(self)
        win.grab_set()
        ctk.CTkLabel(win, text=title, font=("Segoe UI", 20, "bold"), text_color=C["text"]).pack(anchor="w", padx=22, pady=(22, 2))
        if subtitle:
            ctk.CTkLabel(win, text=subtitle, font=("Segoe UI", 10), text_color=C["muted"], wraplength=width-44).pack(anchor="w", padx=22, pady=(0, 15))
        return win

    def _dialog_actions(self, win, save_command):
        bar = ctk.CTkFrame(win, fg_color="transparent")
        bar.pack(fill="x", side="bottom", padx=22, pady=18)
        self._button(bar, "Batal", win.destroy).pack(side="right", padx=(8, 0))
        self._button(bar, "Simpan Data", save_command, primary=True, width=135).pack(side="right")

    def _form_entry(self, parent, label, default=""):
        ctk.CTkLabel(parent, text=label, text_color=C["muted"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(5, 4))
        entry = ctk.CTkEntry(parent, height=38, fg_color=C["panel2"], border_color=C["line"])
        entry.insert(0, default)
        entry.pack(fill="x", padx=22, pady=(0, 8))
        return entry

    def _form_combo(self, parent, label, values, default):
        ctk.CTkLabel(parent, text=label, text_color=C["muted"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(5, 4))
        combo = ctk.CTkComboBox(parent, values=values, height=38, fg_color=C["panel2"], border_color=C["line"], button_color=C["blue"])
        combo.set(default)
        combo.pack(fill="x", padx=22, pady=(0, 8))
        return combo


if __name__ == "__main__":
    app = ApexGarageApp()
    app.mainloop()
