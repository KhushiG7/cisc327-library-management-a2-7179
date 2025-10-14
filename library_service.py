"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books,
    get_patron_borrow_history
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    #Adding a condition to check ISBN only contain digits
    if not isbn.isdigit():
        return False, "ISBN should only contain digits"
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check if patron has already borrowed this book
    borrowed_books = get_patron_borrowed_books(patron_id)
    borrowed_ids = [b["book_id"] for b in borrowed_books]
    if book_id in borrowed_ids:
        return False, "You have already borrowed a copy of this book."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:   #changed to >= to apply max borrow 5 lofic correctly
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4 as per requirements.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to return

    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    # Check if the book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Get patron's currently borrowed books
    borrowed_books = get_patron_borrowed_books(patron_id)

    # Check if patron has borrowed this book and not yet returned it
    borrowed_ids = []
    for b in borrowed_books:
        borrowed_ids.append(b["book_id"])

    if book_id not in borrowed_ids:
        return False, "This book is currently not borrowed by you."

    # Update borrow record with return date
    return_date = datetime.now()
    return_success = update_borrow_record_return_date(patron_id, book_id, return_date)
    if not return_success:
        return False, "Database error occurred while updating borrow record."

    # Increase available copies by 1
    availability_success = update_book_availability(book_id, +1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."

    #Calculate late fee if applicable
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    if fee_info is not None and 'fee_amount' in fee_info:
        late_fee = fee_info['fee_amount']
    else:
        late_fee = 0.0
    
    return True, (
        f'Successfully returned "{book["title"]}". '
        f'Return Date: {return_date.strftime("%Y-%m-%d")}. '
        f'Late fee owed: ${late_fee:.2f}.'
    )

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    Implements R5: Late Fee Calculation API

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book

    Returns:
        dict: {
            fee_amount : float,
            days_overdue : int,      
            message : str            
        }
    """

    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {"fee_amount": 0.0, "days_overdue": 0, "message": "Invalid patron ID."}

    # Check if the book exists
    book = get_book_by_id(book_id)
    if not book:
        return {"fee_amount": 0.0, "days_overdue": 0, "message": "Book not found."}

    # Check if patron has borrowed this book
    borrowed_books = get_patron_borrowed_books(patron_id)
    borrowed_book = None
    for b in borrowed_books:
        if b["book_id"] == book_id:
            borrowed_book = b
            break

    if not borrowed_book:
        return {"fee_amount": 0.0, "days_overdue": 0, "message": "This book is currently not borrowed by you."}

    # Calculate days overdue
    today = datetime.now()
    due_date = borrowed_book["due_date"]
    days_overdue = (today - due_date).days
    if days_overdue <= 0:
        return {"fee_amount": 0.0, "days_overdue": 0, "message": "Book is not overdue."}

    # Calculate fee
    if days_overdue <= 7:
        fee = days_overdue * 0.50
    else:
        fee = (7 * 0.50) + ((days_overdue - 7) * 1.00)

    # Max fee at $15
    if fee > 15.0:
        fee = 15.0

    return {
        "fee_amount": round(fee, 2),
        "days_overdue": days_overdue,
        "message": f'Late fee for "{book["title"]}" calculated successfully.'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    Implements R6: Book Search Functionality

    Args:
        search_term: The term to search for (title, author, or ISBN)
        search_type: Type of search ('title', 'author', or 'isbn')

    Returns:
        list of dict: Matching books in the same format as catalog display
    """
    # Validate input
    if not search_term or not search_term.strip():
        return []

    if search_type not in ["title", "author", "isbn"]:
        return []

    search_term = search_term.strip().lower()
    books = get_all_books()
    results = []

    for book in books:
        # Title search — partial and case-insensitive
        if search_type == "title" and search_term in book["title"].lower():
            results.append(book)

        # Author search — partial and case-insensitive
        elif search_type == "author" and search_term in book["author"].lower():
            results.append(book)

        # ISBN search — exact match
        elif search_type == "isbn" and search_term == book["isbn"]:
            results.append(book)

    return results

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    Implements R7: Patron Status Report
    
    Args:
        patron_id: 6-digit library card ID
        
    Returns:
        dict: {
            'patron_id': str,
            'borrowed_books': List[Dict],  # Books not yet returned with due dates and late fees
            'total_late_fees': float,
            'books_borrowed_count': int,
            'borrowing_history': List[Dict]       # All past borrowed books including returned
        }
    """
    report = {
        'patron_id': patron_id,
        'borrowed_books': [],
        'total_late_fees': 0.0,
        'books_borrowed_count': 0,
        'borrowing_history': []
    }

    # Currently borrowed books count
    borrowed_books = get_patron_borrowed_books(patron_id)
    report['books_borrowed_count'] = len(borrowed_books)

    total_late_fees = 0.0
    for book in borrowed_books:
        fee_info = calculate_late_fee_for_book(patron_id, book['book_id'])
        late_fee = fee_info.get('fee_amount', 0.0) if fee_info else 0.0
        total_late_fees += late_fee

        #Currently Borrowed books with due dates
        report['borrowed_books'].append({
            'book_id': book['book_id'],
            'title': book['title'],
            'author': book['author'],
            'borrow_date': book['borrow_date'].strftime("%Y-%m-%d"),
            'due_date': book['due_date'].strftime("%Y-%m-%d"),
            'is_overdue': book['is_overdue'],
            'late_fee': late_fee
    })

    #Total Late fees
    report['total_late_fees'] = total_late_fees

    # Borrow history
    report['borrowing_history'] = get_patron_borrow_history(patron_id)

    return report