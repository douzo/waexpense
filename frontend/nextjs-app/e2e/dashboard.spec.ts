import { test, expect } from "@playwright/test";

const stubAuthStorage = async (page: any) => {
  await page.addInitScript(() => {
    localStorage.setItem("wa_token", "test-access");
    localStorage.setItem("wa_refresh_token", "test-refresh");
  });
};

const stubExpenses = async (page: any, items: any[]) => {
  await page.route("**/api/expenses**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items }),
    });
  });
};

test("dashboard renders expenses", async ({ page }) => {
  await stubAuthStorage(page);

  const today = new Date().toISOString().slice(0, 10);
  await stubExpenses(page, [
    {
      id: "1",
      user_id: "u1",
      amount: 12.5,
      currency: "USD",
      category: "food",
      merchant: "Local Cafe",
      notes: "Latte",
      expense_date: today,
      receipt_id: null,
      created_at: "2025-01-02T10:00:00Z",
    },
  ]);

  await page.goto("/");

  const row = page.locator('[class*="expenseRow"]').filter({ hasText: "Local Cafe" });
  await expect(row).toBeVisible();
  await expect(row.locator('[class*="expenseAmount"]')).toHaveText("$12.50");
});

test("dashboard shows empty state when no expenses", async ({ page }) => {
  await stubAuthStorage(page);
  await stubExpenses(page, []);

  await page.goto("/");

  await expect(page.getByText("Nothing to show yet.")).toBeVisible();
});

test("month navigation updates the label", async ({ page }) => {
  await stubAuthStorage(page);
  await stubExpenses(page, []);

  await page.goto("/");

  const label = page.locator('[class*="monthLabel"]');
  const before = await label.textContent();
  await page.getByLabel("Next month").click();
  const after = await label.textContent();
  expect(before).not.toEqual(after);
});

test("edit expense flow updates and returns to list", async ({ page }) => {
  await stubAuthStorage(page);
  const today = new Date().toISOString().slice(0, 10);
  await stubExpenses(page, [
    {
      id: "1",
      user_id: "u1",
      amount: 12.5,
      currency: "USD",
      category: "food",
      merchant: "Local Cafe",
      notes: "Latte",
      expense_date: today,
      receipt_id: null,
      created_at: "2025-01-02T10:00:00Z",
    },
  ]);

  let updatePayload: any = null;
  await page.route("**/api/expenses/1", async (route) => {
    updatePayload = JSON.parse(route.request().postData() || "{}");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "1",
        user_id: "u1",
        amount: 15,
        currency: "USD",
        category: "food",
        merchant: "Local Cafe",
        notes: "Updated",
        expense_date: today,
        receipt_id: null,
        created_at: "2025-01-02T10:00:00Z",
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Edit" }).click();

  await expect(page.getByText("Edit transaction")).toBeVisible();
  await page
    .locator('[class*="editRow"]')
    .filter({ hasText: "Note" })
    .locator("input")
    .fill("Updated");
  await page.getByRole("button", { name: "Update" }).click();

  await expect(page.getByText("Transaction")).toBeVisible();
  expect(updatePayload?.notes).toBe("Updated");
});

test("menu opens and saves profile name", async ({ page }) => {
  await stubAuthStorage(page);
  await stubExpenses(page, []);

  await page.route("**/api/profile", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "u1", whatsapp_id: "wa1", name: "Asha" }),
      });
      return;
    }
    if (route.request().method() === "PATCH") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "u1", whatsapp_id: "wa1", name: "Asha N" }),
      });
      return;
    }
    await route.fallback();
  });

  await page.goto("/");
  await page.getByLabel("Open menu").click();
  await expect(page.getByText("Profile & Settings")).toBeVisible();
  await page.getByLabel("Your name").fill("Asha N");
  await page.getByRole("button", { name: "Save profile" }).click();
});
