# Assignment 1

**Author:** Khushi Grover  
**ID:** 20367179  
**Group:** 2

## Project Implementation Status

After going through the application and testing all functionalities, I summarized the implementation status of each requirement below:

| Requirement ID | Functionality Description | Implementation Status | Notes / Missing Features |
|----------------|--------------------------|---------------------|------------------------|
| R1 | Add Book – add new books with title, author, ISBN, total copies | Complete | Adding books works as expected. Validates ISBN is exactly 13 digits. Alerts user if any required fields are missing or if copies <= 0. |
| R2 | Book Catalog – display all books with details and actions | Complete | All books are displayed neatly in a table. Includes ID, title, author, ISBN, availability, and Borrow action button. |
| R3 | Borrow Book – validate patron ID, update availability, enforce borrowing limit | Complete with error | Borrowing updates availability correctly. Maximum of 6 books enforced instead of 5. No consolidated view of borrowed books. |
| R4 | Return Book – process returned books and update availability | Not implemented | Input feilds are present but functionality is not yet implemented. Verifying Patron ID, Updating available copies and late fee calculation is missing. Error Messega is displayed - Functionality not yet implemented |
| R5 | Late Fee Calculation – display late fee amount and days overdue | Not Implemented | Return book feature is not implemented, so late fee display is not visible. Logic for calculating late fee is missing |
| R6 | Search Book – search by title, author, or ISBN | Not Implemented | Only input fields are present, but search functionality is not implemented. Partial matching for title/author and exact ISBN matching is missing. Only error message is displayed instead of results |
| R7 | Patron Status Report – display patron details with books borrowed and late fees owed | Not Implemented | Implementation of all the feilds including borrowing history, books borrowed with due dates, late fees owed are missing. Menu option for patron status in the main interface is also missing. |

---

## R1: Add book to Catalog
- **Tests included:**
  - Add book with valid input
  - Make sure author/title is not missing
  - Author doesn't exceed the character limit
  - ISBN is not too short
  - Total book copies cannot be negative
- **File:** `tests/test_r1.py`  
- **Summary:** Verified that book addition succeeds for valid inputs and fails for invalid data or violations of constraints.

---

## R3: Book Borrowing
- **Tests included:**
  - Successful borrowing of available books
  - Borrowing fails if book unavailable
  - Borrowing fails with invalid book ID
  - Patron borrowing limit enforced (max 5 books)
- **File:** `tests/test_r3.py`  
- **Summary:** Ensures correct borrowing behavior, availability checks, invalid IDs, and limit enforcement. Lest test case failed because there is an error in the implementation of max limit

---

## R4: Book Return Processing
- **Tests included:**
  - Successful return of borrowed books
  - Return fails if book not borrowed by that patron
  - Return fails if invalid book ID is entered
  - Late fee calculation setup for overdue book
- **File:** `tests/test_r4.py`  
- **Summary:** Confirms return processing and verifies the patron that borrowed that book. Late fee is applied when book is overdue. Every test case failed because this function is not yet implemented.

---

## R5: Late Fee Calculation API
- **Tests included:**
  - No late fee if returned within 14 days
  - Late fee for first 7 overdue days ($0.50/day)
  - Late fee after first 7 overdue days ($1/day)
  - Late fee can be maximum $15 per book
- **File:** `tests/test_r5.py`  
- **Summary:** Verifies late fee calculation under different overdue scenarios and implementation of maximum fee. Every test case failed because this function is not yet implemented.

---

## R6: Book Search
- **Tests included:**
  - Partial, case-insensitive search by title
  - Partial, case-insensitive search by author
  - Exact match search by ISBN
  - Search returning no results
  - Invalid search type gives no results
- **File:** `tests/test_r6.py`  
- **Summary:** Ensures search API handles all input cases correctly. Every test case failed because this function is not yet implemented.

---

## R7: Patron Status Report
- **Tests included:**
  - Confirm that report contains borrowed books, total late fees, books borrowed count, and borrowing history
  - Patron with no borrowed books returns empty list and zero counts/fees
  - Correct count of borrowed books
  - Returning a book updates borrowed books count
- **File:** `tests/test_r7.py`  
- **Summary:** Validates patron status report returns expected fields and reflects borrowing activity accurately.

---

### Notes
- All tests use **temporary SQLite databases** for isolation.
- Some tests for features not yet implemented (e.g., late fees in R4, full status report in R7) are expected to fail until implementation is complete.
- Tests follow **pytest conventions** with fixtures for setup and teardown.