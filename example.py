from machine import Pin
import LCD
import time

display = LCD.LCD(Pin(14), Pin(15))

display.write('...Then, shalt '
              'thou count to three.')

time.sleep(3)

display.clear()
display.write_left('1', 0)
time.sleep(1)
display.write_center('2', 0)
time.sleep(1)
display.write_right('5', 0)
time.sleep(1)
display.write_center('Three, sir!', 1)
