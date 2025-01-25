'''
QuarkoFOSS - Main

This is the original Quarko code
Under the MIT license a copy is available in the LICENSE file

(some code is changed for privacy reasons.. (tokens etc))
'''

import hashlib

def hash_text(text):
    sha256 = hashlib.sha256()
    sha256.update(text.encode('utf-8'))
    return sha256.hexdigest()

def compare_hashes(hash1, hash2):
    return hash1 == hash2