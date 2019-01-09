# -----------------------------------------------------------------------------
# Autor: Eduardo Yuzo Nakai
#
# Description: A program for Lexical Analysis.
# -----------------------------------------------------------------------------

import ply.lex as lex
import sys

#reserved words used in t_ID function
reserved = {
    'se': 'IF',
    'então': 'THEN',
    'senão': 'ELSE',
    'fim': 'END',
    'repita': 'REPEAT',
    'flutuante': 'FLOATING',
    'retorna': 'RETURN',
    'até': 'UNTIL',
    'leia': 'READ',
    'escreva': 'WRITE',
    'inteiro': 'INTEGER'
}

#reserved words
tokens = ['IF',         #se
          'THEN',       #então
          'ELSE',       #senão
          'END',        #fim
          'REPEAT',     #repita
          'INTEGER',    #inteiro
          'RETURN',     #retorna
          'UNTIL',      #até
          'READ',       #leia
          'WRITE',      #escreva
          'FLOATING',   #flutuante
          'INTEGER_NUMBER',
          'FLOATING_POINT_NUMBER']

#Regular expressions for reserved words

#symbols
tokens = tokens + ['SUM',
                   'SUB',
                   'MUL',
                   'DIV',
                   'EQUALS',
                   'COMMA',
                   'ASSIGN',
                   'LOWER',
                   'GREATER',
                   'LOWER_EQUAL',
                   'GREATER_EQUAL',
                   'L_PAREN',
                   'R_PAREN',
                   'COLON',
                   'L_BRACKET',
                   'R_BRACKET',
                   'AND_OP',
                   'OR_OP',
                   'NEG_OP',
                   'L_BRACE',
                   'R_BRACE']

#Regular expressions for numbers and ignored characters
t_ignore = " \t"
#t_NUMBER = r'[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?'

#Regular expressions for symbols
t_SUM = r'\+'
t_SUB = r'-'
t_MUL = r'\*'
t_DIV = r'/'
t_EQUALS  = r'='
t_COMMA   = r','
t_ASSIGN  = r':='
t_LOWER   = r'<'
t_GREATER = r'>'
t_LOWER_EQUAL   = r'<='
t_GREATER_EQUAL = r'>='
t_L_PAREN   = r'\('
t_R_PAREN   = r'\)'
t_COLON     = r':'
t_L_BRACKET = r'\['
t_R_BRACKET = r'\]'
t_AND_OP = r'&&'
t_OR_OP  = r'\|\|'
t_NEG_OP = r'!'

#tokens IDs
tokens = tokens + ['ID']

#regex for IDs + reserved words + numbers
def t_ID(t):
    r'[A-Za-z_][\w]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_FLOATING_POINT_NUMBER(t):
	r'\d+\.\d+([eE][-+]?\d+)?'
	#r'\d+\. | \d+\d+ | \d+[eE][-+]\d+'
	#t.value = float(t.value)
	return t

def t_INTEGER_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

#handling comments
states = (('commentary', 'exclusive'),)

def t_comment(t):
    r'\{'
    t.lexer.code_start = t.lexer.lineno
    t.lexer.level = 1
    t.lexer.begin('commentary')

def t_commentary_L_BRACE(t):
    r'\{'
    t.lexer.level += 1

def t_commentary_R_BRACE(t):
    r'\}'
    t.lexer.level -=1
    if t.lexer.level == 0:
        t.lexer.begin('INITIAL')

t_commentary_ignore = " \t"

def t_commentary_error(t):
    t.lexer.skip(1)

def t_commentary_eof(t):
    data = extract_data_from_file()
    if t.lexer.level != 0:
        print("Commentary error found."
              + " Line: " + str(t.lexer.lineno)
              + " Column: " + str(find_column(data, t)))

#line count; column count; errors
def t_ANY_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

def t_error(t):
    data = extract_data_from_file()
    if t.value[0] == "}":
        print("Commentary error found."
              + " Line: " + str(t.lexer.lineno)
              + " Column: " + str(find_column(data, t)))
    else:
        print("Illegal character '" + t.value[0] + "'"
            + " Line: " + str(t.lexer.lineno)
            + " Column: " + str(find_column(data, t)))
    t.lexer.skip(1)

#build the lexer
lexer = lex.lex()

def extract_data_from_file():
    filename = sys.argv[1]
    sourcefile = open(filename, encoding='UTF-8')
    data = sourcefile.read()
    return data

if __name__ == '__main__':
    lexer.input(extract_data_from_file())
    while True:
        tok = lexer.token()
        if not tok:
            break
        print("(" + tok.type + ":" + str(tok.value) + ")")