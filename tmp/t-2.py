from machine import Pin
import time
import rp2

# 配置WS2812B LED的数量
NUM_LEDS = 1

# 定义PIO程序来控制WS2812B LED闪烁
@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    # out_shiftdir=rp2.PIO.SHIFT_LEFT,
    # autopull=True,
    # pull_thresh=24,
)
def ws2812_blink():
    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
    irq(rel(0))
    set(pins, 1)
    set(x, 39)                  [5]  # 设置x为39，总共需要40次循环
    label("delay_high")
    nop()                       [29]   # 延迟29个周期
    jmp(x_dec, "delay_high")     # x减1后如果不为零则跳转到delay_high

    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
    nop()
    set(pins, 0)
    set(x, 39)                  [5]  # 设置x为39，总共需要40次循环
    label("delay_low")
    nop()                       [29]   # 延迟29个周期
    jmp(x_dec, "delay_low")      # x减1后如果不为零则跳转到delay_low

# 创建StateMachine实例，使用第0个状态机，频率设置为2000Hz，输出引脚设置为Pin(25)
sm = rp2.StateMachine(0, ws2812_blink, freq=2000, sideset_base=Pin(16))

# 设置中断处理程序，当状态机触发中断时打印当前时间戳
sm.irq(lambda p: print(time.ticks_ms()))

# 启动状态机
sm.active(1)

# 主循环，保持程序运行
while True:
    time.sleep(1)
