# --- OPCODES ---
# Constantes para identificar las instrucciones
HALT          = 0
LOAD_CONST    = 1  # [idx] -> Carga const[idx] al stack
LOAD_VAR      = 2  # [idx] -> Carga global[vars[idx]] al stack
STORE_VAR     = 3  # [idx] -> Guarda tope del stack en global[vars[idx]]
POP           = 4  # Elimina el tope del stack

ADD           = 10
SUB           = 11
MUL           = 12
DIV           = 13
NEG           = 14
MOD           = 15

EQ            = 20 # ==
NEQ           = 21 # ~=
LT            = 22 # <
LTE           = 23 # <=
GT            = 24 # >
GTE           = 25 # >=

JMP           = 30 # [addr] -> Salta a la dirección addr
JMP_IF_FALSE  = 31 # [addr] -> Salta si el tope es Falso/0

CALL          = 40 # [argc] -> Llama función
RET           = 41 # Retorna
SYS           = 42 # [id, argc] -> Llamada al sistema (opcional por ahora)

OP_NAMES = {v: k for k, v in globals().items() if isinstance(v, int) and k.isupper()}

SYS_FUNCTIONS = {
    "pset": 0,
    "sfx": 1,
    "spr": 2,
    "map": 3,
    "btn": 4,
    "cls": 5,
    "print": 6,
    "log": 7
}

