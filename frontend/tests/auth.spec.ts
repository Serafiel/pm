import { expect, test } from "@playwright/test";

test("unauthenticated visit to / redirects to /login", async ({ page }) => {
  await page.goto("/");
  await page.waitForURL("/login");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.getByLabel("Username")).toBeVisible();
});

test("wrong credentials shows error and does not redirect", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrongpassword");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByText("Invalid username or password.")).toBeVisible();
  await expect(page).toHaveURL("/login");
});

test("correct credentials redirect to board", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
});

test("sign out clears session and redirects to /login", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("/");
  await page.getByRole("button", { name: /sign out/i }).click();
  await page.waitForURL("/login");
  await expect(page.getByLabel("Username")).toBeVisible();
});
