# VM/SystemSpecs.py

# Diccionario de Especificaciones del Sistema
# clave: nombre de la función
# min_args: cantidad mínima de argumentos obligatorios
# snippet: texto a insertar al autocompletar (lo que va después del nombre)

SYS_SPECS = {
    "pset":     {"min_args": 3, "snippet": "(x, y, 7)", "args": ["int", "int", "color"]},
    "line":     {"min_args": 5, "snippet": "(x0, y0, x1, y1, 7)", "args": ["int", "int", "int", "int", "color"]},
    "rect":     {"min_args": 5, "snippet": "(x, y, w, h, 7)", "args": ["int", "int", "int", "int", "color"]},
    "spr":      {"min_args": 3, "snippet": "(0, x, y)", "args": ["int", "int", "int"]},  # spr no pide color
    "btn":      {"min_args": 1, "snippet": "(0)", "args": ["btn_id"]},
    "print":    {"min_args": 4, "snippet": '("TEXT", x, y, 7)', "args": ["str", "int", "int", "color", "int"]},
    "cls":      {"min_args": 0, "snippet": "()", "args": []},
    "sfx":      {"min_args": 1, "snippet": "(0)", "args": ["int"]},

    # Control structures
    "function": {"min_args": 0, "snippet": " name()\n    \nend", "args": []},
    "if":       {"min_args": 0, "snippet": " condition then\n    \nend", "args": []},
    "while":    {"min_args": 0, "snippet": " condition do\n    \nend", "args": []}
}

COLOR_SUGGESTIONS = [
    # --- PICO-8 STANDARD (0-15) ---
    {"label": "0  BLACK", "val": "0", "color_idx": 0},
    {"label": "1  NAVY", "val": "1", "color_idx": 1},
    {"label": "2  PURPLE", "val": "2", "color_idx": 2},
    {"label": "3  DK.GREEN", "val": "3", "color_idx": 3},
    {"label": "4  BROWN", "val": "4", "color_idx": 4},
    {"label": "5  DK.GREY", "val": "5", "color_idx": 5},
    {"label": "6  LT.GREY", "val": "6", "color_idx": 6},
    {"label": "7  WHITE", "val": "7", "color_idx": 7},
    {"label": "8  RED", "val": "8", "color_idx": 8},
    {"label": "9  ORANGE", "val": "9", "color_idx": 9},
    {"label": "10 YELLOW", "val": "10", "color_idx": 10},
    {"label": "11 LIME", "val": "11", "color_idx": 11},
    {"label": "12 BLUE", "val": "12", "color_idx": 12},
    {"label": "13 LAVENDER", "val": "13", "color_idx": 13},
    {"label": "14 PINK", "val": "14", "color_idx": 14},
    {"label": "15 PEACH", "val": "15", "color_idx": 15},

    # --- SPARK EXTENDED (16-31) ---
    {"label": "16 COCOA", "val": "16", "color_idx": 16},
    {"label": "17 MIDNIGHT", "val": "17", "color_idx": 17},
    {"label": "18 PORT", "val": "18", "color_idx": 18},
    {"label": "19 SEAWEED", "val": "19", "color_idx": 19},
    {"label": "20 LEATHER", "val": "20", "color_idx": 20},
    {"label": "21 CHARCOAL", "val": "21", "color_idx": 21},
    {"label": "22 OLIVE", "val": "22", "color_idx": 22},
    {"label": "23 SNOW", "val": "23", "color_idx": 23},
    {"label": "24 CORAL", "val": "24", "color_idx": 24},
    {"label": "25 GOLD", "val": "25", "color_idx": 25},
    {"label": "26 CREAM", "val": "26", "color_idx": 26},
    {"label": "27 MINT", "val": "27", "color_idx": 27},
    {"label": "28 CYAN", "val": "28", "color_idx": 28},
    {"label": "29 INDIGO", "val": "29", "color_idx": 29},
    {"label": "30 MAGENTA", "val": "30", "color_idx": 30},
    {"label": "31 SAND", "val": "31", "color_idx": 31},
]

BUTTON_SUGGESTIONS = [
    {"label": "0  < LEFT",   "val": "0"},
    {"label": "1  > RIGHT",  "val": "1"},
    {"label": "2  ^ UP",     "val": "2"},
    {"label": "3  v DOWN",   "val": "3"},
    {"label": "4  (A) Z-KEY","val": "4"},
    {"label": "5  (B) X-KEY","val": "5"},
]