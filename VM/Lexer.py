import re
from typing import List
from VM.Token import Token

# -----------------------------
# Lexer (mejorado: keywords)
# -----------------------------
TOKEN_SPEC = [
    ("COMMENT",  r"--[^\n]*"),                      # comentario de línea
    ("NEWLINE",  r"\n"),                            # saltos de línea
    ("SKIP",     r"[ \t\r]+"),                      # espacios
    ("STRING",   r"\"([^\"\\]|\\.)*\""),            # strings entre comillas dobles
    ("NUMBER",   r"\d+(\.\d+)?"),                   # enteros y floats
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),        # identificadores / keywords
    ("OP",       r"==|~=|<=|>=|[+\-*/%<>]=?|="),    # operadores
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("COMMA",    r","),
    ("COLON",    r":"),
    ("UNKNOWN",  r"."),                             # cualquier otro carácter
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))
KEYWORDS = {"function", "end", "if", "then", "else", "while", "do", "return"}

def Lexer(src: str) -> List[Token]:
    tokens: List[Token] = []
    line = 1
    line_start = 0
    for m in TOKEN_RE.finditer(src):
        kind = m.lastgroup
        val = m.group(kind)
        col = m.start() - line_start + 1
        if kind == "NEWLINE":
            tokens.append(Token("NEWLINE", "\\n", line, col))
            line += 1
            line_start = m.end()
            continue
        if kind == "SKIP" or kind == "COMMENT":
            continue
        if kind == "IDENT" and val in KEYWORDS:
            tokens.append(Token("KEYWORD", val, line, col))
            continue
        if kind == "STRING":
            inner = val[1:-1]
            inner = inner.replace(r'\"', '"').replace(r'\\', '\\').replace(r'\n', '\n')
            tokens.append(Token("STRING", inner, line, col))
            continue
        tokens.append(Token(kind, val, line, col))
    tokens.append(Token("EOF", "", line, 1))
    return tokens
