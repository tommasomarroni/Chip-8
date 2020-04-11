# Conversions:  DEC TO HEX:     format(i, '04X') or hex()
#               HEX TO DEC:     int(i, 16)

# Remarks:      (x | 0) = x
#               (x & 1) = x
#               (x & 0) = 0
#               !(x & 0) = 1

# Examples:     0xabcd & 0x0fff = 0x0bcd
#               0xabcd & 0x00ff = 0x00cd
#               0xabcd & 0x0f00 = 0x0b00
#               0xabcd & 0xf000 = 0xa000

import sys
import time
import pyglet
import random

from textwrap import wrap

class Chip8(pyglet.window.Window):

    PIXEL = "media/pixel.png"
    SOUND = "media/sound.wav"

    # Constant variables used with & operator in order to cut registers at 8 and 16 bits
    _8BIT = 0xff
    _16BIT = 0xffff

    # START: OPCODE INSTRUCTIONS ...

    def _0xxx(self):
        self.decoder_0.get(self.opcode, -1)()

    def _00e0(self):
        self.display_buff = [0]*64*32
        self._pc += 2

    def _00ee(self):
        self._pc = self.stack.pop() & Chip8._16BIT
        self._pc += 2

    def _1xxx(self):
        self._pc = (self.opcode & 0x0fff) & Chip8._16BIT

    def _2xxx(self):
        self.stack.append(self._pc & Chip8._16BIT)
        self._pc = (self.opcode & 0x0fff) & Chip8._16BIT

    def _3xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        kk = self.opcode & 0xff
        if self.V[x] == kk:
            self._pc += 2
        self._pc += 2

    def _4xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        kk = self.opcode & 0xff
        if self.V[x] != kk:
            self._pc += 2
        self._pc += 2

    def _5xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if self.V[x] == self.V[y]:
            self._pc += 2
        self._pc += 2

    def _6xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        kk = self.opcode & 0xff
        self.V[x] = kk & Chip8._8BIT
        self._pc += 2

    def _7xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        kk = self.opcode & 0xff
        self.V[x] = (self.V[x] + kk) & Chip8._8BIT
        self._pc += 2

    def _8xxx(self):
        self.decoder_8.get(self.opcode & 0xf00f, -1)()

    def _8xx0(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        self.V[x] = self.V[y] & Chip8._8BIT
        self._pc += 2

    def _8xx1(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        self.V[x] = (self.V[x] | self.V[y]) & Chip8._8BIT
        self._pc += 2

    def _8xx2(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        self.V[x] = (self.V[x] & self.V[y]) & Chip8._8BIT
        self._pc += 2

    def _8xx3(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        self.V[x] = (self.V[x] ^ self.V[y]) & Chip8._8BIT
        self._pc += 2

    def _8xx4(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if self.V[x] + self.V[y] > 0xff:
            self.V[0xf] = 1
        else:
            self.V[0xf] = 0
        self.V[x] = (self.V[x] + self.V[y]) & Chip8._8BIT
        self._pc += 2

    def _8xx5(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if self.V[x] < self.V[y]:
            self.V[0xf] = 0
        else:
            self.V[0xf] = 1
        self.V[x] = (self.V[x] - self.V[y]) & Chip8._8BIT
        self._pc += 2

    def _8xx6(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if (self.V[x] & 0x1) == 0x1:
            self.V[0xf] = 1
        else:
            self.V[0xf] = 0
        self.V[x] = (self.V[x] >> 1) & Chip8._8BIT
        self._pc += 2

    def _8xx7(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if self.V[y] < self.V[x]:
            self.V[0xf] = 0
        else:
            self.V[0xf] = 1
        self.V[x] = (self.V[y] - self.V[x]) & Chip8._8BIT
        self._pc += 2

    def _8xxe(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if (self.V[x] & 0x80) == 0x80:
            self.V[0xf] = 1
        else:
            self.V[0xf] = 0
        self.V[x] = (self.V[x] << 1) & Chip8._8BIT
        self._pc += 2

    def _9xxx(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        if self.V[x] != self.V[y]:
            self._pc += 2
        self._pc += 2

    def _axxx(self):
        self.i = (self.opcode & 0x0fff) & Chip8._16BIT
        self._pc += 2

    def _bxxx(self):
        self._pc = ((self.opcode & 0x0fff) + self.V[0]) & Chip8._16BIT

    def _cxxx(self):
        x = (self.opcode & 0x0f00) >> 8
        kk = self.opcode & 0xff
        self.V[x] = (int(random.random() * 255) & kk) & Chip8._8BIT
        self._pc += 2

    def _dxxx(self):
        x = (self.opcode & 0x0f00) >> 8
        y = (self.opcode & 0x00f0) >> 4
        n = self.opcode & 0xf
        self.V[0xf] = 0

        for i in range(0, n):
            line = self.memory[self.i + i]
            current_y = (self.V[y] & 0xff) + i

            for j in range(8):
                current_x = (self.V[x] & 0xff) + j
                current_loc = current_x + current_y * 64

                if current_y >= 32 or current_x >= 64:
                    continue
                mask = 0x1 << (7 - j)
                newBit = (mask & line) >> (7 - j)
                self.display_buff[current_loc] = newBit ^ self.display_buff[current_loc]

                if(self.display_buff[current_loc] == 0 and newBit == 1):
                    self.V[0xf] = 1
        self.draw_flag = True
        self._pc += 2

    def _exxx(self):
        self.decoder_e.get(self.opcode & 0xf0ff, -1)()

    def _ex9e(self):
        x = (self.opcode & 0x0f00) >> 8
        if self.keys[self.V[x] & 0xf] == 1:
            self._pc += 2
        self._pc += 2

    def _exa1(self):
        x = (self.opcode & 0x0f00) >> 8
        if self.keys[self.V[x] & 0xf] == 0:
            self._pc += 2
        self._pc += 2

    def _fxxx(self):
        self.decoder_f.get(self.opcode & 0xf0ff, -1)()

    def _fx07(self):
        x = (self.opcode & 0x0f00) >> 8
        self.V[x] = self.dt & Chip8._8BIT
        self._pc += 2

    def _fx0a(self):
        x = (self.opcode & 0x0f00) >> 8
        key = self.get_key()
        if key >= 0:
            self.V[x] = key & Chip8._8BIT
            self._pc += 2

    def _fx15(self):
        x = (self.opcode & 0x0f00) >> 8
        self.dt = self.V[x] & Chip8._8BIT
        self._pc += 2

    def _fx18(self):
        x = (self.opcode & 0x0f00) >> 8
        self.st = self.V[x] & Chip8._8BIT
        self._pc += 2

    def _fx1e(self):
        x = (self.opcode & 0x0f00) >> 8
        self.i = (self.i + self.V[x]) & Chip8._16BIT
        self._pc += 2

    def _fx29(self):
        x = (self.opcode & 0x0f00) >> 8
        self.i = (5*self.V[x]) & Chip8._16BIT
        self._pc += 2

    def _fx33(self):
        x = (self.opcode & 0x0f00) >> 8
        self.memory[self.i] = (self.V[x] // 100) & Chip8._8BIT
        self.memory[self.i + 1] = ((self.V[x] % 100) // 10) & Chip8._8BIT
        self.memory[self.i + 2] = (self.V[x] % 10) & Chip8._8BIT
        self._pc += 2

    def _fx55(self):
        x = (self.opcode & 0x0f00) >> 8
        for i in range(0, x + 1):
            self.memory[self.i + i] = self.V[i] & Chip8._8BIT
        self.i = self.i + x + 1
        self._pc += 2

    def _fx65(self):
        x = (self.opcode & 0x0f00) >> 8
        for i in range(0, x + 1):
            self.V[i] = self.memory[self.i + i] & Chip8._8BIT
        self.i = self.i + x + 1
        self._pc += 2

    # ... END: OPCODE INSTRUCTIONS

    # START: INITIALIZERS ...

    def init_keyboard(self):
        self.keyboard = {   pyglet.window.key._1: 0x1,
                            pyglet.window.key._2: 0x2,
                            pyglet.window.key._3: 0x3,
                            pyglet.window.key._4: 0xc,
                            pyglet.window.key.Q: 0x4,
                            pyglet.window.key.W: 0x5,
                            pyglet.window.key.E: 0x6,
                            pyglet.window.key.R: 0xd,
                            pyglet.window.key.A: 0x7,
                            pyglet.window.key.S: 0x8,
                            pyglet.window.key.D: 0x9,
                            pyglet.window.key.F: 0xe,
                            pyglet.window.key.Z: 0xa,
                            pyglet.window.key.X: 0,
                            pyglet.window.key.C: 0xb,
                            pyglet.window.key.V: 0xf
                            }

    def init_fontset(self):
        self.fontset = [    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
                            0x20, 0x60, 0x20, 0x20, 0x70, # 1
                            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
                            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
                            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
                            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
                            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
                            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
                            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
                            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
                            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
                            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
                            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
                            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
                            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
                            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
                            ]

    def init_decoders(self):
        self.decoder = {    0x0000: self._0xxx,
                            0x1000: self._1xxx,
                            0x2000: self._2xxx,
                            0x3000: self._3xxx,
                            0x4000: self._4xxx,
                            0x5000: self._5xxx,
                            0x6000: self._6xxx,
                            0x7000: self._7xxx,
                            0x8000: self._8xxx,
                            0x9000: self._9xxx,
                            0xa000: self._axxx,
                            0xb000: self._bxxx,
                            0xc000: self._cxxx,
                            0xd000: self._dxxx,
                            0xe000: self._exxx,
                            0xf000: self._fxxx,
                            }

        self.decoder_0 = {  0x00e0: self._00e0,
                            0x00ee: self._00ee,
                            }

        self.decoder_8 = {  0x8000: self._8xx0,
                            0x8001: self._8xx1,
                            0x8002: self._8xx2,
                            0x8003: self._8xx3,
                            0x8004: self._8xx4,
                            0x8005: self._8xx5,
                            0x8006: self._8xx6,
                            0x8007: self._8xx7,
                            0x800e: self._8xxe,
                            }

        self.decoder_e = {  0xe09e: self._ex9e,
                            0xe0a1: self._exa1,
                            }

        self.decoder_f = {  0xf007: self._fx07,
                            0xf00a: self._fx0a,
                            0xf015: self._fx15,
                            0xf018: self._fx18,
                            0xf01e: self._fx1e,
                            0xf029: self._fx29,
                            0xf033: self._fx33,
                            0xf055: self._fx55,
                            0xf065: self._fx65,
                            }

    # ... END: INITIALIZERS

    # START: MAIN CLASS FUNCTIONS ...

    def __init__(self, console_width, console_height, start = 0x200):
        super().__init__(console_width, console_height)     # Pyglet window.
        self.PROGRAM_START = start                          # Start of Chip-8 program. ETI 660 programs can start at 0x600.
        self.init_keyboard()                                # Initialize keyboard.
        self.init_fontset()                                 # Initialize fontset.
        self.init_decoders()                                # Initialize decoders dictionaries.
        self.initialize()                                   # Initialize chip memory, stack, registers, display, timers and load fontset.

        # Load pixel and sound.
        self.pixel = pyglet.resource.image(Chip8.PIXEL)
        self.sound = pyglet.resource.media(Chip8.SOUND, streaming = False)

        self.batch = pyglet.graphics.Batch()
        self.sprites = []
        for i in range(0, 64*32):
            self.sprites.append(pyglet.sprite.Sprite(self.pixel, batch = self.batch))

    def initialize(self):
        self.memory = [0]*4096                  # Memory: 4096, 8-bit each.

        self.V = [0]*16                         # General purpose registers: V0 to VF, 8-bit each.
        self.i = 0                              # Index register, 16-bit.
        self.dt = 0                             # Delay Timer register, 8-bit.
        self.st = 0                             # Sound Timer register, 8-bit.
        self._pc = 0                            # Program Counter, 16-bit.
        self._sp = 0                            # Stack Pointer, 8-bit.

        self.stack = []                         # Stack: 16, 16-bit each.
        self.opcode = 0                         # Opcode, 16-bit each.

        self.display_buff = [0]*64*32           # Display buffer, 1-bit each.
        self.keys = [0]*16                      # Keyboard inputs, 4-bit each.

        self._pc = self.PROGRAM_START           # Programs start at 0x200.

        self.draw_flag = False                  # Refresh console flag.
        self.stop_flag = False                  # Stop emulation flag.

        self.timer = time.perf_counter()        # Start time of 60Hz clock for Delay and Sound Timers.

        # Load fontset in memory.
        for i in range(0, len(self.fontset)):
            self.memory[i] = self.fontset[i]

    def load_rom(self):
        # Open program binary file.
        try:
            rom_file = open(sys.argv[1], "rb")
            rom_buffer_hex = rom_file.read().hex()
            rom_buffer = [int(i, 16) for i in wrap(rom_buffer_hex, 2)]
            rom_file.close()
        except:
            print("Usage: python", sys.argv[0], "<chip-8 ROM>")
            self.stop_flag = True
            self.close()
            sys.exit(1)

        # Load program in memory.
        for i in range(0, len(rom_buffer)):
            self.memory[i + self.PROGRAM_START] = rom_buffer[i]

    # Start emulation loop.
    def emulate(self):
        self.clear()                    # Clear console.
        self.flip()                     # Flip colors.
        while not self.stop_flag:
            self.dispatch_events()
            self.cycle()                # Single cycle: fetch, decode, execute opcode.
            self.refresh_console()      # Refresh console.

    def cycle(self):
        # Fetch.
        self.opcode = (self.memory[self._pc] << 8) | self.memory[self._pc + 1]

        # Decode and execute.
        try:
            self.decoder.get(self.opcode & 0xf000, -1)()
        except:
            print("Unknown opcode:", str(hex(self.opcode)))
            sys.exit(1)

        # Decrement delay and sound timer registers at 60Hz
        if (time.perf_counter() - self.timer) >= 1/60:
            self.timer = time.perf_counter()

            # Decrement delay timer register.
            if self.dt > 0:
                self.dt -= 1
            # Decrement sound timer register.
            if self.st > 0:
                self.st -= 1
                if self.st == 0:
                    self.sound.play()

    # Refresh console.
    def refresh_console(self):
        if self.draw_flag:
            for i in range(0, 64*32):
                if self.display_buff[i] == 1:
                    self.sprites[i].x = (i % 64) * 10
                    self.sprites[i].y = 310 - ((i // 64) * 10)
                    self.sprites[i].batch = self.batch
                else:
                    self.sprites[i].batch = None
            self.clear()
            self.batch.draw()
            self.flip()
            self.draw_flag = False

    # Get current pressed key.
    def get_key(self):
        for i in range(0, 16):
            if self.keys[i] == 1:
                return i
        return -1

    # Override pyglet.window.Window.on_key_press function.
    def on_key_press(self, symbol, modifiers):
        key_down = self.keyboard.get(symbol, -1)
        if key_down != -1:
            self.keys[key_down] = 1
        else:
            super().on_key_press(symbol, modifiers)

    # Override pyglet.window.Window.on_key_release function.
    def on_key_release(self, symbol, modifiers):
        key_up = self.keyboard.get(symbol, -1)
        if key_up != -1:
            self.keys[key_up] = 0

    # Override pyglet.window.Window.on_close function.
    def on_close(self):
        self.stop_flag = True

    # END: MAIN CLASS FUNCTIONS ...
