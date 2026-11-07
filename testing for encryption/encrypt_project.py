import os
from pathlib import Path
from getpass import getpass
import shutil
import base64
import secrets

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Folders to skip (generated or huge)
EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".git",
    ".next", "dist", "build", ".venv", "venv"
}

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

def encrypt_file(src, dst, fernet):
    data = src.read_bytes()
    enc = fernet.encrypt(data)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(enc)

def main():
    project_path = input("Path to project folder to encrypt: ").strip('"')
    PROJECT_DIR = Path(project_path)
    
    if not PROJECT_DIR.exists():
        raise SystemExit(f"Project folder '{PROJECT_DIR}' not found.")

    client_name = input("Client name: ").strip()
    out_dir = Path(f"locked_for_{client_name}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    encrypted_dir = out_dir / "encrypted"
    encrypted_dir.mkdir()

    # Ask for client password
    print("\nENTER UNIQUE UNLOCK PASSWORD FOR THIS CLIENT:")
    pw = getpass("Password: ")
    if pw != getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")

    # Generate salt
    salt = secrets.token_bytes(16)
    (out_dir / "salt.bin").write_bytes(salt)

    key = derive_key(pw, salt)
    fernet = Fernet(key)

    # Copy the decrypt script into client package
    shutil.copy2("decrypt.py", out_dir / "decrypt.py")

    print("\nEncrypting files...\n")

    for root, dirs, files in os.walk(PROJECT_DIR):
        root = Path(root)

        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for name in files:
            src_file = root / name
            rel = src_file.relative_to(PROJECT_DIR)

            dst_file = encrypted_dir / (str(rel) + ".enc")

            print(f"Encrypt → {rel}")
            encrypt_file(src_file, dst_file, fernet)

    print("\nDONE.\n Ship this folder:", out_dir.resolve())
    print("\nClient will use decrypt.py to unlock the project.")

if __name__ == "__main__":
    main()