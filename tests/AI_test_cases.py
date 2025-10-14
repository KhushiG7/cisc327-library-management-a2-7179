import pytest
import tempfile
import os
from datetime import datetime, timedelta
import database
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report
)

# -----------------------------
# Test Setup
# -----------------------------
@pytest.fixture(autouse=True)
def setup_database():
    """Create a temporary database before each test run."""
    db_fd, db_path = tempfile.mkstemp()
    database.DATABASE = db_path
    database.init_database()

    # Add sample data
    books = [
        ("Book A", "Author A", "1111111111111", 7),
        ("Book B", "Author B", "2222222222222", 1),
        ("Book C", "Author C", "3333333333333", 1),
        ("Book D", "Author D", "4444444444444", 1),
        ("Book E", "Author E", "5555555555555", 2),
        ("Book F", "Author F", "6666666666666", 3),
    ]
    for title, author, isbn, copies in books:
        database.insert_book(title, author, isbn, copies, copies)

    global Book_A_ID, Book_B_ID, Book_C_ID, Book_D_ID, Book_E_ID, Book_F_ID
    Book_A_ID = database.get_book_by_isbn("1111111111111")['id']
    Book_B_ID = database.get_book_by_isbn("2222222222222")['id']
    Book_C_ID = database.get_book_by_isbn("3333333333333")['id']
    Book_D_ID = database.get_book_by_isbn("4444444444444")['id']
    Book_E_ID = database.get_book_by_isbn("5555555555555")['id']
    Book_F_ID = database.get_book_by_isbn("6666666666666")['id']

    yield
    os.close(db_fd)
    os.remove(db_path)

# -----------------------------
# R1: Book Catalog Management
# -----------------------------
def test_add_book_valid():
    success, msg = add_book_to_catalog("New Book", "Author X", "7777777777777", 5)
    assert success is True
    assert "successfully added" in msg.lower()

def test_add_book_duplicate_isbn():
    success, msg = add_book_to_catalog("Duplicate Book", "Author A", "1111111111111", 2)
    assert not success
    assert "already exists" in msg.lower()

def test_add_book_invalid_fields():
    invalid_inputs = [
        ("", "Author", "1234567890123", 1),
        ("Title", "", "1234567890123", 1),
        ("Title", "Author", "123", 1),
        ("Title", "Author", "abcdefghijklm", 1),
        ("Title", "Author", "1234567890123", 0),
    ]
    for title, author, isbn, copies in invalid_inputs:
        success, msg = add_book_to_catalog(title, author, isbn, copies)
        assert not success

def test_add_book_whitespace_title():
    success, msg = add_book_to_catalog("   ", "Author X", "9999999999999", 1)
    assert not success

def test_add_book_long_title():
    long_title = "A" * 500
    success, msg = add_book_to_catalog(long_title, "Author Long", "8888888888888", 2)
    assert success is False

# -----------------------------
# R3: Borrow Books
# -----------------------------
def test_borrow_book_success():
    success, msg = borrow_book_by_patron("123456", Book_A_ID)
    assert success
    assert "successfully borrowed" in msg.lower()
    assert database.get_book_by_id(Book_A_ID)['available_copies'] == 6

def test_borrow_not_available():
    borrow_book_by_patron("123456", Book_B_ID)
    success, msg = borrow_book_by_patron("123456", Book_B_ID)
    assert not success
    assert "not available" in msg.lower()

def test_borrow_invalid_patron_id_format():
    for pid in ["abc123", "12ab56", "12345"]:
        success, msg = borrow_book_by_patron(pid, Book_A_ID)
        assert not success
        assert "invalid patron" in msg.lower()

def test_borrow_same_book_twice():
    borrow_book_by_patron("123456", Book_C_ID)
    success, msg = borrow_book_by_patron("123456", Book_C_ID)
    assert not success
    assert "already borrowed" in msg.lower() or "not available" in msg.lower()

def test_borrow_exceed_max_limit():
    patron = "654321"
    for b_id in [Book_A_ID, Book_B_ID, Book_C_ID, Book_D_ID, Book_E_ID]:
        borrow_book_by_patron(patron, b_id)
    success, msg = borrow_book_by_patron(patron, Book_F_ID)
    assert not success
    assert "maximum borrowing limit" in msg.lower()

def test_borrow_nonexistent_book():
    success, msg = borrow_book_by_patron("123456", 9999)
    assert not success
    assert "book not found" in msg.lower()

# -----------------------------
# R4: Return Books
# -----------------------------
def test_return_book_success():
    patron = "777777"
    borrow_book_by_patron(patron, Book_A_ID)
    success, msg = return_book_by_patron(patron, Book_A_ID)
    assert success
    assert "successfully returned" in msg.lower()

def test_return_book_not_borrowed():
    success, msg = return_book_by_patron("123456", Book_D_ID)
    assert not success
    assert "not borrowed" in msg.lower()

def test_return_book_late_fee_display():
    patron = "888888"
    borrow_book_by_patron(patron, Book_E_ID)
    conn = database.get_db_connection()
    overdue_due_date = datetime.now() - timedelta(days=10)
    conn.execute("UPDATE borrow_records SET due_date=? WHERE patron_id=? AND book_id=? AND return_date IS NULL",
                 (overdue_due_date.isoformat(), patron, Book_E_ID))
    conn.commit()
    conn.close()
    success, msg = return_book_by_patron(patron, Book_E_ID)
    assert success
    assert "late fee" in msg.lower()

# -----------------------------
# R5: Late Fee Calculation
# -----------------------------
def test_late_fee_calculation():
    patron = "999999"
    borrow_book_by_patron(patron, Book_F_ID)
    conn = database.get_db_connection()
    overdue_date = datetime.now() - timedelta(days=10)
    conn.execute("UPDATE borrow_records SET borrow_date=?, due_date=? WHERE patron_id=? AND book_id=?",
                 (overdue_date.isoformat(), (overdue_date + timedelta(days=7)).isoformat(), patron, Book_F_ID))
    conn.commit()
    conn.close()

    fee_info = calculate_late_fee_for_book(patron, Book_F_ID)
    assert fee_info['fee_amount'] > 0
    assert fee_info['days_overdue'] >= 0

def test_late_fee_exact_due_date():
    patron = "555555"
    borrow_book_by_patron(patron, Book_B_ID)
    conn = database.get_db_connection()
    conn.execute("UPDATE borrow_records SET due_date=? WHERE patron_id=? AND book_id=?",
                 (datetime.now().isoformat(), patron, Book_B_ID))
    conn.commit()
    conn.close()
    fee_info = calculate_late_fee_for_book(patron, Book_B_ID)
    assert fee_info['fee_amount'] == 0

def test_late_fee_max_cap():
    patron = "444444"
    borrow_book_by_patron(patron, Book_E_ID)
    conn = database.get_db_connection()
    overdue_date = datetime.now() - timedelta(days=50)
    conn.execute("UPDATE borrow_records SET borrow_date=?, due_date=? WHERE patron_id=? AND book_id=?",
                 (overdue_date.isoformat(), (overdue_date + timedelta(days=7)).isoformat(), patron, Book_E_ID))
    conn.commit()
    conn.close()
    fee_info = calculate_late_fee_for_book(patron, Book_E_ID)
    assert fee_info['fee_amount'] == 15.0

# -----------------------------
# R6: Search Books
# -----------------------------
def test_search_by_title_partial():
    results = search_books_in_catalog("Book A", "title")
    assert len(results) >= 1

def test_search_by_author_partial():
    results = search_books_in_catalog("Author B", "author")
    assert len(results) == 1

def test_search_by_isbn_exact():
    results = search_books_in_catalog("1111111111111", "isbn")
    assert len(results) == 1

def test_search_invalid_input():
    results = search_books_in_catalog("", "title")
    assert results == []
    results = search_books_in_catalog("Book A", "invalid_type")
    assert results == []

def test_search_case_insensitive():
    results = search_books_in_catalog("book a", "title")
    assert any("book a" in r["title"].lower() for r in results)

# -----------------------------
# R7: Patron Status Report
# -----------------------------
def test_patron_status_report_with_books():
    patron = "123456"
    borrow_book_by_patron(patron, Book_A_ID)
    report = get_patron_status_report(patron)
    assert report['patron_id'] == patron
    assert report['books_borrowed_count'] >= 1
    assert isinstance(report['borrowed_books'], list)
    assert isinstance(report['borrowing_history'], list)

def test_patron_status_report_no_books():
    report = get_patron_status_report("000000")
    assert report['books_borrowed_count'] == 0
    assert report['total_late_fees'] == 0.0
    assert report['borrowed_books'] == []

