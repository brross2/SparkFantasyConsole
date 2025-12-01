import pygame


class SparkHardware:
    def __init__(self, scale=3):
        pygame.init()

        # Especificaciones de Hardware
        self.WIDTH = 160
        self.HEIGHT = 160
        self.SCALE = scale

        # 1. La Ventana Física (Lo que ve el usuario)
        window_size = (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE)
        self.window = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Spark Fantasy Console")

        # 2. La VRAM (Buffer interno de 160x160)
        self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.screen.fill((0, 0, 0))  # Limpiar pantalla inicial

        # 3. Paleta de Colores (32 colores fijos)
        # Usamos una lista de tuplas (R, G, B)
        self.palette = [
                           (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
                           (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
                           (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
                           (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
                           # ... (Podemos añadir los otros 16 colores después) ...
                           (0, 0, 0)  # Relleno hasta 32 por seguridad
                       ] * 2

        self.spritesheet = pygame.Surface((128,128))
        self.clock = pygame.time.Clock()
        self.running = True
        self._gen_debug_sprites()

    def clear_screen(self):
        """Limpia la VRAM con color negro (índice 0)"""
        self.screen.fill(self.palette[0])

    def pset(self, x, y, color_idx):
        """Pone un pixel en la VRAM (Sistema de Coordenadas 160x160)"""
        # Protecciones de hardware (Clipping)
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            # Aseguramos que el índice de color sea válido (0-31)
            c = self.palette[int(color_idx) % len(self.palette)]
            self.screen.set_at((int(x), int(y)), c)

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
        # Aseguramos que el ID sea válido (0-255)
        sid = int(sprite_id) % 256

        # Calculamos dónde vive ese sprite dentro de la hoja de 128x128
        sheet_x = (sid % 16) * 8
        sheet_y = (sid // 16) * 8

        # Copiamos (Blit) ese trocito de 8x8 a la pantalla
        # area=(rect) define qué pedazo copiar
        self.screen.blit(self.spritesheet, (x, y), (sheet_x, sheet_y, 8, 8))