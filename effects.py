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
        self._f = tkfont.Font(family="Segoe UI", size=21, weight="bold")
        self._cw = [self._f.measure(c) for c in "APEX GARAGE"]
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
        total, gx = sum(self._cw), cx - sum(self._cw) / 2
        for ch, cw in zip("APEX GARAGE", self._cw):
            col = lerp("#12306B", grad_color(GRAD + (GRAD[0],), ((gx + cw / 2 - (cx - total / 2)) / total + t * .008) % 1), a)
            cv.create_text(gx, 215, text=ch, anchor="w", font=self._f, fill=col, tags="dyn"); gx += cw
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


# ================= v1.2 =================
import math


def _ease(x):
    return 1 - (1 - max(0.0, min(1.0, x))) ** 3


class Hero(tk.Canvas):
    """Banner dashboard: orb bercahaya, garis kecepatan, teks mengetik, dan gauge beban bengkel."""
    def __init__(self, parent, title, subtitle, load, cap=10, height=150):
        super().__init__(parent, height=height, highlightthickness=0, bd=0, bg=PANEL)
        self.title, self.sub, self.load, self.cap, self.t = title, subtitle, load, cap, 0
        self.orbs = [[random.random(), random.uniform(.0006, .0016), random.uniform(0, 6), random.randint(40, 75)] for _ in range(4)]
        self.streaks = [[random.random(), random.random(), random.uniform(.006, .016), random.randint(30, 90)] for _ in range(9)]
        self.bind("<Configure>", lambda e: self._bg())
        self.after(30, self._frame)

    def _bg(self):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        for i in range(60):
            self.create_rectangle(i * w / 60, 0, (i + 1) * w / 60 + 1, h, fill=lerp("#123A7A", "#0C1626", i / 60), outline="", tags="bg")
        self.tag_lower("bg")

    def _frame(self):
        try:
            if not self.winfo_exists():
                return
            if self.winfo_width() > 50:
                self._draw(self.winfo_width(), self.winfo_height())
            self.t += 1
            self.after(33, self._frame)
        except tk.TclError:
            pass

    def _draw(self, w, h):
        t = self.t
        self.delete("dyn")
        for o in self.orbs:
            o[0] = (o[0] + o[1]) % 1.0
            x, y = o[0] * w, h / 2 + math.sin(t * .03 + o[2]) * h * .35
            base = lerp("#123A7A", "#0C1626", x / w)
            for k in range(6):
                r = o[3] * (1 - k / 6)
                self.create_oval(x - r, y - r, x + r, y + r, fill=lerp(base, CYAN, .03 + .04 * k), outline="", tags="dyn")
        for s in self.streaks:
            s[0] = (s[0] + s[2]) % 1.1
            x, y = s[0] * w - s[3], s[1] * h
            self.create_line(x, y, x + s[3], y, fill=lerp("#123A7A", CYAN, .55), tags="dyn")
        nt, ns = min(len(self.title), t // 2), max(0, int((t - 2 * len(self.title) - 6) * 1.5))
        typing = nt < len(self.title) or ns < len(self.sub)
        cur = "▌" if typing and (t // 6) % 2 else ""
        self.create_text(28, 50, anchor="w", text=self.title[:nt] + (cur if ns == 0 else ""), font=("Segoe UI", 22, "bold"), fill="white", tags="dyn")
        self.create_text(28, 88, anchor="w", text=self.sub[:ns] + (cur if ns else ""), font=("Segoe UI", 11), fill="#B6D8FF", tags="dyn")
        if w < 560:
            return
        cx, cy, R = w - 140, h - 22, 78
        f = min(1, self.load / self.cap) * _ease(t / 70)
        self.create_arc(cx - R, cy - R, cx + R, cy + R, start=0, extent=180, style="arc", outline="#1B2D4A", width=10, tags="dyn")
        for i in range(11):
            a = math.pi * (1 - i / 10)
            self.create_line(cx + (R - 18) * math.cos(a), cy - (R - 18) * math.sin(a), cx + (R - 8) * math.cos(a), cy - (R - 8) * math.sin(a),
                             fill="#FF6878" if i > 7 else "#5B7BA6", width=2, tags="dyn")
        if f > 0.005:
            self.create_arc(cx - R, cy - R, cx + R, cy + R, start=180, extent=-180 * f, style="arc",
                            outline=lerp(GREEN, "#FF6878", (f - .4) / .6), width=10, tags="dyn")
        a = math.pi * (1 - f)
        self.create_line(cx, cy, cx + (R - 24) * math.cos(a), cy - (R - 24) * math.sin(a), fill="white", width=3, tags="dyn")
        self.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill=CYAN, outline="", tags="dyn")
        self.create_text(cx - R - 18, cy - 24, anchor="e", text=f"{self.load}/{self.cap}", font=("Segoe UI", 22, "bold"), fill="white", tags="dyn")
        self.create_text(cx - R - 18, cy - 2, anchor="e", text="BEBAN BENGKEL", font=("Segoe UI", 8, "bold"), fill=MUTED, tags="dyn")


def donut(parent, items, height=235):
    """items: [(label, value, color)] — donut dengan animasi sapuan dan legenda."""
    cv = tk.Canvas(parent, height=height, bg=PANEL, highlightthickness=0, bd=0)
    st = {"p": 0.0}

    def draw(_e=None):
        cv.delete("all")
        w, h = max(cv.winfo_width(), 260), max(cv.winfo_height(), 200)
        tot = sum(v for _, v, _ in items)
        s = min(h - 40, w * .42)
        cx, cy = s / 2 + 22, h / 2
        box = (cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
        cv.create_oval(*box, outline="#1B2D4A", width=18)
        a = 90
        for _l, v, c in items:
            if v and tot:
                ext = max(-359.9, -360 * v / tot * st["p"])
                cv.create_arc(*box, start=a, extent=ext, style="arc", outline=c, width=18); a += ext
        cv.create_text(cx, cy - 6, text=str(int(tot * st["p"])), font=("Segoe UI", 24, "bold"), fill="#F3F7FC")
        cv.create_text(cx, cy + 18, text="order servis", font=("Segoe UI", 8), fill=MUTED)
        for i, (l, v, c) in enumerate(items):
            y, x = h / 2 - 54 + i * 27, cx + s / 2 + 26
            cv.create_oval(x, y - 5, x + 10, y + 5, fill=c, outline="")
            cv.create_text(x + 17, y, anchor="w", text=f"{l}  {v}", font=("Segoe UI", 9), fill="#F3F7FC")
    cv.bind("<Configure>", draw)
    cv.after(80, lambda: animate(cv, lambda p: (st.update(p=p), draw()), 30))
    return cv


class Palette(tk.Toplevel):
    """Command palette (Ctrl+K): ketik untuk mencari halaman/aksi, ↑↓ Enter."""
    def __init__(self, master, cmds):
        super().__init__(master)
        self.cmds, self.shown = cmds, cmds
        W, H = 540, 340
        self.overrideredirect(True); self.configure(bg=CYAN)
        self.geometry(f"{W}x{H}+{master.winfo_rootx() + (master.winfo_width() - W) // 2}+{master.winfo_rooty() + 100}")
        try:
            self.attributes("-alpha", 0); self.attributes("-topmost", True)
        except tk.TclError:
            pass
        box = tk.Frame(self, bg="#0D1522"); box.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(box, text="⌕  Ketik perintah atau nama halaman…", bg="#0D1522", fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(12, 0))
        self.e = tk.Entry(box, bg="#0D1522", fg="#F3F7FC", insertbackground=CYAN, relief="flat", font=("Segoe UI", 15))
        self.e.pack(fill="x", padx=16, pady=(4, 8))
        tk.Frame(box, bg=LINE, height=1).pack(fill="x")
        self.lb = tk.Listbox(box, bg="#0D1522", fg="#F3F7FC", selectbackground=BLUE, selectforeground="white", relief="flat",
                             highlightthickness=0, font=("Segoe UI", 12), activestyle="none")
        self.lb.pack(fill="both", expand=True, padx=8, pady=8)
        self.e.bind("<KeyRelease>", self._filter)
        self.e.bind("<Down>", lambda _e: self._move(1)); self.e.bind("<Up>", lambda _e: self._move(-1))
        self.e.bind("<Return>", self._run); self.lb.bind("<Double-Button-1>", self._run)
        self.bind("<Escape>", lambda _e: self.destroy())
        self._fill(); self.lift()
        self.after(30, self.e.focus_force)
        self.after(300, lambda: self.bind("<FocusOut>", lambda _e: self.after(60, self._check)))
        animate(self, lambda p: self.attributes("-alpha", p), 10)

    def _check(self):
        try:
            if self.focus_displayof() is None:
                self.destroy()
        except tk.TclError:
            pass

    def _fill(self):
        self.lb.delete(0, "end")
        for label, hint, _fn in self.shown:
            self.lb.insert("end", f"   {label}      ·  {hint}")
        if self.shown:
            self.lb.selection_set(0)

    def _filter(self, e):
        if e.keysym in ("Up", "Down", "Return", "Escape"):
            return
        q = self.e.get().lower().strip()
        self.shown = [c for c in self.cmds if q in c[0].lower() or q in c[1].lower()]
        self._fill()

    def _move(self, d):
        if not self.shown:
            return "break"
        cur = self.lb.curselection()
        i = max(0, min(len(self.shown) - 1, (cur[0] if cur else 0) + d))
        self.lb.selection_clear(0, "end"); self.lb.selection_set(i); self.lb.see(i)
        return "break"

    def _run(self, _e=None):
        cur = self.lb.curselection()
        if not cur:
            return
        fn, master = self.shown[cur[0]][2], self.master
        self.destroy()
        master.after(60, fn)


def confetti(root, n=110, frames=100):
    """Ledakan confetti di atas jendela (Windows: overlay transparan)."""
    cols = [CYAN, BLUE, GREEN, "#F6BE4F", "#FF6878", "#A78BFA"]
    try:
        w, h = root.winfo_width(), root.winfo_height()
        top = tk.Toplevel(root); top.overrideredirect(True)
        top.geometry(f"{w}x{h}+{root.winfo_rootx()}+{root.winfo_rooty()}")
        try:
            top.attributes("-transparentcolor", "#010203"); top.attributes("-topmost", True)
        except tk.TclError:
            top.destroy(); return
        cv = tk.Canvas(top, bg="#010203", highlightthickness=0); cv.pack(fill="both", expand=True)
    except tk.TclError:
        return
    ps = [[w / 2 + random.uniform(-70, 70), h * .35, random.uniform(-10, 10), random.uniform(-17, -4), random.choice(cols), random.randint(5, 10)] for _ in range(n)]

    def step(i):
        try:
            cv.delete("all")
            for p in ps:
                p[0] += p[2]; p[1] += p[3]; p[3] += .55; p[2] *= .99
                cv.create_rectangle(p[0], p[1], p[0] + p[5], p[1] + p[5] * .6, fill=p[4], outline="")
            if i < frames:
                top.after(16, lambda: step(i + 1))
            else:
                top.destroy()
        except tk.TclError:
            pass
    step(0)


# ================= teks gradien =================
from tkinter import font as tkfont

GRAD = (CYAN, "#7DA8FF", "#A78BFA")


def grad_color(stops, t):
    """Warna pada posisi t (0-1) di sepanjang daftar warna `stops`."""
    n = len(stops) - 1
    s = max(0.0, min(0.9999, t)) * n
    i = int(s)
    return lerp(stops[i], stops[i + 1], s - i)


class GradientText(tk.Canvas):
    """Teks gradien (Tk tidak punya native): tiap huruf diwarnai sesuai posisinya.
    animated=True membuat gradien bergeser pelan (efek shimmer)."""
    def __init__(self, parent, text, size=16, bg=BG, stops=GRAD, weight="bold", animated=False, family="Segoe UI"):
        f = tkfont.Font(family=family, size=size, weight=weight)
        widths = [f.measure(ch) for ch in text]
        w, h = sum(widths) + 4, f.metrics("linespace") + 4
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, bd=0)
        self.stops, self.w, self.t, self.items = tuple(stops) + (stops[0],), w, 0, []
        x = 2
        for ch, cw in zip(text, widths):
            self.items.append((self.create_text(x, h / 2, text=ch, anchor="w", font=f), x + cw / 2))
            x += cw
        self._paint()
        if animated:
            self.after(50, self._loop)

    def _paint(self):
        for item, xc in self.items:
            self.itemconfigure(item, fill=grad_color(self.stops, (xc / self.w + self.t * .012) % 1))

    def _loop(self):
        try:
            if self.winfo_exists():
                self.t += 1
                self._paint()
                self.after(50, self._loop)
        except tk.TclError:
            pass
