from machine import I2C
import time


LCD_CLEARDISPLAY = 1

LCD_DISPLAYCONTROL = 1 << 3
LCD_DISPLAYON = 1 << 2
LCD_CURSORON = 1 << 1
LCD_BLINKON = 1 << 0

LCD_ENTRYMODESET = 1 << 2
LCD_ENTRYLEFT = 1 << 1


LCD_ENABLE_BIT = 1 << 2
LCD_BACKLIGHT = 1 << 3


LCD_COMMAND = 0 << 0
LCD_CHARACTER = 1 << 0

LCD_RETURNHOME = 1 << 1

LCD_SET_DDRAM = 1 << 7


class LCDException(Exception):
    pass


class LCD:
    """
    Interface for the lcd display HD44780U operated over I2C.
    """

    def __init__(self, sda_pin, scl_pin,
                 display_address=None, rows=4, cols=20):
        """
        sda_pin, scl_pin: Pin objects for the I2C interface,
            ex. Pin(14), Pin(15)
        display_address: address of the LCD display on I2C interface.
            Usual value is 0x27.
        If not provided, it will be attempted to get
            the device address automatically.
        """
        self.__i2c = I2C(1, sda=sda_pin, scl=scl_pin)
        if display_address is None:
            devices = self.__i2c.scan()
            if len(devices) == 0:
                raise LCDException(
                    'Display could not be initialised - no i2c device found')
            self.__display_address = devices[0]
        else:
            self.__display_address = display_address

        self.__rows = rows
        self.__cols = cols
        self.__send_byte(0x03, LCD_COMMAND)
        self.__send_byte(0x03, LCD_COMMAND)
        self.__send_byte(0x03, LCD_COMMAND)
        self.__send_byte(0x02, LCD_COMMAND)
        self.__send_byte(LCD_ENTRYMODESET | LCD_ENTRYLEFT, LCD_COMMAND)

        self.__display_on = True
        self.__blink_on = False
        self.__cursor_on = False

        self.__update_display_control()

        self.__send_byte(LCD_CLEARDISPLAY, LCD_COMMAND)

    def __update_display_control(self):
        display_control = LCD_DISPLAYCONTROL

        if self.__display_on:
            display_control |= LCD_DISPLAYON

        if self.__blink_on:
            display_control |= LCD_BLINKON

        if self.__cursor_on:
            display_control |= LCD_CURSORON

        self.__send_byte(display_control, LCD_COMMAND)

    def __write_i2c_byte(self, byte):
        """ writes a single byte
        byte: integer with range [0; 256),
            will be converted to byte inside the function.
        """
        if type(byte) is not int:
            raise LCDException("integer expected for writing to i2c")

        if not (0 <= byte <= 255):
            raise LCDException("byte for sending to i2c is out of bounds")

        self.__i2c.writeto(self.__display_address, bytes([byte]))

    def __toggle_enable(self, value):
        """
        Wait, send the value again with enable bit on, wait,
        then again with enable bit off, then wait.
        """
        time.sleep_us(600)
        self.__write_i2c_byte(value | LCD_ENABLE_BIT)
        time.sleep_us(600)
        self.__write_i2c_byte(value & ~LCD_ENABLE_BIT)
        time.sleep_us(600)

    def __send_byte(self, byte, mode):
        """
        Send byte of data to lcd.
        r/w, rs, enable bits are set appropriately

        Final byte format is:
        bit |   7   |   6   |   5   |   4   |     3     |  2     |  1  | 0
        ----|-------|-------|-------|-------|-----------|--------|-----|----
        val | D7/D3 | D6/D2 | D5/D1 | D4/D0 |     1     | enable | r/w | rs
        """

        first = mode | (byte & 0xf0) | 1 << 3
        second = mode | ((byte << 4) & 0xf0) | 1 << 3

        for byte in [first, second]:
            # set the data
            self.__write_i2c_byte(byte)
            # set enable = 1, enable = 0 to sample the data
            self.__toggle_enable(byte)

    def set_cursor(self, row, col):
        """Set cursor to position [row,col]."""
        row_offsets = [0x00, 0x40, 0x14, 0x54]

        if row not in range(len(row_offsets)):
            raise LCDException('invalid row for cursor: ' + str(row))

        if not (0 <= col < self.__cols):
            raise LCDException('invalid column for cursor: ' + str(col))

        value = (LCD_SET_DDRAM | col) + row_offsets[row]
        self.__send_byte(value, LCD_COMMAND)

    def write_character(self, character):
        """Send a single character to the display."""
        if type(character) is not str:
            raise LCDException("a character (str) is expected")

        if not len(character) == 1:
            raise LCDException("a single character is expected, got a string")

        self.__send_byte(ord(character), LCD_CHARACTER)

    def write(self, string, row=0) -> int:
        """
        Write string to display from row=row and col=0,
        wrap words to new lines.
        Text that cannot fit will be trimmed.
        Returns the next row that is free for writing.
        """

        if type(string) is not str:
            raise LCDException('string is expected for displaying')

        words = string.split()
        words_idx = 0
        while row < self.__rows:
            current_line = ''

            while (words_idx < len(words)) and \
                  (len(current_line) + len(words[words_idx]) <= self.__cols):
                current_line += words[words_idx]
                words_idx += 1
                current_line += ' '

            self.set_cursor(row, 0)
            if len(current_line) > 0:
                self.write_string(current_line.rstrip())
            elif words_idx < len(words):
                # word can never fit on a line, so split it at the end
                self.write_string(words[words_idx][:self.__cols])
                words[words_idx] = words[words_idx][self.__cols:]
            else:
                return row

            row += 1

        return row

    def write_string(self, string):
        """
        Write string to the display
        (from current position, and without text wrapping).
        """
        if type(string) is not str:
            raise LCDException("string expected for writing to display")

        for character in string:
            self.write_character(character)

    def write_center(self, string, row):
        """Write string at center of given row."""

        if type(string) is not str:
            raise LCDException('expected string to write')

        if not (0 <= row < self.__rows):
            raise LCDException('invalid row for writing to display')

        length = len(string)
        self.set_cursor(row, (self.__cols - length) // 2)
        self.write_string(string)

    def write_left(self, string, row):
        """Write text at given row, start at column 0."""
        if type(string) is not str:
            raise LCDException('expected string to write')

        if not (0 <= row < self.__rows):
            raise LCDException('invalid row for writing to display')

        self.set_cursor(row, 0)
        self.write_string(string)

    def write_right(self, string, row):
        """Write text at given row, align to right."""
        if type(string) is not str:
            raise LCDException('expected string to write')

        if not (0 <= row < self.__rows):
            raise LCDException('invalid row for writing to display')

        self.set_cursor(row, self.__cols - len(string))
        self.write_string(string)

    def clear(self):
        """clear the display"""
        self.__send_byte(LCD_CLEARDISPLAY, LCD_COMMAND)

    def return_home(self):
        """Set cursor position to beginning."""
        self.__send_byte(LCD_RETURNHOME, LCD_COMMAND)

    def display_on(self, value=True):
        """Set the display on / off."""
        self.__display_on = value
        self.__update_display_control()

    def blink_on(self, value=True):
        """
        Set blinking of display on / off.
        Blinking on turns cursor on as well.
        """
        self.__blink_on = value
        if self.__blink_on:
            self.__cursor_on = True
        self.__update_display_control()

    def cursor_on(self, value=True):
        """Set cursor on / off."""
        self.__cursor_on = value
        self.__update_display_control()

    def display_off(self):
        """Set the display off."""
        self.display_on(False)

    def cursor_off(self):
        """Set the cursor off."""
        self.cursor_on(False)

    def blink_off(self):
        """Set the blink off."""
        self.blink_on(False)
