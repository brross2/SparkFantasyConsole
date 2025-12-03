import pygame
import re  # Necesario para el Syntax Highlighting
from VM.Lexer import KEYWORDS, Lexer
from VM.Parser import Parser
from VM.SystemSpecs import SYS_SPECS

# Configuración de Colores (Indices de la paleta)
# En Tools/CodeEditor.py

# En Tools/CodeEditor.py

# Configuración de Colores (Indices de la paleta)
# 0:Negro, 1:AzulOsc, 2:Morado, 3:VerdeOsc, 4:Marron, 5:GrisOsc, 6:GrisClaro, 7:Blanco
# 8:Rojo, 9:Naranja, 10:Amarillo, 11:Verde, 12:Azul, 13:Lavanda, 14:Rosa, 15:Melocoton

THEMES = {
    "DARK": {
        "bg": 0,       "num_bg": 1,   "num_fg": 6,
        "text": 7,     "keyword": 12, "string": 11,
        "number": 9,   "comment": 5,  "symbol": 6,
        "func_name": 14,
        "selection": 5,
        "cursor": 8,   "error": 8,
        "bar_bg": 6,   "bar_text": 0
    },
    "RETRO": {
        "bg": 1,       "num_bg": 0,   "num_fg": 13,
        "text": 13,    "keyword": 11, "string": 10,
        "number": 9,   "comment": 6,  "symbol": 7,
        "func_name": 12,
        "selection": 12,
        "cursor": 7,   "error": 2,
        "bar_bg": 7,   "bar_text": 1
    },
    "DRACULA": {
        "bg": 0,       "num_bg": 2,   "num_fg": 13, # Fondo negro, Gutter Morado
        "text": 6,     "keyword": 14, "string": 11, # Texto Gris, Key Rosa, String Verde
        "number": 13,  "comment": 1,  "symbol": 14, # Num Lavanda, Comment Azul Osc
        "func_name": 9,                             # Funciones Naranja
        "selection": 2,                             # Selección Morada
        "cursor": 8,   "error": 8,
        "bar_bg": 2,   "bar_text": 7
    },
    "CREAM": {
        "bg": 15,      "num_bg": 7,   "num_fg": 5,  # Fondo Melocotón, Gutter Blanco
        "text": 5,     "keyword": 2,  "string": 3,  # Texto Gris Osc, Key Morado, String Verde Osc
        "number": 8,   "comment": 13, "symbol": 4,  # Num Rojo, Comment Lavanda, Sym Marron
        "func_name": 12,                            # Funciones Azul
        "selection": 6,                             # Selección Gris Claro
        "cursor": 2,   "error": 8,
        "bar_bg": 5,   "bar_text": 7
    }
}


class CodeEditor:
    def __init__(self, hardware):
        self.hw = hardware
        self.lines = [""]
        self.cx = 0;
        self.cy = 0
        self.scroll_y = 0

        self.theme_name = "DARK"
        self.theme = THEMES[self.theme_name]
        self.error_line = -1
        self.error_msg = "OK"

        # Dimensiones de fuente MINI (4x6)
        self.char_w = 4
        self.char_h = 6
        self.line_h = 8
        self.gutter_w = 25

        # Calculamos líneas visibles (Alta resolución 320px)
        self.max_lines_visible = (self.hw.ED_HEIGHT - 12) // self.line_h

        self.sel_start = None
        self.sel_end = None

        self.history = []
        self.history_idx = -1
        self.max_history = 50

        pygame.scrap.init()
        self.save_history()

    def load_code(self, source_code):
        self.lines = source_code.split('\n')
        self.validate_syntax()

    def get_code(self):
        return "\n".join(self.lines)

    def set_error(self, msg):
        """Permite establecer un error manualmente (ej: desde el compilador)"""
        self.error_msg = str(msg)
        self.error_line = -1  # Error global o desconocido

    def validate_syntax(self):
        code = self.get_code()
        # 1. Reseteamos estado de error
        self.error_line = -1
        self.error_msg = "OK"

        try:
            tokens = Lexer(code)
            Parser(tokens).parse()
        except Exception as e:
            # Capturamos el mensaje real del Parser
            self.error_msg = str(e)
            self.error_line = -1

            # Intentar buscar "line X" en el mensaje del Parser
            parts = str(e).split()
            if "line" in parts:
                try:
                    idx = parts.index("line")
                    self.error_line = int(parts[idx + 1]) - 1
                except:
                    pass

    def toggle_theme(self):
        theme_names = list(THEMES.keys())
        try:
            current_index = theme_names.index(self.theme_name)
        except ValueError:
            current_index = 0  # Fallback de seguridad

        next_index = (current_index + 1) % len(theme_names)
        self.theme_name = theme_names[next_index]
        self.theme = THEMES[self.theme_name]
        print(f"Theme changed to: {self.theme_name}")

    def get_indentation(self, line):
        """Cuenta espacios al inicio de la línea"""
        count = 0
        for char in line:
            if char == ' ':
                count += 1
            else:
                break
        return count

    def get_word_before_cursor(self):
        """Retorna la palabra que está pegada a la izquierda del cursor"""
        line = self.lines[self.cy]
        # Cortamos la línea hasta el cursor
        text_before = line[:self.cx]
        # Usamos regex para buscar la última palabra (letras/números/guiones bajos)
        match = re.search(r'([a-zA-Z_]\w*)$', text_before)
        if match:
            return match.group(1)
        return None

    def handle_input(self, event):
        # Detectar modificadores
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        # ... (Logica del MOUSE se mantiene igual, cópiala si la borraste) ...
        if event.type == pygame.MOUSEBUTTONDOWN:
            # (Pega aquí la lógica del mouse del paso anterior)
            mx, my = pygame.mouse.get_pos()
            editor_scale = 2
            ex = mx // editor_scale
            ey = my // editor_scale
            clicked_row = (ey // self.line_h)
            if clicked_row < self.max_lines_visible:
                target_y = self.scroll_y + clicked_row
                if target_y < len(self.lines):
                    self.cy = target_y
                else:
                    self.cy = len(self.lines) - 1
                rel_x = ex - self.gutter_w
                if rel_x < 0: rel_x = 0
                target_x = round(rel_x / 5)
                current_len = len(self.lines[self.cy])
                self.cx = min(current_len, target_x)

            if shift:
                if not self.sel_start:
                    pass
            else:
                self.sel_start = None

            if not shift:
                self.sel_start = (self.cx, self.cy)

        elif event.type == pygame.KEYDOWN:
            # --- COMANDOS CTRL ---
            if ctrl:
                if event.key == pygame.K_c:
                    self.copy()
                elif event.key == pygame.K_x:
                    self.cut()
                elif event.key == pygame.K_v:
                    self.paste()
                elif event.key == pygame.K_z:
                    self.undo()
                elif event.key == pygame.K_y:
                    self.redo()
                return  # Si fue comando, no escribir la letra

            # --- NAVEGACIÓN CON SELECCIÓN ---
            # Si nos movemos CON Shift, iniciamos/mantenemos selección.
            # Si nos movemos SIN Shift, cancelamos selección.

            old_cx, old_cy = self.cx, self.cy

            moved = False
            if event.key == pygame.K_UP:
                self.cy = max(0, self.cy - 1)
                moved = True
            elif event.key == pygame.K_DOWN:
                self.cy = min(len(self.lines) - 1, self.cy + 1)
                moved = True
            elif event.key == pygame.K_LEFT:
                self.cx = max(0, self.cx - 1)
                moved = True
            elif event.key == pygame.K_RIGHT:
                self.cx = min(len(self.lines[self.cy]), self.cx + 1)
                moved = True

            if moved:
                if shift:
                    # Si acabamos de empezar a seleccionar, el punto de anclaje era el viejo
                    if not self.sel_start:
                        self.sel_start = (old_cx, old_cy)
                else:
                    # Moverse sin shift borra la selección
                    self.sel_start = None

            # Borrado
            elif event.key == pygame.K_BACKSPACE:
                # Si hay selección, borrarla
                if self.sel_start and self.sel_start != (self.cx, self.cy):
                    self.delete_selection()
                else:
                    # Lógica normal de Backspace (pero agregamos save_history)
                    self.save_history()
                    if self.cx > 0:
                        line = self.lines[self.cy]
                        self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
                        self.cx -= 1
                    elif self.cy > 0:
                        curr_line = self.lines.pop(self.cy)
                        self.cy -= 1
                        self.cx = len(self.lines[self.cy])
                        self.lines[self.cy] += curr_line

            # --- AUTO-INDENT Y AUTO-END ---
            elif event.key == pygame.K_RETURN:
                if self.sel_start: self.delete_selection()  # Enter sobre selección la borra
                self.save_history()
                current_line = self.lines[self.cy]
                base_indent_len = self.get_indentation(current_line)
                base_indent_str = " " * base_indent_len

                # Análisis de Bloque
                stripped = current_line.rstrip()
                opens_block = False

                # 1. Palabras clave al final (then, do, else, :)
                block_endings = ["then", "do", "else", ":"]
                for trigger in block_endings:
                    if stripped.endswith(trigger):
                        opens_block = True
                        break

                # 2. Detección especial de Funciones
                # Si contiene "function" y NO termina en "end"
                # Ej: "function update()" -> True
                # Ej: "x = function() end" -> False
                if "function" in stripped and not stripped.endswith("end"):
                    opens_block = True

                # Dividir línea actual
                left_part = self.lines[self.cy][:self.cx]
                right_part = self.lines[self.cy][self.cx:]

                self.lines[self.cy] = left_part

                # Calcular nueva indentación
                new_cursor_indent = base_indent_str
                if opens_block:
                    new_cursor_indent += "    "  # 4 espacios extra

                # Insertar la línea nueva donde va el cursor
                self.lines.insert(self.cy + 1, new_cursor_indent + right_part)

                # LOGICA AUTO-END:
                # Solo insertamos 'end' si abrimos un bloque Y no había nada más a la derecha del cursor
                if opens_block and right_part.strip() == "":
                    # El 'end' debe tener la indentación BASE (la del padre), no la nueva
                    end_line = base_indent_str + "end"
                    self.lines.insert(self.cy + 2, end_line)

                # Mover cursor a la nueva línea indentada
                self.cy += 1
                self.cx = len(new_cursor_indent)

            # Tabulación
            elif event.key == pygame.K_TAB:
                if self.sel_start: self.delete_selection()
                self.save_history()
                # 1. Intentar Autocompletar
                word = self.get_word_before_cursor()

                if word and word in SYS_SPECS:
                    snippet = SYS_SPECS[word]["snippet"]

                    # Insertar el snippet en la posición actual
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx] + snippet + line[self.cx:]

                    # Calcular dónde dejar el cursor después de insertar
                    # Estrategia simple: Al final del snippet
                    # Estrategia Pro: Buscar el primer parentesis o comilla
                    self.cx += len(snippet)

                    # Si el snippet tiene saltos de linea (como if/function), hay que procesarlos
                    # (Para simplificar ahora, asumimos snippets de una linea o manejamos \n basicos)
                    if "\n" in snippet:
                        # Re-procesar la línea actual para dividirla en múltiples líneas
                        full_text = self.get_code()  # Algo bruto pero seguro
                        self.load_code(full_text)
                        # TODO: Recalcular CX/CY es complejo aquí,
                        # por ahora snippets simples de una línea son más seguros para V1.

                else:
                    # 2. Si no es palabra clave, Tabulación normal (4 espacios)
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx] + "    " + line[self.cx:]
                    self.cx += 4

            # Teclas de Función
            elif event.key == pygame.K_F2:
                self.toggle_theme()

            # --- ESCRITURA ---
            elif event.unicode and event.unicode.isprintable():
                if self.sel_start: self.delete_selection()  # Escribir sobre selección la borra
                self.save_history()
                char = event.unicode
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + char + line[self.cx:]
                self.cx += 1

            # Scroll y Clamp
            if self.cy < self.scroll_y:
                self.scroll_y = self.cy
            elif self.cy >= self.scroll_y + self.max_lines_visible:
                self.scroll_y = self.cy - self.max_lines_visible + 1
            self.cx = min(len(self.lines[self.cy]), self.cx)

    # --- MEJORA DE USABILIDAD 4: HIGHLIGHTING REAL ---
    def draw_highlighted_line(self, text, x, y, target):
        """
        Dibuja texto con colores sintácticos avanzados.
        Detecta strings completos, comentarios y nombres de funciones.
        """
        # REGEX EXPLICADO:
        # ("[^"]*")  -> Captura strings entre comillas dobles
        # (--.*)     -> Captura comentarios (-- hasta el final)
        # (\W)       -> Captura cualquier no-alfanumérico (simbolos, espacios)
        # El resto serán identificadores o números
        parts = re.split(r'("[^"]*"|--.*|\W)', text)

        cur_x = x
        next_is_func_decl = False  # Flag para detectar "function NOMBRE"

        for part in parts:
            if not part: continue

            color = self.theme["text"]  # Default

            # 1. Strings (Detectamos comillas al inicio)
            if part.startswith('"') or part.startswith("'"):
                color = self.theme["string"]

            # 2. Comentarios
            elif part.startswith("--"):
                color = self.theme["comment"]

            # 3. Keywords y Lógica de Función
            elif part in KEYWORDS:
                color = self.theme["keyword"]
                if part == "function":
                    next_is_func_decl = True

            # 4. Nombre de Función (Si la palabra anterior fue 'function')
            elif next_is_func_decl and part.strip():
                # Si es un identificador válido (no simbolo)
                if part.isidentifier():
                    color = self.theme["func_name"]
                    next_is_func_decl = False  # Reset flag
                elif part.strip() != "":
                    # Si encontramos un parentesis u otra cosa, cancelamos flag
                    next_is_func_decl = False

            # 5. Números
            elif part.isdigit() or (part.replace('.', '', 1).isdigit() and part.count('.') < 2):
                color = self.theme["number"]

            # 6. Símbolos
            elif part in ["+", "-", "*", "/", "=", "<", ">", "%", "(", ")", "[", "]", "{", "}", ",", "."]:
                color = self.theme["symbol"]
                # Los simbolos rompen la declaración de función
                if part.strip(): next_is_func_decl = False

            # Dibujar
            self.hw.print_text(part, cur_x, y, color, is_small=True, target=target)
            cur_x += len(part) * 5

    def draw(self):
        target = self.hw.editor_screen
        target.fill(self.hw.palette[self.theme["bg"]])

        # 1. Gutter (Margen izquierdo)
        pygame.draw.rect(target, self.hw.palette[self.theme["num_bg"]],
                         (0, 0, self.gutter_w, self.hw.ED_HEIGHT))

        start, end = self.get_sorted_selection()
        sel_color = self.hw.palette[self.theme["selection"]]

        # 2. Dibujar Líneas Visibles
        for i in range(self.max_lines_visible):
            line_idx = self.scroll_y + i
            if line_idx >= len(self.lines): break

            screen_y = i * self.line_h
            line_content = self.lines[line_idx]

            # Lógica de resaltado de selección
            if start and end:
                sx, sy = start
                ex, ey = end

                # Caso 1: Línea completamente dentro de la selección (multilínea intermedia)
                if sy < line_idx < ey:
                    pygame.draw.rect(target, sel_color,  # Azul oscuro hardcoded o usar tema
                                     (self.gutter_w, screen_y, self.hw.ED_WIDTH, self.line_h))

                # Caso 2: Línea de inicio
                elif line_idx == sy:
                    # Si es una selección de una sola línea
                    if sy == ey:
                        start_px = self.gutter_w + 4 + (sx * 5)
                        end_px = self.gutter_w + 4 + (ex * 5)
                        pygame.draw.rect(target, sel_color,
                                         (start_px, screen_y, end_px - start_px, self.line_h))
                    else:
                        # Desde sx hasta el final
                        start_px = self.gutter_w + 4 + (sx * 5)
                        pygame.draw.rect(target, sel_color,
                                         (start_px, screen_y, self.hw.ED_WIDTH, self.line_h))

                # Caso 3: Línea final (multilínea)
                elif line_idx == ey:
                    # Desde 0 hasta ex
                    end_px = self.gutter_w + 4 + (ex * 5)
                    pygame.draw.rect(target, sel_color,
                                     (self.gutter_w, screen_y, end_px - self.gutter_w, self.line_h))

            # A. Highlight de Error (Fondo rojo en la línea)
            if line_idx == self.error_line:
                pygame.draw.rect(target, self.hw.palette[self.theme["error"]],
                                 (self.gutter_w, screen_y, self.hw.ED_WIDTH, self.line_h))

            # B. Número de línea
            num_str = str(line_idx + 1)
            num_x = self.gutter_w - (len(num_str) * 5) - 2
            self.hw.print_text(num_str, num_x, screen_y + 1, self.theme["num_fg"], is_small=True, target=target)

            # C. Contenido de la línea (Syntax Highlighting)
            text_x = self.gutter_w + 4
            self.draw_highlighted_line(line_content, text_x, screen_y + 1, target)

            # D. Cursor
            if line_idx == self.cy:
                cursor_scr_x = text_x + (self.cx * 5)
                # Parpadeo
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    pygame.draw.rect(target, self.hw.palette[self.theme["cursor"]],
                                     (cursor_scr_x, screen_y, 4, 6))

        # 3. BARRA DE ESTADO (LO QUE FALTABA)
        bar_y = self.hw.ED_HEIGHT - 10
        pygame.draw.rect(target, self.hw.palette[self.theme["bar_bg"]], (0, bar_y, self.hw.ED_WIDTH, 10))

        # Posición
        pos_str = f"Ln {self.cy + 1}, Col {self.cx}"
        self.hw.print_text(pos_str, 2, bar_y + 2, self.theme["bar_text"], is_small=True, target=target)

        # Contador Bytes
        byte_count = len(self.get_code())
        usage = f"{byte_count} B"
        self.hw.print_text(usage, 200, bar_y + 2, self.theme["bar_text"], is_small=True, target=target)

        # --- CORRECCIÓN: Mostrar error SIEMPRE que no sea "OK" ---
        if self.error_msg != "OK":
            # Recortamos el mensaje si es muy largo para que entre en pantalla
            display_msg = self.error_msg
            if len(display_msg) > 35:
                display_msg = display_msg[:32] + "..."

            # Dibujamos en rojo (o color de error del tema)
            self.hw.print_text(display_msg, 90, bar_y + 2, self.theme["error"], is_small=True, target=target)

        # --- MÓDULO HISTORIAL ---

    # --- MÓDULO SELECCIÓN Y CLIPBOARD ---
    def get_sorted_selection(self):
        """Retorna (start_x, start_y), (end_x, end_y) ordenados"""
        if not self.sel_start: return None, None

        # Cursor actual es el final dinámico
        p1 = self.sel_start
        p2 = (self.cx, self.cy)

        # Comparar tuplas (y, x) para ver cuál va primero
        # Python compara tuplas elemento a elemento: (0, 5) < (1, 0) es True
        if (p1[1], p1[0]) < (p2[1], p2[0]):
            return p1, p2
        else:
            return p2, p1

    def delete_selection(self):
        """Borra el texto seleccionado y retorna True si borró algo"""
        start, end = self.get_sorted_selection()
        if not start: return False

        self.save_history()  # Guardar antes de destruir

        sx, sy = start
        ex, ey = end

        if sy == ey:
            # Misma línea: fácil
            line = self.lines[sy]
            self.lines[sy] = line[:sx] + line[ex:]
        else:
            # Multilínea: complejo
            # 1. Tomar parte izquierda de la primera línea
            first_part = self.lines[sy][:sx]
            # 2. Tomar parte derecha de la última línea
            last_part = self.lines[ey][ex:]
            # 3. Unir
            self.lines[sy] = first_part + last_part
            # 4. Eliminar líneas intermedias
            # Borramos desde sy+1 hasta ey (incluido)
            del self.lines[sy + 1: ey + 1]

        # Mover cursor al inicio del borrado
        self.cx, self.cy = sx, sy
        self.sel_start = None  # Limpiar selección
        return True

    def get_selected_text(self):
        start, end = self.get_sorted_selection()
        if not start: return ""

        sx, sy = start
        ex, ey = end

        if sy == ey:
            return self.lines[sy][sx:ex]

        # Multilínea
        text = [self.lines[sy][sx:]]  # Resto de primera línea
        for i in range(sy + 1, ey):
            text.append(self.lines[i])  # Líneas intermedias completas
        text.append(self.lines[ey][:ex])  # Inicio de última línea

        return "\n".join(text)

    def copy(self):
        text = self.get_selected_text()
        if text:
            # Ponemos en el clipboard del sistema (UTF-8)
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))

    def cut(self):
        self.copy()
        self.delete_selection()

    def paste(self):
        # Obtener texto del sistema (bytes -> string)
        content = pygame.scrap.get(pygame.SCRAP_TEXT)
        if not content: return

        text = content.decode("utf-8").replace("\0", "")  # Limpieza

        if not text: return
        self.save_history()

        # Si hay selección activa, pegar la reemplaza
        if self.sel_start:
            self.delete_selection()

        # Insertar texto
        lines_to_paste = text.split('\n')

        if len(lines_to_paste) == 1:
            # Caso simple: insertar en línea actual
            line = self.lines[self.cy]
            self.lines[self.cy] = line[:self.cx] + lines_to_paste[0] + line[self.cx:]
            self.cx += len(lines_to_paste[0])
        else:
            # Caso multilínea
            # 1. Cortar línea actual
            prefix = self.lines[self.cy][:self.cx]
            suffix = self.lines[self.cy][self.cx:]

            # 2. Primera línea pegada se une al prefijo
            self.lines[self.cy] = prefix + lines_to_paste[0]

            # 3. Líneas intermedias se insertan nuevas
            for i in range(1, len(lines_to_paste) - 1):
                self.lines.insert(self.cy + i, lines_to_paste[i])

            # 4. Última línea pegada se une al sufijo
            last_pasted = lines_to_paste[-1]
            self.lines.insert(self.cy + len(lines_to_paste) - 1, last_pasted + suffix)

            # 5. Actualizar cursor
            self.cy += len(lines_to_paste) - 1
            self.cx = len(last_pasted)

    # --- MÓDULO HISTORIAL ---
    def save_history(self):
        """Guarda una instantánea del estado actual ANTES de modificarlo"""
        # Si estamos en medio del historial y escribimos, borramos el futuro (Redo perdido)
        if self.history_idx < len(self.history) - 1:
            self.history = self.history[:self.history_idx + 1]

        snapshot = {
            "lines": list(self.lines),  # Copia superficial de la lista
            "cx": self.cx,
            "cy": self.cy
        }
        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        self.history_idx = len(self.history) - 1

    def undo(self):
        if self.history_idx > 0:
            self.history_idx -= 1
            self.restore_state(self.history[self.history_idx])

    def redo(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.restore_state(self.history[self.history_idx])

    def restore_state(self, snapshot):
        self.lines = list(snapshot["lines"])
        self.cx = snapshot["cx"]
        self.cy = snapshot["cy"]
        self.validate_syntax()  # Re-validar al volver atrás
