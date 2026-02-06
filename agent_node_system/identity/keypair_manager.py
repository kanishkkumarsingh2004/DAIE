"""
Agent Node System - Keypair Manager
Decentralized AI Ecosystem

This module manages cryptographic key pairs for the agent identity system.
It provides methods for generating, storing, and loading Ed25519 key pairs
for digital signatures and encryption.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import os
import json
import logging
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class KeypairManager:
    """Manages cryptographic key pairs for agent identity"""
    
    def __init__(self, identity_path: str = "./agent_node_system/identity"):
        """
        Initialize the keypair manager
        
        Args:
            identity_path: Path to store identity files
        """
        self.identity_path = identity_path
        self.private_key_path = os.path.join(identity_path, "private_key.pem")
        self.public_key_path = os.path.join(identity_path, "public_key.pem")
        self.identity_file = os.path.join(identity_path, "identity.json")
        
        # Ensure identity directory exists
        os.makedirs(identity_path, exist_ok=True)
        
        self.private_key = None
        self.public_key = None
        
        logger.info(f"Keypair manager initialized with identity path: {identity_path}")
    
    def has_keys(self) -> bool:
        """
        Check if key pair already exists
        
        Returns:
            True if both private and public keys exist, False otherwise
        """
        return os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path)
    
    def generate_keys(self) -> tuple[bytes, bytes]:
        """
        Generate a new Ed25519 key pair
        
        Returns:
            Tuple containing private key and public key bytes
        """
        logger.info("Generating new Ed25519 key pair...")
        
        # Generate new Ed25519 key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Save keys
        self._save_private_key(private_key)
        self._save_public_key(public_key)
        
        # Save identity file
        self._save_identity_info()
        
        logger.info("Key pair generated successfully")
        
        return self._get_key_bytes(private_key, public_key)
    
    def load_keys(self) -> tuple[bytes, bytes]:
        """
        Load existing key pair from files
        
        Returns:
            Tuple containing private key and public key bytes
            
        Raises:
            FileNotFoundError: If keys are not found
            Exception: If keys cannot be loaded
        """
        logger.info("Loading existing key pair...")
        
        if not self.has_keys():
            raise FileNotFoundError("Key pair not found")
        
        try:
            # Load private key
            with open(self.private_key_path, "rb") as f:
                private_key_bytes = f.read()
            
            # Load public key
            with open(self.public_key_path, "rb") as f:
                public_key_bytes = f.read()
            
            logger.info("Key pair loaded successfully")
            
            return private_key_bytes, public_key_bytes
            
        except Exception as e:
            logger.error(f"Failed to load key pair: {e}")
            raise
    
    def get_private_key(self):
        """
        Get the private key object
        
        Returns:
            Ed25519PrivateKey object
            
        Raises:
            FileNotFoundError: If keys are not found
            Exception: If keys cannot be loaded
        """
        if self.private_key is None:
            if not self.has_keys():
                raise FileNotFoundError("Key pair not found")
            
            try:
                with open(self.private_key_path, "rb") as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
            except Exception as e:
                logger.error(f"Failed to load private key: {e}")
                raise
        
        return self.private_key
    
    def get_public_key(self):
        """
        Get the public key object
        
        Returns:
            Ed25519PublicKey object
            
        Raises:
            FileNotFoundError: If keys are not found
            Exception: If keys cannot be loaded
        """
        if self.public_key is None:
            if not self.has_keys():
                raise FileNotFoundError("Key pair not found")
            
            try:
                with open(self.public_key_path, "rb") as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=default_backend()
                    )
            except Exception as e:
                logger.error(f"Failed to load public key: {e}")
                raise
        
        return self.public_key
    
    def _save_private_key(self, private_key):
        """Save private key to file"""
        try:
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(self.private_key_path, "wb") as f:
                f.write(private_pem)
            
            os.chmod(self.private_key_path, 0o600)
            logger.debug("Private key saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save private key: {e}")
            raise
    
    def _save_public_key(self, public_key):
        """Save public key to file"""
        try:
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            with open(self.public_key_path, "wb") as f:
                f.write(public_pem)
            
            logger.debug("Public key saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save public key: {e}")
            raise
    
    def _save_identity_info(self):
        """Save identity information to JSON file"""
        try:
            identity_info = {
                "version": "1.0.0",
                "key_type": "Ed25519",
                "private_key_path": self.private_key_path,
                "public_key_path": self.public_key_path
            }
            
            with open(self.identity_file, "w") as f:
                json.dump(identity_info, f, indent=2, default=str)
            
            logger.debug("Identity information saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save identity information: {e}")
            raise
    
    def _get_key_bytes(self, private_key, public_key) -> tuple[bytes, bytes]:
        """Convert keys to bytes"""
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return private_bytes, public_bytes
    
    def get_public_key_hex(self) -> str:
        """Get public key as hexadecimal string"""
        public_key = self.get_public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return public_bytes.hex()
    
    def get_private_key_hex(self) -> str:
        """Get private key as hexadecimal string"""
        private_key = self.get_private_key()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return private_bytes.hex()
    
    def sign_message(self, message: bytes) -> bytes:
        """
        Sign a message using the private key
        
        Args:
            message: Message to sign (bytes)
            
        Returns:
            Digital signature (bytes)
        """
        private_key = self.get_private_key()
        return private_key.sign(message)
    
    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """
        Verify a signature using the public key
        
        Args:
            message: Original message (bytes)
            signature: Digital signature to verify (bytes)
            
        Returns:
            True if signature is valid, False otherwise
        """
        public_key = self.get_public_key()
        
        try:
            public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    def delete_keys(self):
        """Delete existing key pair files"""
        logger.warning("Deleting existing key pair...")
        
        for filepath in [self.private_key_path, self.public_key_path, self.identity_file]:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug(f"Deleted: {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to delete {filepath}: {e}")
        
        self.private_key = None
        self.public_key = None
        
        logger.info("Key pair deleted successfully")
    
    def regenerate_keys(self) -> tuple[bytes, bytes]:
        """Regenerate a new key pair"""
        self.delete_keys()
        return self.generate_keys()
    
    def export_public_key(self) -> str:
        """Export public key in PEM format"""
        public_key = self.get_public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")
    
    def export_private_key(self) -> str:
        """Export private key in PEM format"""
        private_key = self.get_private_key()
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")
    
    def import_keys(self, private_key_pem: str, public_key_pem: str):
        """
        Import key pair from PEM format
        
        Args:
            private_key_pem: Private key in PEM format
            public_key_pem: Public key in PEM format
        """
        logger.info("Importing key pair from PEM format...")
        
        try:
            # Load private key
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
                backend=default_backend()
            )
            
            # Load public key
            self.public_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8"),
                backend=default_backend()
            )
            
            # Save keys to files
            self._save_private_key(self.private_key)
            self._save_public_key(self.public_key)
            
            logger.info("Key pair imported successfully")
            
        except Exception as e:
            logger.error(f"Failed to import key pair: {e}")
            raise

def main():
    """Main function for testing"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Key pair manager command-line interface")
    
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a new key pair"
    )
    
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load existing key pair"
    )
    
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete existing key pair"
    )
    
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate key pair"
    )
    
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show key information"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test key functionality"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create keypair manager
    manager = KeypairManager()
    
    if args.generate:
        manager.generate_keys()
    
    elif args.load:
        try:
            private_bytes, public_bytes = manager.load_keys()
            print(f"Private key loaded: {len(private_bytes)} bytes")
            print(f"Public key loaded: {len(public_bytes)} bytes")
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.delete:
        manager.delete_keys()
    
    elif args.regenerate:
        manager.regenerate_keys()
    
    elif args.show:
        try:
            print("=== Public Key ===\n")
            print(manager.export_public_key())
            print(f"\nHex: {manager.get_public_key_hex()}")
            
            print("\n=== Private Key ===\n")
            print(manager.export_private_key())
            print(f"\nHex: {manager.get_private_key_hex()}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.test:
        try:
            # Test key functionality
            if not manager.has_keys():
                manager.generate_keys()
            
            test_message = b"Test message at " + datetime.now().isoformat().encode()
            
            print(f"Test message: {test_message.decode()}")
            
            # Sign
            signature = manager.sign_message(test_message)
            print(f"Signature length: {len(signature)} bytes")
            print(f"Signature hex: {signature.hex()}")
            
            # Verify
            valid = manager.verify_signature(test_message, signature)
            print(f"Signature valid: {valid}")
            
            # Test verification with tampered message
            tampered_message = test_message + b"tampered"
            invalid = manager.verify_signature(tampered_message, signature)
            print(f"Tampered signature valid: {invalid}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
