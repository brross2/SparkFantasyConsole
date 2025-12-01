from VM.Data import *
from VM.Opcodes import *


class Compiler:
    def __init__(self):
        self.code = []  # Aquí guardamos los bytes (enteros)
        self.consts = []  # Aquí guardamos los valores (números, strings)
        self.const_map = {}  # Para no repetir constantes idénticas

    def emit(self, opcode, operand=None):
        """Ayuda a escribir en la lista de código"""
        self.code.append(opcode)
        if operand is not None:
            self.code.append(operand)

    def add_const(self, value):
        """Agrega una constante y devuelve su índice"""
        if value in self.const_map:
            return self.const_map[value]
        idx = len(self.consts)
        self.consts.append(value)
        self.const_map[value] = idx
        return idx

    def compile(self, node):
        """Dispatcher principal: mira el tipo de nodo y llama a su función"""
        method_name = f'compile_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit)
        return method(node)

    def no_visit(self, node):
        raise NotImplementedError(f"No se sabe compilar {type(node).__name__}")

    # --- Visitantes de Nodos ---
    def compile_block(self, nodes):
        for node in nodes:
            self.compile(node)
            if isinstance(node, (Call, BinaryOp, UnaryOp, Number, String, Var)):
                self.emit(POP)
            else:
                pass

    def compile_Program(self, node):
        self.compile_block(node.body)
        self.emit(HALT)

    def compile_Number(self, node):
        idx = self.add_const(node.value)
        self.emit(LOAD_CONST, idx)

    def compile_String(self, node):
        idx = self.add_const(node.value)
        self.emit(LOAD_CONST, idx)

    def compile_Var(self, node):
        idx = self.add_const(node.name)  # Guardamos el nombre de la variable como const
        self.emit(LOAD_VAR, idx)

    def compile_Assign(self, node):
        self.compile(node.value)  # 1. Compilar el valor (se pone en stack)
        idx = self.add_const(node.name)  # 2. Obtener índice del nombre
        self.emit(STORE_VAR, idx)  # 3. Guardar

    def compile_BinaryOp(self, node):
        self.compile(node.left)
        self.compile(node.right)

        op_map = {
            '+': ADD, '-': SUB, '*': MUL, '/': DIV, '%': MOD,
            '==': EQ, '~=': NEQ, '<': LT, '<=': LTE, '>': GT, '>=': GTE
        }
        if node.op in op_map:
            self.emit(op_map[node.op])
        else:
            raise SyntaxError(f"Operador desconocido: {node.op}")

    def compile_UnaryOp(self, node):
        self.compile(node.value)
        if node.op == '-':
            self.emit(NEG)

    # --- Control de Flujo (La parte interesante) ---

    def compile_If(self, node):
        self.compile(node.cond)
        self.emit(JMP_IF_FALSE, 0)
        jump_else = len(self.code) - 1

        self.compile_block(node.body)

        if node.else_body:
            self.emit(JMP, 0)
            jump_end = len(self.code) - 1

            self.code[jump_else] = len(self.code)
            self.compile_block(node.else_body)
            self.code[jump_end] = len(self.code)
        else:
            self.code[jump_else] = len(self.code)

    def compile_While(self, node):
        loop_start = len(self.code)
        self.compile(node.cond)
        self.emit(JMP_IF_FALSE, 0)
        exit_jump_idx = len(self.code) - 1

        self.compile_block(node.body)

        self.emit(JMP, loop_start)
        self.code[exit_jump_idx] = len(self.code)

    def compile_Return(self, node):
        if node.value:
            self.compile(node.value)  # Carga el valor al stack
        else:
            self.emit(LOAD_CONST, self.add_const(None))  # Return nil/None por defecto
        self.emit(RET)

    def compile_Call(self, node):
        # 1. Compilar Argumentos (se ponen en el stack)
        for arg in node.args:
            self.compile(arg)

        # 2. Verificar si es una System Call (Optimización de hardware)
        if node.name in SYS_FUNCTIONS:
            sys_id = SYS_FUNCTIONS[node.name]
            # Emitimos SYS con el ID y la cantidad de argumentos
            self.emit(SYS, sys_id)
            self.emit(len(node.args))
        else:
            # Llamada de usuario normal
            idx = self.add_const(node.name)
            self.emit(LOAD_VAR, idx)
            self.emit(CALL, len(node.args))

    def compile_FuncDecl(self, node):
        self.emit(JMP, 0)
        jump_idx = len(self.code) - 1
        start_addr = len(self.code)

        if node.params:
            for param_name in reversed(node.params):
                idx = self.add_const(param_name)
                self.emit(STORE_VAR, idx)

        self.compile_block(node.body)

        if not self.code or self.code[-1] != RET:
            self.emit(LOAD_CONST, self.add_const(None))
            self.emit(RET)

        self.code[jump_idx] = len(self.code)

        self.emit(LOAD_CONST, self.add_const(start_addr))
        self.emit(STORE_VAR, self.add_const(node.name))