#!/bin/bash

ssh-keygen -t rsa -b 4096 -m PEM -f server.key
# Don't add passphrase
openssl rsa -in server.key -pubout -outform PEM -out server.key.pub
cat server.key
cat server.key.pub