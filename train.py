#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 22:59:39 2021

@author: Charles Petersen and Jamison Barsotti
"""
import random
import numpy as np

import gameState as gs 
import model, mcts
import randomUpDown as rud

import torch
import torch.optim as optim
import torch.nn.functional as F

device = 'cuda' if torch.cuda.is_available() else 'cpu'

def symmetries(train_data, dim = gs.UNIV, num_samples=10):
    '''Returns 'num_samples' symmetries of each example in 'train_data'.
    (A reindexing of node labels in any upset-downset game provides a
     symmetry of the gameboard.)
    
    Parameters
    ----------
    train_data : list
        a list of triples: state, policy and value for training from self-play.
    dim : int (nonnegative), optional
        must be at least as large as the number of nodes in 'game'. 
        The default is UNIV.
    num : int (nonnegative), optional
        The number of symmetries to take (sampled w/ repitition).
        The default is 10.

    Returns
    -------
    sym_train_data : list
        'num_samples' symmetries of 'train_batch'.

    ''' 
    sym_train_data = []
    
    for train_triple in train_data:
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

def evaluation(alpha_net, apprentice_net, device, num_nodes = gs.UNIV, 
               num_plays=400, search_iters=800, win_thrshld=0.55, temp = 0):
    '''Plays 'num_plays' games of randomly generated upset-downset games
    of size 'num'nodes' between 'alpha_net' and 'apprentice_net'. Returns 
    wether 'apprentice_net' won at least 'win_thrshld' percentage of the games.
    
    Parameters
    ----------
    alpha_net : UpDownNet
        The current best model.
    apprentice_net : UpDownNet
        the model currently training.
    num_nodes : int, optional
        the number of nodes in each game played during evaluation. The default
        is gs.UNIV.
    num_plays : int (nonnegative), optional
        the number of games to play during evaluation. The default is 400.
    search_iters : int (nonnegative), optional
        the number of iteratins of  MCTS to be performed for each turn. 
        The default is 800.
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
    # track the models
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
        G = rud.RandomGame(num_nodes, RGB=True)
        cur_state = gs.to_state(G, to_move = up_or_down)
        cur_net = net_to_start
        move_count = 0
        winner = None
        while not gs.is_terminal_state(cur_state):
            root = mcts.PUCTNode(cur_state)
            if cur_net == alpha:
                mcts.MCTS(
                    root, 
                    alpha_net, 
                    device, 
                    num_iters=search_iters)
            else:
                mcts.MCTS(
                    root, 
                    apprentice_net, 
                    device, 
                    num_iters=search_iters)
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
    
def approx_outcome(game, apprentice_net, device):
    ''' Returns the predicted outcome of 'game' from the apprentice model.

    Parameters
    ----------
    game : UpDown
        a game of upset-downset.
    apprentice_net : UpDownNet
        the model currently training. 
    device : str, optional
        the device to run the model on. 'cuda' if available, else 'cpu'.

    Returns
    -------
    aprx_out : str
        the outcome of 'game' as predicetd by the model:
        'Next', Next player (first player to move) wins.
        'Previous', Previous player (second player to move) wins.
        'Up', Up can force a win. (Playing first or second.) 
        'Down', Down can force a win. (Playing first or second.)
        
    '''
    
    aprx_out = None
    N, P, L, R = 'Next', 'Previous', 'Up', 'Down'
    
    # game state from each players perspective
    up_state = gs.to_state(game, to_move=gs.UP)
    down_state = gs.to_state(game, to_move=gs.DOWN)
    
    # get value from net from Ups perspective
    encoded_up_state = torch.from_numpy(
                up_state).float().reshape(1, 4, gs.UNIV, gs.UNIV).to(device)
    _, up_value = apprentice_net(encoded_up_state)
    up_value = up_value.item()
    
    # get value from net from downs perspective
    encoded_down_state = torch.from_numpy(
                down_state).float().reshape(1, 4, gs.UNIV, gs.UNIV).to(device)
    _, down_value = apprentice_net(encoded_down_state)
    down_value = down_value.item()
    
    # determine the approximate outcome
    if up_value > 0 and down_value > 0:
        aprx_out = N
    elif up_value > 0 and down_value < 0:
        aprx_out = L
    elif up_value < 0 and down_value < 0:
        aprx_out = P
    elif up_value < 0 and down_value > 0:
        aprx_out = R
        
    return aprx_out
        
def train(alpha_net=None,
          BATCH_SIZE=100,
          PLAY_EPISODES=20,
          MCTS_SEARCHES=800,
          NUM_SYMMETRIES=10,
          LEARNING_RATE=0.1,
          MOMENTUM=0.9,
          MIN_DATA_TO_TRAIN=100,
          BEST_NET_WIN_RATIO=0.54,
          EVALUATE_EVERY_STEP=1,
          EVALUATION_ROUNDS=10,
          TEMP=1,
          TEMP_THRESH=2,
          NUM_UPDATES = np.inf):
    '''
    Trains the apprentice_net using the alpha_net with respect to loss. 
    Builds on experience by updating the alpha_net once the apprentice_net
    beats it at a BEST_NET_WIN_RATIO rate.
    
    If using apprentice_net or alpha_net, these should Nets (see model.py module).
    Function will initialize these nets if none are given.
    
    The other variables are various (hyper)parameters.
    '''

    # initialize the nets
    print("Initializing nets...")
    if alpha_net == None:
        alpha_net = model.UpDownNet(
            input_shape=gs.STATE_SHAPE,
            actions_n=gs.UNIV).to(device)
        torch.save(alpha_net.state_dict(), '0alpha_net.pt')
    else:
        alpha_net = alpha_net
        torch.save(alpha_net.state_dict(), '0alpha_net.pt')
        print("Alpha Net loaded...")
    # initialize the apprentice net
    apprentice_net = model.UpDownNet(
        input_shape=gs.STATE_SHAPE,
        actions_n=gs.UNIV).to(device)
    apprentice_net.load_state_dict(torch.load('0alpha_net.pt'))

    # initialize the optimizer
    optimizer = optim.SGD(
        apprentice_net.parameters(),
        lr=LEARNING_RATE,
        momentum=MOMENTUM)
    
    # initialize list to store the data generated by 
    # alpha_net during self-play, track the number of times 
    # we've trained on 
    train_data = []
    train_idx = 0
    best_idx = 0
    self_plays = 0
    
    print("starting play, train, eval loop on ", device,'...')
    # train until the alpha_net has been updated 
    # NUM_UPDATES times.
    while best_idx < NUM_UPDATES:
        
        # generate training data for training the apprentice_net 
        # from the alpha_net.
        for _ in range(PLAY_EPISODES):
            print('self-play : ', self_plays)
            size = random.randint(1, gs.UNIV)
            G = rud.RandomGame(size, RGB=True)
            first_move = random.choice([gs.UP, gs.DOWN])
            initial_state = gs.to_state(G, dim=gs.UNIV, to_move=first_move)
            self_play_data = mcts.self_play(
                initial_state, 
                alpha_net, 
                device, 
                search_iters=MCTS_SEARCHES,
                temp=TEMP, 
                tmp_thrshld=TEMP_THRESH)
            train_data.extend(self_play_data)
            
            self_plays +=1
           
        # once the amount of training data gets large enough
        # train the apprentice_net
        if len(train_data) < MIN_DATA_TO_TRAIN:
            print('training data : ' , len(train_data))
            continue
        
        print("Getting symmetries...")
        # get NUM_SYMMETRIES of symmetries of the training 
        # data and shuffle 
        train_data = symmetries(train_data, num_samples=NUM_SYMMETRIES)
        np.random.shuffle(train_data)
        
        print("Training...")
        # train the apprentice net
        while train_data:
            print("taraining step : ", train_idx)
            # get training batch
            batch = train_data[:BATCH_SIZE]
            train_data = train_data[BATCH_SIZE:]
            batch_states, batch_probs, batch_values = zip(*batch)
            
            # query the apprentice net
            optimizer.zero_grad()
            states = torch.FloatTensor(batch_states).to(device)
            probs = torch.FloatTensor(batch_probs).to(device)
            values = torch.FloatTensor(batch_values).to(device)
            out_logits, out_values = apprentice_net(states)
            
            # train appremntice net
            loss_value = F.mse_loss(out_values.squeeze(-1), values)
            loss_policy = -F.log_softmax(out_logits, dim=1) * probs
            loss_policy = loss_policy.sum(dim=1).mean()
            loss = loss_policy + loss_value
            
            print('loss : ', loss)
            
            loss.backward()
            optimizer.step()
        
        train_idx += 1
        
        # after each completion of EVALUATE_EVERY STEP training rounds we 
        # evaluate the apprentice net against the alpha_net. If the apprentice 
        # net wins more than BEST_NET_WIN_RATIO percentage of the games 
        # we update the alpha_net.
        if train_idx % EVALUATE_EVERY_STEP == 0:
            print("Evaluating nets...")
            
            better_than_alpha = evaluation(
                alpha_net, 
                apprentice_net,
                device=device,
                num_plays=EVALUATION_ROUNDS,
                search_iters=MCTS_SEARCHES,
                win_thrshld=BEST_NET_WIN_RATIO, 
                temp=0)
            
            if better_than_alpha[0]:
                
                print("Apprentice is better than current alpha, sync")
                
                #update alpha net
                torch.save(apprentice_net.state_dict(), 
                           str(best_idx) + 'alpha_net.pt')              
                alpha_net.load_state_dict(
                    torch.load(str(best_idx) + 'alpha_net.pt'))
                
                best_idx += 1
                
            score = 0
            for _ in range(EVALUATION_ROUNDS):
                size = size = random.randint(1, gs.UNIV)
                G = rud.RandomGame(size, RGB=True)
                true_outcome = G.outcome()
                approximate_outcome = approx_outcome(G, apprentice_net, device)
                if true_outcome == approximate_outcome:
                    score +=1
            print('accuracy : ', score/EVALUATION_ROUNDS)
                

