import tkinter as tk
from tkinter import font as tkfont
import threading
import math
import datetime
import config
import think
import memory

# ── Palette ─────────────────────────────────────────────────────
BG        = "#080c14"
SURFACE   = "#0d1420"
SURFACE2  = "#111927"
BORDER    = "#1a2535"
ACCENT    = "#00f5d4"
ACCENT2   = "#7c3aed"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#4a5568"
TEXT_MID  = "#8896a8"
USER_BG   = "#0a2a2a"
KAI_BG    = "#0d1420"
RED       = "#ff4466"

# ── Color helpers ────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    r1,g1,b1 = hex_to_rgb(c1)
    r2,g2,b2 = hex_to_rgb(c2)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"

def now_str():
    return datetime.datetime.now().strftime("%H:%M")

# ── Rounded rect on canvas ───────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)

# ════════════════════════════════════════════════════════════════
class KAIApp:
    def __init__(self, root):
        self.root = root
        self.messages = memory.load_memory()
        self._drag_x = 0
        self._drag_y = 0
        self._orb_angle = 0
        self._orb_pulse = 0.0
        self._orb_dir = 1
        self._typing = False
        self._typing_phase = 0
        self._is_thinking = False

        self._build_window()
        self._animate_orb()
        self._animate_typing()

    # ── Window ───────────────────────────────────────────────────
    def _build_window(self):
        self.root.title("KAI")
        self.root.geometry("420x640")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"420x640+{sw-440}+{sh-680}")

        self._build_header()
        self._build_chat()
        self._build_input()

    # ── Header ───────────────────────────────────────────────────
    def _build_header(self):
        self.header = tk.Frame(self.root, bg=SURFACE, height=76)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        for w in [self.header]:
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        # Orb
        self.orb_canvas = tk.Canvas(
            self.header, width=54, height=54,
            bg=SURFACE, highlightthickness=0
        )
        self.orb_canvas.pack(side="left", padx=(16,0), pady=11)
        self.orb_canvas.bind("<ButtonPress-1>", self._drag_start)
        self.orb_canvas.bind("<B1-Motion>",     self._drag_move)

        # Title area
        info = tk.Frame(self.header, bg=SURFACE)
        info.pack(side="left", padx=10)
        info.bind("<ButtonPress-1>", self._drag_start)
        info.bind("<B1-Motion>",     self._drag_move)

        tk.Label(info, text="KAI", bg=SURFACE, fg=TEXT,
                 font=("Consolas", 20, "bold")).pack(anchor="w")

        row = tk.Frame(info, bg=SURFACE)
        row.pack(anchor="w")

        # Blinking dot
        self.dot_canvas = tk.Canvas(row, width=8, height=8,
                                     bg=SURFACE, highlightthickness=0)
        self.dot_canvas.pack(side="left", pady=1)
        self.dot_canvas.create_oval(1,1,7,7, fill=ACCENT, outline="", tags="dot")

        self.status_lbl = tk.Label(row, text="online", bg=SURFACE,
                                    fg=ACCENT, font=("Consolas", 8))
        self.status_lbl.pack(side="left", padx=5)
        self._blink_dot()

        # Synaptic label (right side, subtle)
        tk.Label(self.header, text="SYNAPTIC", bg=SURFACE, fg=TEXT_DIM,
                 font=("Consolas", 7)).pack(side="right", padx=(0,14), anchor="s", pady=6)

        # Controls
        ctrl = tk.Frame(self.header, bg=SURFACE)
        ctrl.pack(side="right", anchor="n", pady=10, padx=14)
        ctrl.bind("<ButtonPress-1>", self._drag_start)
        ctrl.bind("<B1-Motion>",     self._drag_move)

        tk.Button(ctrl, text="⎯", bg=SURFACE, fg=TEXT_DIM,
                  relief="flat", font=("Segoe UI", 12), bd=0,
                  activebackground=SURFACE2, activeforeground=ACCENT,
                  cursor="hand2", command=self._minimise
                  ).pack(side="left")
        tk.Button(ctrl, text="✕", bg=SURFACE, fg=TEXT_DIM,
                  relief="flat", font=("Segoe UI", 11), bd=0,
                  activebackground=SURFACE2, activeforeground=RED,
                  cursor="hand2", command=self.root.destroy
                  ).pack(side="left", padx=(8,0))

        # Bottom accent line on header
        line_c = tk.Canvas(self.root, height=1, bg=BG, highlightthickness=0)
        line_c.pack(fill="x")
        # Gradient-ish line: accent then dim
        line_c.create_line(0, 0, 420, 0, fill=BORDER)
        line_c.create_line(14, 0, 120, 0, fill=ACCENT, width=1)
        line_c.create_line(120, 0, 180, 0, fill=ACCENT2, width=1)

    # ── Blinking status dot ──────────────────────────────────────
    def _blink_dot(self):
        items = self.dot_canvas.find_withtag("dot")
        for item in items:
            current = self.dot_canvas.itemcget(item, "fill")
            new_col = ACCENT if current == SURFACE else SURFACE
            self.dot_canvas.itemconfig(item, fill=new_col)
        self.root.after(1200, self._blink_dot)

    # ── Chat ─────────────────────────────────────────────────────
    def _build_chat(self):
        wrapper = tk.Frame(self.root, bg=BG)
        wrapper.pack(fill="both", expand=True)

        sb = tk.Scrollbar(wrapper, width=3, troughcolor=BG,
                          bg=BORDER, activebackground=ACCENT,
                          relief="flat", bd=0)
        sb.pack(side="right", fill="y", padx=(0,2), pady=4)

        self.chat_canvas = tk.Canvas(
            wrapper, bg=BG, highlightthickness=0,
            yscrollcommand=sb.set
        )
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        sb.config(command=self.chat_canvas.yview)

        self.msg_frame = tk.Frame(self.chat_canvas, bg=BG)
        self.chat_win = self.chat_canvas.create_window(
            (0,0), window=self.msg_frame, anchor="nw", width=413
        )

        self.msg_frame.bind("<Configure>", self._on_frame_cfg)
        self.chat_canvas.bind("<Configure>", self._on_canvas_cfg)
        self.chat_canvas.bind("<MouseWheel>", self._on_scroll)

        # Spacer top
        tk.Frame(self.msg_frame, bg=BG, height=8).pack()

        # Welcome
        self._add_kai_bubble("Hey. I'm KAI.\nWhat do you need?")

        # Typing indicator (hidden initially)
        self.typing_outer = tk.Frame(self.msg_frame, bg=BG)
        self.typing_canvas = tk.Canvas(
            self.typing_outer, width=70, height=34,
            bg=SURFACE2, highlightthickness=0
        )
        self.typing_canvas.pack(padx=(14,0), pady=4)

    def _on_frame_cfg(self, e=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def _on_canvas_cfg(self, e):
        self.chat_canvas.itemconfig(self.chat_win, width=e.width - 4)

    def _on_scroll(self, e):
        self.chat_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def _scroll_bottom(self):
        self.root.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ── Bubbles ──────────────────────────────────────────────────
    def _add_kai_bubble(self, text):
        self._hide_typing()
        f = tk.Frame(self.msg_frame, bg=BG)
        f.pack(fill="x", padx=0, pady=(2,2))

        inner = tk.Frame(f, bg=BG)
        inner.pack(side="left", padx=(12,60))

        # Left accent bar
        bar = tk.Frame(inner, bg=ACCENT, width=2)
        bar.pack(side="left", fill="y")

        bubble = tk.Frame(inner, bg=SURFACE2, padx=14, pady=10)
        bubble.pack(side="left")

        # Header row
        hr = tk.Frame(bubble, bg=SURFACE2)
        hr.pack(fill="x")
        tk.Label(hr, text="KAI", bg=SURFACE2, fg=ACCENT,
                 font=("Consolas", 8, "bold")).pack(side="left")
        tk.Label(hr, text=f"  {now_str()}", bg=SURFACE2, fg=TEXT_DIM,
                 font=("Consolas", 7)).pack(side="left")

        tk.Label(bubble, text=text, bg=SURFACE2, fg=TEXT,
                 font=("Segoe UI", 10), wraplength=250,
                 justify="left", anchor="w"
                 ).pack(anchor="w", pady=(5,0))

        self._scroll_bottom()

    def _add_user_bubble(self, text):
        f = tk.Frame(self.msg_frame, bg=BG)
        f.pack(fill="x", padx=0, pady=(2,2))

        inner = tk.Frame(f, bg=BG)
        inner.pack(side="right", padx=(60,12))

        bubble = tk.Frame(inner, bg=USER_BG, padx=14, pady=10)
        bubble.pack(side="left")

        # Header row
        hr = tk.Frame(bubble, bg=USER_BG)
        hr.pack(fill="x")
        tk.Label(hr, text=f"{now_str()}  ", bg=USER_BG, fg=TEXT_DIM,
                 font=("Consolas", 7)).pack(side="right")
        tk.Label(hr, text="YOU", bg=USER_BG, fg=ACCENT2,
                 font=("Consolas", 8, "bold")).pack(side="right")

        tk.Label(bubble, text=text, bg=USER_BG, fg=TEXT,
                 font=("Segoe UI", 10), wraplength=250,
                 justify="right", anchor="e"
                 ).pack(anchor="e", pady=(5,0))

        # Right bar
        bar = tk.Frame(inner, bg=ACCENT2, width=2)
        bar.pack(side="left", fill="y")

        self._scroll_bottom()

    # ── Typing indicator ─────────────────────────────────────────
    def _show_typing(self):
        self._typing = True
        self.typing_outer.pack(side="left", padx=(12,0), pady=(4,4))
        self._scroll_bottom()

    def _hide_typing(self):
        self._typing = False
        if hasattr(self, "typing_outer"):
            self.typing_outer.pack_forget()

    def _animate_typing(self):
        if self._typing:
            self._typing_phase += 0.15
            self.typing_canvas.delete("all")
            for i in range(3):
                # Each dot bounces at offset phase
                phase = self._typing_phase - i * 0.8
                y_off = abs(math.sin(phase)) * 6
                alpha = 0.3 + abs(math.sin(phase)) * 0.7
                col = lerp_color(SURFACE, ACCENT, alpha)
                cx = 16 + i * 20
                cy = 17 - y_off
                self.typing_canvas.create_oval(
                    cx-4, cy-4, cx+4, cy+4,
                    fill=col, outline=""
                )
        self.root.after(40, self._animate_typing)

    # ── Input ────────────────────────────────────────────────────
    def _build_input(self):
        # Separator
        sep = tk.Canvas(self.root, height=1, bg=BG, highlightthickness=0)
        sep.pack(fill="x")
        sep.create_line(0,0,420,0, fill=BORDER)

        bar = tk.Frame(self.root, bg=SURFACE, height=65)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        wrap = tk.Frame(bar, bg=SURFACE)
        wrap.pack(fill="x", padx=14, pady=12)

        # Border canvas for input
        self.inp_c = tk.Canvas(wrap, height=40, bg=SURFACE,
                                highlightthickness=0)
        self.inp_c.pack(fill="x")

        self._draw_border(False)

        self.entry = tk.Entry(
            self.inp_c, bg=SURFACE2, fg=TEXT,
            font=("Segoe UI", 10), relief="flat",
            insertbackground=ACCENT, bd=0,
            disabledbackground=SURFACE2
        )
        self.inp_c.create_window((2,2), window=self.entry,
                                  anchor="nw", width=332, height=36)

        self.send_btn = tk.Button(
            self.inp_c, text="⟩", bg=ACCENT, fg=BG,
            relief="flat", font=("Consolas", 16, "bold"), bd=0,
            activebackground="#00c9af", activeforeground=BG,
            cursor="hand2", command=self._send
        )
        self.inp_c.create_window((338, 2), window=self.send_btn,
                                  anchor="nw", width=50, height=36)

        self.entry.bind("<Return>",   lambda e: self._send())
        self.entry.bind("<FocusIn>",  lambda e: self._draw_border(True))
        self.entry.bind("<FocusOut>", lambda e: self._draw_border(False))
        self.entry.focus()

    def _draw_border(self, focused):
        c = self.inp_c
        c.delete("bg")
        color = ACCENT if focused else BORDER
        rounded_rect(c, 0, 0, 390, 39, 6,
                     fill=SURFACE2, outline=color, width=1,
                     tags="bg")
        c.lower("bg")

    # ── Send ─────────────────────────────────────────────────────
    def _send(self):
        text = self.entry.get().strip()
        if not text or self._is_thinking:
            return
        self.entry.delete(0, "end")
        self._add_user_bubble(text)
        self._is_thinking = True
        self._show_typing()
        self.entry.config(state="disabled")
        self.send_btn.config(state="disabled", bg=BORDER, fg=TEXT_DIM)
        threading.Thread(target=self._fetch, args=(text,), daemon=True).start()

    def _fetch(self, text):
        self.messages = memory.add_message(self.messages, "user", text)
        try:
            response = think.think(self.messages)
        except Exception as e:
            response = f"[error] {e}"
        self.messages = memory.add_message(self.messages, "assistant", response)
        self.root.after(0, self._show_response, response)

    def _show_response(self, text):
        self._is_thinking = False
        self._add_kai_bubble(text)
        self.entry.config(state="normal")
        self.send_btn.config(state="normal", bg=ACCENT, fg=BG)
        self.entry.focus()

    # ── Orb animation ────────────────────────────────────────────
    def _animate_orb(self):
        c = self.orb_canvas
        c.delete("all")
        cx, cy, R = 27, 27, 19

        # Pulse
        self._orb_pulse += 0.035 * self._orb_dir
        if self._orb_pulse >= 1.0: self._orb_dir = -1
        elif self._orb_pulse <= 0.0: self._orb_dir = 1
        p = self._orb_pulse

        # Outer glow rings
        for r_off, alpha in [(11, 0.06), (7, 0.12), (3, 0.2)]:
            rv = R + r_off + p * 4
            col = lerp_color(SURFACE, ACCENT, alpha)
            c.create_oval(cx-rv, cy-rv, cx+rv, cy+rv,
                          fill="", outline=col, width=1)

        # Rotating arc (main)
        self._orb_angle = (self._orb_angle + 4) % 360
        ang = self._orb_angle
        c.create_arc(cx-R, cy-R, cx+R, cy+R,
                     start=ang, extent=200,
                     style="arc", outline=ACCENT, width=2)
        # Counter arc
        c.create_arc(cx-R+3, cy-R+3, cx+R-3, cy+R-3,
                     start=-ang, extent=120,
                     style="arc", outline=ACCENT2, width=1)

        # Inner fill
        ir = R - 5
        c.create_oval(cx-ir, cy-ir, cx+ir, cy+ir,
                      fill=SURFACE, outline=BORDER, width=1)

        # Center glow
        pd = 3 + p * 2.5
        col = lerp_color(ACCENT, "#ffffff", p * 0.6)
        c.create_oval(cx-pd, cy-pd, cx+pd, cy+pd,
                      fill=col, outline="")

        self.root.after(28, self._animate_orb)

    # ── Drag & minimise ──────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _minimise(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        def _restore(e):
            self.root.overrideredirect(True)
            self.root.unbind("<Map>")
        self.root.bind("<Map>", _restore)


# ── Entry ────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = KAIApp(root)
    root.mainloop()