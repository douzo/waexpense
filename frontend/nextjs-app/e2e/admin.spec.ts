import { test, expect } from "@playwright/test";

test("admin toggles premium", async ({ page }) => {
  await page.route("**/api/admin/users/**/premium", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "u1",
        whatsapp_id: "15551234567",
        is_premium: true,
      }),
    });
  });

  await page.goto("/admin");
  await page.getByLabel("Admin token").fill("test-admin-key");
  await page.getByLabel("WhatsApp ID").fill("15551234567");
  await page.getByLabel("Set as Premium").check();
  await page.getByRole("button", { name: "Update user" }).click();

  await expect(page.getByText("set to Premium")).toBeVisible();
});
