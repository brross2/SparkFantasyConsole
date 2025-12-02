import pygame
import time
from VM.Lexer import Lexer
from VM.Parser import Parser
from VM.Compiler import Compiler
from VM.VirtualMachine import SparkVM
from VM.Hardware import SparkHardware
from Tools.CodeEditor import CodeEditor  # <--- Importamos la herramienta

# --- CÓDIGO INICIAL (VACÍO O DEMO) ---
initial_code = """x = 76
y = 76
c = 8

function update()
    if btn(0) then x = x - 1 end
    if btn(1) then x = x + 1 end
    if btn(2) then y = y - 1 end
    if btn(3) then y = y + 1 end

    if btn(4) then c = c + 1 end
end

function draw()
    cls()
    print("HOLA EDITOR", x, y-10, 7)
    spr(0, x, y)
    pset(x, y, c)
end
"""


def main():
    hw = SparkHardware(scale=4)
    vm = SparkVM([], [], hardware=hw)
    editor = CodeEditor(hw)
    editor.load_code(initial_code)

    # ESTADOS
    MODE_EDITOR = 0
    MODE_GAME = 1
    current_mode = MODE_EDITOR
    pygame.key.set_repeat(400,30)

    running = True
    while running:
        # 1. CAPTURA DE EVENTOS (SINGLE SOURCE OF TRUTH)
        # Solo main.py llama a pygame.event.get()
        events = pygame.event.get()

        for event in events:
            # --- NIVEL 1: SISTEMA OPERATIVO ---
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # --- NIVEL 2: COMANDOS GLOBALES (Hotkeys) ---

                # F1: Volver al Editor (Siempre disponible)
                if event.key == pygame.K_F1:
                    current_mode = MODE_EDITOR
                    pygame.display.set_caption("Spark - EDITOR MODE")
                    # Reactivar repetición de teclas para escribir cómodo
                    pygame.key.set_repeat(400, 30)

                # F5: Ejecutar Juego (Siempre disponible desde el editor)
                elif event.key == pygame.K_F5:
                    if current_mode == MODE_EDITOR:
                        # 1. Validar
                        editor.validate_syntax()

                        if editor.error_msg == "OK":
                            try:
                                print("Compilando sistema...")
                                # Get Code -> Lex -> Parse -> Compile
                                code = editor.get_code()
                                ast = Parser(Lexer(code)).parse()
                                compiler = Compiler()
                                compiler.compile(ast)

                                # Cargar en VM
                                vm.code = compiler.code
                                vm.consts = compiler.consts
                                vm.reset()

                                # Ejecutar Script Principal (Variables globales)
                                while not vm.halted and vm.ip < len(vm.code):
                                    vm.step()
                                vm.halted = False

                                # Cambiar Modo
                                current_mode = MODE_GAME
                                pygame.display.set_caption("Spark - RUNNING")
                                # Desactivar repetición de teclas para el juego (para que btn() no parpadee)
                                pygame.key.set_repeat()

                            except Exception as e:
                                print(f"Error Fatal: {e}")
                                editor.set_error(str(e))
                        else:
                            print("Error de sintaxis, no se puede iniciar.")

                # --- NIVEL 3: DESPACHO A COMPONENTES ---
                else:
                    # Si no es una tecla global, se la pasamos al módulo activo
                    if current_mode == MODE_EDITOR:
                        editor.handle_input(event)

                    elif current_mode == MODE_GAME:
                        # El juego usa Polling (btn), así que generalmente ignoramos eventos individuales.
                        # Pero si agregáramos input de texto al juego (input()),
                        # aquí se lo pasaríamos a la VM.
                        pass

        # --- UPDATE & DRAW LOOP ---
        if current_mode == MODE_EDITOR:
            editor.draw()
            hw.flip(mode="EDITOR")

        elif current_mode == MODE_GAME:
            # El input del juego es por polling en hardware.btn()
            # No necesitamos pasarle eventos.
            vm.call_function("update")
            vm.call_function("draw")
            hw.flip(mode="GAME")


if __name__ == "__main__":
    main()