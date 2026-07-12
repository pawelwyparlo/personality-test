import { expect, test } from '@playwright/test'

/**
 * Happy-path e2e for the Quick form, driven through the real UI against the
 * running Compose stack (requires VITE_TEST_MODE=true so the demographics
 * prefill and "Autofill & finish" control are present).
 *
 * Flow: start → select Quick → start the run → autofill all 60 items → land on
 * the report → assert 5 domain bars + a narrative render → the PDF endpoint
 * returns real %PDF bytes.
 */
test('quick form: start → autofill → domain-only report → PDF', async ({ page, request, baseURL }) => {
  await page.goto('/')

  // Select the Quick length; the CTA label should follow the selection.
  await page.getByRole('button', { name: /Quick/ }).click()
  const startCta = page.getByRole('button', { name: /Start the Quick test/ })
  await expect(startCta).toBeVisible()

  // Test mode prefills age + sex, so the run starts in one click.
  await startCta.click()

  // On the test screen the Quick form has exactly 60 items.
  await expect(page.getByText('Question 1 of 60')).toBeVisible()

  // Autofill every remaining item through the normal answer path, then finish.
  await page.getByRole('button', { name: /Autofill & finish/ }).click()

  // We land on the report for this run.
  await expect(page).toHaveURL(/\/report\//)
  const runId = page.url().split('/').pop() as string

  // Five domain bars (OCEAN) render, with a narrative pull-quote.
  await expect(page.getByText('Your five dimensions')).toBeVisible()
  for (const name of [
    'Openness',
    'Conscientiousness',
    'Extraversion',
    'Agreeableness',
    'Neuroticism',
  ]) {
    await expect(page.getByText(name, { exact: true })).toBeVisible()
  }
  await expect(page.locator('blockquote')).not.toBeEmpty()

  // The Quick-only note appears (domain-only report; Full adds facet nuance).
  await expect(
    page.getByText('Quick test — the Full test adds facet-level nuance.'),
  ).toBeVisible()

  // The PDF endpoint returns real PDF bytes for this facetless run.
  const pdf = await request.get(`${baseURL}/api/v1/reports/${runId}/pdf`)
  expect(pdf.status()).toBe(200)
  expect(pdf.headers()['content-type']).toContain('application/pdf')
  const body = await pdf.body()
  expect(body.subarray(0, 4).toString('latin1')).toBe('%PDF')
  expect(body.byteLength).toBeGreaterThan(2000)
})
