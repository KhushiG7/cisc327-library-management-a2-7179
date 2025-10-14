import pytest
import tempfile
import os
import database
from library_service import return_book_by_patron, borrow_book_by_patron
import datetime

@pytest.fixture(autouse=True)
def setup_database():
    """Set up a temp SQLite DB for R4 tests."""
    db_fd, db_path = tempfile.mkstemp()
    global Book_A_ID, Book_B_ID 
    database.DATABASE = db_path
    database.init_database()

    # Insert test books
    database.insert_book("Book A", "Author A", "1111111111111", 7, 7)
    database.insert_book("Book B", "Author B", "2222222222222", 1, 1)

    Book_A_ID = database.get_book_by_isbn("1111111111111")['id']
    Book_B_ID = database.get_book_by_isbn("2222222222222")['id']

    # Borrow Book A for patron "123456" to setup returns
    borrow_book_by_patron("123456", Book_A_ID)

    yield

    # Cleanup
    os.close(db_fd)
    os.remove(db_path)

def test_return_book_success():
    """Test successful return of a borrowed book."""
    success, message = return_book_by_patron("123456", Book_A_ID)
    assert success is True
    assert "successfully returned" in message.lower()

    book = database.get_book_by_id(Book_A_ID)         # Check available copies increased
    assert book['available_copies'] == 7  # started with 7, borrowed 1, returned 1

def test_return_book_not_borrowed():
    """Test returning a book that was not borrowed by the patron."""
    success, message = return_book_by_patron("123456", Book_B_ID)
    
    assert success is False
    assert "not borrowed" in message.lower()

def test_return_book_invalid_id():
    """Test returning a book with invalid book ID."""
    success, message = return_book_by_patron("123456", 999)
    
    assert success is False
    assert "book not found" in message.lower()

def test_return_book_late_fee():
    """Return a book past due date to calculate late fees."""
    # Manually set borrow date in past to simulate overdue
    overdue_date = datetime.datetime.now() - datetime.timedelta(days=20)
    due_date = datetime.datetime.now() - datetime.timedelta(days=14)
    database.insert_borrow_record("654321", Book_A_ID, overdue_date, due_date)

    success, message = return_book_by_patron("654321", Book_A_ID)

    assert success is True
    assert "late fee" in message.lower()

def test_return_book_on_due_date():
    """Return a book exactly on the due date should not incur a late fee."""
    # Borrow Book A for this patron with borrow date 14 days ago, due today
    borrow_date = datetime.datetime.now() - datetime.timedelta(days=14)
    due_date = datetime.datetime.now()
    database.insert_borrow_record("225566", Book_A_ID, borrow_date, due_date)
    
    # Return the book
    success, message = return_book_by_patron("225566", Book_A_ID)
    
    assert success is True
    assert "late fee" in message.lower()
    assert "$0.00" in message  # Late fee should be 0