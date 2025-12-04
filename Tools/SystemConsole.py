import pygame
import time


class SystemConsole:
    def __init__(self, hardware):
        self.hw = hardware
        self.logs = []  # Lista de tuplas: (tiempo, tipo, mensaje)
        self.visible = False

        # Configuración visual
        self.font_h = 8
        self.max_lines = 35  # Cuántas líneas caben en pantalla (320px / 8)

        # Colores (Indices de la paleta)
        self.colors = {
            "INFO": 7,  # Blanco
            "SUCCESS": 11,  # Verde
            "WARN": 9,  # Naranja
            "ERROR": 8,  # Rojo
            "SYSTEM": 12  # Azul
        }

        self.log("Spark System v1.0 Ready", "SYSTEM")

    def toggle(self):
        self.visible = not self.visible

    def log(self, msg, type="INFO"):
        """Agrega un mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append((timestamp, type, str(msg)))

        # Auto-scroll: mantener solo las últimas N líneas
        if len(self.logs) > 100:
            self.logs.pop(0)

        # Imprimir también en terminal de PyCharm por si acaso
        print(f"[{type}] {msg}")

    def draw(self):
        if not self.visible: return

        target = self.hw.editor_screen
        overlay = pygame.Surface((self.hw.ED_WIDTH, self.hw.ED_HEIGHT))
        overlay.set_alpha(220)  # 0-255
        overlay.fill((10, 10, 20))  # Azul muy oscuro
        target.blit(overlay, (0, 0))

        # 2. Dibujar Logs (de abajo hacia arriba)
        y = self.hw.ED_HEIGHT - 20

        for i in range(len(self.logs) - 1, -1, -1):
            ts, type, text = self.logs[i]
            col_idx = self.colors.get(type, 7)
            full_str = f"[{ts}] {text}"

            # Pasamos target=target para que Hardware use esta superficie
            self.hw.print_text(full_str, 5, y, col_idx, is_small=True, target=target)

            y -= self.font_h + 2
            if y < 0: break

        # 3. Header
        pygame.draw.rect(target, self.hw.palette[1], (0, 0, self.hw.ED_WIDTH, 16))
        self.hw.print_text("--- SYSTEM CONSOLE (F3) ---", 10, 4, 7, is_small=False, target=target)