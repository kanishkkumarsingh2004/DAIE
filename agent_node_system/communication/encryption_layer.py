#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Encryption Layer

This module provides end-to-end encryption for agent communication,
including message encryption, decryption, and secure key exchange.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from cryptography.hazmat.primitives.asymmetric import x25519, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

logger = logging.getLogger(__name__)

class EncryptionLayer:
    """
    Encryption layer for secure agent communication
    
    Provides end-to-end encryption using X25519 for key exchange and
    AES-GCM for message encryption.
    """
    
    def __init__(self):
        """Initialize the encryption layer"""
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        logger.info("Encryption layer initialized")
    
    def get_public_key(self) -> bytes:
        """
        Get the public key for key exchange
        
        Returns:
            bytes: Public key in raw format
        """
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def get_public_key_hex(self) -> str:
        """
        Get public key as hexadecimal string
        
        Returns:
            str: Public key in hex format
        """
        return self.get_public_key().hex()
    
    def generate_shared_key(self, peer_public_key: bytes) -> bytes:
        """
        Generate a shared secret key with a peer using X25519 key exchange
        
        Args:
            peer_public_key: Peer's public key in raw format
            
        Returns:
            bytes: Shared secret key
        """
        try:
            # Load peer public key
            peer_public_key_obj = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
            
            # Perform key exchange
            shared_key = self.private_key.exchange(peer_public_key_obj)
            
            # Derive key using SHA-256 to get 256-bit key for AES-256
            hash_obj = hashes.Hash(hashes.SHA256(), backend=default_backend())
            hash_obj.update(shared_key)
            derived_key = hash_obj.finalize()
            
            logger.debug("Shared key generated successfully")
            return derived_key
            
        except Exception as e:
            logger.error(f"Failed to generate shared key: {e}")
            raise
    
    def encrypt_message(self, message: bytes, key: bytes) -> bytes:
        """
        Encrypt a message using AES-GCM
        
        Args:
            message: Message to encrypt
            key: Encryption key (256 bits)
            
        Returns:
            bytes: Encrypted message with nonce and tag
        """
        try:
            # Generate random nonce (96 bits for GCM)
            nonce = os.urandom(12)
            
            # Create AES-GCM cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # Encrypt message
            ciphertext = encryptor.update(message) + encryptor.finalize()
            
            # Combine nonce, tag, and ciphertext
            encrypted_message = nonce + encryptor.tag + ciphertext
            
            logger.debug(f"Message encrypted successfully (size: {len(encrypted_message)} bytes)")
            return encrypted_message
            
        except Exception as e:
            logger.error(f"Failed to encrypt message: {e}")
            raise
    
    def decrypt_message(self, encrypted_message: bytes, key: bytes) -> bytes:
        """
        Decrypt a message using AES-GCM
        
        Args:
            encrypted_message: Encrypted message with nonce and tag
            key: Decryption key (256 bits)
            
        Returns:
            bytes: Decrypted plaintext message
        """
        try:
            # Extract nonce, tag, and ciphertext
            nonce = encrypted_message[:12]
            tag = encrypted_message[12:28]
            ciphertext = encrypted_message[28:]
            
            # Create AES-GCM cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Decrypt message
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            logger.debug(f"Message decrypted successfully (size: {len(plaintext)} bytes)")
            return plaintext
            
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            raise
    
    def encrypt_for_peer(self, message: bytes, peer_public_key: bytes) -> bytes:
        """
        Encrypt a message for a specific peer
        
        Args:
            message: Message to encrypt
            peer_public_key: Peer's public key
            
        Returns:
            bytes: Encrypted message
        """
        shared_key = self.generate_shared_key(peer_public_key)
        return self.encrypt_message(message, shared_key)
    
    def decrypt_from_peer(self, encrypted_message: bytes, peer_public_key: bytes) -> bytes:
        """
        Decrypt a message from a specific peer
        
        Args:
            encrypted_message: Encrypted message
            peer_public_key: Peer's public key
            
        Returns:
            bytes: Decrypted message
        """
        shared_key = self.generate_shared_key(peer_public_key)
        return self.decrypt_message(encrypted_message, shared_key)
    
    def sign_message(self, message: bytes, private_key) -> bytes:
        """
        Sign a message using Ed25519
        
        Args:
            message: Message to sign
            private_key: Ed25519 private key
            
        Returns:
            bytes: Digital signature
        """
        try:
            signature = private_key.sign(message)
            logger.debug("Message signed successfully")
            return signature
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            raise
    
    def verify_signature(self, message: bytes, signature: bytes, public_key) -> bool:
        """
        Verify a message signature using Ed25519
        
        Args:
            message: Original message
            signature: Digital signature
            public_key: Ed25519 public key
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            public_key.verify(signature, message)
            logger.debug("Signature verified successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to verify signature: {e}")
            return False
    
    def serialize_public_key(self, public_key) -> str:
        """
        Serialize public key to base64 string
        
        Args:
            public_key: Public key object
            
        Returns:
            str: Base64 encoded public key
        """
        try:
            key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            return base64.b64encode(key_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to serialize public key: {e}")
            raise
    
    def deserialize_public_key(self, serialized_key: str):
        """
        Deserialize public key from base64 string
        
        Args:
            serialized_key: Base64 encoded public key
            
        Returns:
            X25519PublicKey object
        """
        try:
            key_bytes = base64.b64decode(serialized_key)
            return x25519.X25519PublicKey.from_public_bytes(key_bytes)
        except Exception as e:
            logger.error(f"Failed to deserialize public key: {e}")
            raise

# Singleton instance for the encryption layer
_encryption_layer_instance = None

def get_encryption_layer() -> EncryptionLayer:
    """
    Get the singleton instance of the encryption layer
    
    Returns:
        EncryptionLayer: Singleton instance
    """
    global _encryption_layer_instance
    if _encryption_layer_instance is None:
        _encryption_layer_instance = EncryptionLayer()
    return _encryption_layer_instance

if __name__ == "__main__":
    # Test encryption layer functionality
    logging.basicConfig(level=logging.DEBUG)
    
    # Create two encryption layers to simulate communication
    alice = EncryptionLayer()
    bob = EncryptionLayer()
    
    # Test key exchange and encryption
    test_message = b"Hello, this is a secure message!"
    
    logger.info(f"Original message: {test_message.decode()}")
    
    # Alice encrypts for Bob
    encrypted = alice.encrypt_for_peer(test_message, bob.get_public_key())
    logger.info(f"Encrypted message size: {len(encrypted)} bytes")
    
    # Bob decrypts from Alice
    decrypted = bob.decrypt_from_peer(encrypted, alice.get_public_key())
    logger.info(f"Decrypted message: {decrypted.decode()}")
    
    # Verify decryption
    assert decrypted == test_message, "Decryption failed"
    logger.info("✅ Encryption/decryption test passed!")
    
    # Test signature
    from agent_node_system.identity.keypair_manager import KeypairManager
    keypair_manager = KeypairManager()
    if not keypair_manager.has_keys():
        keypair_manager.generate_keys()
    
    signature = alice.sign_message(test_message, keypair_manager.get_private_key())
    logger.info(f"Signature size: {len(signature)} bytes")
    
    valid = alice.verify_signature(test_message, signature, keypair_manager.get_public_key())
    logger.info(f"Signature valid: {valid}")
    
    assert valid, "Signature verification failed"
    logger.info("✅ Signature test passed!")
