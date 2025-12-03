import pygame
import re
from VM.Lexer import KEYWORDS
from VM.SystemSpecs import *
from Tools.Themes import *

class CodeEditor:
    def __init__(self, hardware):
        self.hw = hardware
        self.lines = [""]
        self.cx = 0
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

        # Selección
        self.sel_start = None

        # Historial
        self.history = []
        self.history_idx = -1
        self.max_history = 50
        self.save_history()  # Estado inicial

        # IntelliSense
        self.suggest_active = False
        self.suggest_list = []
        self.suggest_idx = 0
        self.suggest_pos = (0, 0)

        # Clipboard init
        pygame.scrap.init()

    def load_code(self, source_code):
        self.lines = source_code.split('\n')
        self.validate_syntax()

    def get_code(self):
        return "\n".join(self.lines)

    def set_error(self, msg):
        self.error_msg = str(msg)
        self.error_line = -1

    def validate_syntax(self):
        # Aquí iría la llamada a tu Parser (resumida para este archivo)
        self.error_line = -1
        self.error_msg = "OK"

    def toggle_theme(self):
        theme_names = list(THEMES.keys())
        try:
            current = theme_names.index(self.theme_name)
        except:
            current = 0
        next_idx = (current + 1) % len(theme_names)
        self.theme_name = theme_names[next_idx]
        self.theme = THEMES[self.theme_name]

    # --- HISTORIAL & CLIPBOARD ---
    def save_history(self):
        if self.history_idx < len(self.history) - 1:
            self.history = self.history[:self.history_idx + 1]
        snapshot = {"lines": list(self.lines), "cx": self.cx, "cy": self.cy}
        self.history.append(snapshot)
        if len(self.history) > self.max_history: self.history.pop(0)
        self.history_idx = len(self.history) - 1

    def undo(self):
        if self.history_idx > 0:
            self.history_idx -= 1
            s = self.history[self.history_idx]
            self.lines = list(s["lines"])
            self.cx = s["cx"]
            self.cy = s["cy"]

    def redo(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            s = self.history[self.history_idx]
            self.lines = list(s["lines"])
            self.cx = s["cx"]
            self.cy = s["cy"]

    def get_sorted_selection(self):
        if not self.sel_start: return None, None
        p1, p2 = self.sel_start, (self.cx, self.cy)
        return (p1, p2) if (p1[1], p1[0]) < (p2[1], p2[0]) else (p2, p1)

    def delete_selection(self):
        start, end = self.get_sorted_selection()
        if not start: return False
        self.save_history()
        sx, sy = start
        ex, ey = end
        if sy == ey:
            self.lines[sy] = self.lines[sy][:sx] + self.lines[sy][ex:]
        else:
            self.lines[sy] = self.lines[sy][:sx] + self.lines[ey][ex:]
            del self.lines[sy + 1: ey + 1]
        self.cx, self.cy = sx, sy
        self.sel_start = None
        return True

    def copy(self):
        start, end = self.get_sorted_selection()
        if not start: return
        sx, sy = start
        ex, ey = end
        if sy == ey:
            text = self.lines[sy][sx:ex]
        else:
            text = [self.lines[sy][sx:]]
            for i in range(sy + 1, ey): text.append(self.lines[i])
            text.append(self.lines[ey][:ex])
            text = "\n".join(text)
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))

    def cut(self):
        self.copy()
        self.delete_selection()

    def paste(self):
        content = pygame.scrap.get(pygame.SCRAP_TEXT)
        if not content: return
        text = content.decode("utf-8").replace("\0", "")
        if self.sel_start: self.delete_selection()
        self.save_history()
        # (Lógica simple de pegado)
        for char in text:
            if char == '\n':
                line = self.lines[self.cy]
                self.lines.insert(self.cy + 1, line[self.cx:])
                self.lines[self.cy] = line[:self.cx]
                self.cy += 1
                self.cx = 0
            else:
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + char + line[self.cx:]
                self.cx += 1

    # --- INTELLISENSE LOGIC ---
    def analyze_cursor_context(self):
        line = self.lines[self.cy]
        text_before = line[:self.cx]
        paren_balance = 0
        arg_index = 0
        for i in range(len(text_before) - 1, -1, -1):
            char = text_before[i]
            if char == ')':
                paren_balance += 1
            elif char == '(':
                if paren_balance > 0:
                    paren_balance -= 1
                else:
                    prefix = text_before[:i].strip()
                    match = re.search(r'([a-zA-Z_]\w*)$', prefix)
                    if match: return match.group(1), arg_index
                    return None, 0
            elif char == ',' and paren_balance == 0:
                arg_index += 1
        return None, 0

    def trigger_suggestion(self):
        func_name, arg_idx = self.analyze_cursor_context()
        should_open = False
        if func_name and func_name in SYS_SPECS:
            specs = SYS_SPECS[func_name]
            if "args" in specs and arg_idx < len(specs["args"]):
                arg_type = specs["args"][arg_idx]
                if arg_type == "color":
                    self.suggest_list = COLOR_SUGGESTIONS
                    should_open = True
                elif arg_type == "btn_id":
                    self.suggest_list = BUTTON_SUGGESTIONS
                    should_open = True

        if should_open:
            self.suggest_active = True
            self.suggest_idx = 0
            screen_x = self.gutter_w + (self.cx * 5)
            screen_y = ((self.cy - self.scroll_y) * self.line_h) + self.line_h
            if screen_x + 80 > self.hw.ED_WIDTH: screen_x = self.hw.ED_WIDTH - 80
            if screen_y + 100 > self.hw.ED_HEIGHT: screen_y = screen_y - 100 - self.line_h
            self.suggest_pos = (screen_x, screen_y)

    def get_indentation(self, line):
        count = 0
        for char in line:
            if char == ' ':
                count += 1
            else:
                break
        return count

    def get_word_before_cursor(self):
        line = self.lines[self.cy]
        text_before = line[:self.cx]
        match = re.search(r'([a-zA-Z_]\w*)$', text_before)
        if match: return match.group(1)
        return None

    # --- INPUT HANDLER REPARADO ---
    def handle_input(self, event):
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        # 1. MOUSE (Corregido)
        if event.type == pygame.MOUSEBUTTONDOWN:
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

                # Guardar posición vieja para selección
                old_sel = (self.cx, self.cy)

                # Actualizar cursor
                self.cx = min(current_len, target_x)

                # Manejo de Selección con Mouse
                if shift:
                    if not self.sel_start: self.sel_start = old_sel  # Empezar desde donde estábamos
                else:
                    self.sel_start = None

        elif event.type == pygame.KEYDOWN:
            # 2. MENU INTELLISENSE
            if self.suggest_active:
                if event.key == pygame.K_UP:
                    self.suggest_idx = max(0, self.suggest_idx - 1)
                    return
                elif event.key == pygame.K_DOWN:
                    self.suggest_idx = min(len(self.suggest_list) - 1, self.suggest_idx + 1)
                    return
                elif event.key in [pygame.K_RETURN, pygame.K_TAB]:
                    item = self.suggest_list[self.suggest_idx]
                    val = item["val"]
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx] + val + line[self.cx:]
                    self.cx += len(val)
                    self.suggest_active = False
                    self.save_history()
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.suggest_active = False
                    return

            # 3. TRIGGER MANUAL (CTRL+SPACE)
            if event.key == pygame.K_SPACE and ctrl:
                self.trigger_suggestion()
                return

            # 4. TRIGGERS AUTOMÁTICOS (Coma y Paréntesis)
            if event.unicode == ",":
                self.save_history()
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + "," + line[self.cx:]
                self.cx += 1
                self.trigger_suggestion()
                return

            if event.unicode == "(":
                self.save_history()
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + "(" + line[self.cx:]
                self.cx += 1
                self.trigger_suggestion()
                return

            # 5. COMANDOS EDITORIALES (Ctrl+C, etc)
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
                return

            # 6. MOVIMIENTO CURSOR
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
                    if not self.sel_start: self.sel_start = (old_cx, old_cy)
                else:
                    self.sel_start = None

            # 7. TECLAS ESPECIALES
            elif event.key == pygame.K_BACKSPACE:
                if self.sel_start:
                    self.delete_selection()
                else:
                    self.save_history()
                    if self.cx > 0:
                        line = self.lines[self.cy]
                        self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
                        self.cx -= 1
                    elif self.cy > 0:
                        curr = self.lines.pop(self.cy)
                        self.cy -= 1
                        self.cx = len(self.lines[self.cy])
                        self.lines[self.cy] += curr

            elif event.key == pygame.K_RETURN:
                if self.sel_start: self.delete_selection()
                self.save_history()
                # Auto Indent Logic
                curr = self.lines[self.cy]
                base_ind = " " * self.get_indentation(curr)
                stripped = curr.rstrip()
                opens = False
                if any(stripped.endswith(t) for t in ["then", "do", "else", ":"]): opens = True
                if "function" in stripped and not stripped.endswith("end"): opens = True

                left = curr[:self.cx]
                right = curr[self.cx:]
                self.lines[self.cy] = left
                new_ind = base_ind + ("    " if opens else "")
                self.lines.insert(self.cy + 1, new_ind + right)
                if opens and right.strip() == "":
                    self.lines.insert(self.cy + 2, base_ind + "end")
                self.cy += 1
                self.cx = len(new_ind)

            elif event.key == pygame.K_TAB:
                if self.sel_start: self.delete_selection()
                self.save_history()
                word = self.get_word_before_cursor()
                if word and word in SYS_SPECS:
                    snip = SYS_SPECS[word]["snippet"]
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx] + snip + line[self.cx:]
                    self.cx += len(snip)
                else:
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx] + "    " + line[self.cx:]
                    self.cx += 4

            elif event.key == pygame.K_F2:
                self.toggle_theme()

            # 8. CARACTERES NORMALES
            elif event.unicode and event.unicode.isprintable():
                if self.sel_start: self.delete_selection()
                self.save_history()
                char = event.unicode
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + char + line[self.cx:]
                self.cx += 1

            # Scroll Follow
            if self.cy < self.scroll_y:
                self.scroll_y = self.cy
            elif self.cy >= self.scroll_y + self.max_lines_visible:
                self.scroll_y = self.cy - self.max_lines_visible + 1
            self.cx = min(len(self.lines[self.cy]), self.cx)

    # --- DRAWING ---
    def draw_highlighted_line(self, text, x, y, target):
        parts = re.split(r'("[^"]*"|--.*|\W)', text)
        cur_x = x
        next_is_func = False
        for part in parts:
            if not part: continue
            col = self.theme["text"]
            if part.startswith('"') or part.startswith("'"):
                col = self.theme["string"]
            elif part.startswith("--"):
                col = self.theme["comment"]
            elif part in KEYWORDS:
                col = self.theme["keyword"]
                if part == "function": next_is_func = True
            elif next_is_func and part.strip():
                if part.isidentifier():
                    col = self.theme["func_name"]
                    next_is_func = False
                elif part.strip() != "":
                    next_is_func = False
            elif part.isdigit():
                col = self.theme["number"]
            elif part in ["+", "-", "*", "/", "=", "<", ">", "%", "(", ")", "[", "]", ",", "."]:
                col = self.theme["symbol"]

            self.hw.print_text(part, cur_x, y, col, is_small=True, target=target)
            cur_x += len(part) * 5

    def draw(self):
        target = self.hw.editor_screen
        target.fill(self.hw.palette[self.theme["bg"]])

        # Gutter
        pygame.draw.rect(target, self.hw.palette[self.theme["num_bg"]], (0, 0, self.gutter_w, self.hw.ED_HEIGHT))

        # Selection
        start, end = self.get_sorted_selection()
        sel_col = self.hw.palette[self.theme["selection"]]

        for i in range(self.max_lines_visible):
            idx = self.scroll_y + i
            if idx >= len(self.lines): break
            y = i * self.line_h
            line = self.lines[idx]

            # Error Highlight
            if idx == self.error_line:
                pygame.draw.rect(target, self.hw.palette[self.theme["error"]],
                                 (self.gutter_w, y, self.hw.ED_WIDTH, self.line_h))

            # Selection Highlight
            if start and end:
                sx, sy = start
                ex, ey = end
                if sy < idx < ey:
                    pygame.draw.rect(target, sel_col, (self.gutter_w, y, self.hw.ED_WIDTH, self.line_h))
                elif idx == sy == ey:
                    px1 = self.gutter_w + 4 + (sx * 5)
                    px2 = self.gutter_w + 4 + (ex * 5)
                    pygame.draw.rect(target, sel_col, (px1, y, px2 - px1, self.line_h))
                elif idx == sy:
                    px = self.gutter_w + 4 + (sx * 5)
                    pygame.draw.rect(target, sel_col, (px, y, self.hw.ED_WIDTH - px, self.line_h))
                elif idx == ey:
                    px = self.gutter_w + 4 + (ex * 5)
                    pygame.draw.rect(target, sel_col, (self.gutter_w, y, px - self.gutter_w, self.line_h))

            # Text
            num = str(idx + 1)
            self.hw.print_text(num, self.gutter_w - (len(num) * 5) - 2, y + 1, self.theme["num_fg"], is_small=True,
                               target=target)
            self.draw_highlighted_line(line, self.gutter_w + 4, y + 1, target)

            # Cursor
            if idx == self.cy:
                cx_px = self.gutter_w + 4 + (self.cx * 5)
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    pygame.draw.rect(target, self.hw.palette[self.theme["cursor"]], (cx_px, y, 4, 6))

        # Status Bar
        by = self.hw.ED_HEIGHT - 10
        pygame.draw.rect(target, self.hw.palette[self.theme["bar_bg"]], (0, by, self.hw.ED_WIDTH, 10))
        self.hw.print_text(f"Ln {self.cy + 1}, Col {self.cx}", 2, by + 2, self.theme["bar_text"], True, target)
        self.hw.print_text(f"{len(self.get_code())} B", 200, by + 2, self.theme["bar_text"], True, target)
        if self.error_msg != "OK":
            self.hw.print_text(self.error_msg[:30], 90, by + 2, self.theme["error"], True, target)

        # IntelliSense Overlay
        if self.suggest_active:
            sx, sy = self.suggest_pos
            h = min(len(self.suggest_list) * 8 + 4, 100)
            pygame.draw.rect(target, (0, 0, 0), (sx + 2, sy + 2, 80, h))
            pygame.draw.rect(target, self.hw.palette[self.theme["num_bg"]], (sx, sy, 80, h))
            pygame.draw.rect(target, self.hw.palette[self.theme["text"]], (sx, sy, 80, h), 1)

            start_i = max(0, self.suggest_idx - 5)
            end_i = min(start_i + 10, len(self.suggest_list))
            iy = sy + 2
            for i in range(start_i, end_i):
                item = self.suggest_list[i]
                fg = self.theme["text"]
                if i == self.suggest_idx:
                    pygame.draw.rect(target, self.hw.palette[self.theme["selection"]], (sx + 1, iy - 1, 78, 8))
                    fg = self.theme["bg"]

                label_x = sx + 4
                if "color_idx" in item:
                    pygame.draw.rect(target, self.hw.palette[item["color_idx"]], (sx + 4, iy + 1, 4, 4))
                    label_x += 8

                self.hw.print_text(item["label"], label_x, iy, fg, True, target)
                iy += 8