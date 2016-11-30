import os

# path to the private key (16 bytes)
PRIVATE_KEY_FILE = 'private-key'

# database uri
DATABASE_URI = 'mysql+mysqlconnector://%(MYSQL_USER)s:%(MYSQL_PASSWORD)s@%(MYSQL_HOST)s/%(MYSQL_DATABASE)s' % os.environ
