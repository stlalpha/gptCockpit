import os
import heapq
import json
from collections import Counter, namedtuple
from collections import defaultdict


# Define a named tuple to represent each node in the Huffman tree
Node = namedtuple('Node', ['freq', 'symbol', 'left', 'right'])

def huffman_codebook(text):
    # Count the frequency of each symbol in the text
    freqs = defaultdict(int)
    for c in text:
        if ord(c) < 128:
            freqs[c] += 1

    # Use a heap to efficiently combine nodes with the lowest frequency
    heap = [Node(freq, sym, None, None) for sym, freq in freqs.items()]
    heapq.heapify(heap)

    # Combine nodes until there is only one root node remaining
    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        parent = Node(node1.freq + node2.freq, None, node1, node2)
        heapq.heappush(heap, parent)

    # Traverse the Huffman tree to generate the codebook
    codebook = {}
    def traverse(node, code):
        if node.symbol is not None:
            codebook[node.symbol] = code
        else:
            traverse(node.left, code + '0')
            traverse(node.right, code + '1')

    root = heap[0]
    traverse(root, '')

    return codebook

# Read in the contents of the sample file
with open('bigfile.txt', 'r') as f:
    text = f.read()

    # Calculate the Huffman codebook
    codebook = huffman_codebook(text)

    # Print the codebook as valid JSON
    json_codebook = json.dumps(codebook)
    print("Codebook:")
    print(json_codebook)
