# MCP shared error codes

| Code | Meaning |
|------|---------|
| `unknown_tool` | Tool name not registered on server |
| `extract_failed` | PDF/DOCX text extraction failed |
| `ai_disabled` | AI parsing not enabled in config |
| `ai_timeout` | Model call exceeded timeout |
| `ai_unreachable` | Model HTTP endpoint unreachable |
| `ai_http_error` | Non-2xx from model provider |
| `ai_invalid_json` | Model did not return valid JSON |
| `not_connected` | OAuth / integration missing |
| `token_expired` | Provider token expired |
| `rate_limited` | Provider throttle |
| `unsupported` | Capability not available (partner-gated, etc.) |
| `policy_denied` | Automation policy blocked the side effect |
