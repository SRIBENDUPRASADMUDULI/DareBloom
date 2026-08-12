import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import random
import math
import numpy as np
import time

# ---------------- MediaPipe Hand Landmarker setup ----------------
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# ---------------- Webcam & Fullscreen ----------------
cap = cv2.VideoCapture(0)
print("Webcam live ho raha hai... Band karne ke liye 'q' dabayein.")

WIN_NAME = "Aesthetic Magical Flowers Filter"
cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WIN_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Get screen resolution
try:
    from ctypes import windll
    SCREEN_W = windll.user32.GetSystemMetrics(0)
    SCREEN_H = windll.user32.GetSystemMetrics(1)
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

particles = []
sparkles = []
prev_hands_pos = {}
smoothed_hands_pos = {}
is_dissipating = False

# Adaptive smoothing
SMOOTH_MIN = 0.35
SMOOTH_MAX = 0.7
SPEED_THRESHOLD = 25.0

# Beautiful palettes (PetalOuter, PetalMid, PetalInner, Center, Highlight) BGR
FLOWER_PALETTES = [
    ((200, 170, 240), (225, 195, 255), (245, 225, 255), (80, 190, 255), (255, 255, 255)),
    ((180, 130, 235), (210, 165, 250), (235, 200, 255), (60, 120, 255), (255, 240, 255)),
    ((245, 175, 210), (255, 200, 230), (255, 225, 245), (80, 180, 255), (255, 255, 255)),
    ((245, 195, 140), (255, 215, 170), (255, 235, 200), (255, 255, 255), (80, 200, 255)),
    ((240, 230, 140), (250, 240, 170), (255, 250, 210), (255, 160, 210), (255, 255, 255)),
    ((200, 245, 195), (220, 250, 215), (240, 255, 235), (80, 200, 255), (255, 255, 255)),
    ((250, 220, 230), (255, 238, 245), (255, 248, 252), (255, 160, 210), (80, 200, 255)),
    ((240, 185, 165), (250, 210, 195), (255, 230, 220), (90, 210, 255), (255, 255, 255)),
    ((195, 185, 245), (220, 212, 255), (240, 235, 255), (130, 190, 255), (255, 255, 255)),
]

def ease_out_elastic(t):
    if t == 0 or t == 1: return t
    return pow(2, -10 * t) * math.sin((t - 0.1) * (2 * math.pi) / 0.4) + 1

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))

def spawn_flower(cx, cy):
    palette = random.choice(FLOWER_PALETTES)
    particles.append({
        'x': float(cx), 'y': float(cy),
        'size': random.randint(4, 8),          # Very small delicate flowers
        'type': random.choice(['rose', 'daisy', 'sakura', 'sunflower', 'lotus', 'cherry']),
        'rot': random.uniform(0, 360),
        'alpha': 0.0, 'scale': 0.0, 'grow_t': 0.0,
        'vy': 0.0, 'vx': 0.0,
        'palette': palette,
        'state': 'growing',
        'spawn_time': time.time(),
        'dissipate_delay': 0.0,
        'wind_phase': random.uniform(0, 2*math.pi),
        'spin_speed': random.uniform(1.5, 5.0),
    })

def spawn_sparkle(cx, cy, color):
    sparkles.append({
        'x': float(cx)+random.uniform(-6,6), 'y': float(cy)+random.uniform(-6,6),
        'size': random.uniform(1.0, 2.5), 'alpha': random.uniform(0.5, 1.0),
        'color': color, 'vy': random.uniform(-1.5, -0.2), 'vx': random.uniform(-1.0, 1.0),
        'life': random.uniform(0.3, 0.8), 'spawn_time': time.time(),
    })

# ---- Petal drawing ----
def draw_petal_grad(overlay, cx, cy, angle, length, width, c_out, c_in):
    cv2.ellipse(overlay, (int(cx), int(cy)), (max(1, int(length)), max(1, int(width))),
                angle, 0, 360, c_out, -1, cv2.LINE_AA)
    il, iw = max(1, int(length*0.55)), max(1, int(width*0.45))
    cv2.ellipse(overlay, (int(cx), int(cy)), (il, iw), angle, 0, 360, c_in, -1, cv2.LINE_AA)

def draw_glow(overlay, cx, cy, radius, color):
    for i in range(2):
        r = radius + i*2
        a = 0.2 * (1 - i/2)
        temp = overlay.copy()
        cv2.circle(temp, (int(cx), int(cy)), max(1, r), color, -1, cv2.LINE_AA)
        cv2.addWeighted(temp, a, overlay, 1-a, 0, dst=overlay)

def draw_flower(overlay, p, now):
    fx, fy = p['x'], p['y']
    size = max(2, int(p['size'] * p['scale']))
    po, pm, pi, cc, hi = p['palette']
    ftype = p['type']

    # Subtle glow
    draw_glow(overlay, fx, fy, int(size*0.5), pm)

    if ftype == 'rose':
        for li, (np_, ls) in enumerate([(5, 0.85), (6, 0.55), (4, 0.3)]):
            for i in range(np_):
                ang = p['rot'] + i*(360/np_) + li*30
                rad = math.radians(ang)
                px = fx + math.cos(rad)*size*ls*0.4
                py = fy + math.sin(rad)*size*ls*0.4
                c = po if li==0 else (pm if li==1 else pi)
                draw_petal_grad(overlay, px, py, ang, size*ls*0.8, size*ls*0.35, c, pi)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.08)), hi, -1, cv2.LINE_AA)

    elif ftype == 'sunflower':
        for i in range(12):
            ang = p['rot'] + i*30
            rad = math.radians(ang)
            px = fx + math.cos(rad)*size*0.35
            py = fy + math.sin(rad)*size*0.35
            draw_petal_grad(overlay, px, py, ang, size*0.45, size*0.13, (0,195,255), (30,225,255))
        cv2.circle(overlay, (int(fx), int(fy)), max(2, int(size*0.25)), (20,50,90), -1, cv2.LINE_AA)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.15)), (35,70,120), -1, cv2.LINE_AA)

    elif ftype == 'lotus':
        for i in range(7):
            ang = p['rot'] - 90 + (i-3)*22
            rad = math.radians(ang)
            px = fx + math.cos(rad)*size*0.25
            py = fy + math.sin(rad)*size*0.25
            draw_petal_grad(overlay, px, py, ang, size*0.5, size*0.18, po, pi)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.1)), cc, -1, cv2.LINE_AA)

    elif ftype == 'daisy':
        for i in range(8):
            ang = p['rot'] + i*45
            rad = math.radians(ang)
            px = fx + math.cos(rad)*size*0.38
            py = fy + math.sin(rad)*size*0.38
            draw_petal_grad(overlay, px, py, ang, size*0.4, size*0.14, po, pi)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.18)), cc, -1, cv2.LINE_AA)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.08)), hi, -1, cv2.LINE_AA)

    elif ftype == 'cherry':
        for i in range(5):
            ang = p['rot'] + i*72
            rad = math.radians(ang)
            px = fx + math.cos(rad)*size*0.3
            py = fy + math.sin(rad)*size*0.3
            r = max(1, int(size*0.24))
            cv2.circle(overlay, (int(px), int(py)), r, po, -1, cv2.LINE_AA)
            cv2.circle(overlay, (int(px), int(py)), max(1, int(r*0.5)), pi, -1, cv2.LINE_AA)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.1)), cc, -1, cv2.LINE_AA)

    else:  # Sakura
        for i in range(5):
            ang = p['rot'] + i*72
            rad = math.radians(ang)
            px = fx + math.cos(rad)*size*0.3
            py = fy + math.sin(rad)*size*0.3
            r = max(1, int(size*0.26))
            cv2.circle(overlay, (int(px), int(py)), r, po, -1, cv2.LINE_AA)
            cv2.circle(overlay, (int(px), int(py)), max(1, int(r*0.55)), pm, -1, cv2.LINE_AA)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.12)), cc, -1, cv2.LINE_AA)
        cv2.circle(overlay, (int(fx), int(fy)), max(1, int(size*0.05)), hi, -1, cv2.LINE_AA)

# Gesture Detection
def is_palm_open(hand_landmarks):
    wrist = hand_landmarks[0]
    tips = [8, 12, 16, 20]
    mips = [6, 10, 14, 18]
    extended = 0
    for tip, mip in zip(tips, mips):
        dt = math.hypot(hand_landmarks[tip].x - wrist.x, hand_landmarks[tip].y - wrist.y)
        dm = math.hypot(hand_landmarks[mip].x - wrist.x, hand_landmarks[mip].y - wrist.y)
        if dt > dm: extended += 1
    return extended >= 3

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    now = time.time()

    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    detection_result = detector.detect(mp_image)

    open_palms_count = 0

    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            if is_palm_open(hand_landmarks):
                open_palms_count += 1

        # Spawn flowers with adaptive smoothing
        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            # Average index + middle tip for stability
            it = hand_landmarks[8]
            mt = hand_landmarks[12]
            raw_cx = (it.x + mt.x) * 0.5 * w
            raw_cy = (it.y + mt.y) * 0.5 * h
            hand_key = f"hand_{idx}"

            # Adaptive smoothing: precise when slow, smooth when fast
            if hand_key in smoothed_hands_pos:
                sx, sy = smoothed_hands_pos[hand_key]
                rd = math.hypot(raw_cx - sx, raw_cy - sy)
                sr = min(1.0, rd / SPEED_THRESHOLD)
                sf = SMOOTH_MAX - (SMOOTH_MAX - SMOOTH_MIN) * sr
                cx = sx + (raw_cx - sx) * sf
                cy = sy + (raw_cy - sy) * sf
            else:
                cx, cy = raw_cx, raw_cy
            smoothed_hands_pos[hand_key] = (cx, cy)

            if hand_key in prev_hands_pos and not is_dissipating:
                px, py = prev_hands_pos[hand_key]
                dist = math.hypot(cx - px, cy - py)

                if dist > 1.5:
                    steps = max(1, int(dist // 4))
                    for s in range(steps):
                        t = s / steps
                        ix = px + (cx - px) * t
                        iy = py + (cy - py) * t
                        if random.random() < 0.85:
                            spawn_flower(ix + random.randint(-2, 2), iy + random.randint(-2, 2))
                        if random.random() < 0.25:
                            palette = random.choice(FLOWER_PALETTES)
                            spawn_sparkle(ix, iy, palette[4])

            prev_hands_pos[hand_key] = (cx, cy)
    else:
        prev_hands_pos.clear()

    # Trigger dissipation when both palms open
    if open_palms_count == 2 and len(particles) > 0 and not is_dissipating:
        is_dissipating = True
        cx_c, cy_c = w/2, h/2
        md = math.hypot(w, h) / 2
        for p in particles:
            d = math.hypot(p['x'] - cx_c, p['y'] - cy_c)
            p['state'] = 'dissipating'
            p['dissipate_delay'] = (d / md) * 0.5
            p['dissipate_start'] = now
            fa = random.uniform(-math.pi*0.85, -math.pi*0.15)
            spd = random.uniform(2.5, 7.0)
            p['vy'] = math.sin(fa) * spd
            p['vx'] = math.cos(fa) * spd * random.choice([-1, 1])
            for _ in range(random.randint(2, 4)):
                spawn_sparkle(p['x'], p['y'], p['palette'][4])

    # ---------- Particle Lifecycle ----------
    for p in particles[:]:
        if p['state'] == 'growing':
            p['grow_t'] = min(1.0, p['grow_t'] + 0.05)
            eased = ease_out_elastic(p['grow_t'])
            p['scale'] = max(0.01, min(1.2, eased))
            p['alpha'] = min(1.0, ease_out_cubic(p['grow_t']) * 1.2)
            if p['grow_t'] >= 1.0:
                p['state'] = 'static'
                p['scale'] = 1.0
                p['alpha'] = 1.0

        elif p['state'] == 'static':
            pass

        elif p['state'] == 'dissipating':
            elapsed = now - p.get('dissipate_start', now)
            delay = p.get('dissipate_delay', 0)
            if elapsed < delay: continue
            td = elapsed - delay
            p['vy'] -= 0.12
            p['y'] += p['vy']
            p['x'] += p['vx']
            p['vx'] *= 0.995
            p['x'] += math.sin(td * 2.5 + p['wind_phase']) * 2.5
            p['rot'] += p['spin_speed']
            p['alpha'] = max(0, p['alpha'] - 0.018)
            p['scale'] *= 0.975
            if random.random() < 0.1 and p['alpha'] > 0.15:
                spawn_sparkle(p['x'], p['y'], p['palette'][4])
            if p['alpha'] <= 0.02 or p['scale'] < 0.02 or p['y'] < -60 or p['y'] > h+60 or p['x'] < -60 or p['x'] > w+60:
                particles.remove(p)

    if is_dissipating and len(particles) == 0:
        is_dissipating = False

    # ---------- Sparkle Lifecycle ----------
    for s in sparkles[:]:
        if now - s['spawn_time'] > s['life'] or s['alpha'] < 0.03:
            sparkles.remove(s); continue
        s['y'] += s['vy']; s['x'] += s['vx']
        s['alpha'] *= 0.93; s['size'] *= 0.97

    # ---------- Render Flowers ----------
    for p in particles:
        fx, fy = p['x'], p['y']
        size = int(p['size'] * max(p['scale'], 0.01)) + 3
        margin = int(size * 2.5)
        x0, y0 = int(max(fx-margin, 0)), int(max(fy-margin, 0))
        x1, y1 = int(min(fx+margin, w)), int(min(fy+margin, h))
        if x1 <= x0 or y1 <= y0: continue
        roi = frame[y0:y1, x0:x1]
        if roi.size == 0: continue
        overlay = roi.copy()
        pl = dict(p); pl['x'] = p['x']-x0; pl['y'] = p['y']-y0
        draw_flower(overlay, pl, now)
        alpha = max(0.0, min(1.0, p['alpha']))
        cv2.addWeighted(overlay, alpha, roi, 1-alpha, 0, dst=roi)

    # ---------- Render Sparkles ----------
    for s in sparkles:
        sx, sy = int(s['x']), int(s['y'])
        if 0 <= sx < w and 0 <= sy < h:
            r = max(1, int(s['size']))
            a = max(0.0, min(1.0, s['alpha']))
            m = r+2
            x0, y0 = max(0, sx-m), max(0, sy-m)
            x1, y1 = min(w, sx+m+1), min(h, sy+m+1)
            if x1 > x0 and y1 > y0:
                roi = frame[y0:y1, x0:x1]
                if roi.size > 0:
                    ov = roi.copy()
                    cv2.circle(ov, (sx-x0, sy-y0), r+1, s['color'], -1, cv2.LINE_AA)
                    cv2.circle(ov, (sx-x0, sy-y0), r, (255,255,255), -1, cv2.LINE_AA)
                    cv2.addWeighted(ov, a*0.7, roi, 1-a*0.7, 0, dst=roi)

    # Resize to fullscreen
    display = cv2.resize(frame, (SCREEN_W, SCREEN_H), interpolation=cv2.INTER_LINEAR)
    cv2.imshow(WIN_NAME, display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()