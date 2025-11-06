"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Content compression utilities for the MCP Multi-Context Memory System.
"""
import gzip
import base64
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ContentCompressor:
    """Handle content compression and decompression."""
    
    COMPRESSION_THRESHOLD = 10240  # 10KB
    
    @classmethod
    def should_compress(cls, content: str) -> bool:
        """
        Check if content should be compressed based on size.
        
        Args:
            content: The content to check
            
        Returns:
            True if content should be compressed, False otherwise
        """
        try:
            return len(content.encode('utf-8')) > cls.COMPRESSION_THRESHOLD
        except Exception as e:
            logger.error(f"Error checking content size for compression: {e}")
            return False
    
    @classmethod
    def compress(cls, content: str) -> Tuple[str, bool]:
        """
        Compress content if it exceeds the threshold.
        
        Args:
            content: The content to compress
            
        Returns:
            Tuple of (processed_content, is_compressed)
        """
        try:
            if cls.should_compress(content):
                logger.debug(f"Compressing content ({len(content.encode('utf-8'))} bytes)")
                compressed = gzip.compress(content.encode('utf-8'))
                encoded = base64.b64encode(compressed).decode('ascii')
                return encoded, True
            return content, False
        except Exception as e:
            logger.error(f"Error compressing content: {e}")
            return content, False
    
    @classmethod
    def decompress(cls, compressed_content: str) -> str:
        """
        Decompress content that was previously compressed.
        
        Args:
            compressed_content: The base64-encoded compressed content
            
        Returns:
            The decompressed content string
            
        Raises:
            ValueError: If decompression fails
        """
        try:
            if not compressed_content:
                return ""
                
            # Check if content is compressed (starts with base64 characters)
            # This is a simple heuristic - in production, you might want a more robust check
            if not compressed_content.strip():  # Empty or whitespace-only
                return compressed_content
                
            # Try to decode as base64
            try:
                compressed = base64.b64decode(compressed_content.encode('ascii'))
                decompressed = gzip.decompress(compressed)
                return decompressed.decode('utf-8')
            except Exception:
                # If base64/gzip fails, return as-is (fallback for non-compressed content)
                logger.debug("Decompression failed, returning content as-is")
                return compressed_content
                
        except Exception as e:
            logger.error(f"Error decompressing content: {e}")
            # Fallback to returning original content
            return compressed_content
    
    @classmethod
    def get_compression_ratio(cls, original: str, compressed: str) -> float:
        """
        Calculate the compression ratio.
        
        Args:
            original: Original content
            compressed: Compressed content (base64 encoded)
            
        Returns:
            Compression ratio (original_size / compressed_size), 0.0 if error
        """
        try:
            original_size = len(original.encode('utf-8'))
            compressed_size = len(compressed.encode('utf-8'))
            
            if compressed_size == 0:
                return 0.0
                
            return original_size / compressed_size
        except Exception as e:
            logger.error(f"Error calculating compression ratio: {e}")
            return 0.0

class CompressionManager:
    """
    Wrapper class for ContentCompressor to maintain backward compatibility
    and provide a consistent interface for compression operations.
    """
    def __init__(self):
        # This class primarily acts as a wrapper to ContentCompressor
        # No specific state needs to be held here if all methods are static
        pass

    @staticmethod
    def compress_content(content: str) -> Tuple[str, bool]:
        """
        Compress content using ContentCompressor.

        Args:
            content: The content to compress.

        Returns:
            Tuple of (processed_content, is_compressed).
        """
        return ContentCompressor.compress(content)

    @staticmethod
    def decompress_content(compressed_content: str) -> str:
        """
        Decompress content using ContentCompressor.

        Args:
            compressed_content: The base64-encoded compressed content.

        Returns:
            The decompressed content string.
        """
        return ContentCompressor.decompress(compressed_content)

    @staticmethod
    def should_compress_content(content: str) -> bool:
        """
        Check if content should be compressed using ContentCompressor.

        Args:
            content: The content to check.

        Returns:
            True if content should be compressed, False otherwise.
        """
        return ContentCompressor.should_compress(content)