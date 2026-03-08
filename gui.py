# GUI Inspiration
# https://onboardintelligence.com/Calculations

import tkinter as tk
from tkinter import ttk, font
import calcs

# ---------------------------------------------------------------------------
# Colour palette — nautical chart / admiralty aesthetic
# ---------------------------------------------------------------------------
BG          = "#0d1b2a"   # deep navy
PANEL       = "#112233"   # slightly lighter panel
BORDER      = "#1e3a5f"   # steel-blue border
ACCENT      = "#00b4d8"   # cyan highlight
ACCENT2     = "#90e0ef"   # lighter cyan
TEXT        = "#caf0f8"   # near-white text
TEXT_DIM    = "#5a8fa8"   # muted label text
RESULT_BG   = "#0a1628"   # result area background
RESULT_FG   = "#39ff14"   # "radar green" result text
ERROR_FG    = "#ff4d6d"   # error red
WARN_FG     = "#ffb703"   # warning amber
INPUT_BG    = "#0d2137"   # input field background
INPUT_FG    = "#e0f7ff"   # input field text
RADIO_SEL   = "#00b4d8"
DIVIDER     = "#1e3a5f"

FONT_TITLE  = ("Courier New", 11, "bold")
FONT_LABEL  = ("Courier New", 9)
FONT_SMALL  = ("Courier New", 8)
FONT_RESULT = ("Courier New", 10, "bold")
FONT_HEADER = ("Courier New", 13, "bold")
FONT_SECT   = ("Courier New", 10, "bold")

PAD = 6

# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------

def _entry(parent, width=5, textvariable=None, **kw):
    e = tk.Entry(parent, width=width, bg=INPUT_BG, fg=INPUT_FG,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, font=FONT_LABEL,
                 textvariable=textvariable, **kw)
    return e


def _label(parent, text, dim=False, **kw):
    return tk.Label(parent, text=text,
                    bg=PANEL if not kw.pop("bg_override", False) else kw.pop("bg", PANEL),
                    fg=TEXT_DIM if dim else TEXT,
                    font=FONT_LABEL, **kw)


def _section_label(parent, text):
    return tk.Label(parent, text=text, bg=PANEL, fg=ACCENT,
                    font=FONT_SECT, anchor="w")


def _result_box(parent, height=3):
    t = tk.Text(parent, height=height, bg=RESULT_BG, fg=RESULT_FG,
                font=FONT_RESULT, relief="flat",
                highlightthickness=1, highlightbackground=BORDER,
                state="disabled", wrap="word")
    return t


def _set_result(widget, text, is_error=False, is_warn=False):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    colour = ERROR_FG if is_error else (WARN_FG if is_warn else RESULT_FG)
    widget.config(fg=colour)
    widget.insert("end", text)
    widget.config(state="disabled")


def _btn(parent, text, command, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=BORDER, fg=ACCENT2, activebackground=ACCENT,
                     activeforeground=BG, relief="flat", cursor="hand2",
                     font=FONT_LABEL, padx=8, pady=3, **kw)


# ---------------------------------------------------------------------------
# Lat / Long coordinate widget  (DD° MM.M'  N/S or E/W radio)
# ---------------------------------------------------------------------------

class CoordWidget(tk.Frame):
    """A compact DD MM.M + hemisphere radio widget.

    axis='lat'  => N / S radios,  DD width 2 (max ±89)
    axis='lon'  => E / W radios,  DD width 3 (max ±179)
    """

    def __init__(self, parent, label, axis="lat", **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._axis = axis

        # ── label ──────────────────────────────────────────────────
        tk.Label(self, text=label, bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL, width=4, anchor="e").pack(side="left")

        # ── DD ─────────────────────────────────────────────────────
        dd_w = 2 if axis == "lat" else 3
        self._dd = tk.StringVar(value="00" if axis == "lat" else "000")
        e_dd = _entry(self, width=dd_w + 1, textvariable=self._dd)
        e_dd.pack(side="left", padx=(2, 0))
        tk.Label(self, text="°", bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")

        # ── MM.M ───────────────────────────────────────────────────
        self._mm = tk.StringVar(value="00.0")
        e_mm = _entry(self, width=5, textvariable=self._mm)
        e_mm.pack(side="left", padx=(4, 0))
        tk.Label(self, text="'", bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")

        # ── hemisphere radios ──────────────────────────────────────
        options = ("N", "S") if axis == "lat" else ("E", "W")
        self._hemi = tk.StringVar(value=options[0])
        for opt in options:
            tk.Radiobutton(self, text=opt, variable=self._hemi, value=opt,
                           bg=PANEL, fg=TEXT, selectcolor=BG,
                           activebackground=PANEL, activeforeground=ACCENT,
                           font=FONT_SMALL).pack(side="left", padx=2)

    # ── public API ──────────────────────────────────────────────────────────

    def get(self):
        """Return (DD, MM.M) tuple with correct sign for calcs.py."""
        try:
            dd = int(self._dd.get())
            mm = float(self._mm.get())
        except ValueError:
            raise ValueError(f"Invalid coordinate in '{self._axis}' field")
        if not (0.0 <= mm < 60.0):
            raise ValueError("Minutes must be 0.0–59.9")
        if self._axis == "lat" and not (0 <= dd <= 89):
            raise ValueError("Latitude degrees must be 0–89")
        if self._axis == "lon" and not (0 <= dd <= 179):
            raise ValueError("Longitude degrees must be 0–179")
        if self._hemi.get() in ("S", "W"):
            if dd == 0:
                # -0 == 0 in Python, so negate mm instead.
                # degrees_to_decimals((0, -mm)) = 0 + (-mm/60) which is negative. ✓
                # Edge case 0°00.0' S/W is genuinely 0 — sign irrelevant.
                mm = -mm
            else:
                dd = -dd
        return (dd, mm)


# ---------------------------------------------------------------------------
# Time / date input row
# ---------------------------------------------------------------------------

class TimeWidget(tk.Frame):
    """DDMMYY  HH  MM entry."""

    def __init__(self, parent, label, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        tk.Label(self, text=label, bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL, width=12, anchor="e").pack(side="left")
        self._date = tk.StringVar(value="010126")
        self._hh   = tk.StringVar(value="00")
        self._mm_  = tk.StringVar(value="00")

        _entry(self, width=7, textvariable=self._date).pack(side="left", padx=(2, 0))
        tk.Label(self, text="DDMMYY", bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")
        _entry(self, width=3, textvariable=self._hh).pack(side="left", padx=(6, 0))
        tk.Label(self, text="HH", bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")
        _entry(self, width=3, textvariable=self._mm_).pack(side="left", padx=(4, 0))
        tk.Label(self, text="MM", bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")

    def get(self):
        return (self._date.get(), int(self._hh.get()), int(self._mm_.get()))


# ---------------------------------------------------------------------------
# Numeric input row
# ---------------------------------------------------------------------------

class NumWidget(tk.Frame):
    def __init__(self, parent, label, default="0", width=7, unit="", **kw):
        super().__init__(parent, bg=PANEL, **kw)
        tk.Label(self, text=label, bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL, width=14, anchor="e").pack(side="left")
        self._var = tk.StringVar(value=default)
        _entry(self, width=width, textvariable=self._var).pack(side="left", padx=(2, 0))
        if unit:
            tk.Label(self, text=unit, bg=PANEL, fg=TEXT_DIM,
                     font=FONT_SMALL).pack(side="left", padx=(2, 0))

    def get(self):
        return float(self._var.get())


# ---------------------------------------------------------------------------
# Individual calculation panels
# ---------------------------------------------------------------------------

def _panel(parent, title):
    """Return a styled LabelFrame."""
    f = tk.LabelFrame(parent, text=f"  {title}  ",
                      bg=PANEL, fg=ACCENT, font=FONT_SECT,
                      bd=1, relief="flat",
                      highlightthickness=1, highlightbackground=BORDER,
                      padx=PAD, pady=PAD)
    return f


class ParallelSailingPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  PARALLEL SAILING")
        f.pack(fill="x")

        self._lat  = CoordWidget(f, "Lat",   axis="lat")
        self._lonA = CoordWidget(f, "LonA",  axis="lon")
        self._lonB = CoordWidget(f, "LonB",  axis="lon")
        for w in (self._lat, self._lonA, self._lonB):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            result = calcs.parallel_sailing(self._lat.get(),
                                            self._lonA.get(),
                                            self._lonB.get())
            if len(result) == 3:
                dist, course, warn = result
                _set_result(self._res,
                    f"Departure: {dist} nm   Course: {course}°T\n⚠ {warn}",
                    is_warn=True)
            else:
                dist, course = result
                _set_result(self._res, f"Departure: {dist} nm   Course: {course}°T")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


class PlaneSailingPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  PLANE SAILING")
        f.pack(fill="x")

        self._latA = CoordWidget(f, "LatA",  axis="lat")
        self._lonA = CoordWidget(f, "LonA",  axis="lon")
        self._latB = CoordWidget(f, "LatB",  axis="lat")
        self._lonB = CoordWidget(f, "LonB",  axis="lon")
        for w in (self._latA, self._lonA, self._latB, self._lonB):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            result = calcs.plane_sailing(self._latA.get(), self._lonA.get(),
                                         self._latB.get(), self._lonB.get())
            if len(result) == 3:
                dist, course, warn = result
                _set_result(self._res,
                    f"Distance: {dist} nm   Course: {course}°T\n⚠ {warn}",
                    is_warn=True)
            else:
                dist, course = result
                _set_result(self._res, f"Distance: {dist} nm   Course: {course}°T")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


class GreatCirclePanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  GREAT CIRCLE SAILING")
        f.pack(fill="x")

        self._latA = CoordWidget(f, "LatA",  axis="lat")
        self._lonA = CoordWidget(f, "LonA",  axis="lon")
        self._latB = CoordWidget(f, "LatB",  axis="lat")
        self._lonB = CoordWidget(f, "LonB",  axis="lon")
        for w in (self._latA, self._lonA, self._latB, self._lonB):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            dist, init_c, final_c = calcs.great_circle_sailing(
                self._latA.get(), self._lonA.get(),
                self._latB.get(), self._lonB.get())
            _set_result(self._res,
                f"Distance: {dist} nm\n"
                f"Initial Course: {init_c}°T   Final Course: {final_c}°T")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


class CompositeGCPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  COMPOSITE GREAT CIRCLE SAILING")
        f.pack(fill="x")

        self._latA  = CoordWidget(f, "LatA",    axis="lat")
        self._lonA  = CoordWidget(f, "LonA",    axis="lon")
        self._latB  = CoordWidget(f, "LatB",    axis="lat")
        self._lonB  = CoordWidget(f, "LonB",    axis="lon")
        self._latLim = CoordWidget(f, "Lim.Lat", axis="lat")
        for w in (self._latA, self._lonA, self._latB, self._lonB, self._latLim):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            dist, init_c, final_c = calcs.composite_great_circle_sailing(
                self._latA.get(),  self._lonA.get(),
                self._latB.get(),  self._lonB.get(),
                self._latLim.get())
            _set_result(self._res,
                f"Total Distance: {dist} nm\n"
                f"Initial Course: {init_c}°T   Final Course: {final_c}°T")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


class ETAPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  ETA CALCULATOR")
        f.pack(fill="x")

        self._dist  = NumWidget(f, "Distance", default="240", unit="nm")
        self._speed = NumWidget(f, "Speed",    default="10",  unit="kn")
        self._dep   = TimeWidget(f, "Departure")
        for w in (self._dist, self._speed, self._dep):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE ETA", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            eta = calcs.get_ETA(self._dist.get(), self._speed.get(),
                                self._dep.get())
            _set_result(self._res,
                f"ETA: {eta.strftime('%d %b %Y  %H:%M')} UTC")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


class SpeedForETAPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PANEL)
        f = _panel(self, "⊳  SPEED FOR ETA")
        f.pack(fill="x")

        self._dist = NumWidget(f, "Distance", default="240", unit="nm")
        self._dep  = TimeWidget(f, "Departure")
        self._arr  = TimeWidget(f, "Arrival")
        for w in (self._dist, self._dep, self._arr):
            w.pack(anchor="w", pady=1)

        _btn(f, "CALCULATE SPEED", self._calc).pack(anchor="w", pady=(4, 2))
        self._res = _result_box(f, height=2)
        self._res.pack(fill="x")

    def _calc(self):
        try:
            spd = calcs.get_speed_for_ETA(self._dist.get(),
                                          self._dep.get(),
                                          self._arr.get())
            _set_result(self._res, f"Required Speed: {spd} knots")
        except Exception as e:
            _set_result(self._res, f"Error: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class NavCalcApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("NavCalc  —  Marine Navigation Calculator")
        self.configure(bg=BG)
        # Maximise window cross-platform
        try:
            self.state("zoomed")           # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)   # some Linux WMs (e.g. i3, openbox)
            except tk.TclError:
                # Fallback: manually fill the screen
                self.update_idletasks()
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")

        self._build_header()
        self._build_body()
        self._build_footer()

    # ── header ──────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG, pady=8)
        hdr.pack(fill="x", padx=12)

        tk.Label(hdr,
                 text="⚓  NAVCALC",
                 bg=BG, fg=ACCENT, font=("Courier New", 20, "bold")
                 ).pack(side="left")
        tk.Label(hdr,
                 text="Marine Navigation Calculator",
                 bg=BG, fg=TEXT_DIM, font=("Courier New", 10)
                 ).pack(side="left", padx=14)

        # thin horizontal rule
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=0)

    # ── body — three columns ────────────────────────────────────────────────

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # configure three equal columns
        for c in range(3):
            body.columnconfigure(c, weight=1, uniform="col")
        body.rowconfigure(0, weight=1)

        # ── col 0: Plane & Parallel ────────────────────────────────
        col0 = tk.Frame(body, bg=BG)
        col0.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        tk.Label(col0, text="RHUMB LINE", bg=BG, fg=ACCENT2,
                 font=FONT_HEADER).pack(anchor="w", pady=(0, 4))

        ParallelSailingPanel(col0).pack(fill="x", pady=(0, 8))
        PlaneSailingPanel(col0).pack(fill="x")

        # ── col 1: Great Circle ────────────────────────────────────
        col1 = tk.Frame(body, bg=BG)
        col1.grid(row=0, column=1, sticky="nsew", padx=5)

        tk.Label(col1, text="GREAT CIRCLE", bg=BG, fg=ACCENT2,
                 font=FONT_HEADER).pack(anchor="w", pady=(0, 4))

        GreatCirclePanel(col1).pack(fill="x", pady=(0, 8))
        CompositeGCPanel(col1).pack(fill="x")

        # ── col 2: Time / ETA ──────────────────────────────────────
        col2 = tk.Frame(body, bg=BG)
        col2.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        tk.Label(col2, text="VOYAGE TIME", bg=BG, fg=ACCENT2,
                 font=FONT_HEADER).pack(anchor="w", pady=(0, 4))

        ETAPanel(col2).pack(fill="x", pady=(0, 8))
        SpeedForETAPanel(col2).pack(fill="x")

    # ── footer ──────────────────────────────────────────────────────────────

    def _build_footer(self):
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")
        ftr = tk.Frame(self, bg=BG, pady=4)
        ftr.pack(fill="x", padx=12)
        tk.Label(ftr,
                 text="Coordinates: DD° MM.M'  N/S  ·  DDD° MM.M'  E/W   |   "
                      "Rhumb warning issued when distance > 600 nm",
                 bg=BG, fg=TEXT_DIM, font=("Courier New", 8)
                 ).pack(side="left")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = NavCalcApp()
    app.mainloop()