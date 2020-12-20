# -*- coding: utf-8 -*-
import torch
import numpy as np
import upDown as ud
import dagUtility as dag

UNIV = 10
TYPE = torch.float32
UP = 0
DOWN = 1

def game_2_state(G, UNIV, type=TYPE):
  '''Take a game and spit out the tensor. The tensor representation of the game 
  state is  representted by four UNIV x UNIV arrays:
  - the ij-th entry of the 0-th array is a 1 if node i >= node j and node j is 
  blue and 0 otherwise.
   and node j is blue.
  - the ij-th entry of a the 1-st array is a 1 node i >= node j and node j is 
  green and 0 otherwise.  
  - the the ij-th entry of a the 2-nd array is a 1 node i >= node j and node j 
  is red and 0 otherwise.
  - the 3-rd array is a constant 0. (UP MOVES FIRST BY DEFAULT.)'''
  game_state = torch.zeros((4, UNIV, UNIV), dtype=TYPE)
  cr = G.cover_relations
  tc = dag.transitive_closure(cr)
  color_dict = G.coloring

  for node in tc:
    color = color_dict[node]

    if color == 1:
      game_state[0, node,node] = 1
    elif color == 0:
      game_state[1, node, node] = 1
    else:
      game_state[2, node, node] = 1
    
    for cover in tc[node]:
      color = color_dict[cover]
      if color == 1:
        game_state[0,node, cover] = 1
      elif color == 0:
        game_state[1, node, cover] = 1
      else:
        game_state[2, node, cover] = 1

  return game_state

class GameState(object):
  '''An abstract class based on a machine readable picture of UpDown. 
  Takes in an UpDown game and the size of the universe that game is played on.'''

  def __init__(self, G, UNIV):
    '''G is an instance of UpDown. UNIV is the size of the universe. The attribute self.state
    holds the tensor describing current state of the game G (using the f'n game_2_state).'''

    #Check to make sure the game G fits in the universe.
    assert len(G) <= UNIV

    #Get initial state
    self.state = game_2_state(G, UNIV)

  def transpose(self):
    '''A method to be used each time the game switches player.
    Takes the tensor self.state, transposes the dimensions 1 and 2, swaps
    the 0th and 2nd matrices, and changes the last matrix from zeros to ones or ones to zeros'''

    self.state = torch.transpose(self.state, 1, 2)

    self.state[[0,2]] = self.state[[2,0]]
    
    if self.state[3,0,0] == 0:
      self.state[3,:,:] += 1
    else:
      self.state[3,:,:] -= 1

  def valid_actions(self):
    '''A method returning (as a tensor) the valid actions for the current player.'''
    
    #Get the diagonals of the first and second matrices and sum their columns
    d = torch.sum(torch.diagonal(self.state[[0,1]], 0,2),0)
    
    #Return the indices of the nonzero entries in d as a row tensor
    return d.nonzero().view(-1)

  def take_action(self,a):
    '''Call this method once an action a is chosen to mutate self.state and remove
    the upset of a.'''
      
    rows = self.state[[0,1,2],[a],:]
    
    #rows.nonzero() is a m x 2 tensor (m is 1 + number of nodes in node a's upset)
    #the (i,j) entry of row tells us to zero out the jth column in the ith matrix of self.state
    #this loop does that.
    for row in rows.nonzero():
      self.state[[row[0]],:,[row[1]]] = 0

  def have_I_lost(self):
    if len(self.valid_actions) == 0:
      return True
    else:
      return False
