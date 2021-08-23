from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import cryptography
import os,sys

print(dir(cryptography.__file__))
prviate_key = Ed25519PrivateKey.generate()
signatures = prviate_key.sign(b'it is secrete message')
public_key = prviate_key.public_key()

public_key.verify(signatures,b'it is secrete message')


