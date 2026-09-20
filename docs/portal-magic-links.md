# Portal magic links: consent and delivery outcomes

`POST /api/v1/portal/magic-link` returns a plain `PortalMagicLink` on HTTP 201.
The generated Portal APIs in TypeScript, Python, C# and Java expose the optional
`optIn` request object and `sendSuppressionReason` response field (Python uses
`opt_in` and `send_suppression_reason`).

For a recipient who has already consented to WhatsApp messages, record the real
consent evidence alongside link creation. This example shows the JSON fields;
replace its placeholders with your recipient and their existing consent record:

```json
{
  "formId": 42,
  "name": "Test Recipient",
  "phone": "+15555550100",
  "sendChannel": "whatsapp",
  "optIn": {
    "source": "web_form",
    "evidenceText": "consent-form-42",
    "evidenceUrl": "https://example.test/consents/42",
    "collectedWhen": "2026-09-17T12:00:00Z"
  }
}
```

`source` accepts `web_form`, `contract`, `in_person`, `import` or `api`.
`evidenceText` is required and cannot be blank. `evidenceUrl` is optional.
`collectedWhen` is the original consent date, defaults to now when omitted or
null, and cannot be more than one day in the future. Supplying an `optIn` block
requires valid source/evidence on every channel, but only WhatsApp records it.

Omit `optIn` or pass null when consent is already on file. Omitting `sendChannel`
continues to create a link without sending a message. Existing integrations do
not have to supply these new optional fields.

HTTP 201 means the link was created; inspect `sent` before assuming delivery.
When `sent` is false, `sendSuppressionReason` can explain why:

| Reason | Meaning |
| --- | --- |
| `whatsapp_no_optin` | No consent is on file; obtain and record consent before sending. |
| `whatsapp_optin_revoked` | Previous consent was revoked; renewed consent is needed. |
| `whatsapp_blocked` | The recipient asked to stop; recording consent cannot override the block. |
| `provider_error` | Transient provider failure; delivery may be retried. |
| null or absent | Delivery succeeded or no send was requested. |
| Any other string | A future reason; preserve it and handle it as an unknown outcome. |

The reason is deliberately an open string, not an enum. The created link exists
even when sending was suppressed; use `url` when returned. The URL is a one-time
secret returned only on initial creation and can be absent on idempotent replay.

These changes are included in the generated source and tested local packages.
Registry availability is separate; follow [RELEASING.md](../RELEASING.md).
