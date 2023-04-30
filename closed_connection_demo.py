from collections import namedtuple
from collections import deque
from time import perf_counter
import itertools as it
import numpy as np
import torch as tr
import matplotlib.pyplot as pt

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

class LiteralNode:
	def __init__(self, literal, parent = None, children = []):
		self.literal = Literal(literal)
		self.children = [] # list of LiteralNode objects

	def __repr__(self): # return a string representation of the node's literal
		return self.literal.__repr__()
	
	def add_child(self, child):
		self.children.append(child)

	# TODO: can be optimized by tracking a path from root to current node
	def is_current_branch_closed(self):
		node = self
		while node.parent != None:
			node = node.parent
			if node.literal == self.literal.negate():
				return True
		return False

	def are_all_branches_closed(self, path_to_node: list):
		# run a DFS from the root node to check if all branches are closed
		# if there is a node that is not closed, return False
		# to determine if a node is closed, check if the path from the root to the node contains a contradiction
		# path_to_node is a list of literals from the root to the current node

		# base case, leaf node
		if self.children == []:
			return path_to_node.contains(self.literal.negate())

		result = True
		for child in self.children:
			result = result and self.are_all_branches_closed(child, [child.literal] + path_to_node)

		return result and path_to_node.contains(self.literal.negate())

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
		self.leaf_queue = deque([self.root]) # a queue of leaf nodes, used for expansion

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

	# action, choose which clause to expand
	# iterative deepening strategy
	def expand_basic(self):
		while self.leaf_queue != []:
			leaf = self.leaf_queue.popleft()

			# if the current branch is closed, skip, don't expand
			if (leaf.is_current_branch_closed()):
				continue

			# choose a clause to expand
			# for now, just choose a random clause that has the negation of the goal literal
			actions = []
			for axiom in self.axioms:
				if axiom.contains(leaf.literal.negate()):
					actions.append(axiom)

			action = np.random.choice(actions) # a clause string
			
			# for axiom in self.axioms:
			# 	axiom_literals = parse(axiom)

			# 	leaf.add_child(LiteralNode(axiom))
			# 	self.leaf_queue.append(leaf.children[-1])

		return (False, None)

			
	# TODO: action, choose which clause to expand
	# MCTS + UCT
	def expand_mcts(self):
		return 


def parse(cnf_string):
	# parse a string into a list of literals
	# for now, assume the string is in CNF form
	return [Literal(literal) for literal in cnf_string.split(' v ')]

# main
def main():
	# test closed_tableau
	c1 = 'P(x)'
	c2 = 'R(x,y) v ~P(x) v Q(y)'
	c3 = 'S(x) v ~Q(b)'
	c4 = '~S(x) v ~Q(x)'
	c5 = '~Q(x) v ~R(a,x)'
	c6 = '~R(a, x) v Q(x)'

	# check parsing all clauses above
	print(parse(c1))
	print(parse(c2))
	print(parse(c3))
	print(parse(c4))
	print(parse(c5))
	print(parse(c6))

	axioms = [c1, c2, c3, c4, c5, c6]
	goal_literal_str = 'P(a)'

	tableau = Tableau(goal_literal_str, axioms)

	# test expand with iterative deepening strategy
	# result = tableau.expand_basic()

	print(tableau)


if __name__ == '__main__':
	main()