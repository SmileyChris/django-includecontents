"""
Tests for icon storage backends.
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings

from includecontents.icons.storage import (
    IconMemoryCache,
    cache_sprite,
    clear_sprite_cache,
    get_cached_sprite,
    get_sprite_filename,
    get_sprite_url,
    is_sprite_on_storage,
    read_sprite_from_storage,
    write_sprite_to_storage,
)
from includecontents.icons.storages import (
    BaseIconStorage,
    DjangoFileIconStorage,
    FileSystemIconStorage,
    MemoryIconStorage,
)


class TestIconMemoryCache(TestCase):
    """Test the IconMemoryCache class."""
    
    def setUp(self):
        self.cache = IconMemoryCache()
    
    def test_get_set(self):
        """Test basic get/set operations."""
        self.assertIsNone(self.cache.get('test-key'))
        
        self.cache.set('test-key', 'test-content')
        self.assertEqual(self.cache.get('test-key'), 'test-content')
    
    def test_has(self):
        """Test has method."""
        self.assertFalse(self.cache.has('test-key'))
        
        self.cache.set('test-key', 'test-content')
        self.assertTrue(self.cache.has('test-key'))
    
    def test_clear(self):
        """Test clearing cache."""
        self.cache.set('key1', 'content1')
        self.cache.set('key2', 'content2')
        
        self.assertTrue(self.cache.has('key1'))
        self.assertTrue(self.cache.has('key2'))
        
        self.cache.clear()
        
        self.assertFalse(self.cache.has('key1'))
        self.assertFalse(self.cache.has('key2'))


class TestMemoryIconStorage(TestCase):
    """Test the MemoryIconStorage backend."""
    
    def setUp(self):
        self.storage = MemoryIconStorage()
    
    def test_save_and_open(self):
        """Test saving and opening files."""
        content = '<svg>test</svg>'
        saved_name = self.storage.save('test.svg', content)
        
        self.assertEqual(saved_name, 'test.svg')
        self.assertEqual(self.storage.open('test.svg'), content)
    
    def test_exists(self):
        """Test exists method."""
        self.assertFalse(self.storage.exists('test.svg'))
        
        self.storage.save('test.svg', '<svg>test</svg>')
        self.assertTrue(self.storage.exists('test.svg'))
    
    def test_delete(self):
        """Test deleting files."""
        self.storage.save('test.svg', '<svg>test</svg>')
        self.assertTrue(self.storage.exists('test.svg'))
        
        result = self.storage.delete('test.svg')
        self.assertTrue(result)
        self.assertFalse(self.storage.exists('test.svg'))
        
        # Try to delete non-existent file
        result = self.storage.delete('nonexistent.svg')
        self.assertFalse(result)
    
    def test_url(self):
        """Test URL method (should return None for memory storage)."""
        self.storage.save('test.svg', '<svg>test</svg>')
        self.assertIsNone(self.storage.url('test.svg'))
    
    def test_clear(self):
        """Test clearing all stored sprites."""
        self.storage.save('file1.svg', '<svg>1</svg>')
        self.storage.save('file2.svg', '<svg>2</svg>')
        
        self.assertTrue(self.storage.exists('file1.svg'))
        self.assertTrue(self.storage.exists('file2.svg'))
        
        self.storage.clear()
        
        self.assertFalse(self.storage.exists('file1.svg'))
        self.assertFalse(self.storage.exists('file2.svg'))


class TestFileSystemIconStorage(TestCase):
    """Test the FileSystemIconStorage backend."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileSystemIconStorage(
            location=self.temp_dir,
            base_url='/test-icons/'
        )
    
    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_open(self):
        """Test saving and opening files."""
        content = '<svg>test sprite</svg>'
        saved_name = self.storage.save('sprite-123.svg', content)
        
        self.assertEqual(saved_name, 'sprite-123.svg')
        self.assertEqual(self.storage.open('sprite-123.svg'), content)
        
        # Check file actually exists on disk
        file_path = Path(self.temp_dir) / 'sprite-123.svg'
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_text(), content)
    
    def test_exists(self):
        """Test exists method."""
        self.assertFalse(self.storage.exists('test.svg'))
        
        self.storage.save('test.svg', '<svg>test</svg>')
        self.assertTrue(self.storage.exists('test.svg'))
    
    def test_url(self):
        """Test URL generation."""
        self.storage.save('test.svg', '<svg>test</svg>')
        url = self.storage.url('test.svg')
        
        self.assertEqual(url, '/test-icons/test.svg')
        
        # Non-existent file should return None
        self.assertIsNone(self.storage.url('nonexistent.svg'))
    
    def test_delete(self):
        """Test deleting files."""
        self.storage.save('test.svg', '<svg>test</svg>')
        self.assertTrue(self.storage.exists('test.svg'))
        
        result = self.storage.delete('test.svg')
        self.assertTrue(result)
        self.assertFalse(self.storage.exists('test.svg'))
        
        # Try to delete non-existent file
        result = self.storage.delete('nonexistent.svg')
        self.assertFalse(result)
    
    def test_path(self):
        """Test path method."""
        path = self.storage.path('test.svg')
        expected = Path(self.temp_dir) / 'test.svg'
        self.assertEqual(path, expected)
    
    def test_default_location(self):
        """Test default location creation."""
        with tempfile.TemporaryDirectory() as temp_base:
            with override_settings(BASE_DIR=temp_base):
                storage = FileSystemIconStorage()
                
                expected_location = Path(temp_base) / 'static' / 'includecontents' / 'icons'
                self.assertEqual(storage.location, expected_location)
                self.assertTrue(expected_location.exists())


class TestDjangoFileIconStorage(TestCase):
    """Test the DjangoFileIconStorage backend."""
    
    def setUp(self):
        # Create a mock storage for testing
        self.mock_storage = Mock()
        self.storage = DjangoFileIconStorage(
            storage=self.mock_storage,
            location='test-icons/'
        )
    
    def test_save(self):
        """Test saving files through Django storage."""
        content = '<svg>test</svg>'
        self.mock_storage.save.return_value = 'test-icons/sprite-123.svg'
        
        saved_name = self.storage.save('sprite-123.svg', content)
        
        self.assertEqual(saved_name, 'sprite-123.svg')
        self.mock_storage.save.assert_called_once()
        
        # Check the content file was created correctly
        args, kwargs = self.mock_storage.save.call_args
        name, content_file = args
        
        self.assertEqual(name, 'test-icons/sprite-123.svg')
        self.assertEqual(content_file.read(), content.encode('utf-8'))
    
    def test_open(self):
        """Test opening files through Django storage."""
        content = '<svg>test</svg>'
        
        # Mock the file object as a context manager
        mock_file = Mock()
        mock_file.read.return_value = content
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        self.mock_storage.open.return_value = mock_file
        
        result = self.storage.open('sprite-123.svg')
        
        self.assertEqual(result, content)
        self.mock_storage.open.assert_called_once_with('test-icons/sprite-123.svg', 'r')
    
    def test_open_file_not_found(self):
        """Test opening non-existent file."""
        self.mock_storage.open.side_effect = FileNotFoundError()
        
        result = self.storage.open('nonexistent.svg')
        self.assertIsNone(result)
    
    def test_exists(self):
        """Test exists method."""
        self.mock_storage.exists.return_value = True
        
        result = self.storage.exists('test.svg')
        
        self.assertTrue(result)
        self.mock_storage.exists.assert_called_once_with('test-icons/test.svg')
    
    def test_url(self):
        """Test URL generation."""
        self.mock_storage.exists.return_value = True
        self.mock_storage.url.return_value = 'https://cdn.example.com/test-icons/test.svg'
        
        url = self.storage.url('test.svg')
        
        self.assertEqual(url, 'https://cdn.example.com/test-icons/test.svg')
        self.mock_storage.url.assert_called_once_with('test-icons/test.svg')
    
    def test_url_file_not_exists(self):
        """Test URL for non-existent file."""
        self.mock_storage.exists.return_value = False
        
        url = self.storage.url('nonexistent.svg')
        self.assertIsNone(url)
    
    def test_url_not_implemented(self):
        """Test URL when storage doesn't support URLs."""
        self.mock_storage.exists.return_value = True
        self.mock_storage.url.side_effect = NotImplementedError()
        
        url = self.storage.url('test.svg')
        self.assertIsNone(url)
    
    def test_delete(self):
        """Test deleting files."""
        result = self.storage.delete('test.svg')
        
        self.assertTrue(result)
        self.mock_storage.delete.assert_called_once_with('test-icons/test.svg')
    
    def test_delete_error(self):
        """Test delete with error."""
        self.mock_storage.delete.side_effect = FileNotFoundError()
        
        result = self.storage.delete('test.svg')
        self.assertFalse(result)
    
    def test_default_storage(self):
        """Test using default Django storage."""
        with patch('django.core.files.storage.default_storage') as mock_default:
            storage = DjangoFileIconStorage()
            
            self.assertEqual(storage.storage, mock_default)
            self.assertEqual(storage.location, 'icons/')


class TestStorageIntegration(TestCase):
    """Test integration with storage functions."""
    
    def setUp(self):
        clear_sprite_cache()
    
    def test_sprite_filename_generation(self):
        """Test sprite filename generation."""
        sprite_hash = 'abc123def456'
        filename = get_sprite_filename(sprite_hash)
        
        self.assertEqual(filename, 'sprite-abc123def456.svg')
    
    def test_cache_and_retrieve(self):
        """Test caching and retrieving sprites."""
        sprite_hash = 'test-hash'
        content = '<svg>cached sprite</svg>'
        
        # Cache the sprite
        cache_sprite(sprite_hash, content)
        
        # Retrieve from cache
        cached_content = get_cached_sprite(sprite_hash)
        self.assertEqual(cached_content, content)
    
    @patch('includecontents.icons.storage.get_icon_storage')
    def test_storage_backend_integration(self, mock_get_storage):
        """Test integration with storage backends."""
        # Setup mock storage
        mock_storage = Mock(spec=BaseIconStorage)
        mock_storage.open.return_value = '<svg>stored sprite</svg>'
        mock_storage.exists.return_value = True
        mock_storage.url.return_value = '/static/sprite-123.svg'
        mock_storage.save.return_value = 'sprite-123.svg'
        mock_get_storage.return_value = mock_storage
        
        sprite_hash = 'test-hash-123'
        content = '<svg>test sprite</svg>'
        
        # Test writing to storage
        result = write_sprite_to_storage(sprite_hash, content)
        self.assertEqual(result, 'sprite-123.svg')
        
        # Test reading from storage
        read_content = read_sprite_from_storage(sprite_hash)
        self.assertEqual(read_content, '<svg>stored sprite</svg>')
        
        # Test existence check
        exists = is_sprite_on_storage(sprite_hash)
        self.assertTrue(exists)
        
        # Test URL generation
        url = get_sprite_url(sprite_hash)
        self.assertEqual(url, '/static/sprite-123.svg')
    
    @patch('includecontents.icons.storage.get_icon_storage')
    def test_storage_error_handling(self, mock_get_storage):
        """Test error handling in storage operations."""
        # Setup mock storage that raises errors
        mock_storage = Mock(spec=BaseIconStorage)
        mock_storage.save.side_effect = Exception('Storage error')
        mock_storage.open.return_value = None
        mock_storage.exists.return_value = False
        mock_storage.url.return_value = None
        mock_get_storage.return_value = mock_storage
        
        sprite_hash = 'error-hash'
        content = '<svg>error sprite</svg>'
        
        # Test write error handling
        result = write_sprite_to_storage(sprite_hash, content)
        self.assertIsNone(result)
        
        # Test read when file doesn't exist
        read_content = read_sprite_from_storage(sprite_hash)
        self.assertIsNone(read_content)
        
        # Test existence check when file doesn't exist
        exists = is_sprite_on_storage(sprite_hash)
        self.assertFalse(exists)
        
        # Test URL when file doesn't exist
        url = get_sprite_url(sprite_hash)
        self.assertIsNone(url)


class TestBaseIconStorage(TestCase):
    """Test that BaseIconStorage is properly abstract."""
    
    def test_cannot_instantiate_base_class(self):
        """Test that BaseIconStorage cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseIconStorage()
    
    def test_subclass_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods."""
        
        class IncompleteStorage(BaseIconStorage):
            def save(self, name: str, content: str) -> str:
                return name
        
        with self.assertRaises(TypeError):
            IncompleteStorage()