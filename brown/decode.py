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
