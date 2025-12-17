# to handle the configuration of the application

import os
import json
import bcrypt
from pathlib import Path
from .address_generator import generate_address, get_Machine_Fingerprint

class ConfigManager:
    
    def __init__(self, config_dir=None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.mydesk'

        self.config_file = self.config_dir / 'config.json'
        self.config = {}

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self): # to load from the existing config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = {}
        else:
            self.config = {}

    def save(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_or_create_address(self):

        if 'address' in self.config and 'fingerprint' in self.config:
            current_fingerprint = get_Machine_Fingerprint()
            if self.config['fingerprint'] == current_fingerprint:
                return self.config['address']
            else:
                print("Machine fingerprint mismatch - generating new address")
        
        # Generate new address
        address = generate_address()
        fingerprint = get_Machine_Fingerprint()
        
        self.config['address'] = address
        self.config['fingerprint'] = fingerprint
        self.save()
        
        return address
    
    def set_pin(self, pin): # store the pin hashed by bcrypt
        hashed = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt())
        self.config['pin_hash'] = hashed.decode('utf-8')
        self.save()

    def verify_pin(self, pin):
        stored_hash = self.config['pin_hash'].encode('utf-8')
        return bcrypt.checkpw(pin.encode('utf-8'), stored_hash)
    
    def has_pin(self):
        return 'pin_hash' in self.config
    
    def get_pin(self):
        return self.config.get('pin_hash')
    
    def get_address(self):
        return self.config.get('address')
    
    def reset(self):
        if self.config_file.exists:
            self.config_file.unlink
        self.config = {}

# test
if __name__ == "__main__":
    print("Testing Config Manager:")
    
    # Create manager
    config = ConfigManager()
    
    # Get or create address
    address = config.get_or_create_address()
    print(f"Your Address: {address}")
    
    # Set PIN
    if not config.has_pin():
        print("\nSetting PIN...")
        config.set_pin("1234")
        print("PIN set!")
    
    # Verify PIN
    print(f"\nVerifying PIN '1234': {config.verify_pin('1234')}")
    print(f"Verifying PIN 'wrong': {config.verify_pin('wrong')}")
    
    # Show config file location
    print(f"\nConfig file: {config.config_file}")
    
    # Run again to verify address persistence
    print("\n--- Creating new instance ---")
    config2 = ConfigManager()
    address2 = config2.get_or_create_address()
    print(f"Address (should be same): {address2}")
    print(f"Addresses match: {address == address2}")