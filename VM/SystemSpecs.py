# VM/SystemSpecs.py

# Diccionario de Especificaciones del Sistema
# clave: nombre de la función
# min_args: cantidad mínima de argumentos obligatorios
# snippet: texto a insertar al autocompletar (lo que va después del nombre)

SYS_SPECS = {
    "pset": {"min_args": 3, "snippet": "(x, y, 7)"},
    "rect": {"min_args": 5, "snippet": "(x, y, w, h, 7)"},  # Si la implementaste en BIOS
    "line": {"min_args": 5, "snippet": "(x0, y0, x1, y1, 7)"},
    "spr": {"min_args": 3, "snippet": "(0, x, y)"},
    "btn": {"min_args": 1, "snippet": "(0)"},
    "print": {"min_args": 4, "snippet": '("TEXT", x, y, 7)'},
    "cls": {"min_args": 0, "snippet": "()"},
    "sfx": {"min_args": 1, "snippet": "(0)"},

    # Estructuras de control (Bonus)
    "function": {"min_args": 0, "snippet": " name()\n    \nend"},
    "if": {"min_args": 0, "snippet": " condition then\n    \nend"},
    "while": {"min_args": 0, "snippet": " condition do\n    \nend"}
}