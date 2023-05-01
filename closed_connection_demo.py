from collections import namedtuple
from collections import deque
from time import perf_counter
import itertools as it
import numpy as np
import torch as tr
import matplotlib.pyplot as pt
import copy

# A clause is a disjunction of literals. in CNF form.
class Clause:
	def __init__(self, literals):
		# for now for simplicity, use a list of strings
		self.literals = literals 

	def __repr__(self):
		if len(self.literals) == 0: return "⊥"
		return ' v '.join(self.literals)
	
	# custom equality and hash functions
	def __eq__(self, other):
		return self.literals == other.literals
	
	def __hash__(self):
		return hash(tuple(self.literals))
	
	def negate(self):
		return Clause([literal.negate() for literal in self.literals])
	
class Literal:
	def __init__(self, atom, negated = False):
		self.atom = atom
		self.negated = negated
	def __negate__(self):
		return Literal(self.atom, not self.negated)
	def __repr__(self):
		return self.__str__()
	def __str__(self):
		if self.negated: return "~" + self.atom
		return self.atom
	def __eq__(self, other):
		return self.atom == other.atom and self.negated == other.negated
	def __hash__(self):
		return hash((self.atom, self.negated))
	def negate(self):
		return Literal(self.atom, not self.negated)

class LiteralNode:
	def __init__(self, literal, parent = None, children = []):
		self.literal = Literal(literal)
		self.children = [] # list of LiteralNode objects
		self.parent = parent # a LiteralNode object

	def __repr__(self): # return a string representation of the node's literal
		return self.literal.__repr__()
	
	def add_child(self, child):
		self.children.append(child)

	def pop_child(self):
		return self.children.pop()

	# TODO: can be optimized by tracking a path from root to current node
	def is_current_branch_closed(self):
		node = self
		while node.parent != None:
			node = node.parent
			if node.literal == self.literal.negate():
				return True
		return False

# A tree structure of clauses. Each node is a literal (string). 
# Each branching is a disjunction (Clause).
# Root: a literal_node object.
# Axioms: a list of clauses.
# One tableau represents one proof state, which is a node in the future MCTS tree.
class Tableau:
	def __init__(self, goal_literal, axioms):
		self.axioms = axioms
		self.root = LiteralNode(goal_literal)
		self.all_branches_closed = False
		self.leaf_queue = [self.root] # a list of leaf nodes, used for expansion
		self.inference = 0 # number of inferences made so far

	# need a way to compare two tableaux to check for loops in MCTS
	def __eq__(self, other):
		return self.root == other.root
	
	def __hash__(self):
		return hash(self.root)
	
	# return the tree structure of the tableau, from root to all the children nodes and to leaves, by level traversal
	def __repr__(self):
		queue = [self.root]
		result = []
		while len(queue) > 0:
			node = queue.pop(0)
			result.append(node)
			queue.extend(node.children)
		return str(result)
	
	def are_all_branches_closed_helper(self, root, path_to_node: list):
		# run a DFS from the root node to check if all branches are closed
		# if there is a node that is not closed, return False
		# to determine if a node is closed, check if the path from the root to the node contains a contradiction
		# path_to_node is a list of literals from the root to the current node

		# base case, leaf node
		if root.children == []:
			return root.literal.negate() in path_to_node

		result = True
		for child in root.children:
			result = result and self.are_all_branches_closed_helpercle(child, [child.literal] + path_to_node)

		return result and (str(root.literal.negate()) in path_to_node)
	
	def are_all_branches_closed(self):
		return self.are_all_branches_closed_helper(self.root, [self.root.literal])
	

	# attemp to do one step of inference, in any possible way on each leaf node. 
	# return all expansion result to a list of tableau objects
	def expand_basic(self):
		queue_size = len(self.leaf_queue)
		for i in range(queue_size):
			leaf = self.leaf_queue[i]
			print("Expanding leaf node: " + str(leaf.literal))
			# if the current branch is closed, skip, don't expand
			if (leaf.is_current_branch_closed()):
				continue

			# choose a clause to expand
			# for now, just go through each clause that has the negation of the goal literal
			possible_actions = []
			
			for axiom in self.axioms:
				axiom_literals = parse(axiom)

				# TODO: need to consider subsitutions when checking, not working yet
				tmp_leaf_literal = copy.deepcopy(leaf.literal.negate())
				tmp_leaf_literal_str = squash_literal(str(tmp_leaf_literal))
				tmp_axiom_literals = copy.deepcopy(axiom_literals)
				for i in range(len(tmp_axiom_literals)):
					tmp_axiom_literals[i] = squash_literal(tmp_axiom_literals[i])

				if tmp_leaf_literal_str in tmp_axiom_literals:
					# append new literal nodes to the leaf node
					for literal_str in axiom_literals:
						leaf.add_child(LiteralNode(literal_str, leaf))
					
					# remove leaf node from leaf_queue, and add all its children to leaf_queue
					self.leaf_queue.remove(leaf)
					self.leaf_queue.extend(leaf.children)
					
					# deep copy self
					tmp_tableau = copy.deepcopy(self)
					tmp_tableau.inference += 1

					# add the new tableau to the result
					possible_actions.append(tmp_tableau)

					# backtrack, remove the new children nodes and add the leaf node back to leaf_queue
					for child in leaf.children:
						leaf.pop_child()
						self.leaf_queue.pop()

					self.leaf_queue.append(leaf)

		return possible_actions

# A proof state is a node in the MCTS tree.
# Each proof state has a tableau frozen at a certain step, which is a tree structure of clauses.
# Each proof state has a list of actions, which are clauses that can be expanded.
# Each proof state has a list of children proof states, which are the result of expanding the current proof state.
class ProofStateNode:
	def __init__(self, tableau, parent = None, children = []):
		self.tableau = tableau
		self.parent = parent
		self.children = children
		self.actions = [] # list of clauses

def iterative_deepening(goal_literal, axioms):
	root = Tableau(goal_literal, axioms)
	leaf_state_queue = deque([root]) # a queue of leaf nodes, used for expansion

	# go through each available action and expand the tableau
	
	while (len(leaf_state_queue) > 0):
		leaf_state = leaf_state_queue.popleft()
		print("leaf state: ")
		print(leaf_state)

		# if the leaf_state is all closed, return proof
		if (leaf_state.are_all_branches_closed()):
			return (True, leaf_state)
		
		# if exceed the max inference step, skip
		if (leaf_state.inference == 5):
			print("g")
			break

		# add all possible actions to the queue
		# for the current leaf, explore all possible ways of expanding every child node of the leaf proof state, unless the current leaf is completely closed
		
		actions = leaf_state.expand_basic()
		print("actions: ", actions)
		leaf_state_queue.extend(actions)

	return (False, None)
			
# TODO: action, choose which clause to expand
# MCTS + UCT
def expand_mcts(goal_literal, axioms):
	mcts_root = ProofStateNode(Tableau(goal_literal, axioms))
	return

# P(a,b) becomes P__ , P(x) becomes P_
def squash_literal(literal_str):
	result = literal_str[0]
	if literal_str[0] == '~':
		result += literal_str[1]
	for char in literal_str:
		if char == '(':
			result += '_'
		elif char == ',':
			result += '_'
	return result

def parse(cnf_string):
	# parse a string into a list of literals
	# for now, assume the string is in CNF form
	# return a list of strings
	return [literal_str for literal_str in cnf_string.split(' v ')]

# main
def main():
	# test closed_tableau
	c1 = 'P(a)'
	c2 = 'R(a,b) v ~P(a) v Q(b)'
	c3 = 'S(b) v ~Q(b)'
	c4 = '~S(b) v ~Q(b)'
	c5 = '~Q(b) v ~R(a,b)'
	c6 = '~R(a, b) v Q(b)'

	# check parsing all clauses above
	print(parse(c1))
	print(parse(c2))
	print(parse(c3))
	print(parse(c4))
	print(parse(c5))
	print(parse(c6))

	axioms = [c2, c3, c4, c5, c6]
	goal_literal_str = 'P(a)'

	tableau = Tableau(goal_literal_str, axioms)
	print('start: ', tableau)

	# test expand with iterative deepening strategy
	# result = tableau.expand_basic()

	(result, proof_state) = iterative_deepening(goal_literal_str, axioms)

	if (result):
		print('proof found')
		print(proof_state.tableau)
	else:
		print('proof not found')
	


if __name__ == '__main__':
	main()