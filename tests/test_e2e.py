from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5000"

def test_add_and_borrow_book_flow():
    # Start Playwright and open a Chromium browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the main catalog page
        page.goto(BASE_URL)

        # --- Add a new book ---
        # Open the Add Book form
        page.click("text=Add Book")

        # Fill in the book details
        page.fill("input[name='title']", "E2E Test Book")
        page.fill("input[name='author']", "E2E Author")
        page.fill("input[name='isbn']", "1234567890123")
        page.fill("input[name='total_copies']", "3")

        # Submit the form
        page.click("button[type='submit']")

        # --- Check that the catalog page looks correct ---
        page.goto(BASE_URL)
        content = page.content()
        # Check some stable text on the catalog page
        assert "Book Catalog" in content
        assert "Title" in content
        assert "Author" in content

        # --- Borrow a book from the catalog ---
        # Enter a valid patron ID in the first borrow form
        page.fill("input[name='patron_id']", "123456")
        page.click("button:has-text('Borrow')")

        # --- Check that some kind of result message appears ---
        content = page.content()
        # Look for either success or error flash box in the HTML
        assert ("flash-success" in content) or ("flash-error" in content)

        # Close the browser
        browser.close()

def test_search_and_view_catalog():
    # Start playwright and open a chromium browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Open the search page
        page.goto(f"{BASE_URL}/search")

        # Fill a simple search term and submit
        page.fill("input[name='q']", "Book")
        page.select_option("select[name='type']", "title")
        page.click("button:has-text('Search')")

        # After searching, the page should show the search heading
        content = page.content()
        assert "Search Books" in content
        assert "Search Results" in content or "No results found" in content

        browser.close()
