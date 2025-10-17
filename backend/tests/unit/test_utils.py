"""
Simple unit tests for utility functions
"""
import pytest
import hashlib
from collections import Counter, defaultdict


@pytest.mark.unit
def test_hash_generation():
    """Test SHA256 hash generation"""
    content = "Test content"
    hash_value = hashlib.sha256(content.encode()).hexdigest()
    assert len(hash_value) == 64
    assert isinstance(hash_value, str)


@pytest.mark.unit
def test_hash_consistency():
    """Test hash is consistent"""
    content = "Same content"
    hash1 = hashlib.sha256(content.encode()).hexdigest()
    hash2 = hashlib.sha256(content.encode()).hexdigest()
    assert hash1 == hash2


@pytest.mark.unit
def test_hash_uniqueness():
    """Test different content produces different hashes"""
    hash1 = hashlib.sha256("Content 1".encode()).hexdigest()
    hash2 = hashlib.sha256("Content 2".encode()).hexdigest()
    assert hash1 != hash2


@pytest.mark.unit
def test_counter_basic():
    """Test Counter for frequency counting"""
    words = ['apple', 'banana', 'apple', 'cherry', 'apple']
    counter = Counter(words)
    assert counter['apple'] == 3
    assert counter['banana'] == 1
    assert counter.most_common(1)[0][0] == 'apple'


@pytest.mark.unit
def test_defaultdict_creation():
    """Test defaultdict for grouping"""
    data = defaultdict(list)
    data['key1'].append('value1')
    data['key2'].append('value2')
    assert len(data['key1']) == 1
    assert len(data['key3']) == 0  # Default empty list


@pytest.mark.unit
def test_string_splitting():
    """Test string splitting"""
    text = "word1 word2 word3"
    words = text.split()
    assert len(words) == 3
    assert words[0] == "word1"


@pytest.mark.unit
def test_list_comprehension_filtering():
    """Test list comprehension for filtering"""
    numbers = [1, 2, 3, 4, 5, 6]
    evens = [n for n in numbers if n % 2 == 0]
    assert evens == [2, 4, 6]


@pytest.mark.unit
def test_dictionary_merging():
    """Test dictionary merging"""
    dict1 = {'a': 1, 'b': 2}
    dict2 = {'b': 3, 'c': 4}
    merged = {**dict1, **dict2}
    assert merged['a'] == 1
    assert merged['b'] == 3  # dict2 overwrites
    assert merged['c'] == 4
