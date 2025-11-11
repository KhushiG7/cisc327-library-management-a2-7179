import pytest
from services.library_service import (
    add_book_to_catalog
    )
import random

def generate_isbn():
    """Generate a random 13-digit ISBN for testing."""
    return str(random.randint(10**12, 10**13 - 1))

def test_add_book_valid_input():
    """Test adding a book with valid input using a random ISBN."""
    isbn = generate_isbn()
    success, message = add_book_to_catalog("Test Book", "Test Author", isbn, 5)
    
    assert success is True
    assert "successfully added" in message.lower()

def test_add_book_invalid_isbn_too_short():
    """Test adding a book with ISBN too short."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
    
    assert success is False
    assert "13 digits" in message

def test_add_book_missing_title():
    """Test when title is missing."""
    isbn = generate_isbn()
    success, message = add_book_to_catalog("", "Test Author", isbn, 5)

    assert success is False
    assert "title" in message.lower()

def test_add_book_author_too_long():
    """Test adding a book with author name longer than 100 characters."""
    isbn = generate_isbn()
    long_author = "A" * 105
    success, message = add_book_to_catalog("Book Title", long_author, isbn, 5)
    
    assert success is False
    assert "author" in message.lower()

def test_add_book_negative_copies():
    """Test when total copies are negative."""
    isbn = generate_isbn()
    success, message = add_book_to_catalog("Book", "Author", isbn, -2)

    assert success is False
    assert "positive integer" in message.lower()

def test_add_book_duplicate_isbn():
    """Test adding a book with an ISBN that already exists in the catalog."""
    isbn = generate_isbn()
    success, message = add_book_to_catalog("First Book", "Author 1", isbn, 3)      # Add first book
    assert success is True

    # Try adding second book with the same ISBN
    success2, message2 = add_book_to_catalog("Second Book", "Author 2", isbn, 2)
    assert success2 is False
    assert "already exists" in message2.lower()

def test_add_book_isbn_with_letters():
    """Test adding a book with letters in ISBN"""
    isbn_with_letters = "12345ABCDE678"
    success, message = add_book_to_catalog("Test Book", "Test Author", isbn_with_letters, 5)
    
    assert success is False
    assert "only contain digits" in message.lower()