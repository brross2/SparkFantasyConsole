from VM.Opcodes import *


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

        # Debugging / Profiling
        self.cycle_count = 0

    def reset(self):
        self.ip = 0
        self.stack = []
        self.halted = False
        self.cycle_count = 0

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
            self.stack.append(a / b if b != 0 else 0)
        elif op == NEG:
            val = self.stack.pop()
            self.stack.append(-val)
        elif op == MOD:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a % b if b != 0 else 0)

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
            if not val:
                self.ip = target

        # --- E. Control ---
        elif op == HALT:
            self.halted = True


        elif op == CALL:
            argc = self.code[self.ip]
            self.ip += 1

            func_target = self.stack.pop()
            target_addr = None
            if isinstance(func_target, int):
                target_addr = func_target
            elif isinstance(func_target, str):
                target_addr = self.globals.get(func_target)
            if isinstance(target_addr, int):
                self.call_stack.append(self.ip)
                self.ip = target_addr
            else:
                for _ in range(argc):
                    if self.stack: self.stack.pop()

        elif op == SYS:
            sys_id = self.code[self.ip]
            self.ip += 1
            argc = self.code[self.ip]
            self.ip += 1

            args = []
            for _ in range(argc):
                args.insert(0, self.stack.pop())

            # --- CORRECCIÓN CRÍTICA DE ESTRUCTURA ---
            if self.hardware:
                if sys_id == 0:  # pset
                    if len(args) >= 3:
                        self.hardware.pset(args[0], args[1], args[2])
                    self.stack.append(0)  # Un solo append

                elif sys_id == 2: #spr(id,x,y)
                    if len(args) >= 3:
                        self.hardware.spr(args[0], args[1], args[2])
                    self.stack.append(0)

                elif sys_id == 4:  # btn
                    if len(args) >= 1:
                        btn_id = int(args[0])
                        is_pressed = self.hardware.btn(btn_id)
                        self.stack.append(1 if is_pressed else 0)
                    else:
                        self.stack.append(0)

                elif sys_id == 5:
                    self.hardware.clear_screen()
                    self.stack.append(0)

                else:  # Otros IDs
                    self.stack.append(0)
            else:
                self.stack.append(0)  # Sin Hardware

        elif op == RET:
            if self.call_stack:
                return_addr = self.call_stack.pop()
                self.ip = return_addr
            else:
                self.halted = True

            # --- CORRECCIÓN CRÍTICA ---
            # Eliminado: self.stack.append(0)
            # El compilador ya puso el valor de retorno en el stack antes de llamar a RET.

        else:
            raise RuntimeError(f"Opcode desconocido: {op} en addr {self.ip - 1}")

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