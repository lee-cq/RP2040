# Example using PIO to blink an LED and raise an IRQ at 1Hz.
# 使用PIO闪烁LED并以1Hz中断IRQ

import time
from machine import Pin
import rp2


@rp2.asm_pio(
        set_init=rp2.PIO.OUT_LOW,
        out_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=True,
        pull_thresh=24,
             )
def blink_1hz():
    # type: ignore
    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
    irq(rel(0))                                 # type: ignore
    set(pins, 1)                                # type: ignore
    set(x, 31)                  [5]             # type: ignore
    label("delay_high")                         # type: ignore
    nop()                       [29]            # type: ignore
    jmp(x_dec, "delay_high")                    # type: ignore

    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
    nop()                                       # type: ignore
    set(pins, 0)                                # type: ignore
    set(x, 31)                  [5]             # type: ignore
    label("delay_low")                          # type: ignore
    nop()                       [29]            # type: ignore
    jmp(x_dec, "delay_low")                     # type: ignore
    # type: ignore


# Create the StateMachine with the blink_1hz program, outputting on Pin(25).
sm = rp2.StateMachine(0, blink_1hz, freq=2000, set_base=Pin(25))

# Set the IRQ handler to print the millisecond timestamp.
sm.irq(lambda p: print(time.ticks_ms()))

# Start the StateMachine.
sm.active(1)

while True:
    time.sleep(1)