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

    def compile_Program(self, node):
        for stmt in node.body:
            self.compile(stmt)
            # Si es una expresión suelta (no asignación), limpiamos el stack
            if isinstance(stmt, (BinaryOp, Number, String, Call)):
                self.emit(POP)
        self.emit(HALT)  # Fin del programa

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
            '+': ADD, '-': SUB, '*': MUL, '/': DIV,
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
        # Estructura:
        #    CONDICION
        #    JMP_IF_FALSE -> salto_a_else
        #    CUERPO_TRUE
        #    JMP -> salto_a_fin  <-- Solo necesario si hay else
        # salto_a_else:
        #    CUERPO_ELSE
        # salto_a_fin:

        self.compile(node.cond)

        # Placeholder para saltar al ELSE (o al fin si no hay else)
        self.emit(JMP_IF_FALSE, 0)
        jump_to_else_idx = len(self.code) - 1

        # Compilar cuerpo TRUE
        for stmt in node.body: self.compile(stmt)

        if node.else_body:
            # Si hay else, al terminar el TRUE debemos saltar al final
            self.emit(JMP, 0)
            jump_to_end_idx = len(self.code) - 1

            # --- Aquí empieza el ELSE ---
            # Corregimos el primer salto (JMP_IF_FALSE) para que caiga aquí
            self.code[jump_to_else_idx] = len(self.code)

            # Compilamos cuerpo ELSE
            for stmt in node.else_body: self.compile(stmt)

            # --- Aquí termina todo ---
            # Corregimos el salto del bloque TRUE para que caiga aquí
            self.code[jump_to_end_idx] = len(self.code)
        else:
            # Si no hay else, el JMP_IF_FALSE salta directo aquí
            self.code[jump_to_else_idx] = len(self.code)

    def compile_While(self, node):
        # 1. Marcar inicio del bucle (para volver aquí)
        loop_start = len(self.code)

        # 2. Compilar condición
        self.compile(node.cond)

        # 3. Salir si es falso
        self.emit(JMP_IF_FALSE, 0)
        exit_jump_idx = len(self.code) - 1

        # 4. Cuerpo
        for stmt in node.body:
            self.compile(stmt)

        # 5. Volver al inicio (Loop)
        self.emit(JMP, loop_start)

        # 6. Patching: Arreglar el salto de salida
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
            self.emit(LOAD_CONST, idx)
            self.emit(CALL, len(node.args))