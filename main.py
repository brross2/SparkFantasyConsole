import pygame
from VM.Lexer import Lexer
from VM.Parser import Parser
from VM.Compiler import Compiler
from VM.VirtualMachine import SparkVM
from VM.Hardware import SparkHardware

# --- JUEGO: CONTROL DE PERSONAJE ---
source_code = """
-- 1. Setup inicial
player_x = 76
player_y = 76
spd = 2
color = 11 -- Verde brillante

function update()
    -- Movimiento Izquierda (0) / Derecha (1)
    if btn(0) then
        player_x = player_x - spd
    end
    if btn(1) then
        player_x = player_x + spd
    end

    -- Movimiento Arriba (2) / Abajo (3)
    if btn(2) then
        player_y = player_y - spd
    end
    if btn(3) then
        player_y = player_y + spd
    end

    -- Boton A (4) cambia color
    if btn(4) then
        color = 8 -- Rojo
    else
        color = 11 -- Verde
    end
end

function draw()
    -- Limpiamos "rastro" (truco barato de clear screen parcial)
    -- En un motor real usariamos cls() o repintaríamos el fondo

    -- Dibujamos al jugador
    pset(player_x, player_y, color)

    -- Dibujamos una "mira" alrededor
    pset(player_x - 1, player_y, color)
    pset(player_x + 1, player_y, color)
    pset(player_x, player_y - 1, color)
    pset(player_x, player_y + 1, color)
end
"""


def main():
    # 1. Compilar
    print("Compilando...")
    tokens = Lexer(source_code)
    ast = Parser(tokens).parse()
    compiler = Compiler()
    compiler.compile(ast)

    # 2. Hardware (Escala x4 para verlo bien grande)
    hw = SparkHardware(scale=4)
    vm = SparkVM(compiler.code, compiler.consts, hardware=hw)

    # 3. Boot (Ejecutar script principal)
    while not vm.halted and vm.ip < len(vm.code):
        vm.step()
    vm.halted = False

    print("Iniciando Game Loop...")
    frame_count = 0

    # 4. Loop
    while hw.running:
        hw.handle_input()
        hw.clear_screen()  # Limpiamos cada frame para que no queden estelas infinitas

        vm.call_function("update")
        vm.call_function("draw")

        hw.flip()
        # --- DEBUG CADA 60 FRAMES (1 seg) ---
        frame_count += 1
        if frame_count % 60 == 0:
            print(f"DEBUG: Stack Size: {len(vm.stack)}")

    pygame.quit()


if __name__ == "__main__":
    main()