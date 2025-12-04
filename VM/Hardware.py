import pygame

from VM.SparkFont import SparkFont


class SparkHardware:
    def __init__(self, scale=4):
        pygame.init()

        # Resolucion de juego.
        self.WIDTH = 160
        self.HEIGHT = 160

        # Resolucion editor.
        self.ED_WIDTH = 320
        self.ED_HEIGHT = 320

        self.SCALE = scale

        # 1. La Ventana Física (Lo que ve el usuario)
        window_size = (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE)
        self.window = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Spark Fantasy Console")

        # 2. La VRAM (Buffer interno de 160x160)
        self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.screen.fill((0, 0, 0))  # Limpiar pantalla inicial

        self.editor_screen = pygame.Surface((self.ED_WIDTH, self.ED_HEIGHT))

        # 3. Paleta de Colores (32 colores fijos)
        # Usamos una lista de tuplas (R, G, B)
        self.palette = [
            (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
            (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
            (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
            (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
            (41, 36, 33), (8, 10, 20), (60, 10, 20), (10, 60, 20),
            (100, 40, 20), (50, 40, 40), (120, 120, 130), (255, 255, 255),
            (255, 100, 100), (255, 200, 100), (240, 255, 150), (150, 255, 150),
            (150, 240, 255), (180, 150, 255), (255, 150, 200), (200, 150, 100)
        ]

        self.spritesheet = pygame.Surface((128,128))
        self.clock = pygame.time.Clock()
        self.running = True
        self._gen_debug_sprites()

    def clear_screen(self):
        """Limpia la VRAM con color negro (índice 0)"""
        self.screen.fill(self.palette[0])

    def pset(self, x, y, color_idx):
        """Pone un pixel en la VRAM (Sistema de Coordenadas 160x160)"""
        try:
            # 1. SANITIZACIÓN: Convertir a Enteros (Quitar decimales)
            # Esto arregla el problema de "ry + j" siendo float
            ix = int(x)
            iy = int(y)
            ic = int(color_idx)

            # 2. Protecciones de hardware (Clipping)
            if 0 <= ix < self.WIDTH and 0 <= iy < self.HEIGHT:
                # Aseguramos que el índice de color sea válido usando módulo
                safe_idx = ic % len(self.palette)
                c = self.palette[safe_idx]

                self.screen.set_at((ix, iy), c)
        except Exception as e:
            # Si algo falla (ej: valores nulos), fallamos silenciosamente
            # para no romper el juego por un pixel malo.
            print(f"HARDWARE ERROR (pset): {e} | Val: {x}, {y}, {color_idx}")
            pass

    def flip(self):
        """Renderiza la VRAM a la ventana escalada"""
        # 1. Escalar la superficie pequeña a la grande (Nearest Neighbor para look retro)
        pygame.transform.scale(self.screen, self.window.get_size(), self.window)

        # 2. Actualizar la ventana real
        pygame.display.flip()

        # 3. Mantener 60 FPS fijos
        self.clock.tick(60)

    def handle_input(self):
        """Procesa eventos del SO (cerrar ventana, etc)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def btn(self, btn_id):
        keys = pygame.key.get_pressed()
        key_map = {
            0: pygame.K_LEFT,
            1: pygame.K_RIGHT,
            2: pygame.K_UP,
            3: pygame.K_DOWN,
            4: pygame.K_a,
            5: pygame.K_s,
        }
        if btn_id in key_map:
            return keys[key_map[btn_id]]

        return False

    def _gen_debug_sprites(self):
        """Genera patrones de colores para probar spr() sin archivos"""
        for i in range(256):
            # Coordenadas en la hoja (0-15) * 8
            sx = (i % 16) * 8
            sy = (i // 16) * 8

            # Color base (usamos el ID para variar el color)
            col = self.palette[i % len(self.palette)]
            contrast_col = self.palette[(i + 8) % len(self.palette)]

            # Dibujamos un cuadradito relleno
            pygame.draw.rect(self.spritesheet, col, (sx, sy, 8, 8))
            # Dibujamos un detalle (un punto en el centro)
            pygame.draw.rect(self.spritesheet, contrast_col, (sx + 2, sy + 2, 4, 4))

        # IMPORTANTE: Definir el color transparente (Color 0 = Negro)
        # Esto hace que el fondo del sprite no tape lo que hay detrás
        self.spritesheet.set_colorkey(self.palette[0])

    def spr(self, sprite_id, x, y):
        """Dibuja el sprite ID (0-255) en la posición (x, y)"""
        try:
            sid = int(sprite_id % 256)
            ix = int(x)
            iy = int(y)

            sheet_x = (sid % 16) * 8
            sheet_y = (sid // 16) * 8

            self.screen.blit(self.spritesheet, (ix, iy), (sheet_x, sheet_y, 8, 8))
        except Exception as e:
            print(f"HARDWARE ERROR (spr): {e} | Val:  {x}, {y}")
            pass

        # En VM/Hardware.py -> SparkHardware

    def print_text(self, text, x, y, color_idx, is_small=False, target=None):
        """
        Dibuja texto.
        target: Surface de destino. Si es None, usa self.screen (Juego)
        """
        # Si no especifican target, usamos la pantalla del juego (comportamiento default)
        dest_surf = target if target else self.screen
        dest_w = dest_surf.get_width()
        dest_h = dest_surf.get_height()

        cursor_x = int(x)
        cursor_y = int(y)

        safe_idx = int(color_idx) % len(self.palette)
        color = self.palette[safe_idx]

        font_data = SparkFont.DATA_SMALL if is_small else SparkFont.DATA_BIG
        width = 4 if is_small else 8
        height = 6 if is_small else 8
        spacing = 5 if is_small else 9

        for char in str(text).upper():
            if char in font_data:
                bitmap = font_data[char]
                for row_idx, row_byte in enumerate(bitmap):
                    bits_to_read = width
                    for col_idx in range(bits_to_read):
                        shift = (width - 1) - col_idx
                        if (row_byte >> shift) & 1:
                            px = cursor_x + col_idx
                            py = cursor_y + row_idx
                            # Check de limites contra la superficie de destino
                            if 0 <= px < dest_w and 0 <= py < dest_h:
                                dest_surf.set_at((px, py), color)
            cursor_x += spacing

    def flip(self, mode="GAME", overlay_callback=None):
        """
        Renderiza la VRAM a la ventana.
        overlay_callback: Función para dibujar UI encima (Consola) antes del flip.
        """
        # 1. Escalar la capa base (Juego o Editor) a la ventana física
        if mode == "GAME":
            pygame.transform.scale(self.screen, self.window.get_size(), self.window)
        else:
            pygame.transform.scale(self.editor_screen, self.window.get_size(), self.window)

        # 2. Dibujar Overlay (Consola) directamente en la ventana física
        # Esto asegura que la consola siempre se vea nítida y encima de todo
        if overlay_callback:
            overlay_callback(self.window)  # Le pasamos la ventana real

        # 3. Refrescar
        pygame.display.flip()
        self.clock.tick(60)
