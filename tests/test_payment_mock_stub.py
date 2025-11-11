import pytest
from services.library_service import (
    add_book_to_catalog,
    pay_late_fees,
    refund_late_fee_payment,
    borrow_book_by_patron
)

from services.payment_service import PaymentGateway

"""Test cases for pay_late_fees using stubbing and mocking techniques"""

def test_pay_late_fees_success(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 5.5})
    mocker.patch('services.library_service.get_book_by_id', return_value={'title': 'Book A'})
    pg = mocker.Mock(spec=PaymentGateway)
    pg.process_payment.return_value = (True, "txn_123", "Paid")
    success, msg, txn_id = pay_late_fees("112233", 100, pg)
    assert success is True
    assert "payment successful" in msg.lower()
    assert txn_id == "txn_123"
    pg.process_payment.assert_called_once_with(
        patron_id="112233", amount=5.5, description="Late fees for 'Book A'"
    )

def test_pay_late_fees_payment_declined(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 7})
    mocker.patch('services.library_service.get_book_by_id', return_value={'title': 'Book A'})
    pg = mocker.Mock(spec=PaymentGateway)
    pg.process_payment.return_value = (False, None, "Declined")
    success, msg, txn_id = pay_late_fees("223344", 102, pg)
    assert not success
    assert "payment failed" in msg.lower()
    assert txn_id is None
    pg.process_payment.assert_called_once_with(
        patron_id="223344", amount= 7, description="Late fees for 'Book A'"
    )

def test_pay_late_fees_invalid_patron(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 4})
    mocker.patch('services.library_service.get_book_by_id', return_value={'title': 'Book A'})
    pg = mocker.Mock(spec=PaymentGateway)
    success, msg, txn_id = pay_late_fees("xyz", 200, pg)
    assert success is False
    assert "invalid patron id" in msg.lower()
    assert txn_id is None
    pg.process_payment.assert_not_called()

def test_pay_late_fees_zero_fee(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 0})
    mocker.patch('services.library_service.get_book_by_id', return_value={'title': 'Book A'})
    pg = mocker.Mock(spec=PaymentGateway)
    success, msg, txn_id = pay_late_fees("998877", 555, pg)
    assert not success
    assert "no late fees" in msg.lower()
    assert txn_id is None
    pg.process_payment.assert_not_called()

def test_pay_late_fees_network_error(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 2.5})
    mocker.patch('services.library_service.get_book_by_id', return_value={'title': 'Book A'})
    pg = mocker.Mock(spec=PaymentGateway)
    pg.process_payment.side_effect = Exception("Service Down")
    success, msg, txn_id = pay_late_fees("554433", 17, pg)
    assert not success
    assert "payment processing error" in msg.lower()
    assert txn_id is None
    pg.process_payment.assert_called_once()

"""Test cases for refund_late_fees using stubbing and mocking techniques"""

def test_refund_late_fee_payment_success(mocker):
    pg = mocker.Mock(spec=PaymentGateway)
    pg.refund_payment.return_value = (True, "Refund processed")
    success, msg = refund_late_fee_payment("txn_456", 6, pg)
    assert success is True
    assert "refund processed" in msg.lower()
    pg.refund_payment.assert_called_once_with("txn_456", 6)

def test_refund_late_fee_payment_invalid_transaction(mocker):
    pg = mocker.Mock(spec=PaymentGateway)
    success, msg = refund_late_fee_payment("wrong_id", 8, pg)
    assert not success
    assert "invalid transaction" in msg.lower()
    pg.refund_payment.assert_not_called()

@pytest.mark.parametrize("amt", [-5, 0, 17])
def test_refund_late_fee_payment_invalid_amounts(mocker, amt):
    """Rejects negative, zero, or excessive refund amounts."""
    pg = mocker.Mock(spec=PaymentGateway)
    success, msg = refund_late_fee_payment("txn_456", amt, pg)
    assert not success
    assert ("greater than 0" in msg or "exceeds" in msg)
    pg.refund_payment.assert_not_called()

"""Additional tests for improving coverage"""

def test_add_book_database_error(mocker):
    mocker.patch('services.library_service.get_book_by_isbn', return_value=None)
    mocker.patch('services.library_service.insert_book', return_value=False)
    from services.library_service import add_book_to_catalog
    success, msg = add_book_to_catalog("Database Failure Book", "Test Author", "9876543210123", 1)
    assert success is False
    assert "database error" in msg.lower()

def test_add_book_long_title(mocker):
    long_title = "A" * 201
    success, msg = add_book_to_catalog(long_title, "Author", "1234567890123", 1)
    assert not success
    assert "less than 200" in msg.lower()

def test_add_book_missing_author(mocker):
    success, msg = add_book_to_catalog("BOOK XYZ", "", "1234567890123", 1)
    assert not success
    assert "author is required" in msg.lower()

@pytest.mark.parametrize("patron_id", ["", "abcdef", "12ab56", "12345", "1234567"])
def test_invalid_patron_id_variants(patron_id):
    success, msg = borrow_book_by_patron(patron_id, 101)
    assert not success
    assert "invalid patron id" in msg.lower()

