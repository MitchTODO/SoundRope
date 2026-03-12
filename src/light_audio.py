from machine import Pin, ADC
import neopixel
import time

# ===== CONFIG =====
LED_PIN = 18
ADC_PIN = 26          # GP26 = ADC0
NUM_PIXELS = 90
BRIGHTNESS = 0.20

# Audio tuning from your test code
SAMPLES_PER_FRAME = 60
NOISE_FLOOR = 1200
SMOOTHING = 0.5
PEAK_FALL = 0.02
MIDPOINT = 15000
MAX_LEVEL = 18000

# ===== SETUP =====
np = neopixel.NeoPixel(Pin(LED_PIN, Pin.OUT), NUM_PIXELS)
adc = ADC(ADC_PIN)

COLOR_TABLE = []


def set_pixel(i, r, g, b):
    np[i] = (
        int(r * BRIGHTNESS),
        int(g * BRIGHTNESS),
        int(b * BRIGHTNESS)
    )


def clear():
    for i in range(NUM_PIXELS):
        np[i] = (0, 0, 0)
    np.write()


def hsv_to_rgb(h, s=1.0, v=1.0):
    i = int(h * 6)
    f = (h * 6) - i
    p = int(255 * v * (1 - s))
    q = int(255 * v * (1 - f * s))
    t = int(255 * v * (1 - (1 - f) * s))
    v = int(255 * v)

    i = i % 6

    if i == 0:
        return (v, t, p)
    elif i == 1:
        return (q, v, p)
    elif i == 2:
        return (p, v, t)
    elif i == 3:
        return (p, q, v)
    elif i == 4:
        return (t, p, v)
    else:
        return (v, p, q)


def build_color_table():
    global COLOR_TABLE
    COLOR_TABLE = []

    for i in range(NUM_PIXELS):
        h = 0.33 - (0.33 * i / (NUM_PIXELS - 1))
        COLOR_TABLE.append(hsv_to_rgb(h, 1.0, 1.0))


def startup_flash():
    clear()
    time.sleep(0.15)

    for i in range(NUM_PIXELS):
        set_pixel(i, 40, 40, 40)
    np.write()
    time.sleep(0.15)

    clear()
    time.sleep(0.15)


def read_level():
    total = 0

    for _ in range(SAMPLES_PER_FRAME):
        sample = adc.read_u16()
        total += abs(sample - MIDPOINT)

    level = total // SAMPLES_PER_FRAME
    print(level)

    if level < NOISE_FLOOR:
        level = 0
    else:
        level -= NOISE_FLOOR

    return level


def draw_meter(level_fraction, peak_fraction):
    lit = int(level_fraction * NUM_PIXELS)

    # clear everything first
    for i in range(NUM_PIXELS):
        np[i] = (0, 0, 0)

    # fill from top down
    for n in range(lit):
        idx = NUM_PIXELS - 1 - n
        r, g, b = COLOR_TABLE[idx]
        set_pixel(idx, r, g, b)

    # peak dot from top down
    if peak_fraction > 0:
        peak_idx = NUM_PIXELS - 1 - int(peak_fraction * (NUM_PIXELS - 1))
        if 0 <= peak_idx < NUM_PIXELS:
            set_pixel(peak_idx, 255, 255, 255)

    np.write()


# ===== MAIN =====
build_color_table()
startup_flash()

smoothed_level = 0.0
peak_level = 0.0

while True:
    raw_level = read_level()

    level = raw_level / MAX_LEVEL
    if level > 1.0:
        level = 1.0

    smoothed_level = (SMOOTHING * smoothed_level) + ((1.0 - SMOOTHING) * level)

    if smoothed_level > peak_level:
        peak_level = smoothed_level
    else:
        peak_level -= PEAK_FALL
        if peak_level < 0:
            peak_level = 0

    draw_meter(smoothed_level, peak_level)
    time.sleep(0.005)