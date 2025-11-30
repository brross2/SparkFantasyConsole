from VM.Opcodes import *

class SparkVM:
    def __init__(self, bytecode, constants):
        self.code = bytecode  # El "ROM" del juego
        self.consts = constants  # Datos estáticos (strings, nums)

        # Estado del Procesador
        self.ip = 0  # Instruction Pointer (PC)
        self.sp = 0  # Stack Pointer (implícito en len(stack))
        self.stack = []  # Pila de operandos
        self.globals = {}  # RAM para variables (x, y, score...)
        self.is_halted = False

        # Debugging / Profiling
        self.cycle_count = 0


    def reset(self):
        self.ip = 0
        self.stack = []
        self.is_halted = False
        self.cycle_count = 0


    def run_frame(self, max_cycles=60):
        """
        Ejecuta instrucciones hasta gastar los ciclos del frame
        o hasta que el programa termine (HALT).
        Según specs.md: 60 ciclos por frame.
        """
        cycles_left = max_cycles

        while cycles_left > 0 and not self.is_halted and self.ip < len(self.code):
            # Fetch
            op = self.code[self.ip]
            self.ip += 1

            # Decode & Execute
            self._exec_opcode(op)

            # Accounting
            cycles_left -= 1
            self.cycle_count += 1


    def _exec_opcode(self, op):
        """Dispatcher gigante: El cerebro de la CPU"""

        # --- A. Datos ---
        if op == LOAD_CONST:
            idx = self.code[self.ip]
            self.ip += 1
            self.stack.append(self.consts[idx])

        elif op == LOAD_VAR:
            idx = self.code[self.ip]
            self.ip += 1
            name = self.consts[idx]
            # En Lua/Python acceder a var no definida es nil/Error.
            # Aquí asumimos 0 para simplicidad retro o lanzamos error.
            val = self.globals.get(name, 0.0)
            self.stack.append(val)

        elif op == STORE_VAR:
            idx = self.code[self.ip]
            self.ip += 1
            name = self.consts[idx]
            val = self.stack.pop()
            self.globals[name] = val

        elif op == POP:
            if self.stack: self.stack.pop()

        # --- B. Aritmética ---
        elif op == ADD:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a + b)
        elif op == SUB:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a - b)
        elif op == MUL:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a * b)
        elif op == DIV:
            b = self.stack.pop()
            a = self.stack.pop()
            # Proteger contra división por cero estilo retro (retornar 0 o inf)
            self.stack.append(a / b if b != 0 else 0)
        elif op == NEG:
            val = self.stack.pop()
            self.stack.append(-val)

        # --- C. Comparaciones ---
        elif op == EQ:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a == b)
        elif op == NEQ:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a != b)
        elif op == LT:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a < b)
        elif op == LTE:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a <= b)
        elif op == GT:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a > b)
        elif op == GTE:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a >= b)

        # --- D. Saltos ---
        elif op == JMP:
            target = self.code[self.ip]
            self.ip += 1
            self.ip = target

        elif op == JMP_IF_FALSE:
            target = self.code[self.ip]
            self.ip += 1
            val = self.stack.pop()
            # En Python 0 y False son falsy.
            if not val:
                self.ip = target

        # --- E. Control ---
        elif op == HALT:
            self.is_halted = True

        elif op == CALL:
            # Complejidad futura: Manejar llamadas a funciones definidas
            # Por ahora saltamos los argumentos
            argc = self.code[self.ip]
            self.ip += 1
            pass

        elif op == SYS:
            sys_id = self.code[self.ip];
            self.ip += 1
            argc = self.code[self.ip];
            self.ip += 1

            # Sacamos los argumentos del stack
            args = []
            for _ in range(argc):
                args.insert(0, self.stack.pop())

            # Aquí despacharemos a Pygame luego. Por ahora DEBUG:
            sys_name = [k for k, v in SYS_FUNCTIONS.items() if v == sys_id][0]
            print(f">> SYSTEM CALL: {sys_name}{tuple(args)}")

        elif op == RET:
            pass

            # Resultado dummy (0) al stack
            self.stack.append(0)
        else:
            raise RuntimeError(f"Opcode desconocido: {op} en addr {self.ip - 1}")

    # Método helper para ver qué pasa adentro
    def dump_stack(self):
        print(f"[Stack]: {self.stack} | [Globals]: {self.globals}")