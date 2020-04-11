from chip8 import Chip8

def main():

    # Create instance of Chip8.
    chip = Chip8(640, 320)

    # Initialize chip memory, stack, registers, display, timers and load fontset if needed.
    chip.initialize()

    # Load chip-8 program in memory.
    chip.load_rom()

    # Start emulating cycles
    chip.emulate()

main()
