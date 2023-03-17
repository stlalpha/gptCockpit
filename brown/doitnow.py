import os
import heapq
import json
import sys
from collections import Counter, defaultdict, namedtuple


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


def huffman_encode(text, codebook):
    # Encode the text using the provided codebook
    encoded_text = ""
    for c in text:
        if c in codebook:
            encoded_text += codebook[c]
        else:
            print(f"Error: {c} not in codebook")
            return None

    return encoded_text


def huffman_decode(encoded_text, codebook):
    # Invert the codebook to map from codes to symbols
    inv_codebook = {v: k for k, v in codebook.items()}

    # Decode the encoded text using the inverted codebook
    decoded_text = ""
    code = ""
    for bit in encoded_text:
        code += bit
        if code in inv_codebook:
            decoded_text += inv_codebook[code]
            code = ""

    return decoded_text


def main():
    # Read in the contents of the sample file
    if len(sys.argv) < 3:
        print("Usage: python huffman.py <codebook_file> <text_to_encode>")
        return

    with open(sys.argv[1], 'r') as f:
        codebook = json.load(f)

    # Encode the input text using the codebook
    encoded_text = huffman_encode(sys.argv[2], codebook)
    if encoded_text is None:
        return

    print(f"Encoded text: {encoded_text}")

    # Decode the encoded text using the codebook
    decoded_text = huffman_decode(encoded_text, codebook)
    print(f"Decoded text: {decoded_text}")


if __name__ == "__main__":
    main()

