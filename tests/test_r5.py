import pytest
import tempfile
import os
import database
from services.library_service import calculate_late_fee_for_book, borrow_book_by_patron
import datetime

@pytest.fixture(autouse=True)
def setup_database():
    """Set up a temp SQLite DB for R5 tests."""
    db_fd, db_path = tempfile.mkstemp()
    global Book_A_ID, Book_B_ID
    database.DATABASE = db_path
    database.init_database()

    # Insert test books
    database.insert_book("Book A", "Author A", "1111111111111", 7, 7)
    database.insert_book("Book B", "Author B", "2222222222222", 1, 1)

    Book_A_ID = database.get_book_by_isbn("1111111111111")['id']
    Book_B_ID = database.get_book_by_isbn("2222222222222")['id']

    # Borrow Book A for patron "123456" to setup late fee tests
    borrow_book_by_patron("123456", Book_A_ID)

    yield

    # Cleanup
    os.close(db_fd)
    os.remove(db_path)

def test_no_late_fee_if_not_overdue():
    """Test that no late fee is applied if book is not overdue."""
    # Borrow date: today, due in 14 days not overdue
    fee_info = calculate_late_fee_for_book("123456", Book_A_ID)
    assert fee_info['fee_amount'] == 0.0
    assert fee_info['days_overdue'] == 0

def test_late_fee_within_first_7_days():
    """Test late fee calculation for overdue within first 7 days."""
    borrow_date = datetime.datetime.now() - datetime.timedelta(days=20)
    due_date = datetime.datetime.now() - datetime.timedelta(days=6)  # 6 days overdue
    database.insert_borrow_record("654321", Book_B_ID, borrow_date, due_date)

    fee_info = calculate_late_fee_for_book("654321", Book_B_ID)
    assert fee_info['days_overdue'] == 6
    assert fee_info['fee_amount'] == 6 * 0.50  # $0.50/day

def test_late_fee_after_first_7_days():
    """Test late fee for overdue more than 7 days (additional $1/day)."""
    borrow_date = datetime.datetime.now() - datetime.timedelta(days=29)
    due_date = datetime.datetime.now() - datetime.timedelta(days=12)  # 12 days overdue
    database.insert_borrow_record("654321", Book_A_ID, borrow_date, due_date)

    fee_info = calculate_late_fee_for_book("654321", Book_A_ID)
    assert fee_info['days_overdue'] == 12
    # 7 days * 0.50 + 5 days * 1.00
    expected_fee = (7 * 0.50) + (5 * 1.00)
    assert fee_info['fee_amount'] == expected_fee

def test_late_fee_maximum_at_15():
    """Test that late fee is capped at $15 per book."""
    borrow_date = datetime.datetime.now() - datetime.timedelta(days=50)
    due_date = datetime.datetime.now() - datetime.timedelta(days=30)  # 30 days overdue
    database.insert_borrow_record("654321", Book_B_ID, borrow_date, due_date)

    fee_info = calculate_late_fee_for_book("654321", Book_B_ID)
    assert fee_info['days_overdue'] == 30
    assert fee_info['fee_amount'] <= 15.0