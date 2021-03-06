"""
@author: Charles Petersen and Jamison Barsotti
"""

import digraph 
from upDownPlot import UpDownPlot
import random                                              
import matplotlib.pyplot as plt
from IPython.display import clear_output
import time

class UpDown(object):
    ''' Abstract class for construction of an upset-downset game from a 
    directed acyclic graph with blue-green-red node coloring. 
    '''
    def __init__(self, dag, coloring=None, reduced=False):
        '''
        Parameters
        ----------
        dag : dict
            djacecny representation of a directed acyclic graph. 
            (Adjacecny lists keyed by node.) Nodes are to be labelled by
            nonnegative integers. All nodes must be a key in the dict. If a 
            node is a sink, its value is to be an empty list.
        coloring : dict, optional
            a coloring of the nodes of 'dag': color keyed by node.
            (The colors are 1 (resp. 0,-1) for blue (resp. green, red).
            If no coloring is given all nodes will be colored green. 
            The default is None.
        reduced : bool, optional
            if True, it is assumed that 'dag' is acyclic and 
            transitively reduced. Otherwise, 'dag' will be checked for cycles 
            and transitvely reduced. The default is False.

        Returns
        -------
        None.

        '''
        if reduced is False:
            assert digraph.is_acyclic(dag), 'Check the dag. There is a cycle.'
            self.dag = digraph.transitive_reduction(dag)
        else:
            self.dag = dag
        if coloring is None:
            self.coloring = {x:0 for x in self.dag}
        else:
            self.coloring = coloring
        self._layout = None
        
    @property
    def layout(self):
        if self._layout is None:
            self._layout = digraph.hasse_layout(self.dag)
        return self._layout
    
    @layout.setter
    def layout(self, x):
        self._layout = x
        
##############################################################################
################################## COLORING ###################################
##############################################################################
    
    def up_nodes(self):
        ''' Returns all blue/green nodes.
        
        Returns
        -------
        list
            all blue/green nodes.

        '''
        return list(filter(lambda x : self.coloring[x] in {0,1}, self.dag))
    
    def down_nodes(self):
        '''Returns all red/green nodes
        
        Returns
        -------
        list
            all red/green nodes

        '''
        return list(filter(lambda x : self.coloring[x] in {-1,0}, self.dag)) 
               
    def color_sum(self):
        '''Returns the sum over all node colors.
        
        Returns
        -------
        int
            the sum the colors over all nodes.

        '''
        return sum(self.coloring.values())
        
##############################################################################
##################################   MOVES  ###################################
##############################################################################

    def upset(self, x):
        '''Returns the upset of node 'x'.
        
        Parameters
        ----------
        x : int (nonnegative)
            node 

        Returns
        -------
        upset : list
            all nodes reachable from 'x', including 'x' itself. 

        '''
        upset = digraph.descendants(self.dag, x)
        upset.append(x)
        
        return upset
    
    def downset(self, x):
        '''Returns the downset of node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node

        Returns
        -------
        downset : list
            all nodes having a path to node 'x', including node 'x' itself.

        '''
        downset = digraph.ancestors(self.dag, x)
        downset.append(x)
        
        return downset

    def up_play(self, x):
        '''Returns the upset-downset game left after Up plays node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node having color blue or green.

        Returns
        -------
        UpDown
            the upset-downset game left after Up plays node 'x'.

        '''
        assert x in self.up_nodes()
        option_nodes = list(set(self.dag) - set(self.upset(x)))
        option_coloring = {node: color for node, color in 
                           self.coloring.items() if node in option_nodes}
        option_dag = digraph.subgraph(self.dag, option_nodes) 
        option = UpDown(option_dag, option_coloring, reduced=True)
        option.layout = {x: self.layout[x] for x in option_nodes}
        
        return option
    
    def down_play(self, x):
        '''Returns the upset-downset game left after Down plays node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node having color red or green.

        Returns
        -------
        UpDown
            the upset-downset game left after Down plays node 'x'

        '''
        assert x in self.down_nodes()
        option_nodes = list(set(self.dag) - set(self.downset(x)))
        option_coloring = {node: color for node, color in 
                           self.coloring.items() if node in option_nodes}
        option_dag = digraph.subgraph(self.dag, option_nodes) 
        option = UpDown(option_dag, option_coloring, reduced=True)
        option.layout = {x: self.layout[x] for x in option_nodes}
        
        return UpDown(option_dag, option_coloring, reduced=True)
           
              
##############################################################################    
###############################   PLOT  ######################################
##############################################################################
    
    def plot(self, save=None, marker = 'o'):
        '''Plots the game.

        Parameters
        ----------
        marker : matplotlib marker, optional
            the marker is the node style for the game plot. The default is 'o'.
            for all options: https://matplotlib.org/3.3.3/api/markers_api.html.
        save : str, optional
            If youd like to save the plot of your game put the path to the file
            here: save='/the/path/to/your/game/plot'. The default is None

        Returns
        -------
        None.

        '''
        UpDownPlot(self, marker=marker)
        if save:
            plt.savefig(save, bbox_inches='tight', transparent=True)
        plt.show()
    
##############################################################################    
########################### GAMEPLAY #########################################
##############################################################################
    
    def play(self, agent1= None, agent2=None, marker='o'):
        ''' Interactively play the game.
        
        Parameters
        ----------
        agent1 : Agent, optional
            can play against an Agent or have two Agents play against 
            one another. The default is None. (agent1 will always play first.)
        agent2 : Agent, optional
            can play ageainst an Agent or have two Agents play against 
            one another. The default is None. (agent2 will always play second.)
        marker : matplotlib marker, optional
            the marker is the node style for the game plot. The default is 'o'.
            for all options: https://matplotlib.org/3.3.3/api/markers_api.html

        Returns
        -------
        None.
        '''
        initl_pos = self
        
        # who plays first
        players = ['up', 'down']
        if agent1 == None or agent2 == None:
            first = input("Which player will start, 'Up' or 'Down'? ")       
            while first.casefold() not in players:
                first = input("Please choose 'Up' or 'Down'! ")
        else:
            first = random.choice(players)
            print(f'{first.casefold().capitalize()}, will play first.')
        first = first.casefold()
        players.remove(first)
        second = players[0]
        
        # need to keep track of nodes colorws for each player
        if first == 'up':
            first_colors, second_colors = {0,1}, {-1,0}
        else:
            first_colors, second_colors = {-1,0}, {0,1}
        
        # initialize the figure.
        # fig_info contains various dicts that point to specific
        # objects in our figure. These are used to remove
        # these objects from the figure as the game progresses
        clear_output(wait=True)
        board = UpDownPlot(initl_pos, marker=marker)                     
        plt.pause(0.01)
    
        # play. The general theme is while the game still has nodes:
        # - if either player no longer has any moves, end.
        # - allow player to choose a valid node
        # - update game/figure to reflect players choice
        # - change player to turn
        # - repeat
        cur_pos = initl_pos
        cur_player = first
        choice_dict = {'up': ' Blue or Green', 'down': ' Red or Green'}
        
        while cur_pos.dag:
            
            # players can only choose nodes of their allowed colors.
            first_options = list(
                filter(
                    lambda x : cur_pos.coloring[x]in first_colors,
                    cur_pos.dag
                    )
                )            
            second_options = list(
                filter(
                    lambda x : cur_pos.coloring[x] in second_colors, 
                    cur_pos.dag
                    )
                )     
            options_dict = {first: first_options, second: second_options}
            
            # if either player has no valid moves the 
            # game will end and the player with the player w/ valid moves 
            # remaining will be declared the winner. Note, cannot be inside 
            # gameplay loop and have both both players have no valid moves.
            if not first_options:
                cur_player = first
                break
            if not second_options:
                cur_player = second
                break
                      
            if cur_player == first and agent1 != None:
                u = agent1.predict_next_move(cur_pos, cur_player, 100)
                print(f'The Agent choose {str(u)}')
                time.sleep(1.5)
            elif cur_player == second and agent2 != None:
                u = agent2.predict_next_move(cur_pos, cur_player, 100)
                print(f'The Agent choose {str(u)}')
                time.sleep(1.5)
            else:
                u = int(input(f'{cur_player.capitalize()}, choose a node: '))
                while not (u in options_dict[cur_player]):
                    print(u, " is not a valid choice.")
                    u = int(
                        input(f'{cur_player.capitalize()},'\
                              f' choose a {choice_dict[cur_player]},'\
                              ' node: '))
                    
            if cur_player == 'up':
                cur_pos = cur_pos.up_play(u)
            else:
                cur_pos = cur_pos.down_play(u) 
                
            clear_output(wait=True)
            board = UpDownPlot(initl_pos, marker=marker) 
            board.leave_subgraph_fig(cur_pos)
            plt.pause(1)
            
            if cur_player == 'up':
                cur_player = 'down'
            else:
                cur_player = 'up'

        # declare the winner based on what value player token was at
        # when game ended.
        if cur_player == 'up':
            cur_player = 'down'
        else:
            cur_player = 'up'
            
        print(f'\n {cur_player.capitalize()} wins!')
        plt.pause(1)
        
##############################################################################    
########### UPDOWNS PARTIALLY ORDERED ABELIAN GROUP STRUCTURE ################
##############################################################################
    
    def outcome(self):
        ''' Returns the outcome of the game. (Due to the possibly huge number 
        of suboptions, for all but relitively small games, this algorithm is 
        extremely slow.)
        
        Returns
        -------
        str
            'Next', Next player (first player to move) wins.
            'Previous', Previous player (second player to move) wins.
            'Up', Up can force a win. (Playing first or second). 
            'Down', Down can force a win. (Playing first or second). 

        '''
        def get_outcome(G, nodes, memo):
            num_nodes = len(G)
            num_edges = digraph.number_of_edges(G.dag)
            color_sum = G.color_sum()
            # possible outcomes
            N, P, L, R = 'Next', 'Previous', 'Up', 'Down'
            # base cases/heuristics for recursion (no nodes or no edges):
            # no nodes, second player win.
            if num_nodes == 0:
                out = P
            # nonzero # of nodes and all are blue,  Up wins.
            elif color_sum == num_nodes:
                out = L
            # nozero # of nodes and all are red,  Down wins.
            elif color_sum == -num_nodes:
               out = R
            # nonzero # of nodes, but no edges:
            elif num_edges == 0:
                if color_sum == 0:
                    # no edges, equal # of blue and red nodes, even # of 
                    # nodes, second player win.
                    if num_nodes%2 == 0:
                        out = P
                    # no edges, equal # of blue and red nodes, odd # of 
                    # nodes, second player win.
                    else:
                        out = N
                # no edges, more blue nodes than red, Up wins
                elif color_sum > 0:
                    out = L
                # no edges, more red nodes than blue, Down wins
                else:
                    out = R
            # w/ memoization, recursively find outcome of all of G's options.
            else:
                # store outcomes of G's options:
                up_outcomes = set()
                down_outcomes = set()
                # determine the outcome of all of G's options:
                for x in G.up_nodes():
                    GL = G.up_play(x)
                    GLnodes = frozenset(GL.dag)
                    GLout = outcomes_store[GLnodes] if GLnodes in \
                        outcomes_store else \
                            get_outcome(GL, GLnodes, outcomes_store)
                    up_outcomes.add(GLout)
                    del GL
                for x in G.down_nodes():
                    GR = G.down_play(x)
                    GRnodes = frozenset(GR.dag)
                    GRout = outcomes_store[GRnodes] if GRnodes in \
                        outcomes_store else \
                            get_outcome(GR, GRnodes, outcomes_store)
                    down_outcomes.add(GRout)
                    del GR
                # determine outcome of G via the outcomes of the options:
                # first player to move wins
                if ({P, L} & up_outcomes) and ({P,R} & down_outcomes):
                    out = N
                # second player to move wins
                elif not ({P, L} & up_outcomes) and not ({P, R} & down_outcomes):
                    out = P
                # up wins no matter who moves first
                elif ({P, L} & up_outcomes) and not ({P,R} & down_outcomes):
                    out = L
                # down wins no matter who moves first
                elif not ({P, L} & up_outcomes)  and ({P,R} & down_outcomes):
                    out = R
            # memoize the outcome
            outcomes_store[nodes] = out
           
            return out
            
        # store nodes of the game to a hashable object
        nodes = frozenset(self.dag)
        # recursively find the outcome of the game by determining 
        # the outcome of each of the games options (and memoizing).
        outcomes_store = {}
        
        return get_outcome(self, nodes, outcomes_store)
    
    def __neg__(self):                
        '''Returns the negative of the game. 
    
        Returns
        -------
        UpDown
            the upset-downset game on the reverse directed acyclic graph
            and opposite coloring.

        '''
        # get reversed graph and inverted coloring
        dual = digraph.reverse(self.dag)
        reverse_coloring = {x: -self.coloring[x] for x in self.dag}
        # get layout of the negative
        components = digraph.connected_components(self.dag)
        levels_dict = digraph.longest_path_lengths(
            self.dag, 
            direction = 'incoming'
            )
        flipped_layout = {}
        for component in components:
            height = max(levels_dict[x] for x in component)
            flipped_layout.update(
                {x: (self.layout[x][0], 
                     height-self.layout[x][1]) for x in component}
                ) 
        # instantiate game and set layout
        negative = UpDown(dual, reverse_coloring, reduced=True)
        negative.layout = flipped_layout
        
        return negative

    def __add__(self, other):              
        '''Returns the (disjunctive) sum of games. **Relabels elements in 'other'
        to consecutive nonnegative integers starting from len('self').
        
        Parameters
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        UpDown
            The upset-downset game on the disjoint union of directed acyclic 
            graphs with unchanged colorings.
            
        Note: the sum retains all nodes ('other' being relabelled), edges 
            and coloring from both 'self' and 'other' with no new edges added 
            between 'self' and 'other'

        '''
        # initialze dag in sum and update with selfs relations
        sum_dag = {}
        sum_dag.update(self.dag)
        # initialze coloring in sum and update with selfs relations
        sum_coloring = {}
        sum_coloring.update(self.coloring)
        # relabelling for other.
        n = len(self)
        # relabel other
        relabel_map = {i : i+n for i in other.dag}
        other_relabel = digraph.relabel(other.dag, relabel_map)
        # update dag in sum with others nodes/edges
        sum_dag.update(other_relabel)
        # update coloring of sum with others colors
        for x in relabel_map:
            y = relabel_map[x]
            sum_coloring[y] = other.coloring[x]
        # get the layout of the sum
        largest_x = max(x[0] for x in self.layout.values())
        sum_layout = {x:self.layout[x] for x in self.dag}
        sum_layout.update(
            {relabel_map[x]: (other.layout[x][0]+largest_x, 
                 other.layout[x][1]) for x in other.dag}
                 )
        # instantiate the game and set the layout
        sum_game = UpDown(sum_dag, sum_coloring, reduced=True)
        sum_game.layout = sum_layout
        
        return sum_game
    
    def __sub__(self, other):
        ''' Returns the difference of games.
    
        Parameters
        ----------
        other : UpDown
            a game of upset-downset

        Returns
        -------
        UpDown
            the upset-downset game on the disjoint union of the directed 
            acyclic graph of 'self' with unchanged coloring and the reverse
            of the the directed acyclic graph of 'other' with the opposite 
            coloring.

        '''
        return self + (-other)
    
    def __eq__(self, other):
        ''' Returns wether the games are equal. (Depends on the outcome 
        method.)

        Parameters
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        bool
            True if the games 'self' and 'other' are equal (their differecne 
            is a second player win) and False otherwise.

        '''
        return (self - other).outcome() == 'Previous'
    
    def __or__(self, other):
        ''' Returns wether games are incomparable (fuzzy). (Depends on the 
        outcome method.)

        Parameters     
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        bool
            True if the games 'self' and 'other' are fuzzy (their difference 
            is a first player win) and False otherwise.
        '''
        return (self - other).outcome == 'Next'

    def __gt__(self, other):
        ''' Returns wether games are comparable in specified order. (Depends 
        on the outcome method.)

        Parameters
        ----------
        other : UpDown 
            a game of upset-downset.

        Returns
        -------
        bool
            True if 'self' is greater than 'other' (better for Up: their 
            differnce is a win for Up) and False otherwise.

        '''
        return (self - other).outcome() == 'Up'
    
    def __lt__(self, other):
        ''' Returns wether games are comparable in specified order. ** Depends 
        on the outcome method.

        Parameters
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        bool
            True if 'self' is less than 'other' (better for Down: their 
            differnce is a win for Down) and False otherwise.

        '''
        return (self - other).outcome() == 'Down'
    
    def __len__(self):
        ''' Returns the number of nodes.
        Returns
        -------
        int (nonnegative)
            the number of nodes.

        '''
        return len(self.dag)
    

###############################################################################
######################### NEW GAMES FROM OLD ##################################
##############################################################################
    

    def __truediv__(self, other):          
        ''' Returns the ordinal sum of games. (This is not a commutative 
        operation). Relabels all elements of 'self' with consecutive 
        nonnegative integers starting from len('other').
        
        Parameters
        ----------      
        other: UpDown
            a gme of upset-downset.

        Returns
        -------
        UpDown
            The ordinal sum retains all nodes ('self' relabelled), edges,
            and coloring from both 'self' and 'other' and adds an edge 
            from each sink of 'other' to every source of 'self'.

        '''
        # initialze dag for ordinal sum and update with nodes/edges in other
        ordinal_dag= {}
        for x in other.dag:
            ordinal_dag[x] = []
            for y in other.dag[x]:
                ordinal_dag[x].append(y)
        # initialize coloring in ordinal sum and update with others coloring.
        ordinal_coloring = {}
        ordinal_coloring.update(other.coloring)
        # relabel self
        n = len(other)
        relabel_map = {i : i+n for i in self.dag}
        self_relabel = digraph.relabel(self.dag, relabel_map)
        # update dag in ordinal sum with selfs nodes/edges
        ordinal_dag.update(self_relabel)
        # update dag in ordinal sum with new edges between self 
        # and others sink and source nodes
        other_sinks = digraph.sinks(other.dag)
        self_sources = [relabel_map[x] for x in digraph.sources(self.dag)]
        for x in other_sinks:
            ordinal_dag[x].extend(self_sources)
        # update coloring of ordinal sum with selfs coloring
        self_colors = {relabel_map[x]: self.coloring[x] for x in \
                       self.dag}
        ordinal_coloring.update(self_colors)
        # get the layout of ordinal sum
        largest_y = max(x[0] for x in other.layout.values())
        ordinal_layout = {x:other.layout[x] for x in other.dag}
        ordinal_layout.update(
            {relabel_map[x]: (self.layout[x][0], 
                 self.layout[x][1]+largest_y+1) for x in self.dag}
                 )
        # instantiate the game and set the layout
        ordinal = UpDown(ordinal_dag, ordinal_coloring, reduced = True)
        ordinal.layout = ordinal_layout
        
        return ordinal
