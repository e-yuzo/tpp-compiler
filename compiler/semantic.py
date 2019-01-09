# -----------------------------------------------------------------------------
# Author: Eduardo Yuzo Nakai
#
# Description: A program for Semantic Analysis.
# -----------------------------------------------------------------------------

import sys
from graphviz import Graph
import string
import types
from ast import literal_eval
import re

#style: ex: dimensão do vetor, parâmetros da função.
#value: ex: valor retornado, valor atribuído
#key: nome das funções e variáveis
#scope: escopo da variável ou função

#: tipo da variável ou tipo do retorno

#data_structure: se é uma função, variável básica ou array
#used: se a variável ou função foi utilizada
#value_types: tipos das variáveis e constantes presentes na expressão do atributo 'value'

class Vector_Entry: #uma entrada da variavel vetor da classe Semantic
    def __init__(self, scope, type, key, value, style, data_structure):
        self.scope = scope
        self.type = type
        self.key = key
        self.value = value
        self.style = style
        self.data_structure = data_structure
        self.used = False
        self.value_types = []

class Semantic:

    def __init__(self, tree):
        self.parser_tree = tree
        self.symbol_table = []

        self.auxiliar = ''
        self.second_auxiliar = False
        self.scope_stack = []
        self.parameter_list = []

        self.warnings = []
        self.errors = []

        self.called_functions = [] #list of lists ([key][vars])

        self.create_symbol_table(tree, 'global')
        self.find_semantic_bugs()

        self.show_table_symbol()
        self.show_warnings()
        self.show_errors()

#-----------------------Symbol Table-----------------------#

    def represents_int(self, s):
        return re.match(r"[-+]?\d+$", str(s)) is not None

    def get_value_of_branch_leafs(self, node):
        if len(node.children) == 0:
            self.auxiliar += node.type
        for children in node.children:
            if children.type == 'var': #só quando var for usada em expressões e não parâmetros de funções, ela é usada.
                self.check_var_usage(children)
            self.get_value_of_branch_leafs(children)
            
    def get_type_list_of_attr(self, node):
        if node.type == 'number':
            if self.represents_int(node.children[0].type):
                number = ['inteiro']
            else:
                number = ['flutuante']
            self.second_auxiliar.append(number)
        elif node.type == 'function_call':
            function_key = node.children[0].type
            for sym in self.symbol_table:
                if sym.data_structure == 'function' and sym.key == function_key:
                    func_tuple = [function_key, sym.type]
                    self.second_auxiliar.append(func_tuple)
                    break
        elif node.type == 'var':
            var_key = node.children[0].type
            var = None
            for sym in self.scope_stack:
                if sym.data_structure != 'function' and sym.key == var_key:
                    var = sym
            if var:
                var_tuple = [var.key, var.type]
                self.second_auxiliar.append(var_tuple)

        for children in node.children:
            if children.type != 'argument_list':
                self.get_type_list_of_attr(children)

    def show_table_symbol(self):
        print('\n#-----------------------Symbol Table-----------------------#\n')
        for entry in self.symbol_table:
            print('[(' + entry.scope + '), (' + entry.type + '), (' + entry.key + '), (' + str(entry.value) + '), (' + str(entry.style) + '), (' + entry.data_structure + '), (' + str(entry.used) + '), (' + str(entry.value_types) + ')]')
        print('\n')

    def add_index_var_to_table(self, index_node, key, var_scope, var_type):
        array_indexes = []
        while len(index_node.children) == 4:
            self.auxiliar = ''
            self.second_auxiliar = False
            self.get_value_of_branch_leafs(index_node.children[2]) #value
            array_indexes.append(self.auxiliar)
            index_node = index_node.children[0]
        self.auxiliar = ''
        self.second_auxiliar = False
        self.get_value_of_branch_leafs(index_node.children[1]) #value
        array_indexes.append(self.auxiliar)
        array_indexes.reverse()
        entry = Vector_Entry(var_scope, var_type, key, None, array_indexes, 'array')
        self.symbol_table.append(entry)
        self.scope_stack.append(entry) #push stack
        
    def add_plain_var_to_table(self, var_scope, var_node, var_type):
        key = var_node.children[0].type
        entry = Vector_Entry(var_scope, var_type, key, None, [], 'plain')
        self.symbol_table.append(entry)
        self.scope_stack.append(entry) #push stack

    def add_declaration_symbol_table(self, scope, var_type, node):
        if node.children[0].type == 'variable_list':
            self.add_declaration_symbol_table(scope, var_type, node.children[0])

        if len(node.children) == 1: #última variable_list
            var_node = node.children[0]
            key = var_node.children[0].type
            if len(var_node.children) == 2: #verifica se é vetor
                index_node = var_node.children[1]
                self.add_index_var_to_table(index_node, key, scope, var_type)
            else:
                self.add_plain_var_to_table(scope, var_node, var_type)

        elif len(node.children) == 3: #mais de uma variable_list
            var_node = node.children[2]
            key = var_node.children[0].type
            if len(var_node.children) == 2: #verifica se é vetor
                index_node = var_node.children[1]
                self.add_index_var_to_table(index_node, key, scope, var_type)
            else:
                self.add_plain_var_to_table(scope, var_node, var_type)

    def add_attribution_symbol_table(self, node, key): #node = attribution_node
        self.auxiliar = ''
        self.second_auxiliar = []
        self.get_value_of_branch_leafs(node.children[2])
        self.get_type_list_of_attr(node.children[2])
        attr_var = False
        for entry in self.scope_stack:
            if entry.key == key:
                attr_var = entry
    
        if attr_var:
            attr_var.value = self.auxiliar
            attr_var.value_types = self.second_auxiliar
            self.check_for_implicit_coercion(attr_var)

    def check_for_implicit_coercion(self, attr_var):
        probable_type = self.get_probable_type_from_expression(attr_var)
        type_attr = None
        if probable_type:
            if len(probable_type) == 2:
                type_attr = probable_type[1]
            else:
                type_attr = probable_type[0]
        if type_attr and type_attr != 'void':
            if type_attr != attr_var.type:#Coerção implícita do valor atribuído para 'a'
                self.warnings.append('Warning: Coerção implícita do valor atribuído para \'' + attr_var.key + '\', variável ' + attr_var.type + ' recebendo um ' + type_attr + '.')
                attr_var.type = type_attr

    def add_function_symbol_table(self, scope, node, key):
        type = 'void'
        if len(node.children) == 2:
            type = node.children[0].children[0].type
        entry = Vector_Entry(scope, type, key, None, self.parameter_list, 'function') #value = return type AND style = parameter variables
        self.symbol_table.append(entry)
        self.scope_stack.append(entry)

    def add_parameter_list_symbol_table(self, scope, node): #node = param_list_node
        self.parameter_list = []
        if node.children[0].type == 'parameter_list':
            self.add_parameter_list_symbol_table(scope, node.children[0])

        data_structure = 'plain'
        if len(node.children) == 1 and node.children[0].type != 'Empty':#last parameter_list node
            parameter_node = node.children[0]
            if parameter_node.children[0] == 'parameter':
                parameter_node = parameter_node.children[0]
                data_structure = 'array'
            type = parameter_node.children[0].children[0].type
            key = parameter_node.children[2].type
            self.parameter_list.append(key)
            entry = Vector_Entry(scope, type, key, None, [], data_structure)
            self.symbol_table.append(entry)
            self.scope_stack.append(entry)

        elif len(node.children) == 3:
            parameter_node = node.children[2]
            if parameter_node.children[0].type == 'parameter':
                parameter_node = parameter_node.children[0]
                data_structure = 'array'
            type = parameter_node.children[0].children[0].type
            key = parameter_node.children[2].type
            self.parameter_list.append(key)
            entry = Vector_Entry(scope, type, key, None, [], data_structure)
            self.symbol_table.append(entry)
            self.scope_stack.append(entry)

    def pop_scope_stack(self, scope):
        if len(self.scope_stack) > 0:
            entry_scope = self.scope_stack[-1].scope
            if entry_scope == scope:
                self.scope_stack.pop()
                self.pop_scope_stack(scope)

    def create_symbol_table(self, node, scope):
        if node.type != 'Empty':
            if node.type == 'variable_declaration':
                var_type = node.children[0].children[0].type #var_dec -> type -> inteiro
                var_node = node.children[2] #variable_list node
                self.add_declaration_symbol_table(scope, var_type, var_node) #add to table
            elif node.type == 'attribution':
                key = node.children[0].children[0].type
                self.add_attribution_symbol_table(node, key) #add to table
            elif node.type == 'function_declaration':
                if len(node.children) == 2:
                    header_node = node.children[1]
                elif len(node.children) == 1:
                    header_node = node.children[0]
                key = header_node.children[0].type
                scope += '.' + key
                parameter_list_node = header_node.children[2]
                self.add_parameter_list_symbol_table(scope, parameter_list_node) #add to table
                self.add_function_symbol_table(scope, node, key)
            elif node.type == 'if': #mudar de escopo de novo para 'if'
                scope += '.' + node.type
            elif node.type == 'repeat':#mudar o escopo novamente para 'repeat'
                scope += '.' + node.type
            elif node.type == 'return':
                self.auxiliar = ''
                self.second_auxiliar = []
                self.add_function_return_value(node)
                self.get_type_list_of_attr(node)
            elif node.type == 'function_call':
                self.add_called_function(node)
            elif node.type == 'write': #adicionar mais nodes para verificar utilização das variáveis
                self.auxiliar = ''
                self.get_value_of_branch_leafs(node.children[2])
            elif node.type == 'read': #variável não está sendo utilizada em 'read'
                args_list = self.get_argument_list(node.children[2])
                ss_var = None
                for ss in reversed(self.scope_stack):
                    if args_list[0] == ss.key:
                        ss_var = ss
                        break
                ss_var.value = 'read'
        for children in node.children:
            self.create_symbol_table(children, scope) #verificação top down

        node_type = node.type
        if node_type == ('function_declaration' or 'if' or 'repeat'):
            self.pop_scope_stack(scope)

    def get_argument_list(self, argument_list_node):
        arg_list = []
        if argument_list_node.children[0].type == 'argument_list':
            arg_list = self.get_argument_list(argument_list_node.children[0])
        if len(argument_list_node.children) == 3:
            self.auxiliar = ''
            self.second_auxiliar = False
            self.get_value_of_branch_leafs(argument_list_node.children[2])
            if not self.auxiliar == 'Empty':
                arg_list.append(self.auxiliar)
        else:
            self.auxiliar = ''
            self.second_auxiliar = False
            self.get_value_of_branch_leafs(argument_list_node.children[0])
            if not self.auxiliar == 'Empty':
                arg_list.append(self.auxiliar)
        return arg_list

    def add_called_function(self, node):
        arg_list = self.get_argument_list(node.children[2])
        func_key = node.children[0].type
        func = [func_key, arg_list]
        self.called_functions.append(func)
        if func_key == 'main':
            self.check_illegal_main_function_call()
        
    def add_function_return_value(self, node):
        function = None
        for scope in self.scope_stack:
            if scope.data_structure == 'function': #get last function
                function = scope
        if function:
            if function.key == function.scope.split('.')[-1]: #verifica se o retorno é relevante (não está dentro de um if)
                self.get_value_of_branch_leafs(node.children[2])
                function.value = self.auxiliar
                function.value_types = self.second_auxiliar

#-----------------------Semantic Errors/Warnings-----------------------#

    def find_semantic_bugs(self):
        self.check_main_function_declaration()
        self.check_function_return_value()
        self.check_index_value()
        self.check_imaginary_function_usage()
        self.check_imaginary_var_usage()
        self.check_conflicting_types_attr()
        self.check_multiple_declarations()
        self.check_function_usage()

    def check_multiple_declarations(self):
        for i in range(len(self.symbol_table)):
            scope = self.symbol_table[i].scope
            key = self.symbol_table[i].key
            declaration_count = 0
            for j in range(i+1, len(self.symbol_table)):
                if scope == self.symbol_table[j].scope and key == self.symbol_table[j].key:
                    declaration_count += 1
            if declaration_count:
                self.warnings.append('Warning: Variável \'' + key + '\' já declarada anteriormente.')

    def check_var_usage(self, var_node): #called in symbol table construction, para conseguir pegar os 'var'
        var_key = var_node.children[0].type
        used_scope = None #se for None a variável está sendo usada e não declarada.
        for scope in self.scope_stack:
            if var_key == scope.key:
                used_scope = scope
        if used_scope:
            used_scope.used = True
        else:
            self.errors.append('Error: Variável \'' + var_key + '\' utilizada, mas não declarada.')

    def check_imaginary_var_usage(self):
        for symbol in self.symbol_table:
            if symbol.data_structure != 'function':
                if symbol.value and not symbol.used: #foi atribuída mas não foi utilizada
                    self.warnings.append('Warning: Variável \'' + symbol.key + '\' declarada e inicializada, mas não utilizada.')
                elif not symbol.value and not symbol.used: #não foi usado nem atribuído
                    self.warnings.append('Warning: Variável \'' + symbol.key + '\' declarada e não utilizada.')
                elif not symbol.used and not symbol.value:
                    if not self.is_parameter(symbol): #verificar se a variável está ou não nos parâmetros, pode haver várias variáveis com o mesmo nome no mesmo escopo
                        self.warnings.append('Warning: Variável \'' + symbol.key + '\' declarada e não inicializada.')
                elif not symbol.value and symbol.used: #foi usada, mas não possui nenhum valor
                    if not self.is_parameter(symbol):
                        self.errors.append('Error: Variável \'' + symbol.key + '\' declarada e utilizada, mas não possui valor atribuído.')

    def is_parameter(self, symbol):
        function = None
        for s in self.symbol_table:
            if s.data_structure == 'function':
                function = s
                if s.scope == symbol.scope[:len(s.scope)]:
                    break
        is_param = False
        for i in range(self.symbol_table.index(function) - 1, self.symbol_table.index(function) - len(function.style) - 1, -1):
            #print(self.symbol_table[i].key)
            if self.symbol_table[i] == symbol:
                #print('true')
                is_param = True
            #print('\n')
        return is_param

    def check_conflicting_types_attr(self): #verifica conflitos de tipos na atribuição
        for symbol in self.symbol_table:
            probable_type = self.get_probable_type_from_expression(symbol)
            type_attr = None
            if probable_type:
                if len(probable_type) == 2:
                    type_attr = probable_type[1]
                else:
                    type_attr = probable_type[0]
            if symbol.data_structure != 'function':
                if probable_type and symbol.type != type_attr:
                    if len(probable_type) == 2:
                        self.warnings.append('Warning: Atribuição de tipos distintos: \'' + symbol.key + '\' ' + symbol.type + ' recebe \'' + probable_type[0] + '\' ' + probable_type[1] + '.')
                    else:
                        self.warnings.append('Warning: Atribuição de tipos distintos: \'' + symbol.key + '\' ' + symbol.type + ' recebe ' + probable_type[0] + '.')
            elif symbol.key != 'main':
                if type_attr == None:
                    type_attr = 'void'
                if (probable_type and symbol.type != type_attr) or (probable_type == None and symbol.type != 'void'):
                    if type_attr == 'void' and symbol.value:
                        self.errors.append('Error: Função \'' + symbol.key + '\' do tipo ' + symbol.type + ' retornando \'' + str(symbol.value) + '\': expressão com variáveis sem valor/não inicializadas.')
                    else:
                        self.errors.append('Error: Função \'' + symbol.key + '\' do tipo ' + symbol.type + ' retornando ' + type_attr + '.')

    def get_probable_type_from_expression(self, symbol):
        probable_type = None
        d_type = None
        for ty in symbol.value_types:
            type = None
            if len(ty) == 2:
                type = ty[1]
            else:
                type = ty[0]
            if type == 'inteiro' and d_type != 'flutuante':
                probable_type = ty
                d_type = 'inteiro'
            elif type == 'flutuante':
                probable_type = ty
                d_type = 'flutuante'
            else:
                probable_type = ty
                d_type = 'void'
                break
        return probable_type
                    
    def check_function_usage(self):
        for symbol in self.symbol_table:
            used_func = False
            if symbol.data_structure == 'function' and symbol.key != 'main':
                for cf in self.called_functions:
                    if symbol.key == cf[0]:
                        used_func = True
                        break
                if not used_func:
                    self.warnings.append('Warning: Função \'' + symbol.key + '\' declarada, mas não utilizada.')

    def check_imaginary_function_usage(self): #uso de coisas que não foram declaradas; checar tipos dos parametros e argumentos
        for func in self.called_functions:
            func_key = func[0]
            exists = False
            for symbol in self.symbol_table:
                if symbol.data_structure == 'function' and func_key == symbol.key:
                    if len(symbol.style) !=  len(func[1]): #verifica tamanho do argumento/parâmetro
                        if len(symbol.style) >  len(func[1]):
                            self.errors.append('Error: Chamada à função \'' + func_key + '\' com número de parâmetros menor que o declarado.')
                        else:
                            self.errors.append('Error: Chamada à função \'' + func_key + '\' com número de parâmetros maior que o declarado.')
                    exists = True
            if not exists:
                self.errors.append('Error: Chamada a função \'' + func_key +  '\' que não foi declarada.')
            

    def check_main_function_declaration(self):
        for symbol in self.symbol_table:
            if symbol.key == 'main':
                return symbol
        self.errors.append('Error: Função principal não declarada.')

    def check_index_value(self):
        for symbol in self.symbol_table:
            if symbol.data_structure == 'array':
                for index in symbol.style: #verifica o tipo do índice
                    if not self.represents_int(index):
                        self.errors.append('Error: índice de array \'' + symbol.key + '\' não inteiro.')

    def check_illegal_main_function_call(self): #chamada durante a construção da tabela de símbolos
        main_func_scope = 'global.main'
        sym = self.scope_stack[-1]
        if main_func_scope == sym.scope[:len(main_func_scope)]:
            self.warnings.append('Warning: Chamada recursiva para a função principal.')
        else:
            self.errors.append('Error: Chamada para a função principal não permitida.')

    def check_function_return_value(self): #complementar para o resto das funções
        for symbol in self.symbol_table:
            if symbol.data_structure == 'function':
                if symbol.key == 'main': #erro de retorno para funções principal
                    return_type = symbol.type
                    if return_type != 'inteiro':
                        self.errors.append('Error: Função principal deveria retornar inteiro.')
                    else:
                        return_value = symbol.value
                        if not self.represents_int(return_value):
                            if return_value == None:
                                self.errors.append('Error: Função principal deveria retornar inteiro, mas retorna vazio.')
                            else:
                                self.errors.append('Error: Função principal deveria retornar inteiro.')
                else: #qualquer outra função
                    return_type = symbol.type


    def get_type_of_var(self, var):
        for symbol in self.symbol_table:
            if symbol.data_structure == 'plain' and symbol.key == var:
                return symbol.type

    def show_warnings(self):
        print('#-----------------------  Warnings  -----------------------#\n')
        for warn in self.warnings:
            print(warn)
        print('\n')

    def show_errors(self):
        print('#-----------------------   Errors   -----------------------#\n')
        for error in self.errors:
            print(error)
        print('\n')