# -----------------------------------------------------------------------------
# Author: Eduardo Yuzo Nakai
#
# Description: A program for growing abstract syntax trees.
# -----------------------------------------------------------------------------

import sys
from graphviz import Graph
import string
import types
from ast import literal_eval
import re

# For windows:
# import os
# os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'

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

class AST:

    def __init__(self, tree):
        self.aux_node_list = []
        self.second_aux = []

        self.parser_tree = tree
        self.count = 0
        self.dot = Graph('AST')
        self.shape_parser_tree(self.parser_tree)
        # self.bonsai_to_pdf(self.parser_tree, 0)
        # self.dot.render('ast.gv', view=True)

    def handle_expressions(self, node): #almost all 
        if len(node.children) == 3 and not node.type == 'factor':
            left = self.handle_expressions(node.children[0])
            operator = self.handle_expressions(node.children[1])
            right = self.handle_expressions(node.children[2])
            operator.children = [left, right]
            return operator
        elif node.type[-8:] == 'operator':
            operator = node.children[0]
            return operator
        elif node.type == 'var' and len(node.children[0].children) == 0:
            var_node = node.children[0]
            return var_node
        elif node.type == 'factor':
            factor_node = node.children[0]
            factor = node.children[0].type
            if len(node.children) == 3:
                factor_node = node.children[1]
                factor = node.children[1].type
            if factor == 'number':
                number = factor_node.children[0]
                print(number.type)
                return number
            elif factor == 'function_call':
                return factor_node
            elif factor == 'var':
                if len(factor_node.children) == 2:
                    self.second_aux = []
                    self.extract_indexes(factor_node.children[1])
                    factor_node.children[0].children = self.second_aux
                var = factor_node.children[0]
                return var
            else:
                return self.handle_expressions(factor_node)
        elif len(node.children) == 1:
            return self.handle_expressions(node.children[0])
        elif len(node.children) == 2:
            left = self.handle_expressions(node.children[0])
            left.children = [self.handle_expressions(node.children[1])]
            return left
        else:
            return node

    def extract_argument_list(self, node):
        if len(node.children) == 3:
            self.aux_node_list.append(self.handle_expressions(node.children[2]))
        elif len(node.children) == 1 and node.children[0].type != 'Empty':
            self.aux_node_list.append(self.handle_expressions(node.children[0]))
        if node.children[0].type == 'argument_list':
            self.extract_argument_list(node.children[0])
                
    def extract_indexes(self, index_node):
        if len(index_node.children) == 4:
            self.second_aux.append(self.handle_expressions(index_node.children[3]))
        elif len(index_node.children) == 3:
            self.second_aux.append(self.handle_expressions(index_node.children[1]))
        if index_node.children[0].type == 'index':
            self.extract_indexes(index_node.children[0])

    def extract_variable_list(self, node):
        var_node = None
        if len(node.children) == 3:
            var_node = node.children[2]
            var_key = var_node.children[0]
            if len(var_node.children) == 2:
                self.extract_indexes(var_node.children[1])
                self.second_aux.reverse()
                var_key.children = self.second_aux
            self.aux_node_list.append(var_key)
        elif len(node.children) == 1 and node.children[0].type != 'Empty':
            var_node = node.children[0]
            var_key = var_node.children[0]
            if len(var_node.children) == 2:
                self.extract_indexes(var_node.children[1])
                self.second_aux.reverse()
                var_key.children = self.second_aux
            self.aux_node_list.append(var_key)
        if node.children[0].type == 'variable_list':
            self.extract_variable_list(node.children[0])

    def extract_actions(self, node):
        if len(node.children) == 2:
            aux_node = node.children[1].children[0]
            if aux_node.type == 'expression':
                if aux_node.children[0].type[-11:] == '_expression':
                    self.aux_node_list.append(self.handle_expressions(node.children[1].children[0]))
                else:
                    self.aux_node_list.append(node.children[1].children[0].children[0])
            else:
                self.aux_node_list.append(node.children[1].children[0])
        if node.children[0].type == 'body':
            self.extract_actions(node.children[0])

    def extract_declarations(self, node):
        if len(node.children) == 2:
            self.aux_node_list.append(node.children[1].children[0])
        elif len(node.children) == 1:
            self.aux_node_list.append(node.children[0].children[0])
        if node.children[0].type == 'declaration_list':
            self.extract_declarations(node.children[0])

    def extract_parameter_list(self, node): #adicionar suporte para vetores
        if len(node.children) == 3:
            node.children[2].children[2].children = [node.children[2].children[0].children[0]]
            self.aux_node_list.append(node.children[2].children[2])
        elif len(node.children) == 1 and node.children[0].type != 'Empty':
            node.children[0].children[2].children = [node.children[0].children[0].children[0]]
            self.aux_node_list.append(node.children[0].children[2])
        if node.children[0].type == 'parameter_list':
            self.extract_parameter_list(node.children[0])

    def shape_parser_tree(self, node):
        for child in node.children:
            self.shape_parser_tree(child)
        if node:
            self.aux_node_list = [] #list of actions
            if node.type == 'function_call':
                self.extract_argument_list(node.children[2])
                self.aux_node_list.reverse()
                node.children[0].children = self.aux_node_list
                node.children = [node.children[0]]
            elif node.type == 'attribution':
                if len(node.children[0].children) == 2:
                    self.second_aux = []
                    self.extract_indexes(node.children[0].children[1])
                    node.children[0].children[0].children = self.second_aux
                node.children[0] = node.children[0].children[0]
                node.children[2] = self.handle_expressions(node.children[2])
                node.children = [node.children[0], node.children[2]]
            elif node.type == 'return' or node.type == 'write' or node.type == 'read':
                node.children[2] = self.handle_expressions(node.children[2])
                node.children = [node.children[2]]
            elif node.type == 'if':
                node.children[1] = self.handle_expressions(node.children[1])

                if len(node.children) == 7:
                    self.extract_actions(node.children[5])
                    self.aux_node_list.reverse()
                    node.children[5].children = self.aux_node_list

                self.aux_node_list = []
                self.extract_actions(node.children[3])
                self.aux_node_list.reverse()
                node.children[3].children = self.aux_node_list

                node.children[0].children = [node.children[1]]
                node.children[2].children = [node.children[3]]
                if len(node.children) == 7:
                    node.children[4].children = [node.children[5]]
                    node.children = [node.children[0], node.children[2], node.children[4]]
                else:
                    node.children = [node.children[0], node.children[2]]
            elif node.type == 'repeat':
                node.children[3] = self.handle_expressions(node.children[3])
                
                self.extract_actions(node.children[1])
                self.aux_node_list.reverse()
                node.children[1].children = self.aux_node_list

                node.children[0].children = [node.children[1]]
                node.children[2].children = [node.children[3]]
                node.children = [node.children[0], node.children[2]]

            elif node.type == 'variable_declaration': #adicionar suporte aos indexes
                self.aux_node_list = []
                self.second_aux = []
                self.extract_variable_list(node.children[2])
                self.aux_node_list.reverse()
                node.children[2].children = self.aux_node_list
                node.children = [node.children[0].children[0], node.children[2]]
            elif node.type == 'header': #body precisa de action
                self.extract_actions(node.children[4])
                self.aux_node_list.reverse()
                node.children[4].children = self.aux_node_list

                self.aux_node_list = []
                self.extract_parameter_list(node.children[2])
                self.aux_node_list.reverse()
                node.children[2].children = self.aux_node_list

                node.type = node.children[0].type
                node.children = [node.children[2], node.children[4]]

            elif node.type == 'program':
                self.extract_declarations(node.children[0])
                self.aux_node_list.reverse()
                node.children = self.aux_node_list

            elif node.type == 'function_declaration':
                if len(node.children) == 2:
                    node.children = [node.children[0].children[0], node.children[1]]
                else:
                    node.children = [Node('void'), node.children[0]]

    def print_node(self, node):
        for n in node.children:
            print(str(n.type))

    def bonsai_to_pdf(self, node, count_node):
        self.dot.node(str(count_node), str(node.type))
        for children in node.children:
            if children:
                self.count = self.count + 1
                self.dot.edges([(str(count_node), str(self.count))])
                self.bonsai_to_pdf(children, self.count)
