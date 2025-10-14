import pytest
import tempfile
import os
import database
from library_service import search_books_in_catalog

@pytest.fixture(autouse=True)
def setup_database():
    """Set up a temp SQLite DB for R6 tests."""
    db_fd, db_path = tempfile.mkstemp()
    global BOOK1_ID, BOOK2_ID, BOOK3_ID
    database.DATABASE = db_path
    database.init_database()

    # Insert test books
    database.insert_book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3, 3)
    database.insert_book("To Kill a Mockingbird", "Harper Lee", "9780061120084", 2, 2)
    database.insert_book("1984", "George Orwell", "9780451524935", 1, 1)

    BOOK1_ID = database.get_book_by_isbn("9780743273565")['id']
    BOOK2_ID = database.get_book_by_isbn("9780061120084")['id']
    BOOK3_ID = database.get_book_by_isbn("9780451524935")['id']

    yield

    # Cleanup
    os.close(db_fd)
    os.remove(db_path)


def test_search_by_title_partial():
    """Test partial, case-insensitive search by title."""
    results = search_books_in_catalog(search_term="great", search_type="title")
    assert len(results) == 1
    assert results[0]['title'] == "The Great Gatsby"


def test_search_by_author_partial():
    """Test partial, case-insensitive search by author."""
    results = search_books_in_catalog(search_term="orwell", search_type="author")
    assert len(results) == 1
    assert results[0]['author'] == "George Orwell"


def test_search_by_isbn_exact():
    """Test exact match search by ISBN."""
    results = search_books_in_catalog(search_term="9780451524935", search_type="isbn")
    assert len(results) == 1
    assert results[0]['title'] == "1984"


def test_search_no_results():
    """Test search that returns no results."""
    results = search_books_in_catalog(search_term="Nonexistent", search_type="title")
    assert len(results) == 0


def test_search_invalid_type():
    """Test search with invalid type."""
    results = search_books_in_catalog(search_term="1984", search_type="publisher")
    assert len(results) == 0

def test_search_empty_term():
    """Searching with empty string should return no results."""
    results = search_books_in_catalog(search_term="", search_type="title")
    assert len(results) == 0