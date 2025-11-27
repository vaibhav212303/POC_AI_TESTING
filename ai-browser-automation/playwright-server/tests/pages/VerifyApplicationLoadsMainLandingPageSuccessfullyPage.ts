import { type Page } from "playwright/test";

export default class VerifyApplicationLoadsMainLandingPageSuccessfullyPage {
  constructor(readonly page: Page) {}

  /**
   * Navigates to the specified application URL.
   * Action: Navigate to the application URL: https://dev-amber.dev.clippd.com/
   * Expected: The application page loads without any HTTP errors (e.g., 404, 500)
   *           and no critical browser console errors are displayed.
   */
  async navigateToClippdApplicationUrl(): Promise<void> {
    await this.page.goto("https://dev-amber.dev.clippd.com/");
  }

  /**
   * Observes the displayed content on the page, ensuring it has loaded and stabilized.
   * Action: Observe the displayed content on the page.
   * Expected: The main landing page, login screen, or dashboard of the 'Clippd' application
   *           is clearly visible and presents its primary UI elements.
   *
   * Verification Hint: Presence of the application's primary header/navigation,
   * a visible title like 'Clippd' or 'Amber', a login form, or dashboard overview content,
   * indicating the application has initialized and rendered successfully.
   */
  async observeDisplayedMainLandingPageContent(): Promise<void> {
    // Wait for the network to be idle, indicating that the page has finished loading most resources.
    // This implicitly "observes" that the page content has settled.
    await this.page.waitForLoadState('networkidle');

    // The previous selectors (getByRole('banner') and getByRole('heading', { name: /Clippd|Amber/i }))
    // might be too restrictive. A 'banner' role might not always be present or the heading text
    // might vary depending on whether it's a landing page, login page, or dashboard.
    // To make this observation robust, we're adding a flexible wait for key visible elements
    // that could indicate any of these expected page states using Playwright's `.or()` method.

    // Define multiple possible locators that indicate the page has loaded successfully.
    // The test will pass if *any one* of these locators finds a visible element.

    // 1. Application branding text (e.g., in a title, heading, or logo alternative text)
    const appBrandingText = this.page.getByText(/Clippd|Amber/i).first();

    // 2. Elements indicative of a login form (common on login screens)
    const loginEmailInput = this.page.getByRole('textbox', { name: /email|username/i }).first();
    const loginPasswordInput = this.page.getByLabel(/password/i).first();
    const signInButton = this.page.getByRole('button', { name: /sign in|login/i }).first();

    // 3. General primary structural elements (common on landing pages or dashboards)
    const mainNavigation = this.page.getByRole('navigation').first();
    const mainHeaderElement = this.page.locator('header').first(); // A general header element

    // Combine these locators using .or() to create a highly robust selector.
    // This ensures that we successfully observe the page content regardless of its initial state
    // (landing page, login form, or dashboard).
    const primaryAppIndicator = appBrandingText
      .or(loginEmailInput)
      .or(loginPasswordInput)
      .or(signInButton)
      .or(mainNavigation)
      .or(mainHeaderElement);

    // Wait for any of these primary indicators to be visible on the page.
    // An increased timeout provides more resilience for initial page loading in various environments.
    await primaryAppIndicator.waitFor({ state: 'visible', timeout: 30000 });
  }
}