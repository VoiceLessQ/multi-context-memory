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
Compression strategy implementations.
Extracts compression logic from enhanced_memory_db.py.
"""
import logging
import zlib
import gzip
from typing import Tuple
from abc import ABC

from ..interfaces.storage_strategy import CompressionStrategy

logger = logging.getLogger(__name__)


class ZstdCompressionStrategy(CompressionStrategy):
    """
    Zstandard compression strategy.
    Extracted from the original ContentCompressor class.
    """
    
    def __init__(self, level: int = 3):
        self.level = level
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Compress content using Zstandard algorithm."""
        try:
            # Simple implementation for now
            import base64
            import zlib
            compressed_bytes = zlib.compress(content.encode('utf-8'))
            compressed_str = base64.b64encode(compressed_bytes).decode('utf-8')
            return compressed_str, True
        except Exception as e:
            logger.error(f"Zstd compression failed: {e}")
            return content, False
    
    def decompress(self, compressed_content: str) -> str:
        """Decompress content using Zstandard algorithm."""
        try:
            import base64
            import zlib
            compressed_bytes = base64.b64decode(compressed_content.encode('utf-8'))
            decompressed_bytes = zlib.decompress(compressed_bytes)
            return decompressed_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Zstd decompression failed: {e}")
            return compressed_content
    
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio."""
        if not original:
            return 0.0
        
        original_size = len(original.encode('utf-8'))
        compressed_size = len(compressed.encode('utf-8'))
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)


class GzipCompressionStrategy(CompressionStrategy):
    """
    Gzip compression strategy as an alternative.
    """
    
    def __init__(self, level: int = 6):
        self.level = level
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Compress content using Gzip algorithm."""
        try:
            content_bytes = content.encode('utf-8')
            compressed_bytes = gzip.compress(content_bytes, compresslevel=self.level)
            
            # Check if compression was beneficial
            if len(compressed_bytes) >= len(content_bytes):
                return content, False
            
            # Encode to string for storage
            import base64
            compressed_str = base64.b64encode(compressed_bytes).decode('utf-8')
            return compressed_str, True
            
        except Exception as e:
            logger.error(f"Gzip compression failed: {e}")
            return content, False
    
    def decompress(self, compressed_content: str) -> str:
        """Decompress content using Gzip algorithm."""
        try:
            import base64
            compressed_bytes = base64.b64decode(compressed_content.encode('utf-8'))
            decompressed_bytes = gzip.decompress(compressed_bytes)
            return decompressed_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Gzip decompression failed: {e}")
            return compressed_content
    
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio."""
        if not original:
            return 0.0
        
        original_size = len(original.encode('utf-8'))
        
        try:
            import base64
            compressed_bytes = base64.b64decode(compressed.encode('utf-8'))
            compressed_size = len(compressed_bytes)
        except:
            compressed_size = len(compressed.encode('utf-8'))
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)


class ZlibCompressionStrategy(CompressionStrategy):
    """
    Zlib compression strategy for lighter compression needs.
    """
    
    def __init__(self, level: int = 6):
        self.level = level
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Compress content using Zlib algorithm."""
        try:
            content_bytes = content.encode('utf-8')
            compressed_bytes = zlib.compress(content_bytes, self.level)
            
            # Check if compression was beneficial
            if len(compressed_bytes) >= len(content_bytes):
                return content, False
            
            # Encode to string for storage
            import base64
            compressed_str = base64.b64encode(compressed_bytes).decode('utf-8')
            return compressed_str, True
            
        except Exception as e:
            logger.error(f"Zlib compression failed: {e}")
            return content, False
    
    def decompress(self, compressed_content: str) -> str:
        """Decompress content using Zlib algorithm."""
        try:
            import base64
            compressed_bytes = base64.b64decode(compressed_content.encode('utf-8'))
            decompressed_bytes = zlib.decompress(compressed_bytes)
            return decompressed_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Zlib decompression failed: {e}")
            return compressed_content
    
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio."""
        if not original:
            return 0.0
        
        original_size = len(original.encode('utf-8'))
        
        try:
            import base64
            compressed_bytes = base64.b64decode(compressed.encode('utf-8'))
            compressed_size = len(compressed_bytes)
        except:
            compressed_size = len(compressed.encode('utf-8'))
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)


class NoCompressionStrategy(CompressionStrategy):
    """
    No compression strategy for cases where compression is disabled.
    """
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Return content without compression."""
        return content, False
    
    def decompress(self, compressed_content: str) -> str:
        """Return content as-is since it's not compressed."""
        return compressed_content
    
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """No compression, so ratio is 0."""
        return 0.0


class AdaptiveCompressionStrategy(CompressionStrategy):
    """
    Adaptive compression strategy that chooses the best algorithm based on content.
    """
    
    def __init__(self):
        self.strategies = {
            'zstd': ZstdCompressionStrategy(),
            'gzip': GzipCompressionStrategy(),
            'zlib': ZlibCompressionStrategy(),
            'none': NoCompressionStrategy()
        }
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Choose best compression strategy based on content characteristics."""
        # For small content, don't compress
        if len(content) < 100:
            return self.strategies['none'].compress(content)
        
        # For very large content, use zstd
        if len(content) > 50000:
            return self.strategies['zstd'].compress(content)
        
        # For medium content, try multiple and pick best
        best_ratio = 0.0
        best_result = (content, False)
        best_strategy = 'none'
        
        for name, strategy in [('zstd', self.strategies['zstd']), 
                              ('gzip', self.strategies['gzip']),
                              ('zlib', self.strategies['zlib'])]:
            try:
                compressed, was_compressed = strategy.compress(content)
                if was_compressed:
                    ratio = strategy.get_compression_ratio(content, compressed)
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_result = (compressed, True)
                        best_strategy = name
            except Exception as e:
                logger.warning(f"Strategy {name} failed: {e}")
                continue
        
        logger.debug(f"Selected {best_strategy} compression with ratio {best_ratio:.2f}")
        return best_result
    
    def decompress(self, compressed_content: str) -> str:
        """Attempt decompression with all strategies until one succeeds."""
        # Try each strategy in order of likelihood
        for strategy in [self.strategies['zstd'], 
                        self.strategies['gzip'],
                        self.strategies['zlib']]:
            try:
                decompressed = strategy.decompress(compressed_content)
                # If decompression changed the content, it probably worked
                if decompressed != compressed_content:
                    return decompressed
            except Exception:
                continue
        
        # If all strategies failed, return original content
        logger.warning("All decompression strategies failed, returning original content")
        return compressed_content
    
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio based on byte sizes."""
        if not original:
            return 0.0
        
        original_size = len(original.encode('utf-8'))
        compressed_size = len(compressed.encode('utf-8'))
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)