import pygame
import time

from BIOS import BIOS_SOURCE
from VM.Lexer import Lexer
from VM.Parser import Parser
from VM.Compiler import Compiler
from VM.VirtualMachine import SparkVM
from VM.Hardware import SparkHardware
from Tools.CodeEditor import CodeEditor
from Tools.SystemConsole import SystemConsole

GAME_SOURCE = """
x = 76
y = 76
c = 8

function update()
    if btn(0) then x = x - 2 end
    if btn(1) then x = x + 2 end
    if btn(2) then y = y - 2 end
    if btn(3) then y = y + 2 end

    if btn(4) then c = c + 1 end
end

function draw()
    cls()
    print("HOLA EDITOR", x-10, y-10, 7)
    spr(0, x, y)
    pset(x, y, c)
end
"""


# ==========================================
# 2. CLASE PRINCIPAL DEL SISTEMA
# ==========================================
class SparkSystem:
    def __init__(self):
        # Constantes de Estado
        self.MODE_EDITOR = 0
        self.MODE_GAME = 1

        # Inicialización de Componentes
        self.hw = SparkHardware(scale=4)
        self.console = SystemConsole(self.hw)
        self.vm = SparkVM([], [], hardware=self.hw)

        # Inyectar consola en VM para logs
        self.vm.console = self.console

        self.editor = CodeEditor(self.hw)
        self.editor.load_code(GAME_SOURCE)

        # Estado Inicial
        self.current_mode = self.MODE_EDITOR
        self.running = True

        # Secuencia de Arranque (BIOS)
        self.bios_mode = True
        self.start_time = time.time()
        self.console.log("Booting Kernel...", "SYSTEM")

        if not self.load_cartridge(BIOS_SOURCE):
            self.console.log("BIOS Corrupta. Saltando.", "WARN")
            self.bios_mode = False
            self.switch_to_editor()
        else:
            pygame.key.set_repeat()  # Desactivar repeat durante BIOS

    def switch_to_editor(self):
        """Cambio de contexto centralizado al Editor"""
        self.current_mode = self.MODE_EDITOR
        self.bios_mode = False
        pygame.display.set_caption("Spark - EDITOR MODE")
        pygame.key.set_repeat(400, 30)  # Activar repetición para escribir
        self.hw.clear_screen()  # Limpiar basura visual

    def switch_to_game(self):
        """Cambio de contexto centralizado al Juego"""
        self.current_mode = self.MODE_GAME
        self.bios_mode = False
        pygame.display.set_caption("Spark - RUNNING")
        pygame.key.set_repeat()  # Desactivar repetición para inputs de juego

    def load_cartridge(self, source_code):
        """Compila y carga código en la VM. Retorna True/False."""
        t0 = time.time()
        self.console.log("--- COMPILING ---", "INFO")

        try:
            tokens = Lexer(source_code)
            ast = Parser(tokens).parse()
            compiler = Compiler()
            compiler.compile(ast)

            self.vm.code = compiler.code
            self.vm.consts = compiler.consts
            self.vm.reset()

            # Ejecutar inicialización (Variables globales)
            while not self.vm.halted and self.vm.ip < len(self.vm.code):
                self.vm.step()

            # Chequeo post-inicialización
            if self.vm.runtime_error:
                raise Exception(self.vm.runtime_error)

            self.vm.halted = False
            elapsed = round((time.time() - t0) * 1000, 2)
            self.console.log(f"Success ({elapsed}ms)", "SUCCESS")
            return True

        except Exception as e:
            self.console.log(f"Error: {e}", "ERROR")
            if self.current_mode == self.MODE_EDITOR:
                self.editor.set_error(str(e))
            return False

    def handle_global_input(self, event):
        """Maneja teclas globales (F1, F3, F5, Quit)"""
        if event.type == pygame.QUIT:
            self.running = False
            return True

        if event.type == pygame.KEYDOWN:
            # F1: Editor
            if event.key == pygame.K_F1:
                self.switch_to_editor()
                self.console.log("Switched to Editor", "INFO")
                return True

            # F3: Consola
            if event.key == pygame.K_F3:
                self.console.toggle()
                return True

            # F5: Ejecutar
            if event.key == pygame.K_F5:
                if self.current_mode == self.MODE_EDITOR:
                    self.editor.validate_syntax()
                    if self.editor.error_msg == "OK":
                        if self.load_cartridge(self.editor.get_code()):
                            self.switch_to_game()
                    else:
                        self.console.log("Sintaxis Inválida", "WARN")
                return True

        return False

    def check_vm_crash(self, context="GAME"):
        """Verifica si la VM murió y maneja el retorno al editor"""
        if self.vm.halted and self.vm.runtime_error:
            self.console.log(f"{context} CRASH: {self.vm.runtime_error}", "ERROR")
            self.switch_to_editor()
            self.editor.set_error(self.vm.runtime_error)
            self.console.visible = True

    def update(self):
        """Lógica de actualización por frame"""

        # 1. BIOS Update
        if self.bios_mode:
            self.vm.call_function("update")
            self.check_vm_crash("BIOS")

            if time.time() - self.start_time > 8:
                self.switch_to_editor()
                self.console.log("System Ready.", "INFO")

        # 2. GAME Update
        elif self.current_mode == self.MODE_GAME:
            self.hw.handle_input()  # Polling de botones
            self.vm.call_function("update")
            self.check_vm_crash("GAME")

        # 3. EDITOR Update (Nada por ahora)
        pass

    def draw(self):
        """Pipeline Gráfico Unificado"""

        # 1. Dibujar Capa Base (Juego/Bios o Editor)
        if self.bios_mode or self.current_mode == self.MODE_GAME:
            self.vm.call_function("draw")
            # Escalar 160x160 -> Ventana
            pygame.transform.scale(self.hw.screen, self.hw.window.get_size(), self.hw.window)

        elif self.current_mode == self.MODE_EDITOR:
            self.editor.draw()
            # Escalar 320x320 -> Ventana
            pygame.transform.scale(self.hw.editor_screen, self.hw.window.get_size(), self.hw.window)

        # 2. Dibujar Overlay (Consola)
        if self.console.visible:
            # Dibujar consola sobre su canvas transparente
            # Limpiamos el canvas de la consola primero si es necesario,
            # pero console.draw ya maneja su fondo.
            self.console.draw()

            # Pegar consola sobre la ventana
            overlay = pygame.transform.scale(self.hw.editor_screen, self.hw.window.get_size())
            # Usamos colorkey negro para transparencia si el fondo no es sólido
            # (Depende de tu implementación de SystemConsole, aquí asumimos overlay sólido o alpha blit)
            self.hw.window.blit(overlay, (0, 0))

        # 3. Flip Final
        pygame.display.flip()
        self.hw.clock.tick(60)

    def run(self):
        """Bucle Principal (Limpio y sin indentación excesiva)"""
        while self.running:
            # A. INPUT ROUTER
            events = pygame.event.get()
            for event in events:
                if self.handle_global_input(event):
                    continue  # Evento consumido globalmente

                # Despacho local
                if self.current_mode == self.MODE_EDITOR:
                    self.editor.handle_input(event)

            # B. LOGIC & RENDER
            self.update()
            self.draw()


# ==========================================
# 3. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    sys = SparkSystem()
    sys.run()
    pygame.quit()