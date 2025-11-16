
import re
from ..core import Term, Hole, Rew, Comp

class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass

class Token:
    def __init__(self, type, value, position=None):
        self.type = type
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

def tokenize(line):
    """
    Tokenize a line of text according to the specified grammar.
    
    Returns:
        list of Token objects
    """
    tokens = []
    i = 0
    line = line.strip()
    
    while i < len(line):
        char = line[i]
        
        # Skip whitespace
        if char.isspace():
            i += 1
            continue
            
        # Numbers (including decimals)
        if char.isdigit() or char == '.':
            start = i
            while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                i += 1
            tokens.append(Token('WORD', line[start:i], start))
            continue
            
        # Words (alpha characters)
        if char.isalpha() or char == '_':
            start = i
            while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                i += 1
            word = line[start:i]
            # Check for 'in' keyword (used in quantifier syntax)
            if word == 'in':
                tokens.append(Token('IN', word, start))
            else:
                tokens.append(Token('WORD', word, start))
            continue
            
        # Holes [content]
        if char == '[':
            start = i
            i += 1  # skip '['
            hole_content = ""
            while i < len(line) and line[i] != ']':
                hole_content += line[i]
                i += 1
            if i < len(line) and line[i] == ']':
                i += 1  # skip ']'
                tokens.append(Token('HOLE', hole_content, start))
            else:
                raise ParseError(f"Unclosed hole at position {start}")
            continue
            
        # Rules (starts with =, -, >, < but not - alone)
        if char in '=><' or (char == '-' and i + 1 < len(line) and not line[i + 1].isspace()):
            start = i
            while i < len(line) and line[i] in '=><-':
                i += 1
            rule_text = line[start:i]
            if rule_text != '-':  # - alone is not a rule
                tokens.append(Token('RULE', rule_text, start))
            else:
                # - alone is an operator
                tokens.append(Token('OP', '-', start))
            continue
            
        # Operators
        if char in '+-*/':
            tokens.append(Token('OP', char, i))
            i += 1
            continue
            
        # Parentheses and commas
        if char in '(),':
            token_type = 'LPAREN' if char == '(' else 'RPAREN' if char == ')' else 'COMMA'
            tokens.append(Token(token_type, char, i))
            i += 1
            continue
            
        # Pipe for application
        if char == '|':
            tokens.append(Token('PIPE', '|', i))
            i += 1
            continue
            
        # Unknown character
        raise ParseError(f"Unexpected character '{char}' at position {i}")
    
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1
    
    def expect(self, token_type):
        token = self.current_token()
        if token is None or token.type != token_type:
            expected = token_type
            got = token.type if token else "EOF"
            raise ParseError(f"Expected {expected}, got {got}")
        self.advance()
        return token
    
    def parse_directive(self):
        """Parse: Directive arg_list"""
        if not self.tokens:
            return None, None
            
        # First token must be a word (directive)
        directive_token = self.expect('WORD')
        directive = directive_token.value
        
        # Parse argument list
        if self.current_token() is None:
            # No arguments
            return directive, []
        
        args = self.parse_arg_list()
        return directive, args
    
    def parse_arg_list(self):
        """Parse: arg1, arg2, ... => [arg1, arg2...]"""
        args = []
        
        if self.current_token() is None:
            return args
            
        # Parse first argument
        args.append(self.parse_arg())
        
        # Parse remaining arguments separated by commas
        while self.current_token() and self.current_token().type == 'COMMA':
            self.advance()  # skip comma
            args.append(self.parse_arg())
        
        return args
    
    def parse_arg(self):
        """Parse: word(arg_list) | word | arg1 RULE arg2 | arg1 | arg2 | expr"""
        # Parse the left side first - start with expr to handle arithmetic
        left = self.parse_expr()

        # Check for right-associative rules
        while self.current_token() and self.current_token().type == 'RULE':
            rule_symbol = self.current_token().value
            self.advance()
            right = self.parse_arg()  # Right associative - parse the rest as an arg
            left = Rew(left, rule_symbol, right)

        # Check for pipe (application)
        if self.current_token() and self.current_token().type == 'PIPE':
            self.advance()
            right = self.parse_arg()
            left = Comp(left, right)

        return left
    
    def parse_expr(self):
        """Parse: factor | factor + expr | factor - expr"""
        left = self.parse_factor()

        while self.current_token() and self.current_token().type == 'OP' and self.current_token().value in ('+', '-'):
            op = self.current_token().value
            self.advance()  # skip '+' or '-'
            right = self.parse_expr()
            if op == '+':
                left = Term("plus", [left, right])
            else:  # op == '-'
                left = Term("minus", [left, right])

        return left
    
    def parse_factor(self):
        """Parse: term | term * factor"""
        left = self.parse_term()
        
        while self.current_token() and self.current_token().type == 'OP' and self.current_token().value == '*':
            self.advance()  # skip '*'
            right = self.parse_factor()
            left = Term("mult", [left, right])
        
        return left
    
    def parse_term(self):
        """Parse: primary | primary / term"""
        left = self.parse_primary()

        while self.current_token() and self.current_token().type == 'OP' and self.current_token().value == '/':
            self.advance()  # skip '/'
            right = self.parse_term()
            left = Term("div", [left, right])

        return left

    def parse_quantifier(self, quantifier_name):
        """
        Parse quantifier syntax sugar: forall [x] in N, P
        Converts to: forall(N, [x] -> P)
        """
        # Expect a hole [x]
        if not self.current_token() or self.current_token().type != 'HOLE':
            raise ParseError(f"Expected hole after {quantifier_name}")
        hole_token = self.current_token()
        hole = Hole(hole_token.value)
        self.advance()

        # Expect 'in' keyword
        if not self.current_token() or self.current_token().type != 'IN':
            raise ParseError(f"Expected 'in' keyword in {quantifier_name} expression")
        self.advance()

        # Parse domain
        domain = self.parse_primary()

        # Expect comma
        if not self.current_token() or self.current_token().type != 'COMMA':
            raise ParseError(f"Expected comma after domain in {quantifier_name} expression")
        self.advance()

        # Parse body/predicate
        body = self.parse_arg()

        # Construct: quantifier(domain, [x] -> body)
        rule_term = Rew(hole, "->", body)
        return Term(quantifier_name, [domain, rule_term])
    
    def parse_primary(self):
        """Parse: word | word(arg_list) | (expr) | [hole] | quantifier syntax"""
        token = self.current_token()
        if token is None:
            raise ParseError("Unexpected end of input")

        if token.type == 'WORD':
            word = token.value

            # Check for quantifier syntax sugar: forall [x] in N, P
            if word in ('forall', 'exists'):
                self.advance()
                # Peek at next token - if it's a HOLE, use quantifier syntax
                if self.current_token() and self.current_token().type == 'HOLE':
                    return self.parse_quantifier(word)
                # Otherwise, fall back to function call syntax
                # Need to backtrack by checking for LPAREN
                if self.current_token() and self.current_token().type == 'LPAREN':
                    self.advance()  # skip '('
                    arg_list = self.parse_arg_list()
                    self.expect('RPAREN')  # expect ')'
                    return Term(word, arg_list)
                else:
                    return Term(word)

            self.advance()

            # Check if it's a numeric literal - convert to Church numeral
            if word.isdigit():
                n = int(word)
                if n == 0:
                    return Term("zero")
                else:
                    # Build nested S(S(S(...(zero))))
                    result = Term("zero")
                    for _ in range(n):
                        result = Term("S", [result])
                    return result

            # Check if followed by parentheses
            if self.current_token() and self.current_token().type == 'LPAREN':
                self.advance()  # skip '('
                arg_list = self.parse_arg_list()
                self.expect('RPAREN')  # expect ')'
                return Term(word, arg_list)
            else:
                return Term(word, [])
        
        elif token.type == 'HOLE':
            hole_name = token.value
            self.advance()
            return Hole(hole_name)
        
        elif token.type == 'LPAREN':
            self.advance()  # skip '('
            expr = self.parse_arg()  # Use parse_arg to handle rules inside parentheses
            self.expect('RPAREN')  # expect ')'
            return expr
        
        else:
            raise ParseError(f"Unexpected token {token}")

def parse_line(line):
    """
    Parse a single line of text.
    
    Returns:
        tuple: (directive, content) where directive is a string and content is a list of parsed terms
    """
    line = line.strip()
    
    if not line or line.startswith('#'):
        return None, None
    
    try:
        tokens = tokenize(line)
        parser = Parser(tokens)
        directive, content = parser.parse_directive()
        return directive, content
    except Exception as e:
        raise ParseError(f"Parse error: {str(e)}")

