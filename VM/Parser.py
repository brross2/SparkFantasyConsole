from VM.Data import *
from VM.Token import Token
from typing import List, Optional


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def next(self) -> Token:
        t = self.tokens[self.i]
        self.i += 1
        return t

    def expect(self, ttype: str, val: Optional[str] = None) -> Token:
        t = self.peek()
        if t.type != ttype and (val is None or t.value != val):
            raise SyntaxError(
                f"Expected {ttype} {val or ''}, got {t.type}({t.value}) at pos {self.i} line {t.line} col {t.col}")
        return self.next()

    def skip_newlines(self):
        while self.peek().type == "NEWLINE":
            self.next()

    def parse(self) -> Program:
        body = []
        while self.peek().type != "EOF":
            self.skip_newlines()
            if self.peek().type == "EOF":
                break
            body.append(self.parse_statement())
            self.skip_newlines()
        return Program(body)

    def parse_statement(self):
        t = self.peek()

        # --- Statements de Control ---
        if t.type == "KEYWORD" and t.value == "function":
            return self.parse_function()
        if t.type == "KEYWORD" and t.value == "if":
            return self.parse_if()
        if t.type == "KEYWORD" and t.value == "while":
            return self.parse_while()
        if t.type == "KEYWORD" and t.value == "return":
            return self.parse_return()

        # --- Asignaciones y Llamadas sueltas ---
        if t.type == "IDENT":
            # Guardamos el nombre y avanzamos
            name_tok = self.next()
            name = name_tok.value

            # Caso 1: Llamada a función: foo(args)
            if self.peek().type == "LPAREN":
                return self.parse_call_suffix(name)

            # Caso 2: Asignación: x = expr
            elif self.peek().type == "OP" and self.peek().value == "=":
                self.next()  # Consumir '='
                expr = self.parse_expression()
                return Assign(name, expr)
            else:
                raise SyntaxError(f"Token inesperado después de identificador '{name}': {self.peek().type}")

        raise SyntaxError(f"No se pudo parsear el statement comenzando con {t.type}({t.value}) en linea {t.line}")

    def parse_return(self):
        self.expect("KEYWORD", "return")
        # Si lo que sigue NO es un fin de bloque o nueva línea, asumimos que es una expresión
        val = None
        if self.peek().type not in ("NEWLINE", "EOF") and \
                not (self.peek().type == "KEYWORD" and self.peek().value in ("end", "else")):
            val = self.parse_expression()
        return Return(val)

    def parse_function(self):
        self.expect("KEYWORD", "function")
        name = self.expect("IDENT").value
        self.expect("LPAREN")
        params = []
        if self.peek().type == "IDENT":
            params.append(self.next().value)
            while self.peek().type == "COMMA":
                self.next()
                params.append(self.expect("IDENT").value)
        self.expect("RPAREN")

        body = []
        self.skip_newlines()
        while not (self.peek().type == "KEYWORD" and self.peek().value == "end"):
            body.append(self.parse_statement())
            self.skip_newlines()
        self.expect("KEYWORD", "end")
        return FuncDecl(name, params, body)

    def parse_if(self):
        self.expect("KEYWORD", "if")
        cond = self.parse_expression()

        # Soporte para ':' o 'then'
        if self.peek().type == "COLON":
            self.next()
        elif self.peek().type == "KEYWORD" and self.peek().value == "then":
            self.next()

        self.skip_newlines()
        body = []
        # Leemos el bloque principal (IF)
        while not (self.peek().type == "KEYWORD" and self.peek().value in ("end", "else")):
            body.append(self.parse_statement())
            self.skip_newlines()

        else_body = []  # Por defecto None o lista vacía
        # Leemos el bloque opcional (ELSE)
        if self.peek().type == "KEYWORD" and self.peek().value == "else":
            self.next()  # Consumir 'else'
            self.skip_newlines()
            while not (self.peek().type == "KEYWORD" and self.peek().value == "end"):
                else_body.append(self.parse_statement())  # <--- AHORA SÍ GUARDAMOS ESTO
                self.skip_newlines()

        self.expect("KEYWORD", "end")
        # Asegúrate de que tu dataclass 'If' acepte 3 argumentos: cond, body, else_body
        return If(cond, body, else_body if len(else_body) > 0 else None)

    def parse_while(self):
        self.expect("KEYWORD", "while")
        cond = self.parse_expression()
        if self.peek().type == "KEYWORD" and self.peek().value == "do":
            self.next()
        self.skip_newlines()
        body = []
        while not (self.peek().type == "KEYWORD" and self.peek().value == "end"):
            body.append(self.parse_statement())
            self.skip_newlines()
        self.expect("KEYWORD", "end")
        return While(cond, body)

    # --- Expresiones ---

    def parse_expression(self):
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_relational()
        while self.peek().type == "OP" and self.peek().value in ("==", "~="):
            op = self.next().value
            right = self.parse_relational()
            node = BinaryOp(op, node, right)
        return node

    def parse_relational(self):
        node = self.parse_additive() # <--- OJO: Llama a Additive
        while self.peek().type == "OP" and self.peek().value in ("<", ">", "<=", ">="):
            op = self.next().value
            right = self.parse_additive()
            node = BinaryOp(op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.next().value
            right = self.parse_factor()
            node = BinaryOp(op, node, right)
        return node

        # 3. NIVEL ADITIVO (+, -) -> Aquí se resuelve y-10
    def parse_additive(self):
        node = self.parse_multiplicative()  # <--- OJO: Llama a Multiplicative
        while self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.next().value
            right = self.parse_multiplicative()
            node = BinaryOp(op, node, right)
        return node

        # 4. NIVEL MULTIPLICATIVO (*, /, %)
    def parse_multiplicative(self):
        node = self.parse_factor()  # <--- OJO: Llama a Factor
        while self.peek().type == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.next().value
            right = self.parse_factor()
            node = BinaryOp(op, node, right)
        return node

    def parse_factor(self):
        if self.peek().type == "OP" and self.peek().value == "-":
            op = self.next().value
            right = self.parse_factor()
            return UnaryOp(op, right)
        return self.parse_primary()

    def parse_unary(self):
        if self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.next().value
            right = self.parse_unary()
            return UnaryOp(op, right)
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()

        if t.type == "NUMBER":
            self.next()
            return Number(float(t.value))

        if t.type == "STRING":
            self.next()
            return String(t.value)

        if t.type == "IDENT":
            name = self.next().value
            # Llamada a función: foo(x)
            if self.peek().type == "LPAREN":
                return self.parse_call_suffix(name)
            # Variable simple: x
            return Var(name)

        if t.type == "LPAREN":
            self.next()
            node = self.parse_expression()  # Reinicia la jerarquía
            self.expect("RPAREN")
            return node

        raise SyntaxError(f"Token inesperado en expresión: {t.type}({t.value}) linea {t.line}")

    def parse_call_suffix(self, name):
        self.expect("LPAREN")
        args = []
        if self.peek().type != "RPAREN":
            args.append(self.parse_expression()) # Argumento 1
            while self.peek().type == "COMMA":
                self.next()
                args.append(self.parse_expression()) # Argumentos N
        self.expect("RPAREN")
        return Call(name, args)