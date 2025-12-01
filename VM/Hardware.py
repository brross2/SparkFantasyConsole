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

        self.clock = pygame.time.Clock()
        self.running = True

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