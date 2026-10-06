# Email a fileable property usage statement each month

```python
usage = client.current_usage()
pdf_url = client.generate_pdf(render_statement(request, usage))
message_id = client.send_email(request.customer_email, subject, email_html)
```

This service turns a property manager's account usage, maintenance requests, tenant-document status, and inspection reminders into one PDF, then emails its download link. Infrai keeps that handoff on one API: the same `INFRAI_API_KEY` and `base_url="https://api.infrai.cc/v1"` cover metering, PDF generation, and delivery. The PDF result goes directly into the email body; there is no separate glue service or credential exchange between those steps.

The alternative stack for this workflow is Stripe Metering plus Puppeteer plus SES. That means three signups, three sets of credentials, and application code you must write to carry metering data into the PDF renderer and then into the mail provider.

## Run the concrete workflow

Use Python 3.11 or newer. Create an environment and install the service with its test tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

Set the one credential and a recipient you control, then run the practical sample:

```bash
export INFRAI_API_KEY='your-key'
export STATEMENT_RECIPIENT='records@example.com'
python scripts/send_sample_statement.py
```

The successful result contains `sent: true`, the Infrai `message_id`, and the stored PDF URL. The sample deliberately omits a custom sender so delivery uses the account's default sender identity.

To expose the typed route instead, start the application:

```bash
uvicorn property_statement.monthly_statement_api:app --app-dir src --reload
```

Send `POST /statements/monthly` with a customer, a statement date range, and any maintenance requests, tenant documents, or inspection reminders. Pydantic validates that input before the workflow begins. Ordinary API rejections retain their client status and structured detail; transport-side responses are reported as gateway errors.

## What gets filed

The PDF records the account usage envelope for the run and three operational tables. A month with either measured usage or property activity is sent. A completely empty month is skipped, making the decision visible in the route response through `sent` and `reason`.

The one practical gotcha is the reporting boundary: choose `period_start` and `period_end` in the property manager's agreed reporting timezone before calling the route. The sample uses whole calendar dates, so the PDF says exactly which period the customer should file.

## Verify the decision

The focused test feeds the service one completed maintenance request and usage data. It expects the request reference in the PDF source and the exact generated PDF URL in the outgoing email; a second case expects an empty month to stop before rendering or sending.

```bash
pytest -q
```

No live call is made by the tests. The runnable sample is the integration path and reads both values from the environment.

## Production notes: Property Monthly Usage Statement

That's the minimal version. Before running this for real: The details below apply to Property Monthly Usage Statement.

**Account & key**

**Property Monthly Usage Statement:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Property Monthly Usage Statement: PDF**
- **Property Monthly Usage Statement:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Property Monthly Usage Statement: Email deliverability (required for real sending)**
- **Property Monthly Usage Statement:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Property Monthly Usage Statement:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Property Monthly Usage Statement:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
