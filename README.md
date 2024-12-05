# HD44780U-driver

This is a small driver for LCD HD44780U display with I2C communication.

I used the driver on Raspberry Pico 2 with micropython and 20x4 LDC display.

To use, simply add the file `LCD.py` to your project.

You can try out the example. For that, connect SDA to pin 14 and SCL to pin 15 on Pico.
For the display to work properly, you will probably also need a level shifter from 3.3 V to 5 V.

The code is inspired by the (https://github.com/raspberrypi/pico-examples/blob/master/i2c/lcd_1602_i2c/lcd_1602_i2c.c)[C example of LCD display control on Raspberry Pi GitHub].
