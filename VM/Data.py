from dataclasses import dataclass
from typing import List, Optional

class Node: pass

@dataclass
class Program(Node):
    body: List[Node]

@dataclass
class FuncDecl(Node):
    name: str
    params: List[str]
    body: List[Node]

@dataclass
class Call(Node):
    name: str
    args: List[Node]

@dataclass
class Assign(Node):
    name: str
    value: Node

@dataclass
class Return(Node):
    value: Optional[Node]

@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    value: Node

@dataclass
class Number(Node):
    value: float

@dataclass
class String(Node):
    value: str

@dataclass
class Var(Node):
    name: str

@dataclass
class If(Node):
    cond: Node
    body: List[Node]
    else_body: Optional[List[Node]] = None

@dataclass
class While(Node):
    cond: Node
    body: List[Node]