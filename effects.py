"""Efek visual APEX GARAGE PRO: loading screen, animasi angka, hover, transisi halaman, toast."""
import random
import tkinter as tk

BG, PANEL, LINE, BLUE, CYAN, GREEN, MUTED = "#0A101A", "#111C2B", "#26364B", "#2878FF", "#42D9F5", "#2DD4A7", "#9BAEC4"


def lerp(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def animate(widget, fn, steps=20, delay=16):
    """Jalankan fn(p) dengan p 0→1 (ease-out). Aman jika widget sudah dihancurkan."""
    def go(i):
        try:
            fn(1 - (1 - i / steps) ** 3)
            if i < steps:
                widget.after(delay, lambda: go(i + 1))
        except Exception:
            pass
    go(0)


def count_up(label, text, steps=26):
    digits = "".join(ch for ch in str(text) if ch.isdigit())
    if not digits:
        return
    n, rp = int(digits), str(text).startswith("Rp")
    fmt = (lambda v: "Rp " + f"{v:,}".replace(",", ".")) if rp else str
    label.configure(text=fmt(0))
    animate(label, lambda p: label.configure(text=fmt(int(n * p))), steps)


def hover(w, on, off):
    """Ubah properti widget saat kursor masuk/keluar (tanpa kedip saat melewati child)."""
    def leave(_e):
        x, y = w.winfo_pointerxy()
        under = w.winfo_containing(x, y)
        if under is not None and str(under).startswith(str(w)):
            return
        w.configure(**off)
    w.bind("<Enter>", lambda _e: w.configure(**on), add="+")
    w.bind("<Leave>", leave, add="+")


def fade_in(win, steps=14):
    animate(win, lambda p: win.attributes("-alpha", p), steps)


def curtain(page, parent, bg):
    """Transisi halaman: tirai penutup menyusut dari atas sehingga isi halaman 'terbuka'."""
    import customtkinter as ctk
    ov = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0)

    def step(p):
        if p >= 1:
            ov.destroy()
            return
        ov.place(in_=page, relx=0, rely=1, anchor="sw", relwidth=1, relheight=1 - p)
        ov.lift()
    animate(page, step, 14)


def toast(root, msg, color=GREEN):
    import customtkinter as ctk
    f = ctk.CTkFrame(root, fg_color="#162438", border_width=1, border_color=color, corner_radius=12)
    ctk.CTkLabel(f, text="●  " + msg, font=("Segoe UI", 12, "bold"), text_color="#F3F7FC").pack(padx=20, pady=12)
    ys = list(range(-50, 26, 5))

    def go(i, d):
        if i < 0 or i >= len(ys):
            if d < 0:
                f.destroy()
            else:
                f.after(2200, lambda: go(len(ys) - 1, -1))
            return
        f.place(relx=1.0, x=-24, y=ys[i], anchor="ne")
        f.lift()
        f.after(14, lambda: go(i + d, d))
    go(0, 1)


class Splash(tk.Toplevel):
    """Loading screen: ring berputar, partikel naik, progress bar + pesan status, fade in/out."""
    W, H = 600, 360
    MSGS = [(0, "Menginisialisasi sistem…"), (22, "Memuat database SQLite…"), (50, "Menyiapkan dashboard…"),
            (78, "Menyinkronkan data servis…"), (97, "Siap digunakan")]

    def __init__(self, master, on_done, frames=150):
        super().__init__(master)
        self.on_done, self.frames, self.t = on_done, frames, 0
        W, H = self.W, self.H
        self.overrideredirect(True)
        self.geometry(f"{W}x{H}+{(self.winfo_screenwidth() - W) // 2}+{(self.winfo_screenheight() - H) // 2}")
        try:
            self.attributes("-alpha", 0); self.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.cv = tk.Canvas(self, width=W, height=H, highlightthickness=0, bg=BG)
        self.cv.pack()
        for y in range(H):
            self.cv.create_line(0, y, W, y, fill=lerp("#12306B", "#070B12", y / H))
        self.cv.create_rectangle(0, 0, W - 1, H - 1, outline=LINE)
        self.dots = [[random.uniform(10, W - 10), random.uniform(0, H), random.uniform(.4, 1.6), random.choice((2, 3, 4))]
                     for _ in range(26)]
        self.lift()
        self.after(16, self.tick)

    def tick(self):
        cv, W, H, t = self.cv, self.W, self.H, self.t
        cv.delete("dyn")
        for d in self.dots:  # partikel naik
            d[1] -= d[2]
            if d[1] < -5:
                d[0], d[1] = random.uniform(10, W - 10), H + 5
            c = lerp("#0B1424", CYAN, .55 * (1 - abs(d[1] - H / 2) / (H / 2)))
            cv.create_oval(d[0], d[1], d[0] + d[3], d[1] + d[3], fill=c, outline="", tags="dyn")
        cx, cy, r = W / 2, 120, 50
        cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1B2D4A", width=3, tags="dyn")
        cv.create_arc(cx - r, cy - r, cx + r, cy + r, start=-t * 7, extent=110, style="arc", outline=CYAN, width=5, tags="dyn")
        cv.create_arc(cx - r + 9, cy - r + 9, cx + r - 9, cy + r - 9, start=t * 5 + 180, extent=75, style="arc", outline=BLUE, width=4, tags="dyn")
        pulse = abs(((t % 40) - 20) / 20)
        cv.create_text(cx, cy, text="◆", font=("Segoe UI Symbol", 28 + int(pulse * 4), "bold"), fill=lerp(BLUE, CYAN, pulse), tags="dyn")
        a = min(1, t / 40)
        cv.create_text(cx, 215, text="APEX GARAGE", font=("Segoe UI", 28, "bold"), fill=lerp("#12306B", "#FFFFFF", a), tags="dyn")
        cv.create_text(cx, 247, text="PRO  /  WORKSHOP OS", font=("Segoe UI", 10, "bold"), fill=lerp("#12306B", MUTED, max(0, a * 2 - 1)), tags="dyn")
        p = min(1, t / self.frames)
        p = p * p * (3 - 2 * p)
        x0, x1, y = 140, 460, 296
        cv.create_rectangle(x0, y, x1, y + 6, fill="#1B2D4A", outline="", tags="dyn")
        cv.create_rectangle(x0, y, x0 + (x1 - x0) * p, y + 6, fill=CYAN, outline="", tags="dyn")
        cv.create_rectangle(x0 + (x1 - x0) * p - 24, y, x0 + (x1 - x0) * p, y + 6, fill="#BDF3FF", outline="", tags="dyn")
        pct = int(p * 100)
        msg = [m for th, m in self.MSGS if pct >= th][-1]
        cv.create_text(x0, y + 22, text=msg, anchor="w", font=("Segoe UI", 9), fill=MUTED, tags="dyn")
        cv.create_text(x1, y + 22, text=f"{pct}%", anchor="e", font=("Segoe UI", 9, "bold"), fill=CYAN, tags="dyn")
        try:  # fade in di awal, fade out di akhir
            end = self.frames + 12
            alpha = min(1, t / 14) if t < end else max(0, 1 - (t - end) / 10)
            self.attributes("-alpha", alpha)
        except tk.TclError:
            pass
        self.t += 1
        if self.t > self.frames + 22:
            self.destroy(); self.on_done()
        else:
            self.after(16, self.tick)
