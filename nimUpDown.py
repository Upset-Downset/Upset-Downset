"""
@author: Charles Petersen and Jamison Barsotti
"""
from upDown import UpDown
import digraph
import copy

def int_to_bin(n):
    ''' Returns the binary representation of the integer 'n'.
    
    Parameters
    ----------
    n : int

    Returns
    -------
    str
        binary representation of the integer 'n'.

    '''
    return bin(n).replace('0b', '')

def nim_dag(heaps):
    ''' Returns a directed acyclic graph corresonding to the Nim heaps, 
    'heaps'.
    
    Parameters
    ----------
    heaps : list
        positive ints, each representing the size of the corresponding 
        Nim heap.
    Returns
    -------
    dict
        adjacency representation of the directed acyclic graph (adjacency 
        lists keyed by node) corresponing to' heaps'. A disjoint union of
        directed acyclic graphs, one for each heap in 'heaps': each is 
        comprised of consecutively linked nodes.
        

    '''
    dag = {}
    node_count = 0
    for k in heaps:  
        heap = {j:[j+1] for j in range(node_count, node_count+k-1)}
        heap[node_count+k-1] = []
        dag.update(heap)
        node_count += k
        
    return dag

class NimGame(UpDown):
    ''' Subclass of UpDown for Nim games of upset-downset.
    '''
    def __init__(self, heaps):
        ''' Initializes an all green game of upset-downset on a disjoint union 
        of directed acyclic graphs, each comprised of consecutively linked 
        nodes. (Equivalent to a game of Nim!)
        
        Parameters
        ----------
        heaps : list 
            positive ints, each representing the size of the corresponding 
            Nim heap. 

        Returns
        -------
        None

        '''
        dag = nim_dag(heaps)
        UpDown.__init__(self, dag, reduced=True)
        self.heaps = heaps
        
    def up_play(self, x):
        '''returns the nim game of upset-downset left after Up plays node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node

        Returns
        -------
        NimGame
            the game after Up plays node 'x'.

        '''      
        # get the index of the heap containing node x in the list of heaps
        option_heaps = self.heaps.copy()
        nodes = sorted(list(self.dag))
        x_idx = nodes.index(x)
        x_heap_idx = 0
        heap_sum = 0
        while heap_sum <= x_idx:
            heap_sum += option_heaps[x_heap_idx]
            x_heap_idx += 1
        x_heap_idx -= 1
        
        # remove nodes from heap containing x and mutate list of 
        # heaps accordingly
        x_upset = self.upset(x)
        num_to_remove = len(x_upset)
        new_heap_size = option_heaps[x_heap_idx] - num_to_remove
        if new_heap_size > 0:
            option_heaps[x_heap_idx] = new_heap_size 
        else:
            del option_heaps[x_heap_idx]
            
        # instantiate option, relable nodes and set coloring
        option_nodes = sorted(list(set(nodes) - set(x_upset)))  
        option = NimGame(option_heaps)
        relabelling = {i: option_nodes[i] for i in range(len(option_nodes))}
        option.dag = digraph.relabel(option.dag, relabelling)
        option.coloring = {i:0 for i in option_nodes}
        option.layout = {i: self.layout[i] for i in option_nodes}
        
        return option
    
    def down_play(self, x):
        '''Returns the nim game of  upset-downset left after Down plays 
        node 'x'.

        Parameters
        ----------
        x : int (nonnegative)
            node

        Returns
        -------
        NimGame
            the game after Down plays node 'x'.

        '''
        # get the index of the heap containing node x in the list of heaps
        option_heaps = self.heaps.copy()
        nodes = sorted(list(self.dag))
        x_idx = nodes.index(x)
        x_heap_idx = 0
        heap_sum = 0
        while heap_sum <= x_idx:
            heap_sum += option_heaps[x_heap_idx]
            x_heap_idx += 1
        x_heap_idx -= 1
        
        # remove nodes from heap containing x
        x_downset = self.downset(x)
        num_to_remove = len(x_downset)
        new_heap_size = option_heaps[x_heap_idx] - num_to_remove
        if new_heap_size > 0:
            option_heaps[x_heap_idx] = new_heap_size 
        else:
            del option_heaps[x_heap_idx]
        
        # instantiate option, relable nodes and set coloring
        option_nodes = sorted(list(set(nodes) - set(x_downset))) 
        option = NimGame(option_heaps)
        relabelling = {i: option_nodes[i] for i in range(len(option_nodes))}
        option.dag = digraph.relabel(option.dag, relabelling)
        option.coloring = {i:0 for i in option_nodes}
        option.layout = {i: self.layout[i] for i in option_nodes}
        
        return option
               
    def nim_sum(self):
        ''' Returns the Nim sum of the heaps in the game.
        
        Returns
        -------
        nim_sum : int (nonnegative)
            to compute the NIM sum convert the heap sizes to binarty and sum them 
            without carrying!

        '''
        # write each heap size as binary string each having a common length.
        bin_heaps = [int_to_bin(heap) for heap in self.heaps]
        n = max(len(bin_heap) for bin_heap in bin_heaps)
        bin_heaps = [bin_heap.zfill(n) for bin_heap in bin_heaps]
        # convert binary strings to lists of bits
        bin_heaps = [list(bin_heap) for bin_heap in bin_heaps] 
        bin_heaps = [list(map(int,bin_heap)) for bin_heap in bin_heaps]
        # compute teh nim sum
        _nim_sum = 0
        for i in range(n):
            digit = 0
            for bin_heap in bin_heaps:
                digit = (digit + bin_heap[-1-i]) % 2
            _nim_sum += digit*(2**i)
        return _nim_sum
    
    def outcome(self):
        ''' Returns the outcome of the game. Overloads outcome method from 
        UpDown class.
        -------
        str
            'Previous' if the game is a second player win, and 'Next' if the
            game is a first player win.
        '''        
        return 'Previous' if self.nim_sum() == 0 else 'Next'
    
    def __neg__(self):                
        '''Returns the negative of the nim game. (Since a game of nim is its 
        own negative a copy of 'self' is returned.)
    
        Returns
        -------
        NimGame
            the negative of the nim game of upset-downset.

        '''
        return copy.deepcopy(self)

    def __add__(self, other):              
        '''Returns the (disjunctive) sum of nim games of upset-dowmnset.
        . **Relabels elements in 'other to consecutive nonnegative integers
        starting from len('self'). If 'other' is also a nim game then the 
        sum will be too!
        
        Parameters
        ----------
        other : UpDown
            a game of upset-downset.

        Returns
        -------
        UpDown (NimGame)
            The upset-downset game on the disjoint union of directed acyclic 
            graphs with unchanged colorings.
            
        Note: the sum retains all nodes ('other' being relabelled), edges 
            and coloring from both 'self' and 'other' with no new edges added 
            between 'self' and 'other'

        '''
        if isinstance(other, NimGame):
            add_heaps = self.heaps + other.heaps
            return NimGame(add_heaps)
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
        UpDown (NimGame)
            the upset-downset game on the disjoint union of the directed 
            acyclic graph of 'self' with unchanged coloring and the reverse
            of the the directed acyclic graph of 'other' with the opposite 
            coloring.

        '''
        return self + (-other)
