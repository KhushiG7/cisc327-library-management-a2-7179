import pytest
import tempfile
import os
import database
from services.library_service import (
    get_patron_status_report,
    borrow_book_by_patron,
    return_book_by_patron
)

@pytest.fixture(autouse=True)
def setup_database():
    """Set up a temp SQLite DB for R7 tests."""
    db_fd, db_path = tempfile.mkstemp()
    global Book_A_ID, Book_B_ID
    database.DATABASE = db_path
    database.init_database()

    # Insert sample books
    database.insert_book("Book A", "Author A", "1111111111111", 3, 3)
    database.insert_book("Book B", "Author B", "2222222222222", 2, 2)

    Book_A_ID = database.get_book_by_isbn("1111111111111")['id']
    Book_B_ID = database.get_book_by_isbn("2222222222222")['id']

    # Setup patron borrows
    borrow_book_by_patron("112233", Book_A_ID)
    borrow_book_by_patron("112233", Book_B_ID)

    yield

    # Cleanup
    os.close(db_fd)
    os.remove(db_path)


def test_patron_status_report():
    """Test that patron status report includes key sections."""
    report = get_patron_status_report("112233")

    # Structure checks
    assert isinstance(report, dict)
    assert "borrowed_books" in report
    assert "total_late_fees" in report
    assert "books_borrowed_count" in report
    assert "borrowing_history" in report

def test_patron_with_no_borrowed_books():
    """Test report for patron with no current or past borrows."""
    patron_id = "000000"
    report = get_patron_status_report(patron_id)

    assert report["books_borrowed_count"] == 0
    assert report["total_late_fees"] == 0.0
    assert report["borrowed_books"] == []

def test_patron_borrowed_books_count():
    """Test number of currently borrowed books."""
    report = get_patron_status_report("112233")
    assert report["books_borrowed_count"] == 2
    assert len(report["borrowed_books"]) == 2


def test_return_updates_patron_status():
    """Test that returning a book updates the patron’s borrowed list."""
    return_book_by_patron("112233", Book_A_ID)        # Return one of the books
    report = get_patron_status_report("112233")

    assert report["books_borrowed_count"] == 1        # Should only have one borrowed book now

def test_patron_borrow_history_contents():
    """Ensure borrowing history includes all past borrows including returned books."""
    return_book_by_patron("112233", Book_B_ID)
    report = get_patron_status_report("112233")
    assert len(report["borrowing_history"]) >= 2  # both borrowed books should appear

