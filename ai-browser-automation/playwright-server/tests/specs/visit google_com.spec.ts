import { test, expect } from "playwright/test";
import SuccessfulGoogleSearchPage from '../pages/SuccessfulGoogleSearchPage';

test('Successful Google Search', async ({ page }) => {
  const successfulGoogleSearchPage = new SuccessfulGoogleSearchPage(page);

  // Step 1: Open a web browser.
  // Expected Result: Web browser application is launched.

  // Step 2: Navigate to google.com in the address bar.
  // Expected Result: Google's homepage is displayed with a prominent search bar.
  await page.goto('https://www.google.com');
  await expect(page).toHaveScreenshot();

  // Step 3: Enter a search query (e.g., 'test automation') into the search bar.
  // Expected Result: The search query is entered into the search bar.
  await successfulGoogleSearchPage.enterSearchQuery('test automation');
  await expect(page).toHaveScreenshot();

  // Step 4: Press the 'Enter' key or click the 'Google Search' button.
  // Expected Result: The search results page is displayed.
  await successfulGoogleSearchPage.performSearch();
  await expect(page).toHaveScreenshot();

  // Verification: Verify that the search results page displays relevant results related to the search query and that the page loads without errors.
  // Add assertions for relevant search results here.  Example:
  // await expect(page.locator('#search')).toContainText('test automation');
  await expect(page).toHaveScreenshot();
});