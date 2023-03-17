import argparse
import json
import heapq
from collections import Counter, defaultdict, namedtuple

parser = argparse.ArgumentParser(description='Encode or decode a string using Huffman and LZ77 encoding.')
parser.add_argument('action', choices=['encode', 'decode'], help='specify whether to encode or decode a string')
parser.add_argument('string', help='the string to encode or decode')
args = parser.parse_args()

if args.action != 'encode':
    print("Error: Only 'encode' action is currently supported.")
    exit()

input_str = args.string

# Define a named tuple to represent each node in the Huffman tree
Node = namedtuple('Node', ['freq', 'symbol', 'left', 'right'])

heap = []

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

# Read in the input string from the command line
parser = argparse.ArgumentParser(description='Encode or decode a string using Huffman and LZ77 encoding.')
parser.add_argument('input_str', metavar='input_str', type=str, help='the input string to encode or decode')
args = parser.parse_args()
input_str = args.input_str

# Calculate the Huffman codebook
codebook = huffman_codebook(input_str)

# Encode the input string using the Huffman codebook
encoded_text = ''
for c in input_str:
    if ord(c) < 128:
        encoded_text += codebook[c]
    else:
        encoded_text += '{0:b}'.format(ord(c)).zfill(8)

# Apply LZ77 encoding to the Huffman-encoded string
lz77_encoded_text = encode_lz77(encoded_text)

# Print the results
print("Input string:", input_str)
print("Huffman-encoded string:", encoded_text)
print("LZ77-encoded string:", lz77_encoded_text)

# Allow the user to optionally decode the Huffman and LZ77-encoded strings
if len(sys.argv) > 2 and sys.argv[2] == 'decode':
    # Decode the LZ77-encoded string
    decoded_lz77_text = decode_lz77(lz77_encoded_text)

    # Decode the Huffman-encoded string
    decoded_huffman_text = huffman_decode(encoded_text, codebook
