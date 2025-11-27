import { test, expect } from "playwright/test";

test('AI Generated Flow', async ({ page }) => {
  await page.goto('https://www.google.com');
  await page.screenshot({ path: 'google_homepage.png' });
});