import time

from ws2812 import WS2812, timing_calculator

if __name__ == "__main__":
    timing_calculator(4_000_000)  # try it yourself

    led = WS2812(12, "/dev/spidev0.0", 4_000_000)
    hue = 0
    while True:
        hue += 0.5
        for i in range(len(led)):
            led[i] = led.hsv_to_rgb(hue + i * 10, 255, 255, merge=True)
        led.show()
        time.sleep(0.01)
