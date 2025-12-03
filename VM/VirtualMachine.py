from VM.Opcodes import *
from VM.SystemSpecs import SYS_SPECS


class SparkVM:
    def __init__(self, bytecode, constants, hardware=None):
        self.code = bytecode
        self.consts = constants
        self.hardware = hardware

        # Estado del Procesador
        self.ip = 0
        self.sp = 0
        self.stack = []
        self.globals = {}
        self.call_stack = []
        self.halted = False
        self.runtime_error = None

        # Debugging / Profiling
        self.cycle_count = 0

    def reset(self):
        self.ip = 0
        self.stack = []
        self.halted = False
        self.cycle_count = 0
        self.runtime_error = None

    def _error(self, msg):
        """Detiene la VM y registra el error"""
        self.halted = True
        self.runtime_error = f"RUNTIME ERR: {msg}"
        print(self.runtime_error)  # Para debug en consola
        return False  # Señal para detener bucles

    def _check_type(self, value, expected_type):
        """Valida un valor individual contra un tipo esperado"""
        if expected_type == "int" or expected_type == "float" or expected_type == "btn_id":
            # Aceptamos int y float como números
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "color":
            return isinstance(value, (int, float))
        elif expected_type == "str":
            return isinstance(value, str)
        elif expected_type == "any":
            return True
        return True  # Si el tipo no está definido, pasamos

    def step(self, max_cycles=60):
        cycles_left = max_cycles

        while cycles_left > 0 and not self.halted and self.ip < len(self.code):
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
        if self.halted:
            return

        # --- A. Datos ---
        if op == LOAD_CONST:
            idx = self.code[self.ip]
            self.ip += 1
            self.stack.append(self.consts[idx])

        elif op == LOAD_VAR:
            idx = self.code[self.ip]
            self.ip += 1
            name = self.consts[idx]
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

            # --- B. ARITMÉTICA SEGURA (BLINDADA) ---
            elif op in [ADD, SUB, MUL, DIV, MOD]:
                if len(self.stack) < 2: return self._error("Stack Underflow")
                b = self.stack.pop()
                a = self.stack.pop()

                # 1. Chequeo de Tipos Numéricos
                if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
                    # Excepción: Concatenación de strings con ADD (+)
                    if op == ADD and (isinstance(a, str) or isinstance(b, str)):
                        self.stack.append(str(a) + str(b))
                        return
                    else:
                        return self._error(f"Math Error: Cannot {op} {type(a)} and {type(b)}")

                # 2. Ejecución Segura
                if op == ADD:
                    self.stack.append(a + b)
                elif op == SUB:
                    self.stack.append(a - b)
                elif op == MUL:
                    self.stack.append(a * b)
                elif op == DIV:
                    if b == 0: return self._error("Division by Zero")
                    self.stack.append(a / b)
                elif op == MOD:
                    if b == 0: return self._error("Modulo by Zero")
                    self.stack.append(a % b)

        elif op == NEG:
            if not self.stack: return self._error("Stack Underflow")
            val = self.stack.pop()
            if not isinstance(val, (int, float)): return self._error("Cannot negate non-number")
            self.stack.append(-val)

        # --- C. COMPARACIONES (Seguras) ---
        elif op in [EQ, NEQ, LT, LTE, GT, GTE]:
            if len(self.stack) < 2: return self._error("Stack Underflow")
            b = self.stack.pop()
            a = self.stack.pop()

            # Python maneja comparaciones de tipos mixtos bien (False),
            # pero < > pueden crashear entre str e int.
            try:
                if op == EQ:
                    self.stack.append(a == b)
                elif op == NEQ:
                    self.stack.append(a != b)
                elif op == LT:
                    self.stack.append(a < b)
                elif op == LTE:
                    self.stack.append(a <= b)
                elif op == GT:
                    self.stack.append(a > b)
                elif op == GTE:
                    self.stack.append(a >= b)
            except TypeError:
                return self._error(f"Cannot compare {type(a)} and {type(b)}")

        # --- D. Saltos ---
        elif op == JMP:
            target = self.code[self.ip]
            self.ip += 1
            self.ip = target

        elif op == JMP_IF_FALSE:
            target = self.code[self.ip]
            self.ip += 1
            val = self.stack.pop()
            if not val:
                self.ip = target

        # --- E. Control ---
        elif op == HALT:
            self.halted = True


        elif op == CALL:
            argc = self.code[self.ip];
            self.ip += 1
            if len(self.stack) < argc + 1: return self._error("Stack Underflow CALL")
            func_idx = -1 - argc
            func_target = self.stack[func_idx]

            args_temp = []
            for _ in range(argc): args_temp.append(self.stack.pop())

            self.stack.pop()

            for arg in reversed(args_temp): self.stack.append(arg)

            target_addr = None
            if isinstance(func_target, int):
                target_addr = func_target
            elif isinstance(func_target, str):
                target_addr = self.globals.get(func_target)

            if isinstance(target_addr, int):
                self.call_stack.append(self.ip)
                self.ip = target_addr
            else:
                for _ in range(argc): self.stack.pop()
                # Opcional: self._error(f"Function '{func_target}' not found")

        elif op == SYS:
            sys_id = self.code[self.ip];
            self.ip += 1
            argc = self.code[self.ip];
            self.ip += 1

            # 1. Recuperar argumentos
            if len(self.stack) < argc: return self._error(f"Stack Underflow SYS {sys_id}")

            args = []
            for _ in range(argc):
                args.insert(0, self.stack.pop())

            # 2. Identificar función y Validar Tipos
            func_name = None
            func_spec = None

            # Buscar nombre por ID (Inverso del diccionario SYS_FUNCTIONS en Opcodes)
            # Esto es lento en cada frame, idealmente tendríamos un mapa ID->Spec precalculado.
            # Pero para empezar está bien.
            for name, fid in SYS_FUNCTIONS.items():
                if fid == sys_id:
                    func_name = name
                    break

            if func_name and func_name in SYS_SPECS:
                specs = SYS_SPECS[func_name]
                expected_types = specs.get("args", [])

                # Chequeo de cantidad (Runtime check, por si el compilador falló o se hizo manual)
                if len(args) < len(expected_types):
                    # Permitimos args opcionales si la logica interna lo soporta,
                    # pero validamos los que hay.
                    pass

                    # Chequeo de Tipos
                for i, val in enumerate(args):
                    if i < len(expected_types):
                        req_type = expected_types[i]
                        if not self._check_type(val, req_type):
                            return self._error(
                                f"'{func_name}' arg {i + 1}: expected {req_type}, got {type(val).__name__}")

            # 3. Ejecución (Solo si self.halted es False)
            if not self.halted:
                if self.hardware:
                    if sys_id == 0:  # pset
                        if len(args) >= 3: self.hardware.pset(args[0], args[1], args[2])
                        self.stack.append(0)
                    elif sys_id == 2:  # spr
                        if len(args) >= 3: self.hardware.spr(args[0], args[1], args[2])
                        self.stack.append(0)
                    elif sys_id == 4:  # btn
                        val = 0
                        if len(args) >= 1: val = 1 if self.hardware.btn(int(args[0])) else 0
                        self.stack.append(val)
                    elif sys_id == 5:  # cls
                        self.hardware.clear_screen()
                        self.stack.append(0)
                    elif sys_id == 6:  # print
                        if len(args) >= 4:
                            is_small = False
                            if len(args) >= 5 and args[4] == 1: is_small = True
                            self.hardware.print_text(str(args[0]), args[1], args[2], args[3], is_small)
                        self.stack.append(0)
                    else:
                        self.stack.append(0)
                else:
                    self.stack.append(0)

        elif op == RET:
            if self.call_stack:
                self.ip = self.call_stack.pop()
            else:
                self.halted = True  # Fin del programa principal

        else:
            return self._error(f"Unknown Opcode {op}")

    def call_function(self, func_name):
        if func_name in self.globals:
            addr = self.globals[func_name]
            initial_stack_size = len(self.stack)

            self.call_stack.append(len(self.code))
            self.ip = addr

            while self.ip < len(self.code) and len(self.call_stack) > 0 and not self.halted:
                self.step()

            # Limpiador de basura del main loop
            if len(self.stack) > initial_stack_size:
                self.stack.pop()