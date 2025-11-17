
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

        # Alphanumeric symbols (words, numbers, identifiers)
        if char.isalnum() or char == '_' or char == '.':
            start = i
            while i < len(line) and (line[i].isalnum() or line[i] == '_' or line[i] == '.'):
                i += 1
            tokens.append(Token('SYMBOL', line[start:i], start))
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

        # Pipe for application
        if char == '|':
            tokens.append(Token('PIPE', '|', i))
            i += 1
            continue

        # Special character sequences (symbols like -->, <-=->, etc.) or operators
        if char in '=><-+*/!@#$%^&~`\\':
            start = i
            # Collect all consecutive special characters
            while i < len(line) and line[i] in '=><-+*/!@#$%^&~`\\':
                i += 1
            symbol_text = line[start:i]

            # Check if it's a single arithmetic operator
            if symbol_text in ['+', '-', '*', '/']:
                tokens.append(Token('OP', symbol_text, start))
            else:
                # Otherwise it's a symbol (like -->, <-=->, etc.)
                tokens.append(Token('SYMBOL', symbol_text, start))
            continue

        # Parentheses and commas
        if char in '(),':
            token_type = 'LPAREN' if char == '(' else 'RPAREN' if char == ')' else 'COMMA'
            tokens.append(Token(token_type, char, i))
            i += 1
            continue

        # Unknown character
        raise ParseError(f"Unexpected character '{char}' at position {i}")
    
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    @staticmethod
    def is_special_char_symbol(symbol):
        """Check if a symbol is composed only of special characters (not alphanumeric)"""
        if not symbol:
            return False
        return not any(c.isalnum() or c == '_' for c in symbol)

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

        # First token must be a symbol (directive)
        directive_token = self.expect('SYMBOL')
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
        """Parse composition (lowest precedence): arg | arg"""
        left = self.parse_alphanumeric_rules()

        # Check for pipe (composition) - lowest precedence
        if self.current_token() and self.current_token().type == 'PIPE':
            self.advance()
            right = self.parse_arg()  # Right associative
            left = Comp(left, right)

        return left

    def parse_alphanumeric_rules(self):
        """Parse alphanumeric symbol rules (low precedence): A B C, A gives B, etc."""
        left = self.parse_special_rules()

        # Check for adjacent objects (error case)
        # If we see LPAREN or HOLE after an expression, it means two objects are side by side
        if self.current_token() and self.current_token().type in ('LPAREN', 'HOLE'):
            raise ParseError(f"Unexpected token {self.current_token()} after expression")

        # Check for alphanumeric symbol as infix rule operator (right-associative)
        # This handles cases like: A B C, A gives B, etc.
        while self.current_token() and self.current_token().type == 'SYMBOL':
            symbol = self.current_token().value
            # Only parse alphanumeric symbols at this level
            if self.is_special_char_symbol(symbol):
                break  # Leave it for lower precedence level

            self.advance()
            right = self.parse_alphanumeric_rules()  # Right associative
            left = Rew(left, symbol, right)

        return left

    def parse_special_rules(self):
        """Parse special character symbol rules (high precedence): A => B, A -> B, etc."""
        left = self.parse_expr()

        # Check for special character symbol as infix rule operator (right-associative)
        # This handles cases like: A => B, A -> B, A <=> B, etc.
        while self.current_token() and self.current_token().type == 'SYMBOL':
            symbol = self.current_token().value
            # Only parse special character symbols at this level
            if not self.is_special_char_symbol(symbol):
                break  # Leave it for higher level (alphanumeric rules)

            self.advance()
            right = self.parse_special_rules()  # Right associative
            left = Rew(left, symbol, right)

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

    def parse_primary(self):
        """Parse: symbol | symbol(arg_list) | (expr) | [hole]"""
        token = self.current_token()
        if token is None:
            raise ParseError("Unexpected end of input")

        if token.type == 'SYMBOL':
            symbol = token.value
            self.advance()

            # Check if followed by parentheses (function call)
            if self.current_token() and self.current_token().type == 'LPAREN':
                self.advance()  # skip '('
                arg_list = self.parse_arg_list()
                self.expect('RPAREN')  # expect ')'
                return Term(symbol, arg_list)
            else:
                return Term(symbol, [])
        
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

