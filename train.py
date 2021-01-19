#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 22:59:39 2021

@author: Charles Petersen and Jamison Barsotti
"""
#import os
import random
#import collections
import numpy as np

import gameState as gs 
import model, mcts
import randomUpDown as rud

#from tensorboardX import SummaryWriter

import torch
import torch.optim as optim
import torch.nn.functional as F

def symmetries(training_data, dim = gs.UNIV, num_samples=10):
    '''Returns 'num_samples' symmetries of each example in 'training_data'.
    (A reindexing of node labels in any upset-downset game provides a
     symmetry of the gameboard.)
    
    Parameters
    ----------
    training_triple : tuple
        a triple of state, policy and value for training from self-play.
    dim : int (nonnegative), optional
        must be at least as large as the number of nodes in 'game'. 
        The default is UNIV.
    num : int (nonnegative), optional
        The number of symmetries to take (sampled w/ repitition).
        The default is 10.

    Returns
    -------
    sym_train_data : list
        'num_samples' symmetries of 'training data'.

    ''' 
    sym_train_data = []
    for train_triple in training_data:
        state, policy, value =  train_triple
        for _ in range(num_samples):
            # get random permutation on dim # letters
            p = np.random.permutation(dim)
            # re-index nodes by permuting columns and rows
            state_sym = state[:,:,p]
            state_sym = state_sym[:,p,:]
            # permute nodes in policy too!
            policy_sym = policy[p]
            sym_train_data.append((state_sym, policy_sym, value)) 
            
    return sym_train_data

def evaluation(alpha_net, apprentice_net, num_nodes = gs.UNIV, num_plays=400, 
               win_thrshld=0.55, temp = 0):
    '''Plays 'num_plays' games of randomly generated upset-downset games
    of size 'num'nodes' between 'alpha_net' and 'apprentice_net'. Returns 
    wether 'apprentice_net' won at least 'win_thrshld' percentage of the games.

    Parameters
    ----------
    alpha_net : neural network
        The current best model.
    apprentice_net : neural network
        the model currently training.
    num_nodes : int, optional
        the number of nodes in each game played during evaluation. The default
        is gs.UNIV.
    num_plays : int (nonnegative), optional
        the number of games to play during evaluation. The default is 400.
    win_thrshld : float, optional
        between 0 and 1. The win percentage over all games played during 
        evaluation needed for'apprentice_net' to be considered better than 
        'alpha_net'. The default is 0.55.
    temp : float (nonnegative), optional
        controls the exploration in picking the next move. The default is 0.

    Returns
    -------
    bool
        True if 'apprentice_net' won at least 'win_thrshld' percentage of 
        the games played during evaluation, and False otherwise.
    apprentice_wins : TYPE
        DESCRIPTION.

    '''
    # keep track of the models
    alpha = 0
    apprentice = 1
    
    # evaluation
    apprentice_wins = 0
    actions = np.arange(gs.UNIV) 
    
    for _ in range(num_plays):
        # uniformly randomly choose which model plays first
        # and which player moves first.
        net_to_start = np.random.choice([alpha, apprentice])     
        up_or_down = np.random.choice([gs.UP, gs.DOWN])
        
        # play a randomly generated game of upset-downset
        G = rud.RandomGame(num_nodes, colored=True)
        cur_state = gs.to_state(G, to_move = up_or_down)
        cur_net = net_to_start
        move_count = 0
        winner = None
        while not gs.is_terminal_state(cur_state):
            root = mcts.PUCTNode(cur_state)
            if cur_net == alpha:
                mcts.MCTS(root, alpha_net)
            else:
                mcts.MCTS(root, apprentice_net)
            policy = mcts.MCTS_policy(root, temp)
            move = np.random.choice(actions, p=policy)
            cur_state = root.edges[move].state
            cur_net = 1 - cur_net
            move_count += 1
        if move_count %2 == 0:
            winner = 1-net_to_start
        else:
            winner = net_to_start
        if winner == apprentice:
            apprentice_wins+=1
            
    if (apprentice_wins/num_plays) > win_thrshld:
        return True, apprentice_wins
    else: 
        return False, apprentice_wins
  
def loss(net_pol, net_vals, batch_probs, batch_vals):
    """
    Loss function to be used in training.    
    """
    loss_value_v = F.mse_loss(net_vals.squeeze(-1), batch_vals)
    loss_policy_v = -F.log_softmax(net_pol, dim=1) * batch_probs
    loss_policy_v = loss_policy_v.sum(dim=1).mean()

    return loss_policy_v, loss_value_v
        
def train(apprentice_net=None, alpha_net=None,
          BATCH_SIZE=256,
          PLAY_EPISODES = 20,
          MCTS_SEARCHES = 10,
          MCTS_BATCH_SIZE = 8,
          REPLAY_BUFFER = 5000,
          LEARNING_RATE = 0.1,
          TRAIN_ROUNDS = 10,
          MIN_REPLAY_TO_TRAIN = 2000,
          BEST_NET_WIN_RATIO = 0.54,
          EVALUATE_EVERY_STEP = 100,
          EVALUATION_ROUNDS = 100,
          STEPS_BEFORE_TAU_0 = 10,
          TEMP = 1,
          TEMP_THRESH = 2,
          NUM_BEST = np.inf):
    '''
    Trains the apprentice_net using the alpha_net with respect to loss. 
    Builds on experience by updating the alpha_net once the apprentice_net
    beats it at a BEST_NET_WIN_RATIO rate.
    
    If using apprentice_net or alpha_net, these should Nets (see model.py module).
    Function will initialize these nets if none are given.
    
    The other variables are various (hyper)parameters.
    '''

    #Initialize the nets if they aren't already given.
    if apprentice_net == None:
        apprentice_net = model.Net(input_shape=model.OBS_SHAPE, actions_n=gs.UNIV)
    
    if alpha_net == None:    
        torch.save(apprentice_net.state_dict(), '0alpha_net.pt')
        alpha_net = apprentice_net
    else:
        torch.save(alpha_net.state_dict(), '0alpha_net.pt')

    #Initialize the optimizer.
    optimizer = optim.SGD(apprentice_net.parameters(), lr=LEARNING_RATE, momentum=0.9)

    #Initialize the list to store the information generated by alpha_net and some trackers.
    training_batch = []
    train_idx = 0
    best_idx = 0

    #While loop will keep going until the alpha_net has been updated NUM_BEST number of times. This is
    #set to infinity as default.
    while best_idx < NUM_BEST:
        
        #This for loop generates data for training the apprentice_net from the alpha_net.
        for _ in range(PLAY_EPISODES):
            size = random.randint(1, gs.UNIV)
            G = rud.RandomGame(size, colored=True)
            first_move = random.choice([1,0])
            initial_state = gs.to_state(G, dim=gs.UNIV, to_move=first_move)
            train_data = mcts.self_play(initial_state, alpha_net, temp=TEMP, tmp_thrshld=TEMP_THRESH)
            training_batch.extend(train_data)
        
        
        #Once the training batch gets large enough, move to training the apprentice_net
        if len(training_batch) < MIN_REPLAY_TO_TRAIN:
            continue

        #Train
        #Before backpropagating the apprentice net, we take the training batch and we use a sample of symmetries
        #for each state.
        train_idx += 1
        sum_loss = 0.0
        sum_value_loss = 0.0
        sum_policy_loss = 0.0
        training_batch = symmetries(training_batch)
        np.random.shuffle(training_batch)

        while training_batch:
            batch = training_batch[:BATCH_SIZE]
            training_batch = training_batch[BATCH_SIZE:]
            batch_states, batch_probs, batch_values = zip(*batch)
            
            

            optimizer.zero_grad()
            states_v = torch.FloatTensor(batch_states)
            probs_v = torch.FloatTensor(batch_probs)
            values_v = torch.FloatTensor(batch_values)
            out_logits_v, out_values_v = apprentice_net(states_v)

            loss_policy_v, loss_value_v = loss(out_logits_v, out_values_v, probs_v, values_v)
            loss_v = loss_policy_v + loss_value_v
            loss_v.backward()
            optimizer.step()
            sum_loss += loss_v.item()
            sum_value_loss += loss_value_v.item()
            sum_policy_loss += loss_policy_v.item()

        #Evaluate
        #Every 100 times the apprentice_net has trained, we evaluate it against the alpha_net. If it 
        #beats the alpha_net by a rate better than BEST_NET_WIN_RATIO, we make it the new alpha_net.
        if train_idx % EVALUATE_EVERY_STEP == 0:
            alpha_net = model.Net(input_shape=model.OBS_SHAPE, actions_n=gs.UNIV)
            alpha_net.load_state_dict(torch.load(str(best_idx) + 'alpha_net.pt'))
            apprentice_better_than_alpha = evaluation(alpha_net, apprentice_net, num_plays=EVALUATION_ROUNDS, \
                                                      win_thrshld=BEST_NET_WIN_RATIO, temp=0)

            if apprentice_better_than_alpha[0]:
                print("Apprentice is better than current alpha, sync")
                best_idx += 1
                torch.save(apprentice_net.state_dict(), str(best_idx) + 'alpha_net.pt')
                alpha_net = apprentice_net

