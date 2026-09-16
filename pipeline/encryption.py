from cryptography.fernet import Fernet
from pathlib import Path

# Input and output files
input_file = Path("data/processed/urban_secure.csv")
encrypted_file = Path("data/processed/urban_secure.csv.encrypted")
key_file = Path("data/processed/encryption.key")

print("Starting data encryption...")

# --------------------------------------------------
# 1. GENERATE ENCRYPTION KEY
# --------------------------------------------------

key = Fernet.generate_key()

# Save the key
with open(key_file, "wb") as file:
    file.write(key)

# Create encryption object
fernet = Fernet(key)


# --------------------------------------------------
# 2. READ SECURE DATA
# --------------------------------------------------

with open(input_file, "rb") as file:
    data = file.read()

print(f"Data size: {len(data)} bytes")


# --------------------------------------------------
# 3. ENCRYPT DATA
# --------------------------------------------------

encrypted_data = fernet.encrypt(data)

with open(encrypted_file, "wb") as file:
    file.write(encrypted_data)


# --------------------------------------------------
# 4. RESULT
# --------------------------------------------------

print()
print("Data encryption completed!")
print(f"Encrypted file: {encrypted_file}")
print(f"Encryption key: {key_file}")
print()
print("The secure dataset is now stored in encrypted form.")