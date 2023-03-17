import json

def huffman_decode(encoded_str, codebook_file):
    # Read the codebook from the JSON file
    with open(codebook_file, 'r') as f:
        codebook = json.load(f)

    # Invert the codebook so that codes map to symbols
    inv_codebook = {v: k for k, v in codebook.items()}

    # Decode the Huffman-encoded string
    decoded_str = ''
    code = ''
    for bit in encoded_str:
        code += bit
        if code in inv_codebook:
            decoded_str += inv_codebook[code]
            code = ''

    return decoded_str

encoded_str = '101011110110001011001101111101101011110111101100100111001101110101111011001100011110101111101100011111011010110010011100110111010111101100011111011010110010011100110111010111101100011111011010110010011100110111010111101100011111011010110010011100110111010111101100011111011010110010011100110111010111101100011111011010110010011100110111010111101101'
codebook_file = 'thecodebook.json'
decoded_str = huffman_decode(encoded_str, codebook_file)
print(decoded_str)
