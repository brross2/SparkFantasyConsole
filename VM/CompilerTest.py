from VM.Lexer import Lexer
from VM.Parser import Parser
from VM.Compiler import Compiler
from VM.Opcodes import *
from VM.VirtualMachine import SparkVM

if __name__ == "__main__":
    # --- CÓDIGO FUENTE SPARKLANG ---
    # Prueba: Aritmética, Negativos, While, If y Asignación
    source_code = """
    -- 1. Prueba de Aritmética y Unarios
    val = (10 + 2) * -2 
    -- val debería ser -24

    -- 2. Prueba de Condicional
    abs_val = 0
    if val < 0 then
        abs_val = val * -1
    end
    -- abs_val debería ser 24

    -- 3. Prueba de Bucle (Cálculo de Factorial de 5)
    n = 5
    fact = 1

    while n > 0 do
        fact = fact * n
        n = n - 1
    end
    -- fact debería ser 120

    h = 10
    if h > 50 then
        res = 1
    else
        res = 2
        pset(10, 10, 7) -- Prueba de SYS call
    end

    -- 4. Verificación final
    result = 0
    if fact == 120 then
        result = 1
    end
    """

    print("=== 1. SOURCE CODE ===")
    print(source_code)

    # 2. Parsing
    print("\n=== 2. PARSING (AST) ===")
    try:
        # Nota: lex devuelve una lista de tokens
        tokens = Lexer(source_code)
        parser = Parser(tokens)
        ast = parser.parse()
        # pprint(ast) # Descomentar si quieres ver el árbol completo
        print("AST generado correctamente.")
    except Exception as e:
        print(f"Error de Parsing: {e}")
        exit()

    # 3. Compilation
    print("\n=== 3. COMPILATION (BYTECODE) ===")
    compiler = Compiler()
    compiler.compile(ast)

    print(f"Tabla de Constantes: {compiler.consts}")

    print("\n--- Bytecode Decodificado ---")
    i = 0
    # Usamos OP_NAMES importado de VM.Opcodes
    while i < len(compiler.code):
        op = compiler.code[i]
        name = OP_NAMES.get(op, str(op))

        # Instrucciones con argumento
        if op in [LOAD_CONST, LOAD_VAR, STORE_VAR, JMP, JMP_IF_FALSE]:
            arg = compiler.code[i + 1]

            # Hacemos el debug más bonito mostrando el valor real
            val_str = ""
            if op == LOAD_CONST: val_str = f"({compiler.consts[arg]})"
            if op in [LOAD_VAR, STORE_VAR]: val_str = f"('{compiler.consts[arg]}')"
            if op in [JMP, JMP_IF_FALSE]: val_str = f"(addr {arg})"

            print(f"{i:03}: {name:<14} {arg} {val_str}")
            i += 2
        else:
            print(f"{i:03}: {name:<14}")
            i += 1

    # 4. Execution
    print("\n=== 4. VM RUNTIME TRACE ===")
    vm = SparkVM(compiler.code, compiler.consts)

    cycles = 0
    print(f"{'CICLO':<6} | {'OPCODE':<12} | {'STACK (Top derecha)'}")
    print("-" * 50)

    # Ejecutamos paso a paso para ver el trace
    while vm.ip < len(vm.code) and not vm.is_halted:
        # Hack visual: Imprimimos antes de ejecutar para ver qué va a pasar
        current_op = vm.code[vm.ip]
        op_name = OP_NAMES.get(current_op, "?")

        vm.run_frame()  # Ejecuta una instrucción
        cycles += 1

        # Mostramos estado
        print(f"{cycles:04d}   | {op_name:<12} | {vm.stack}")

        if cycles > 200:  # Protección contra bucles infinitos
            print("!!! Infinite loop protection triggered !!!")
            break

    print("\n=== 5. ESTADO FINAL DE MEMORIA (RAM) ===")
    for var, val in vm.globals.items():
        print(f"{var}: {val}")

    print(f"\nCiclos totales usados: {cycles}")

    # Verificación automática del Test
    if vm.globals.get("fact") == 120 and vm.globals.get("result") == 1:
        print("\nSUCCESS: ¡Todas las pruebas pasaron correctamente!")
    else:
        print("\nFAILURE: Algo falló en la lógica.")