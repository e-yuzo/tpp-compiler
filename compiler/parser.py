# -----------------------------------------------------------------------------
# Autor: Eduardo Yuzo Nakai
#
# Description: A program for Syntax Analysis.
# -----------------------------------------------------------------------------

import ply.yacc as yacc
from lexical import tokens
import sys
from graphviz import Graph
import os
import string

# For windows:
# os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'

#-----------------------tree structure-----------------------#

class Node:
	def __init__(self, type, children=None, leaf=None):
		self.type = type
		if children:
			self.children = children
		else:
			self.children = []
		if leaf:
			self.leaf = leaf
		else:
			self.leaf = []

#-----------------------precedence declaration-----------------------#

precedence = (
	('left', 'EQUALS', 'LOWER', 'GREATER', 'LOWER_EQUAL', 'GREATER_EQUAL'),
	('left', 'SUM', 'SUB'),
	('left', 'MUL', 'DIV'),
)

#-----------------------grammar rules-----------------------#

def p_program(p):
	'''program : declaration_list'''
	p[0] = Node('program', [p[1]])

def p_declaration_list(p):
	'''declaration_list : declaration_list declaration
						 | declaration'''
	if len(p) == 3:
		p[0] = Node('declaration_list', [p[1], p[2]])
	elif len(p) == 2:
		p[0] = Node('declaration_list', [p[1]])

def p_declaration(p):
	'''declaration : variable_declaration
				   | variable_initialization
				   | function_declaration'''
	p[0] = Node('declaration', [p[1]])

def p_variable_declaration(p):
	'''variable_declaration : type COLON variable_list'''
	p[0] = Node('variable_declaration', [p[1], Node(str(p[2])), p[3]])

def p_variable_initialization(p):
	'''variable_initialization : attribution'''
	p[0] = Node('variable_initialization', [p[1]])

def p_variable_list(p):
	'''variable_list : variable_list COMMA var
					 | var'''
	if len(p) == 4:
		p[0] = Node('variable_list', [p[1], Node(str(p[2])), p[3]])
	elif len(p) == 2:
		p[0] = Node('variable_list', [p[1]])

def p_var(p):
	'''var : ID
		   | ID index'''
	if len(p) == 2:
		p[0] = Node('var', [Node(str(p[1]))])
	elif len(p) == 3:
		p[0] = Node('var', [Node(str(p[1])), p[2]])

def p_index(p):
	'''index : index L_BRACKET expression R_BRACKET
			 | L_BRACKET expression R_BRACKET'''
	if len(p) == 5:
		p[0] = Node('index', [p[1], Node(str(p[2])), p[3], Node(str(p[4]))])
	elif len(p) == 4:
		p[0] = Node('index', [Node(str(p[1])), p[2], Node(str(p[3]))])

def p_type(p):
	'''type : INTEGER
			| FLOATING'''
	p[0] = Node('type', [Node(str(p[1]))])

def p_function_declaration(p):
	'''function_declaration : type header
							| header'''
	if len(p) == 3:
		p[0] = Node('function_declaration', [p[1], p[2]])
	elif len(p) == 2:
		p[0] = Node('function_declaration', [p[1]])

def p_header(p):
	'''header : ID L_PAREN parameter_list R_PAREN body END'''
	p[0] = Node('header', [Node(str(p[1])), Node(str(p[2])), p[3], Node(str(p[4])), p[5], Node(str(p[6]))], leaf=[p[1], p[2], p[4], p[6]])

def p_parameter_list(p):
	'''parameter_list : parameter_list COMMA parameter
					  | parameter
					  | empty'''
	if len(p) == 4:
		p[0] = Node('parameter_list', [p[1], Node(str(p[2])), p[3]])
	else:
		if p[1] == None:
			p[0] = Node('parameter_list', [Node('Empty')])
		else:		
			p[0] = Node('parameter_list', [p[1]])

def p_parameter(p):
	'''parameter : type COLON ID
				 | parameter L_BRACKET R_BRACKET'''
	if p[2] == ':':
		p[0] = Node('parameter', [p[1], Node(str(p[2])), Node(str(p[3]))])
	elif p[2] == '[':
		p[0] = Node('parameter', [p[1], Node(str(p[2])), Node(str(p[3]))])

def p_body(p):
	'''body : body action
			| empty'''
	if len(p) == 3:
		p[0] = Node('body', [p[1], p[2]])
	else:
		if p[1] == None:
			p[0] = Node('body', [Node('Empty')])
		else:
			p[0] = Node('body', [p[1]])
		
def p_action(p):
	'''action : expression
			  | variable_declaration
			  | if
			  | repeat
			  | read
			  | write
			  | return'''
	p[0] = Node('action', [p[1]])

def p_if(p):
	'''if : IF expression THEN body END
		  | IF expression THEN body ELSE body END'''
	if p[5] == 'fim':
		p[0] = Node('if', [Node(str(p[1])), p[2], Node(str(p[3])), p[4], Node(str(p[5]))])
	elif p[5] == 'senão':
		p[0] = Node('if', [Node(str(p[1])), p[2], Node(str(p[3])), p[4], Node(str(p[5])), p[6], Node(str(p[7]))])
		
def p_repeat(p):
	'''repeat : REPEAT body UNTIL expression'''
	p[0] = Node('repeat', [Node(str(p[1])), p[2], Node(str(p[3])), p[4]])

def p_attribution(p):
	'''attribution : var ASSIGN expression'''
	p[0] = Node('attribution', [p[1], Node(str(p[2])), p[3]])

def p_read(p):
	'''read : READ L_PAREN var R_PAREN'''
	p[0] = Node('read', [Node(str(p[1])), Node(str(p[2])), p[3], Node(str(p[4]))])

def p_write(p):
	'''write : WRITE L_PAREN expression R_PAREN'''
	p[0] = Node('write', [Node(str(p[1])), Node(str(p[2])), p[3], Node(str(p[4]))])

def p_return(p):
	'''return : RETURN L_PAREN expression R_PAREN'''
	p[0] = Node('return', [Node(str(p[1])), Node(str(p[2])), p[3], Node(str(p[4]))])

def p_expression(p):
	'''expression : logical_expression
				  | attribution'''
	p[0] = Node('expression', [p[1]])

def p_logical_expression(p):
	'''logical_expression : simple_expression
						  | logical_expression logical_operator simple_expression'''
	if len(p) == 2:
		p[0] = Node('logical_expression', [p[1]])
	elif len(p) == 4:
		p[0] = Node('logical_expression', [p[1], p[2], p[3]])

def p_simple_expression(p):
	'''simple_expression : additive_expression
	 					 | simple_expression relational_operator additive_expression'''
	if len(p) == 2:
		p[0] = Node('simple_expression', [p[1]])
	elif len(p) == 4:
		p[0] = Node('simple_expression', [p[1], p[2], p[3]])

def p_additive_expression(p):
	'''additive_expression : multiplicative_expression
						   | additive_expression sum_operator multiplicative_expression'''
	if len(p) == 2:
		p[0] = Node('additive_expression', [p[1]])
	elif len(p) == 4:
		p[0] = Node('additive_expression', [p[1], p[2], p[3]])

def p_multiplicative_expression(p):
	'''multiplicative_expression : unary_expression
								 | multiplicative_expression mult_operator unary_expression'''
	if len(p) == 2:
		p[0] = Node('multiplicative_expression', [p[1]])
	elif len(p) == 4:
		p[0] = Node('multiplicative_expression', [p[1], p[2], p[3]])

def p_unary_expression(p):
	'''unary_expression : factor
						| sum_operator factor
						| neg_operator factor'''
	if len(p) == 2:
		p[0] = Node('unary_expression', [p[1]])
	elif len(p) == 3:
		p[0] = Node('unary_expression', [p[1], p[2]])

def p_relational_operator(p): #what about '<>' ?
	'''relational_operator : LOWER
						   | GREATER
						   | EQUALS
						   | LOWER_EQUAL
						   | GREATER_EQUAL'''
	p[0] = Node('relational_operator', [Node(str(p[1]))])

def p_sum_operator(p):
	'''sum_operator : SUM
					| SUB'''
	p[0] = Node('sum_operator', [Node(str(p[1]))])

def p_logical_operator(p):
	'''logical_operator : AND_OP
						| OR_OP'''
	p[0] = Node('logical_operator', [Node(str(p[1]))])

def p_neg_operator(p):
	'''neg_operator : NEG_OP'''
	p[0] = Node('neg_operator', [Node(str(p[1]))])

def p_mult_operator(p):
	'''mult_operator : MUL
					 | DIV'''
	p[0] = Node('mult_operator', [Node(str(p[1]))])
				
def p_factor(p):
	'''factor : L_PAREN expression R_PAREN
			  | var
			  | function_call
			  | number'''
	if len(p) == 4:
		p[0] = Node('factor', [Node(str(p[1])), p[2], Node(str(p[3]))])
	elif len(p) == 2:
		p[0] = Node('factor', [p[1]])

def p_number(p):
	'''number : INTEGER_NUMBER
	 		  | FLOATING_POINT_NUMBER'''
	p[0] = Node('number', [Node(str(p[1]))])

def p_function_call(p):
	'''function_call : ID L_PAREN argument_list R_PAREN'''
	p[0] = Node('function_call', [Node(str(p[1])), Node(str(p[2])), p[3], Node(str(p[4]))])

def p_argument_list(p): #possible error here
	'''argument_list : argument_list COMMA expression
					 | expression
					 | empty'''
	if len(p) == 4:
		p[0] = Node('argument_list', [p[1], Node(str(p[2])), p[3]])
	elif len(p) == 2:
		if p[1] == None:
			p[0] = Node('argument_list', [Node('Empty')])
		else:
			p[0] = Node('argument_list', [p[1]])

def p_empty(p):
	'''empty :'''
	pass

#-----------------------error rules-----------------------#

error_flag = False
def p_error(p):
	global error_flag
	error_flag = True
	print("\n")
	if p:
		print("Syntax error in input. Character: %s. Line: %d." % (p.value, p.lineno))
	else:
		print("Syntax error at EOF.")

#-----------------------repeat error rules-----------------------#

def p_repeat_miscellaneous_error(p):
	'''repeat : REPEAT body UNTIL expression error'''
	pass

def p_repeat_until_error(p):
	'''repeat : REPEAT body error expression'''
	print("Syntax error in 'repita': missing 'até'.")

def p_repeat_expression_error(p):
	'''repeat : REPEAT body UNTIL error'''
	print("Syntax error in 'repita': bad expression.")

def p_repeat_body_error(p):
	'''repeat : REPEAT error UNTIL expression'''
	print("Syntax error in 'repita'.")

#-----------------------if error rules-----------------------#

def p_if_miscellaneous_error(p):
	'''if : IF expression THEN body END error
		  | IF expression THEN body ELSE body END error'''
	pass

def p_if_end_error(p):
	'''if : IF expression THEN body error
		  | IF expression THEN body ELSE body error'''
	print("Syntax error in 'se': missing 'fim'.")

def p_if_then_error(p):
	'''if : IF expression error body error
		  | IF expression error body ELSE body error'''
	print("Syntax error in 'se': missing 'então'.")

def p_if_expression_error(p):
	'''if : IF error THEN body END
		  | IF error THEN body ELSE body END'''
	print("Syntax error in 'se': bad expression.")

def p_if_body_error(p):
	'''if : IF expression THEN error END
		  | IF expression THEN error ELSE error END'''
	print("Syntax error in 'se'.")

#-----------------------header error rules-----------------------#

def p_header_miscellaneous_error(p):
	'''header : ID L_PAREN parameter_list R_PAREN body END error'''
	pass

def p_header_end_error(p):
	'''header : ID L_PAREN parameter_list R_PAREN body error'''
	print("Syntax error in 'cabeçalho': missing 'fim'.")

def p_header_body_error(p):
	'''header : ID L_PAREN parameter_list R_PAREN error END'''
	print("Syntax error in 'cabeçalho'.")

#-----------------------simple error rules-----------------------#

def p_parameter_error(p):
	'''parameter : error COLON ID
				 | error L_BRACKET R_BRACKET'''
	print("Syntax error in parameter.")

def p_index_error(p):
	'''index : index L_BRACKET error R_BRACKET
			 | L_BRACKET error R_BRACKET'''
	print("Syntax error in index definition.")

def p_variable_declaration_error(p):
	'''variable_declaration : type COLON error'''
	print("Syntax error in variable declaration.")

def p_attribution_error(p):
	'''attribution : var ASSIGN error'''
	print("Syntax error in variable initialization.")

def p_write_error(p):
	'''write : WRITE L_PAREN error R_PAREN'''
	print("Syntax error in 'escreva'. Bad expression.")

def p_return_error(p):
	'''return : RETURN L_PAREN error R_PAREN'''
	print("Syntax error in 'retorna'. Bad expression.")

def p_read_error(p):
	'''read : READ L_PAREN error R_PAREN'''
	print("Syntax error in 'leia'. Bad expression.")

dot = Graph('AST')
count = 0
def show_tree(node, count_node):
	global count
	dot.node(str(count_node), str(node.type))
	for children in node.children:
		if children:
			count = count + 1
			dot.edges([(str(count_node), str(count))])
			show_tree(children, count)

from semantic import Semantic
from cultivation import AST
from code_gen import Gen_Code

if __name__ == '__main__':
	filename = sys.argv[1]
	sourcefile = open(filename, encoding='UTF-8')
	data = sourcefile.read()
	parser = yacc.yacc(debug=True)
	p = parser.parse(data) #sintatic analysis
	if not error_flag:
		Semantic(p) #semantic analysis: object 'p' won't be modified
		AST(p) #generate abstract syntax tree: object 'p' will be modified
		Gen_Code(p) #code generation: object 'p' won't be modified
		#show_tree(p, 0) #uncomment to show tree
		#dot.render('tree.gv', view=True) #uncomment to show tree
