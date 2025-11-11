import pytest
import tempfile
import os
import database
from services.library_service import borrow_book_by_patron



@pytest.fixture(autouse=True)
def setup_database():
    """Set up a temp SQLite DB for tests."""
    # create a temp file
    db_fd, db_path = tempfile.mkstemp()
    global Book_A_ID, Book_B_ID, Book_C_ID, Book_D_ID, Book_E_ID, Book_F_ID
    database.DATABASE = db_path
    database.init_database()
    
    # Insert test books
    database.insert_book("Book A", "Author A", "1111111111111", 7, 7)
    database.insert_book("Book B", "Author B", "2222222222222", 1, 1)
    database.insert_book("Book C", "Author C", "3333333333333", 1, 1)
    database.insert_book("Book D", "Author D", "4444444444444", 1, 1)
    database.insert_book("Book E", "Author E", "5555555555555", 2, 2)
    database.insert_book("Book F", "Author F", "6666666666666", 3, 3)  # for testing 6th borrow attempt

    # Store IDs in globals for test access
    Book_A_ID = database.get_book_by_isbn("1111111111111")['id']
    Book_B_ID = database.get_book_by_isbn("2222222222222")['id']
    Book_C_ID = database.get_book_by_isbn("3333333333333")['id']
    Book_D_ID = database.get_book_by_isbn("4444444444444")['id']
    Book_E_ID = database.get_book_by_isbn("5555555555555")['id']
    Book_F_ID = database.get_book_by_isbn("6666666666666")['id']

    yield

    # cleanup
    os.close(db_fd)
    os.remove(db_path)


def test_borrow_book_success():
    """Test borrowing an available book with valid Patron ID"""
    success, message = borrow_book_by_patron("123456", Book_A_ID)

    assert success is True
    assert "successfully borrowed" in message.lower()

    # Check if the available copies is reduced
    book = database.get_book_by_id(Book_A_ID)
    assert book['available_copies'] == 6  # started with 7, now 6


def test_borrow_book_not_available():
    """Test trying to borrow a book that has no available copies"""
    borrow_book_by_patron("123456", Book_B_ID)                        # Borrow last copy of Book B
    success, message = borrow_book_by_patron("123456", Book_B_ID)     # Try borrowing again

    assert success is False
    assert "not available" in message.lower()


def test_borrow_book_invalid_id():
    """Test borrowing a book with invalid book ID"""
    success, message = borrow_book_by_patron("123456", 999)

    assert success is False
    assert "book not found" in message.lower()


def test_patron_borrow_count_limit():
    """Test patron cannot borrow more than 5 books"""
    patron_id = "654321"

    # Borrow 5 different books (using IDs we already have or predefined test books)
    books_to_borrow = [Book_A_ID, Book_B_ID, Book_C_ID, Book_D_ID, Book_E_ID]
    for book_id in books_to_borrow:
        borrow_book_by_patron(patron_id, book_id)

    # Try borrowing 6th book
    success, message = borrow_book_by_patron(patron_id, Book_F_ID)

    assert success is False
    assert "maximum borrowing limit" in message.lower()


def test_borrow_same_book_again():
    """Test patron cannot borrow same book twice"""
    # First borrow should succeed
    borrow_book_by_patron("123456", Book_A_ID)
    # Second borrow of same book should fail
    success, message = borrow_book_by_patron("123456", Book_A_ID)
    assert success is False
    assert "already borrowed" in message.lower()