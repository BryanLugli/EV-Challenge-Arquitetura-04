# =============================================================
#  lcd_i2c.py  -  Driver mínimo para LCD HD44780 com módulo
#  I2C PCF8574 (padrão do Wokwi: endereço 0x27)
#
#  Mapa do PCF8574: P0=RS  P1=RW  P2=EN  P3=Backlight  P4..P7=D4..D7
#  O LCD trabalha em modo 4 bits: cada byte vai em 2 "nibbles".
# =============================================================
import time

_RS = 0x01
_EN = 0x04
_BL = 0x08
_OFFSETS = (0x00, 0x40, 0x14, 0x54)  # início de cada linha (LCD 20x4)


class LcdI2C:
    def __init__(self, i2c, addr=0x27, cols=20, rows=4):
        self.i2c = i2c
        self.addr = addr
        self.cols = cols
        self.rows = rows
        time.sleep_ms(50)
        # Sequência de inicialização do HD44780 em modo 4 bits
        for _ in range(3):
            self._nibble(0x30, 0)
            time.sleep_ms(5)
        self._nibble(0x20, 0)
        self.cmd(0x28)   # 4 bits, 2+ linhas, fonte 5x8
        self.cmd(0x0C)   # display ligado, sem cursor
        self.cmd(0x06)   # cursor anda para a direita
        self.clear()

    def _pulso(self, dado):
        self.i2c.writeto(self.addr, bytes([dado | _EN | _BL]))
        time.sleep_us(1)
        self.i2c.writeto(self.addr, bytes([(dado & ~_EN) | _BL]))
        time.sleep_us(50)

    def _nibble(self, alto, rs):
        self._pulso((alto & 0xF0) | rs)

    def _enviar(self, valor, rs):
        self._nibble(valor & 0xF0, rs)          # 4 bits mais significativos
        self._nibble((valor << 4) & 0xF0, rs)   # 4 bits menos significativos

    def cmd(self, c):
        self._enviar(c, 0)
        if c in (0x01, 0x02):
            time.sleep_ms(2)

    def clear(self):
        self.cmd(0x01)

    def move_to(self, col, linha):
        self.cmd(0x80 | (col + _OFFSETS[linha]))

    def putstr(self, texto):
        for ch in texto:
            self._enviar(ord(ch), _RS)
