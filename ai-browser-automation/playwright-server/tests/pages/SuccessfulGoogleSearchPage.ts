import { type Page } from "playwright/test";

export default class SuccessfulGoogleSearchPage {
  readonly page: Page;
  readonly searchBar: string = 'textarea[aria-label="Search"]';
  readonly searchButton: string = 'input[value="Google Search"]'; // Using value attribute for more robustness
  readonly searchResults: string = '#search';

  constructor(page: Page) {
    this.page = page;
  }

  async openBrowser(): Promise<void> {
    // Step 1: Open a web browser.
    // Expected Result: Web browser application is launched.
    // No specific action needed in POM as browser launch is handled in test setup.
  }

  async navigateToGoogle(): Promise<void> {
    // Step 2: Navigate to google.com in the address bar.
    // Expected Result: Google's homepage is displayed with a prominent search bar.
    await this.page.goto("https://www.google.com");
  }

  async enterSearchQuery(query: string): Promise<void> {
    // Step 3: Enter a search query (e.g., 'test automation') into the search bar.
    // Expected Result: The search query is entered into the search bar.
    await this.page.locator(this.searchBar).fill(query);
  }

  async performSearch(): Promise<void> {
    // Step 4: Press the 'Enter' key or click the 'Google Search' button.
    // Expected Result: The search results page is displayed.
     // Attempt to click the "Google Search" button first
    try {
      await this.page.locator(this.searchButton).click();
    } catch (error) {
      // If the button is not visible or clickable (e.g., due to autocomplete suggestions), press Enter
      await this.page.locator(this.searchBar).press("Enter");
    }
  }

  async verifySearchResults(query: string): Promise<boolean> {
    // Verification: Verify that the search results page displays relevant results related to the search query and that the page loads without errors.
    await this.page.waitForSelector(this.searchResults);
    const resultsText = await this.page.locator(this.searchResults).innerText();
    return resultsText.toLowerCase().includes(query.toLowerCase());
  }
}