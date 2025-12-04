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

        # Estado de Error
        self.runtime_error = None
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
        # print(self.runtime_error) # Descomentar para debug en consola
        return False

    def _check_type(self, value, expected_type):
        """Valida tipos en tiempo de ejecución"""
        if expected_type in ["int", "float", "btn_id", "color"]:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "str":
            return isinstance(value, str)
        return True

    def step(self, max_cycles=60):
        cycles_left = max_cycles
        while cycles_left > 0 and not self.halted:
            if self.ip >= len(self.code):
                self.halted = True
                break

            try:
                # --- CORRECCIÓN AQUÍ ---
                # Casteamos self.ip a int por seguridad
                op = self.code[int(self.ip)]
                self.ip += 1
                self._exec_opcode(op)

                cycles_left -= 1
                self.cycle_count += 1

            except IndexError:
                self._error("Segmentation Fault (Read beyond end of code)")
                break
            except Exception as e:
                self._error(f"CPU Exception: {e}")
                break

    def _exec_opcode(self, op):
        if self.halted: return

        # --- A. DATOS ---
        if op == LOAD_CONST:
            idx = self.code[self.ip];
            self.ip += 1
            self.stack.append(self.consts[idx])

        elif op == LOAD_VAR:
            idx = self.code[self.ip];
            self.ip += 1
            name = self.consts[idx]
            val = self.globals.get(name, 0.0)
            self.stack.append(val)

        elif op == STORE_VAR:
            idx = self.code[self.ip];
            self.ip += 1
            name = self.consts[idx]
            if not self.stack: return self._error("Stack Underflow (STORE)")
            val = self.stack.pop()
            self.globals[name] = val

        elif op == POP:
            if self.stack: self.stack.pop()

        # --- B. ARITMÉTICA (CORREGIDA) ---
        # ¡IMPORTANTE! SUB (11) y ADD (10) deben estar en esta lista
        elif op in [ADD, SUB, MUL, DIV, MOD]:
            if len(self.stack) < 2: return self._error(f"Stack Underflow ({op})")
            b = self.stack.pop()
            a = self.stack.pop()

            # Chequeo de Tipos
            are_numbers = isinstance(a, (int, float)) and isinstance(b, (int, float))

            if not are_numbers:
                # Excepción: Concatenar strings con '+'
                if op == ADD:
                    self.stack.append(str(a) + str(b))
                    return
                else:
                    return self._error(f"Math Error: Cannot op {op} on {type(a)} and {type(b)}")

            # Ejecución
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
            if not self.stack: return self._error("Stack Underflow (NEG)")
            val = self.stack.pop()
            if not isinstance(val, (int, float)): return self._error("Cannot negate non-number")
            self.stack.append(-val)

        # --- C. COMPARACIONES ---
        elif op in [EQ, NEQ, LT, LTE, GT, GTE]:
            if len(self.stack) < 2: return self._error("Stack Underflow (COMP)")
            b = self.stack.pop()
            a = self.stack.pop()
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

        # --- D. SALTOS ---
        elif op == JMP:
            target = self.code[self.ip]
            self.ip += 1
            self.ip = int(target)

        elif op == JMP_IF_FALSE:
            target = self.code[self.ip]
            self.ip += 1
            if not self.stack: return self._error("Stack Underflow (JMP_IF)")
            val = self.stack.pop()
            if not val: self.ip = int(target)

        # --- E. CONTROL ---
        elif op == HALT:
            self.halted = True

        elif op == CALL:
            argc = self.code[self.ip];
            self.ip += 1
            if len(self.stack) < argc + 1: return self._error("Stack Underflow (CALL)")

            # 1. Extraer argumentos (sin perderlos)
            args_temp = []
            for _ in range(argc): args_temp.append(self.stack.pop())

            # 2. Extraer destino
            func_target = self.stack.pop()

            # 3. Devolver argumentos al stack
            for arg in reversed(args_temp): self.stack.append(arg)

            target_addr = None

            # --- CORRECCIÓN AQUÍ ---
            # Aceptamos int Y float para la dirección
            if isinstance(func_target, (int, float)):
                target_addr = int(func_target)  # Forzamos entero
            elif isinstance(func_target, str):
                target_addr = self.globals.get(func_target)

            if isinstance(target_addr, int):
                self.call_stack.append(self.ip)
                self.ip = target_addr
            else:
                # Si falla, limpiamos los argumentos para no corromper la pila
                for _ in range(argc): self.stack.pop()
                # Opcional: Avisar si no es una función del sistema
                # print(f"Warning: Function {func_target} not found/invalid")

        # --- F. SYSCALLS ---
        elif op == SYS:
            sys_id = self.code[self.ip];
            self.ip += 1
            argc = self.code[self.ip];
            self.ip += 1

            if len(self.stack) < argc: return self._error(f"Stack Underflow (SYS {sys_id})")

            args = []
            for _ in range(argc): args.insert(0, self.stack.pop())

            # Identificar nombre para validación
            func_name = None
            for name, fid in SYS_FUNCTIONS.items():
                if fid == sys_id: func_name = name; break

            # Validar Tipos
            if func_name and func_name in SYS_SPECS:
                specs = SYS_SPECS[func_name]
                expected = specs.get("args", [])
                for i, val in enumerate(args):
                    if i < len(expected):
                        if not self._check_type(val, expected[i]):
                            return self._error(
                                f"'{func_name}' arg {i + 1}: expected {expected[i]}, got {type(val).__name__}")

            # Ejecutar
            if not self.halted and self.hardware:
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
                elif sys_id == 7:  # log
                    if len(args) >= 1:
                        msg = str(args[0])
                        # Enviar a la consola del sistema (si existe)
                        if hasattr(self, 'console') and self.console:
                            self.console.log(msg, "USER")
                        else:
                            print(f"[USER LOG] {msg}")  # Fallback
                    self.stack.append(0)
                else:
                    self.stack.append(0)
            else:
                self.stack.append(0)

        elif op == RET:
            if self.call_stack:
                self.ip = self.call_stack.pop()
            else:
                self.halted = True

        else:
            return self._error(f"Unknown Opcode {op}")

    def call_function(self, func_name):
        if func_name in self.globals:
            addr = self.globals[func_name]
            initial_stack = len(self.stack)
            self.call_stack.append(len(self.code))
            self.ip = int(addr)
            self.halted = False

            while self.ip < len(self.code) and len(self.call_stack) > 0 and not self.halted:
                self.step()

            if len(self.stack) > initial_stack:
                self.stack.pop()