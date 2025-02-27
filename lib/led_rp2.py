"""PIO文档：https://docs.micropython.org/en/latest/rp2/tutorial/pio.html"""

import rp2
import array


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24,
)
def _ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()                                   # type: ignore
    label("bitloop")                                # type: ignore
    out(x, 1)               .side(0)    [T3 - 1]    # type: ignore
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]    # type: ignore
    jmp("bitloop")          .side(1)    [T2 - 1]    # type: ignore 
    label("do_zero")                                # type: ignore
    nop()                   .side(0)    [T2 - 1]    # type: ignore
    wrap()                                          # type: ignore


class WS2812:

    def __init__(self, pin, num_leds=1) -> None:
        self.ar = array.array("I", [0 for _ in range(num_leds)])
        self.sm = rp2.StateMachine(0, _ws2812, freq=80_000_000, sideset_base=pin)
        self.sm.active(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sm.active(0)

    def set_rgb(self, r,g,b):
        self.ar[0] = g << 16 | r<<8| b  # TODO 目前仅一个LED灯的情况
        self.sm.put(self.ar, 8)

    def red(self):
        self.set_rgb(100, 0, 0)

    def green(self):
        self.set_rgb(0,100,0)

    def blue(self):
        self.set_rgb(0,0,100)

    def close(self):
        self.set_rgb(0,0,0)


if __name__ == "__main__":
    import time
    from machine import Pin
    with WS2812(Pin(17)) as led:
        led.red()
        print(f"down {17}")