import sys
import json
from lark import Lark, Transformer, exceptions

grammar = r"""
start: statement+
statement: const_decl
const_decl: "(" "define" NAME value ")" ";"
?value: NUMBER
      | array
      | expr
      | NAME        -> var_ref
array: "[" [value ("," value)*] "]"
expr: "^" "(" expr_body ")"
?expr_body: value
          | expr_body "+" expr_body   -> add
          | expr_body "-" expr_body   -> sub
          | expr_body "*" expr_body   -> mul
          | "max" "(" expr_body "," expr_body ")" -> max_func
          | "pow" "(" expr_body "," expr_body ")" -> pow_func
NUMBER: /0[oO][0-7]+/
NAME: /[a-z]+/
%ignore /\s+/
"""

class ConfigTransformer(Transformer):
    def __init__(self):
        self.constants = {}
    def NUMBER(self, token):
        return int(token, 8)
    def NAME(self, token):
        return str(token)
    def array(self, items):
        return list(items)
    def var_ref(self, items):
        name = items[0]
        if name not in self.constants:
            raise ValueError(f"Неизвестная константа: {name}")
        return self.constants[name]
    def const_decl(self, items):
        name = items[0]
        value = items[1]
        self.constants[name] = value
    def add(self, items):
        return items[0] + items[1]
    def sub(self, items):
        return items[0] - items[1]
    def mul(self, items):
        return items[0] * items[1]
    def max_func(self, items):
        return max(items[0], items[1])
    def pow_func(self, items):
        return pow(items[0], items[1])
    def expr(self, items):
        return items[0]
    def start(self, items):
        return self.constants

def parse_config(text: str):
    parser = Lark(grammar, parser="lalr")
    try:
        tree = parser.parse(text)
        transformer = ConfigTransformer()
        return transformer.transform(tree)
    except exceptions.LarkError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

def run_tests():
    tests = {
        "Компьютеры": """
            (define cores 0o10);
            (define threads ^(cores * 0o2));
            (define memory [0o400, 0o1000, 0o2000]);
        """,
        "Космос": """
            (define engines 0o4);
            (define thrust ^(pow(engines, 0o2)));
            (define fuel [0o100, 0o200, 0o300]);
        """,
        "Образование": """
            (define lectures 0o20);
            (define labs 0o10);
            (define total ^(lectures + labs));
        """
    }

    for name, text in tests.items():
        print(f"\n--- {name} ---")
        result = parse_config(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "tests":
        run_tests()
    elif len(sys.argv) == 2:
        result = parse_config(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Использование:")
        print("  python Konf.py tests")
        print("  python Konf.py \"(define a 0o10); (define b 0o4); (define c ^(a+b));\"")
        sys.exit(1)

if __name__ == "__main__":
    main()