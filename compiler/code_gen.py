# -----------------------------------------------------------------------------
# Author: Eduardo Yuzo Nakai
#
# Description: A program for code generation using llvm.
# -----------------------------------------------------------------------------

from llvmlite import ir
import sys
import re

class Gen_Code:
    def __init__(self, tree):
        print("#-----------------------  Code Gen  -----------------------#")
        self.global_clock = 0

        self.tree = tree
        self.module = ir.Module('module.bc')
        self.current_scope = ['global']

        self.global_var_list = []
        self.scope_var_list = []
        self.function_list = []
        self.exit_block = ''
        self.entry_block = ''
        self.generate_code(self.tree)

        self.file = open('file.ll', 'w')
        self.file.write(str(self.module))
        self.file.close()
        #print(self.module)

    def generate_code(self, node):
        if node:
            if node.type == 'variable_declaration' and self.current_scope[0] == 'global' and len(self.current_scope) == 1:
                self.global_declaration(node) 
            elif node.type == 'function_declaration':
                self.current_scope.append(self.get_function_key(node))
                self.function_declaration(node)
            for children in node.children:
                self.generate_code(children)
            if node.type == ('function_declaration'):
                self.current_scope.pop(-1)

    def global_declaration(self, node):
        variable_type = self.get_type(node) #tipo da variável
        variable_list = self.get_variable_list(node) #lista com vários nós 'variável'
        if variable_type == 'inteiro':
            for var in variable_list:
                global_variable = None
                if len(var.children) == 0:
                    global_variable = ir.GlobalVariable(self.module, ir.IntType(32), var.type)
                    global_variable.initializer = ir.Constant(ir.IntType(32), 0)
                    global_variable.linkage = 'common'
                    global_variable.align = 4
                elif len(var.children) == 1: #array unidimensional
                    dimension = int(var.children[0].type)
                    array_type = ir.ArrayType(ir.IntType(32), dimension)
                    global_variable = ir.GlobalVariable(self.module, array_type, var.type)
                    global_variable.initializer = ir.Constant(ir.ArrayType(ir.IntType(32), dimension), None)
                    global_variable.linkage = 'common'
                    global_variable.align = 4
                self.global_var_list.append(global_variable)
        elif variable_type == 'flutuante':
            for var in variable_list:
                global_variable = None
                if len(var.children) == 0:
                    global_variable = ir.GlobalVariable(self.module, ir.DoubleType(), var.type)
                    global_variable.initializer = ir.Constant(ir.DoubleType(), 0)
                    global_variable.linkage = 'common'
                    global_variable.align = 4
                elif len(var.children) == 1: #array unidimensional
                    dimension = int(var.children[0].type)
                    array_type = ir.ArrayType(ir.DoubleType(), dimension)
                    global_variable = ir.GlobalVariable(self.module, array_type, var.type)
                    global_variable.initializer = ir.Constant(ir.ArrayType(ir.DoubleType(), dimension), None)
                    global_variable.linkage = 'common'
                    global_variable.align = 4
                self.global_var_list.append(global_variable)

    def get_variable_list(self, node):
        variable_list = []
        for var in node.children[1].children:
            variable_list.append(var)
        return variable_list

    def get_type(self, node):
        return node.children[0].type

    def get_function_parameter_list(self, node):
        param_list_node = node.children[1].children[0]
        parameter_list = []
        parameter_key_list = []
        if len(param_list_node.children) > 0:
            for param in param_list_node.children:
                parameter_key_list.append(param.type)
                param_type = param.children[0].type
                if param_type == 'inteiro':
                    parameter_list.append(ir.IntType(32))
                elif param_type == 'flutuante':
                    parameter_list.append(ir.DoubleType())
        return parameter_list, parameter_key_list

    def get_function_key(self, node):
        return node.children[1].type

    def function_declaration(self, node):
        self.scope_var_list = []
        return_type = self.get_type(node)
        parameter_type_list, parameter_key_list = self.get_function_parameter_list(node) #parametros: nomes e tipos
        function_key = self.get_function_key(node) #nome da função
        return_value = None
        function_type = None
        if return_type == 'void':
            function_type = ir.FunctionType(ir.VoidType(), (parameter_type_list))
            return_value = ir.VoidType()
        else:
            if return_type == 'inteiro':
                function_type = ir.FunctionType(ir.IntType(32), (parameter_type_list))
                return_value = ir.IntType(32)
            elif return_type == 'flutuante':
                function_type = ir.FunctionType(ir.DoubleType(), (parameter_type_list))
                return_value = ir.DoubleType()
        function = ir.Function(self.module, function_type, function_key)
        self.function_list.append(function)

        self.entry_block = function.append_basic_block(name='entry_' + function_key)
        self.exit_block = function.append_basic_block(name='exit_' + function_key)
        builder = ir.IRBuilder(self.entry_block)

        with builder.goto_entry_block():
            self.parameter_list(function.args, parameter_type_list, parameter_key_list, builder) #resolve os parametros da função
            if return_type != 'void':
                return_value = builder.alloca(return_value, name='return_value')
            self.body(node.children[1].children[1], builder, return_value) #resolve actions
            builder.branch(self.exit_block)

        with builder.goto_block(self.exit_block):
            if return_type == 'void':
                builder.ret_void()
            else:
                load_return = builder.load(return_value)
                builder.ret(load_return)

    def parameter_list(self, args, type_list, key_list, builder):
        for i in range(len(key_list)):
            if str(type_list[i]) == 'i32':
                alloca = builder.alloca(ir.IntType(32), size=None, name=key_list[i])
                alloca.align = 4
                builder.store(args[i], alloca)
                self.scope_var_list.append(alloca)
            else:
                alloca = builder.alloca(ir.DoubleType(), size=None, name=key_list[i])
                alloca.align = 4
                builder.store(args[i], alloca)
                self.scope_var_list.append(alloca)

    def get_assigned_var(self, node):
        return node.children[0].type

    def get_function_object(self, key):
        for fc in self.function_list:
            if fc.name == key:
                return fc
        return None

    def get_argument_list(self, node, builder):
        arg_list = []
        for children in node.children:
            expression = self.expression(children, builder)
            arg_list.append(expression)
        return arg_list

    def change_argument_type(self, function, arguments, builder):
        function_param = function.args
        modified_arguments = []
        for i in range(len(function_param)):
            if str(function_param[i].type) not in str(arguments[i].type):
                if 'i32' in str(function_param[i].type):
                    modified_arguments.append(builder.fptosi(arguments[i], ir.IntType(32)))
                else:
                    modified_arguments.append(builder.sitofp(arguments[i], ir.DoubleType()))
            else:
                modified_arguments.append(arguments[i])
        return modified_arguments

    def expression(self, node, builder):
        if node.type == '!':
            return builder.neg(self.expression(node.children[0], builder), name='neg')
        elif node.type in ['-', '+', '*', '/']:
            left = self.expression(node.children[0], builder)
            right = self.expression(node.children[1], builder)
            if node.type == '+':
                if str(left.type) in 'i32' and str(right.type) in 'i32':
                    return builder.add(left, right, name='add', flags=())
                else:
                    left = builder.sitofp(left, ir.DoubleType())
                    right = builder.sitofp(right, ir.DoubleType())
                    return builder.fadd(left, right, name='add', flags=())
            elif node.type == '-':
                if str(left.type) in 'i32' and str(right.type) in 'i32':
                    return builder.sub(left, right, name='sub', flags=())
                else:
                    left = builder.sitofp(left, ir.DoubleType())
                    right = builder.sitofp(right, ir.DoubleType())
                    return builder.fsub(left, right, name='sub', flags=())
            elif node.type == '*':
                if str(left.type) in 'i32' and str(right.type) in 'i32':
                    return builder.mul(left, right, name='mul', flags=())
                else:
                    left = builder.sitofp(left, ir.DoubleType())
                    right = builder.sitofp(right, ir.DoubleType())
                    return builder.fmul(left, right, name='mul', flags=())
            elif node.type == '/':
                if str(left.type) in 'i32' and str(right.type) in 'i32':
                    return builder.sdiv(left, right, name='div', flags=())
                else:
                    left = builder.sitofp(left, ir.DoubleType())
                    right = builder.sitofp(right, ir.DoubleType())
                    return builder.fdiv(left, right, name='div', flags=())
        elif node.type in ['=', '<', '>', '>=', '<=']:
            cond = node.type
            if node.type == '=':
                cond = '=='
            return builder.icmp_signed(cond, self.expression(node.children[0], builder), self.expression(node.children[1], builder), name='cond')
        elif node.type == '||':
            return builder.or_(self.expression(node.children[0], builder), self.expression(node.children[1], builder), name='cond')
        elif node.type == '&&':
            return builder.and_(self.expression(node.children[0], builder), self.expression(node.children[1], builder), name='cond')
        elif node.type == 'function_call':
            function = self.get_function_object(node.children[0].type)
            arg_list = self.get_argument_list(node.children[0], builder) #retorna lista com argumentos prontos
            modified_arguments = self.change_argument_type(function, arg_list, builder)
            call = builder.call(function, modified_arguments, 'ret')
            return call
        elif len(node.children) == 0: #simplesmente coloca no ir.constant ou faz load e retorna
            var_type = self.get_string_type(node.type)
            value = None
            if var_type == 1:
                value = ir.Constant(ir.IntType(32), int(node.type))
            elif var_type == 2:
                value = ir.Constant(ir.DoubleType(), float(node.type))
            else:
                alloca = self.get_alloca_object(node.type)
                value = builder.load(alloca, name='', align=4)
            return value
        elif self.represents_id(node.type) != None: #significa que é o ID de um vetor
            alloca = self.get_alloca_object(node.type)
            index = self.expression(node.children[0], builder) #índice do vetor
            zero = ir.Constant(ir.IntType(32), 0)
            gep = builder.gep(alloca, [zero, zero], inbounds=True)
            gep = builder.gep(gep, [index], inbounds=True)
            return builder.load(gep, '', 4)

    def represents_id(self, s):
        return re.match(r"[A-Za-z_][\w]*", str(s)) is not None

    def represents_int(self, s):
        return re.match(r"[-+]?\d+$", str(s)) is not None

    def represents_float(self, s):
        return re.match(r"[-+]?[\d]+\.[\d]+", str(s)) is not None

    def get_string_type(self, value_key): #pega o tipo do '-1' '2.0' 'a'
        if self.represents_int(value_key):
            return 1
        elif self.represents_float(value_key):
            return 2
        else: #é ID
            return 0

    def get_alloca_object(self, var):
        for alloca in reversed(self.scope_var_list):
            if var == alloca.name:
                return alloca
        for alloca in reversed(self.global_var_list):
            if var == alloca.name:
                return alloca

    def get_current_function(self):
        return self.function_list[-1]

    #leia e escreva
    def external_declaration(self, name):
        ftype = ir.FunctionType(ir.IntType(32), (), var_arg=True)
        return self.module.declare_intrinsic(name, (), ftype)

    def string_declaration(self, string):
        self.global_clock += 1
        array_type = ir.ArrayType(ir.IntType(8), len(string))
        tmp = ir.GlobalVariable(self.module, array_type, name='external_' + str(self.global_clock))
        tmp.initializer = ir.Constant(array_type, bytearray(string, encoding='utf-8'))
        tmp.global_constant = True
        return tmp
        
    def body(self, node, builder, return_value): #ações do body
        for children in node.children:
            if children.type == 'variable_declaration':
                var_type = self.get_type(children)
                var_node_list = self.get_variable_list(children) #varios nós
                if var_type == 'inteiro':
                    for var in var_node_list:
                        alloca = builder.alloca(ir.IntType(32), name=var.type)
                        alloca.align = 4
                        self.scope_var_list.append(alloca)
                elif var_type == 'flutuante':
                    for var in var_node_list:
                        alloca = builder.alloca(ir.DoubleType(), name=var.type)
                        alloca.align = 4
                        self.scope_var_list.append(alloca)
            elif children.type == 'attribution':
                assigned_var_key = self.get_assigned_var(children)
                alloca = self.get_alloca_object(assigned_var_key)
                expression = self.expression(children.children[1], builder)
                if not str(expression.type) in str(alloca.type):
                    if 'i32' in str(alloca.type):
                        expression = builder.fptosi(expression, ir.IntType(32))
                    else:
                        expression = builder.sitofp(expression, ir.DoubleType())
                if len(children.children[0].children) == 1: #vetor unidimensional
                    index = self.expression(children.children[0].children[0], builder)
                    zero = ir.Constant(ir.IntType(32), 0)
                    gep = builder.gep(alloca, [zero, zero], inbounds=True)
                    assigned_vector = builder.gep(gep, [index], inbounds=True)
                    builder.store(expression, assigned_vector)

                elif len(children.children[0].children) == 0: #variavel normal
                    builder.store(expression, alloca)
            elif children.type == 'read':
                alloca = self.get_alloca_object(children.children[0].type)
                alloca_type = None
                if 'i32' in str(alloca.type):
                    alloca_type = '%d\0'
                else:
                    alloca_type = '%lf\0'
                read = self.external_declaration('scanf')
                args = [self.string_declaration(alloca_type), alloca]
                builder.call(read, args)
            elif children.type == 'write':
                loaded_var = self.expression(children.children[0], builder)
                write = self.external_declaration('printf')
                loaded_var_type = None
                args = None
                if 'i32' in str(loaded_var.type):
                    loaded_var_type = '%d\n\0'
                    args = [self.string_declaration(loaded_var_type), loaded_var]
                else:
                    loaded_var_type = '%lf\n\0'
                    args = [self.string_declaration(loaded_var_type), loaded_var]
                builder.call(write, args)
            elif children.type == 'return':
                function = self.get_current_function()
                entry_return = function.append_basic_block('entry_return')
                builder.branch(entry_return)
                with builder.goto_block(entry_return):
                    expression = self.expression(children.children[0], builder)
                    builder.store(expression, return_value)
                    builder.branch(self.exit_block)
                exit_return = function.append_basic_block('exit_return')
                builder.position_at_end(exit_return)
            elif children.type == 'if':
                self.global_clock += 1
                if_expression = self.expression(children.children[0].children[0], builder) # corrigir essa parte
                if len(children.children) == 2:
                    with builder.if_then(if_expression):
                        self.body(children.children[1].children[0], builder, return_value)
                else:
                    with builder.if_else(if_expression) as (then, otherwise):
                        with then:
                            self.body(children.children[1].children[0], builder, return_value)
                        with otherwise:
                            self.body(children.children[2].children[0], builder, return_value)
            elif children.type == 'function_call':
                function = self.get_function_object(children.children[0].type)
                arg_list = self.get_argument_list(children.children[0], builder) #retorna lista com argumentos prontos
                modified_arguments = self.change_argument_type(function, arg_list, builder)
                builder.call(function, modified_arguments, 'call')
            elif children.type == 'repeat':
                self.global_clock += 1
                function = self.get_current_function()
                repeat_entry_block = function.append_basic_block('entry_repeat')
                repeat_exit_block = function.append_basic_block('exit_repeat')
                builder.branch(repeat_entry_block)
                builder.position_at_end(repeat_entry_block)
                self.body(children.children[0].children[0], builder, return_value)
                repeat_expression = self.expression(children.children[1].children[0], builder)
                builder.cbranch(repeat_expression, repeat_exit_block, repeat_entry_block)
                builder.position_at_end(repeat_exit_block)
