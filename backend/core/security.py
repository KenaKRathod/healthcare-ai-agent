import os
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import bcrypt

# Set up paths to load/write environment variables
BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

encryption_key = os.getenv("ENCRYPTION_KEY")

if not encryption_key:
    # Generate a new Fernet key
    generated_key = Fernet.generate_key().decode()
    encryption_key = generated_key
    # Ensure env_path exists before appending
    try:
        with open(env_path, "a") as f:
            f.write(f"\nENCRYPTION_KEY={generated_key}\n")
    except Exception as e:
        print(f"Warning: Could not write ENCRYPTION_KEY to .env: {e}")
    os.environ["ENCRYPTION_KEY"] = generated_key

try:
    fernet = Fernet(encryption_key.encode())
except Exception as e:
    # If the key is invalid, generate a temporary valid one for runtime safety
    print(f"Warning: Invalid ENCRYPTION_KEY. Generating a temporary runtime key. Error: {e}")
    fernet = Fernet(Fernet.generate_key())


def encrypt_data(data: str | None) -> str | None:
    """Encrypts a plaintext string to a ciphertext string."""
    if data is None:
        return None
    try:
        # Stringify input to handle numbers/boolean values if passed accidentally
        str_data = str(data)
        return fernet.encrypt(str_data.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return data


def decrypt_data(data: str | None) -> str | None:
    """Decraw ciphertext string back to plaintext. Returns original value if decryption fails."""
    if data is None:
        return None
    try:
        return fernet.decrypt(str(data).encode()).decode()
    except Exception:
        # If decryption fails (e.g. data is not encrypted or format is invalid), return as-is
        return data


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt directly, truncating to 72 bytes if necessary."""
    # Bcrypt maximum input length is 72 bytes. We safely truncate using utf-8 bytes.
    truncated = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(truncated, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hashed password directly, truncating if necessary."""
    try:
        truncated = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
    except Exception:
        return False


