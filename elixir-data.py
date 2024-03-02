import re
import sys
from collections import namedtuple

Token = namedtuple("Token", ["kind", "lexeme"])

TOKEN_KINDS = {
    "INTEGER": "INT",
    "BOOLEAN": "BOOL",
    "ATOM": "ATOM",
    "LIST": "LIST",
    "TUPLE": "TUPLE",
    "MAP": "MAP",
    "ARROW": "ARROW",
    "EOF": "EOF",
    "LEFT_BRACKET": "LEFT_BRACKET",
    "RIGHT_BRACKET": "RIGHT_BRACKET",
    "LEFT_BRACE": "LEFT_BRACE",
    "RIGHT_BRACE": "RIGHT_BRACE",
    "COMMA": "COMMA",
    "DELIMITER": "$",
    "COLON": "COLON",
}

TOKEN_DEFINITION = {
    "{": "LEFT_BRACE",
    "}": "RIGHT_BRACE",
    "[": "LEFT_BRACKET",
    "]": "RIGHT_BRACKET",
    "%": "MAP",
    ",": "COMMA",
    "=>": "ARROW"
   
}

INTEGER_PATTERN = re.compile(r'\b\d[\d_]*\b')
ATOM_PATTERN = re.compile(r':[a-zA-Z_][a-zA-Z0-9_]*')
BOOLEAN_PATTERN = re.compile(r'\b(true|false)\b')



def lexer(input_str):
    tokens = []
    pos = 0
    str_at_pos = input_str[pos]

    def next_char(number=1):
        nonlocal pos, str_at_pos
        pos += number
        str_at_pos = input_str[pos] if pos < len(input_str) else None

    def read_int():
        nonlocal pos, str_at_pos
        result = ""
        is_invalid_num = False
        while str_at_pos is not None and (str_at_pos.isdigit() or str_at_pos == '_'):
            if str_at_pos != "_":
                result += str_at_pos
            else:
                if not input_str[pos + 1]:
                    is_invalid_num = True
            next_char()
        tokens.append({
            "kind": result if is_invalid_num else TOKEN_KINDS["INTEGER"],
            "lexeme": int(result)
        })

    def read_atom_val():
        nonlocal pos, str_at_pos
        result = ""
        while pos < len(input_str) and str_at_pos is not None and (re.match(r'[a-zA-Z0-9]+', str_at_pos) or str_at_pos == "_"):
            result += str_at_pos
            next_char()
        return  result

    while pos < len(input_str):
        if re.match(r'^[ \t]+', str_at_pos) or str_at_pos == TOKEN_KINDS["DELIMITER"]:
            next_char()
        elif str_at_pos == ",":
            tokens.append({"kind": TOKEN_KINDS["COMMA"], "lexeme": ","})
            next_char()
        elif str_at_pos in TOKEN_DEFINITION and TOKEN_DEFINITION[str_at_pos]:
            tokens.append({"kind": TOKEN_DEFINITION[str_at_pos], "lexeme": str_at_pos})
            next_char()
        elif str_at_pos == "#":
            while str_at_pos and str_at_pos != TOKEN_KINDS["DELIMITER"]:
                next_char()
            continue
        elif str_at_pos == "=" and input_str[pos + 1] == ">":
            tokens.append({"kind": TOKEN_KINDS["ARROW"], "lexeme": "=>"})
            next_char(2)
        elif str_at_pos == ":":
            next_token = input_str[pos + 1]
            if next_token == " ":
                tokens.append({"kind": TOKEN_KINDS["COLON"], "lexeme": ":"})
            next_char()
        elif str_at_pos and re.match(r'^\d+', str_at_pos):
            read_int()
        elif str_at_pos and re.match(r'^[^\s]+$', str_at_pos):
            is_bool = str_at_pos.lower() in ["t", "f"] and \
                         (input_str[pos: pos + 4].lower() == "true" or input_str[pos: pos + 5].lower() == "false")

            if is_bool:
                if (str_at_pos == "t" and input_str[pos + 4] and input_str[pos + 4] != "$" and input_str[pos + 4] != " ") or \
                        (str_at_pos == "f" and input_str[pos + 5] and input_str[pos + 5] not in ["$", " "]):
                    kind = fetch_char(input_str, pos)
                    tokens.append({"kind": kind, "lexeme": kind})
                    next_char(len(kind))
                else:
                    tokens.append({"kind": TOKEN_KINDS["BOOLEAN"], "lexeme": True if input_str[pos: pos + 4] == "true" else False})
                next_char(4 if str_at_pos == "t" else 5)
            else:
                is_atom = input_str[pos - 1] == ":"
                atom_value = read_atom_val()
                if not is_atom:
                    is_atom = str_at_pos == ":"
                tokens.append({"kind": TOKEN_KINDS["ATOM"] if is_atom else atom_value, "lexeme": atom_value})
        else:
            tokens.append({"kind": str_at_pos, "lexeme": str_at_pos})
            next_char()

    return tokens


def fetch_char(input_str, pos):
    substr = input_str[pos:]
    curr_pos = 0
    kind = ""
    while curr_pos < len(substr):
        if substr[curr_pos] == " ":
            break
        else:
            kind += substr[curr_pos]
        curr_pos += 1

    return kind

def parse(tokens):
    parsed = []
    stack = []
    for token in tokens:
        if token["kind"] == TOKEN_KINDS["LEFT_BRACE"] or token["kind"] == TOKEN_KINDS["LEFT_BRACKET"]:
            stack.append({"%k": "list" if token["kind"] == TOKEN_KINDS["LEFT_BRACKET"] else "tuple", "%v": []})
        elif token["kind"] == TOKEN_KINDS["RIGHT_BRACE"] or token["kind"] == TOKEN_KINDS["RIGHT_BRACKET"]:
            top = stack.pop()
            if len(stack) > 0:
                stack[-1]["%v"].append(top)
            else:
                parsed.append(top)
        elif token["kind"] == TOKEN_KINDS["MAP"]:
            stack.append({"%k": "map", "%v": {}})
        elif token["kind"] == TOKEN_KINDS["COMMA"]:
            pass  # Ignore commas
        elif token["kind"] == TOKEN_KINDS["ATOM"]:
            if len(stack) > 0:
                stack[-1]["%v"].append({"%k": "atom", "%v": token["lexeme"]})
            else:
                parsed.append({"%k": "atom", "%v": token["lexeme"]})
        elif token["kind"] == TOKEN_KINDS["INTEGER"]:
            if len(stack) > 0:
                stack[-1]["%v"].append({"%k": "int", "%v": token["lexeme"]})
            else:
                parsed.append({"%k": "int", "%v": token["lexeme"]})
        elif token["kind"] == TOKEN_KINDS["BOOLEAN"]:
            if len(stack) > 0:
                stack[-1]["%v"].append({"%k": "bool", "%v": True if token["lexeme"] == "true" else False})
            else:
                parsed.append({"%k": "bool", "%v": True if token["lexeme"] == "true" else False})
        elif token["kind"] == TOKEN_KINDS["COLON"]:
            if len(stack) > 0:
                stack[-1]["%v"].append({"%k": "atom", "%v": ":" + tokens[tokens.index(token) + 1]["lexeme"]})
    return parsed

def main():
    try:
        while True:
            input_text = input().rstrip()
            tokens = lexer(input_text)
            parsed = parse(tokens)
            print(parsed)
    except EOFError:
            pass  # Ctrl+D encountered, exit the loop
        
if __name__ == "__main__":
    main()
