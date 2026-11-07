import os
from pathlib import Path
from getpass import getpass
import shutil
import base64
import secrets

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

ENCRYPTED_DIR = Path("encrypted")
OUTPUT_DIR = Path("decrypted_project")
SALT_FILE = Path("salt.bin")

def derive_key(password, salt):
    """Derive AES key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def decrypt_file(src, dst, fernet):
    ciphertext = src.read_bytes()
    plaintext = fernet.decrypt(ciphertext)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(plaintext)
    
def main():
    if not ENCRYPTED_DIR.exists():
        raise SystemExit("Missing 'encrypted/' folder")
    
    if not SALT_FILE.exists():
        raise SystemExit("Missing salt.bin - package corrupted")
        
    salt = SALT_FILE.read_bytes()
    password = getpass("Enter unlock password: ")
    
    key = derive_key(password, salt)
    f = Fernet(key)
    
    print("\nVerifying password... \n")
    
    #validation: trying first file
    first = None
    for root, dirs, files in os.walk(ENCRYPTED_DIR):
        if files:
            first = Path(root) / files[0]
            break
    
    if first is None:
        raise SystemExit("Encrypted folder is empty")
    
    
    try:
        f.decrypt(first.read_bytes())
    except InvalidToken:
        raise SystemExit("Invalid password. Cannot unlock.")
    
    print("Password correct. Decrypting project...\n")
    
    for root, dirs, files in os.walk(ENCRYPTED_DIR):
        root = Path(root)
        for name in files:
            src = root / name
            rel = src.relative_to(ENCRYPTED_DIR)
            
            #removing .enc extension
            if rel.suffix == ".enc":
                rel = rel.with_suffix("")
            
            dst = OUTPUT_DIR / rel
            print(f"Decrypt to: {rel}")
            decrypt_file(src, dst, f)
            
    print("\n Success")
    print(f"The unlocked project can be found in: {OUTPUT_DIR.resolve()}")
    print("Project can now be run as normal")
    
if __name__ == "__main__":
    main()
                
            