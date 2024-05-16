# RC4 cipher with vigenere-algorithm-enhanced PRGA
# 
# Inputs:
# - Plaintext/ciphertext as byte array
# - Key as byte array
# Output: Ciphertext as byte array
def rc4(text, key):

    # Initialise cipher byte array
    cipher = bytearray(text)

    # KSA
    # S array initialization
    S = [c for c in range(256)]
    # S array permutation
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    
    # PRGA
    i = 0
    j = 0
    for k in range(len(text)):
        i = (i+1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        t = (S[i] + S[j]) % 256
        u = S[t]
        v = key[t % len(key)] # Vigenere substitution
        w = (u + v) % 256 # Apply vigenere substitution
        cipher[k] = cipher[k] ^ w

    return cipher

# Demo
if __name__ == '__main__':
    from binascii import hexlify
    plain = bytearray("Plaintext",'utf-8')
    key = bytes("Key",'utf-8')
    enc = rc4(plain,key)
    print(enc.hex().upper())
    print(hexlify(plain).decode('ascii').upper())
    cipher = "6674A3935EED709354"
    dec = bytes.fromhex(cipher)
    print(rc4(dec,key).decode())
    print(rc4(enc,key).decode())
    import sys
    if len(sys.argv) > 1:
        f = open(sys.argv[1], 'rb')
        plain = memoryview(f.read())
        enc = rc4(plain,key)
        fe = open("enc.jpg","wb")
        fe.write(enc)
        fe.close()
        f.close()
        f = open("enc.jpg","rb")
        cipher = memoryview(f.read())
        dec = rc4(cipher,key)
        fd = open("dec.jpg","wb")
        fd.write(dec)
        fd.close()
        f.close()
