# generate key pair
import random
import base64
import struct

def isprime(n):
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def generate_prime_number():
    while True:
        # generate random number between 10000 and 50000
        p = random.randint(10000, 20000)
        if isprime(p):
            return p

def generate_key_pair():
    # generate prime number p and q
    p = generate_prime_number()
    q = generate_prime_number()
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537 # public exponent
    # d = e^(-1) mod phi
    d = pow(e, -1, phi)
    public_key = (e, n)
    private_key = (d, n)
    return public_key, private_key

def save_key_pair(public_key, private_key):
    public_file = open('public_key.pub', 'w')
    private_file = open('private_key.pri', 'w')
    public_file.write(str(public_key))
    private_file.write(str(private_key))
    public_file.close()
    private_file.close()

def load_key_pair():
    public_file = open('public_key.pub', 'r')
    private_file = open('private_key.pri', 'r')
    public_key = eval(public_file.read())
    private_key = eval(private_file.read())
    public_file.close()
    private_file.close()
    return public_key, private_key


def encrypt(public_key, base64_text):
    
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    # convert plaintext to base64
    message = ""

    for char in base64_text:
        # convert base64 to number based on index
        char_index = base64_chars.find(char)
        message += str(char_index).zfill(2)
    # split message into blocks of x (mi < n, for all i)
    x = 4
    message = [int(message[i:i + x]) for i in range(0, len(message), x)]
    # encrypt message
    e, n = public_key
    return [pow(char, e, n) for char in message]



def decrypt(private_key, ciphertext):
    d, n = private_key
    message = [pow(char, d, n) for char in ciphertext]
    
    # convert message to string
    x = 4
    message = "".join([str(char).zfill(x) for char in message])
    # convert message to base64
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    # split message into blocks of 2
    blocks = [message[i:i+2] for i in range(0, len(message), 2)]
    print("blocks")
    print(blocks)
    # convert blocks to base64
    plaintext = "".join([base64_chars[int(block)] for block in blocks])
    print("plaintext")
    print(plaintext)
    
    # decode base64
    # missing_padding = len(plaintext) % 4
    # if missing_padding != 0:
    #     plaintext += '=' * (missing_padding)
    return base64.b64decode(plaintext)



if __name__ == '__main__':
    public_key, private_key = generate_key_pair()
    print(public_key)
    print(private_key)
    pub1, pri1 = load_key_pair()
    print(pub1)
    print(pri1)

    text = 'tes'
    b64 = str(base64.b64encode(text.encode('utf-8')).decode('utf-8'))
    print(b64)
    ciphertext = encrypt(public_key, b64)
    print(ciphertext)
    plaintext = decrypt(private_key, ciphertext).decode('utf-8')
    print(plaintext)

    # file 
    # with open('build\K01_18221163_Aufar_Ramadhan_Milestone3.pdf', 'rb') as file:
    #     data = file.read()
    #     base64_data = base64.b64encode(data).decode('utf-8')
    #     ciphertext = encrypt(public_key, base64_data)
    #     with open('test_encrypted.pdf', 'wb') as file:
    #         for integer in ciphertext:
    #             file.write(struct.pack('I', integer))
    # with open('test_encrypted.pdf', 'rb') as file:
    #     data = file.read()
    #     num_integers = len(data) // 4
    #     ciphertext_in_file = struct.unpack(f"{num_integers}I", data)
    #     plaintext = decrypt(private_key, ciphertext_in_file)
    #     with open('test_decrypted.pdf', 'wb') as file:
    #         file.write(plaintext)

    