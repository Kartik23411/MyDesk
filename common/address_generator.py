# For the generation of 12 digit address for specific machine

import hashlib
import uuid
import platform
import random
import string
from datetime import datetime

def get_Machine_Fingerprint():
    # It provides a fingerprint based on the MAC, OS and hostname

    mac = uuid.getnode()
    mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2)) # 6 byte mac has 12 hex numbers with the zero padding
    
    hostname = platform.node()
    
    os_info = platform.system() + platform.release()
    
    fingerprint = f"{mac_str}_{hostname}_{os_info}"    
    return fingerprint

def generate_machine_hash():
    # converts the fingerprint into 5-character Base36 hash 

    fingerprint = get_Machine_Fingerprint()

    hash_obj = hashlib.sha256(fingerprint.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    base36_chars = string.digits + string.ascii_uppercase # to convert in base36[0-9 A-Z], it first creates the 36 char array and then on basis of the index char is choosen from the array
    result = []
    
    for _ in range(5):
        result.append(base36_chars[hash_int % 36])
        hash_int //= 36
    
    return ''.join(result)

def generate_date_code():
    #to generate 3-character date code from day of year and year in base 36.

    now = datetime.now()
    day_of_year = now.timetuple().tm_yday  # 1-366
    year_last_digit = now.year % 10  # 0-9
    combined = (year_last_digit * 366) + day_of_year
    
    base36_chars = string.digits + string.ascii_uppercase
    result = []
    
    for _ in range(3):
        result.append(base36_chars[combined % 36])
        combined //= 36
    
    return ''.join(result)

def generate_random_code():
    # to generate 4-character random code in base 36
    base36_chars = string.digits + string.ascii_uppercase
    return ''.join(random.choice(base36_chars) for _ in range(4))

def generate_address():
    # to combine all three parts in a single 12 character address
    machine_hash = generate_machine_hash()
    date_code = generate_date_code()
    random_code = generate_random_code()

    return f"{machine_hash}-{date_code}-{random_code}"

def validate_address_format(address):

    if not address or len(address) != 14: #12 char + 2 dash
        return False
    
    parts = address.split('-')
    if len(parts) != 3:
        return False
    
    if len(parts[0]) != 5 or len(parts[1]) != 3 or len(parts[2]) != 4:
        return False
    
    base36_chars = set(string.digits + string.ascii_uppercase)
    for part in parts:
        if not all(c in base36_chars for c in part.upper()):
            return False
    
    return True

if __name__ == "__main__":
    print("Testing Address Generation:")
    print(f"Machine Fingerprint: {get_Machine_Fingerprint()}")
    print(f"Machine Hash: {generate_machine_hash()}")
    print(f"Date Code: {generate_date_code()}")
    print(f"Random Code: {generate_random_code()}")
    print(f"\nGenerated Address: {generate_address()}")

    test_addr = "AB3F9-2K7-8XQM"
    print(f"\nValidating '{test_addr}': {validate_address_format(test_addr)}")