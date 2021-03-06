"""
@author: Charles Petersen and Jamison Barsotti 
"""

from upDown import UpDown
import digraph

def complete_bipartite_dag(graphs):
    ''' Returns a directed acyclic graph corresponding to the complete 
    bipartite graphs, 'graphs'.
    
    Parameters
    ----------
    graphs : list
        ordered pairs of nonnegative integers 'm','n' each 
        representinting a distinct instance of the (horizontally-oriented) 
        complete bipartite  graph having 'm' nodes on top and 'n' nodes on 
        bottom.
        
    Returns
    -------
    dict
        adjacency representation of a directed graph (adjacency lists keyed 
        by node.) corresponding to 'graphs'. A disjoint union of directed 
        acyclic graphs, one for each graph in 'graphs': Each is a directed 
        (horizontally-oriented) complete bipartite graph with edges directed 
        from bottom nodes to top nodes. 

    '''
    dag = {}
    # update total number of nodes processed after each iteration
    last_count = 0  
    for graph in graphs:
        #determine relations for current graph 
        graph_rels = {}
        # number of elements on bottom and top
        bottom_count = graph[1]
        top_count = graph[0]
        # total number of elements in current graph
        count = top_count + bottom_count
        # label elements on top and bottom.
        bot_elems = [i for i in range(last_count, last_count + bottom_count)]
        top_elems = [i for i in 
                     range(last_count + bottom_count, last_count + count)]
        # edges amongst bottom and top nodes
        graph_rels.update({i: top_elems for i in bot_elems})
        graph_rels.update({i:[] for i in top_elems})
        # update before processing next graph
        dag.update(graph_rels)      
        last_count += count
        
    return dag


class CompleteBipartiteGame(UpDown):
    ''' Subclass of UpDown for games of upset-downset on disjoint unions of
    directed (horizontally-oriented) complete bipartite graphs.
    '''
    def __init__(self, graphs):
        ''' Initializes an all green game of upset-downset on a poset whose 
        Hasse diagram is a disjoint union of (horizontally-oriented) complete 
        bipartite graphs.
        
        Parameters
        ----------
        graphs : list
            ordered pairs (tuples or lists) of non-negative integers (m,n) each 
            representinting a distinct (horizontally-oriented) complete 
            bipartite having m nodes on top and n nodes on bottom.
            
        Returns
        -------
        None

        '''
        dag = complete_bipartite_dag(graphs)
        UpDown.__init__(self, dag, reduced = True)
        self.graphs = graphs
        
        
    def up_play(self, x):
        '''returns the complete bipartite game of upset-downset 
        left after Up plays node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node

        Returns
        -------
        CompleteBipartiteGame
            the game after Up plays node 'x'.

        '''
        # get the index of the graph containing node x in the list of graphs 
        option_graphs = self.graphs.copy()
        nodes = sorted(list(self.dag))
        x_idx = nodes.index(x)
        x_graph_idx = 0
        num_nodes_before_x = 0
        while num_nodes_before_x <= x_idx:
            num_nodes_before_x += sum(option_graphs[x_graph_idx])
            x_graph_idx += 1
        x_graph_idx -= 1
        
        # remove nodes from graph containing x and mutate list of 
        # graphs accordingly
        x_upset = self.upset(x)
        num_to_remove = len(x_upset)        
        if num_to_remove > 1:
            option_m = 0
            option_n = option_graphs[x_graph_idx][1] - 1
        else:
            option_m = option_graphs[x_graph_idx][0] - 1
            option_n = option_graphs[x_graph_idx][1]
        graph = (option_m, option_n) 
        if option_m != 0 or option_n != 0:
            option_graphs[x_graph_idx] = graph
        else:
            del option_graphs[x_graph_idx]
            
        # instantiate option, relable nodes and set coloring
        # (I wish I had a cleaner idea for this, but im lazy...)
        option_nodes = sorted(list(set(nodes) - set(x_upset)))
        option = CompleteBipartiteGame(option_graphs)
        relabelling = {i: option_nodes[i] for i in range(len(option_nodes))}
        option.dag = digraph.relabel(option.dag, relabelling)
        option.coloring = {i:0 for i in option_nodes}
        option.layout = {i: self.layout[i] for i in option_nodes}
        
        return  option
    
    def down_play(self, x):
        '''Returns the complete bipartite game of upset-downset 
        left after Down plays node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node

        Returns
        -------
        CompleteBipartiteGame
            the game after Down plays node 'x'.

        '''
        # get the index of the graph containing node x in the list of graphs 
        option_graphs = self.graphs.copy()
        nodes = sorted(list(self.dag))
        x_idx = nodes.index(x)
        x_graph_idx = 0
        num_nodes_before_x = 0
        while num_nodes_before_x <= x_idx:
            num_nodes_before_x += sum(option_graphs[x_graph_idx])
            x_graph_idx += 1
        x_graph_idx -= 1
        
        # remove nodes from graph containing x and mutate list of 
        # graphs accordingly
        x_downset = self.downset(x)
        num_to_remove = len(x_downset)        
        if num_to_remove > 1:
            option_m = option_graphs[x_graph_idx][0] - 1
            option_n = 0
        else:
            option_m = option_graphs[x_graph_idx][0]
            option_n = option_graphs[x_graph_idx][1] - 1
        graph = (option_m, option_n) 
        if option_m != 0 or option_n != 0:
            option_graphs[x_graph_idx] = graph
        else:
            del option_graphs[x_graph_idx]
            
        # instantiate option, relable nodes and set coloring
        # (I wish I had a cleaner idea for this, but im lazy...)
        option_nodes = sorted(list(set(nodes) - set(x_downset)))
        option = CompleteBipartiteGame(option_graphs)
        relabelling = {i: option_nodes[i] for i in range(len(option_nodes))}
        option.dag = digraph.relabel(option.dag, relabelling)
        option.coloring = {i:0 for i in option_nodes}
        option.layout = {i: self.layout[i] for i in option_nodes}
        
        return  option
    
    def __neg__(self):                
        '''Returns the negative of the complete bipartite game of
        upset-downset.
    
        Returns
        -------
        CompletBipartiteGame
            the complete bipartite game of upset-downset on the reverse 
            directed acyclic graph.

        '''
        flipped_graphs = []
        for graph in self.graphs:
            flipped_graphs.append((graph[1],graph[0]))
        return CompleteBipartiteGame(flipped_graphs)

    def __add__(self, other):              
        '''Returns the (disjunctive) sum of games. **Relabels elements in 
        'other' to consecutive nonnegative integers starting from len('self').
        If 'other' is a complete bipartote game, then the sum will be too!
        
        Parameters
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        UpDown (CompleteBipartiteGame)
            The upset-downset game on the disjoint union of directed acyclic 
            graphs with unchanged colorings.
            
        Note: the sum retains all nodes ('other' being relabelled), edges 
            and coloring from both 'self' and 'other' with no new edges added 
            between 'self' and 'other'

        '''
        if isinstance(other, CompleteBipartiteGame):
            add_graphs = self.graphs + other.graphs
            return CompleteBipartiteGame(add_graphs)
        else:
            return super().__add__(other)
    
    def __sub__(self, other):
        ''' Returns the difference of games.
    
        Parameters
        ----------
        other : UpDown
            a game of upset-downset

        Returns
        -------
        UpDown (CompleteBipartiteGame)
            the upset-downset game on the disjoint union of the directed 
            acyclic graph of 'self' with unchanged coloring and the reverse
            of the the directed acyclic graph of 'other' with the opposite 
            coloring.

        '''
        return self + (-other)

            
