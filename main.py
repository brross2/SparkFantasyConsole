import time
import pygame

from BIOS import bios_source
from VM.Lexer import Lexer
from VM.Parser import Parser
from VM.Compiler import Compiler
from VM.VirtualMachine import SparkVM
from VM.Hardware import SparkHardware

# 2. EL CÓDIGO DEL JUEGO (Tu demo de la pelota)
game_source = """
x = 76
y = 76

function update()
   if btn(1) then x = x + 2 end
   if btn(0) then x = x - 2 end
   if btn(2) then y = y - 2 end
   if btn(3) then y = y + 2 end
end

function draw()
   cls()          -- <--- AHORA LLAMA DIRECTO AL HARDWARE (Super rápido)
   spr(1, x, y)
   pset(x, y, 7)
end
"""


def load_cartridge(vm, source_code):
    print(f"--- CARGANDO CODIGO ({len(source_code)} bytes) ---")
    try:
        tokens = Lexer(source_code)
        ast = Parser(tokens).parse()
        compiler = Compiler()
        compiler.compile(ast)
        vm.code = compiler.code
        vm.consts = compiler.consts
        vm.reset()
        # Inicializar variables globales ejecutando el script una vez
        while not vm.halted and vm.ip < len(vm.code):
            vm.step()
        vm.halted = False
    except Exception as e:
        print(f"ERROR CARGANDO CARTUCHO: {e}")


def main():
    hw = SparkHardware(scale=3)
    vm = SparkVM([], [], hardware=hw)

    # Cargar BIOS
    load_cartridge(vm, bios_source)

    bios_running = True
    start_time = time.time()

    print("--- INICIANDO SISTEMA ---")

    while hw.running:
        hw.handle_input()

        # --- CAMBIO IMPORTANTE: YA NO HACEMOS hw.clear_screen() ---
        # Dejamos que el software decida cuándo borrar.
        # hw.clear_screen() <--- ELIMINADO/COMENTADO

        if bios_running:
            vm.call_function("update")
            vm.call_function("draw")

            # Esperamos 12 segundos para ver toda la intro
            if time.time() - start_time > 12:
                print("BIOS completada. Ejecutando juego...")
                # Limpiamos pantalla físicamente antes de cambiar de cartucho
                hw.clear_screen()
                load_cartridge(vm, game_source)
                bios_running = False
        else:
            vm.call_function("update")
            vm.call_function("draw")

        hw.flip()

    pygame.quit()


if __name__ == "__main__":
    main()