from Crypto.PublicKey import RSA

# This attempts to generate an RSA key
# Your new engine should flag this as "Broken by Shor's Algorithm"
key = RSA.generate(2048)
print(key.exportKey())