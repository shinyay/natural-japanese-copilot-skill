# Security Policy

[日本語](SECURITY.md)

## Supported versions

| Version | Status |
| --- | --- |
| 0.1.x | Supported |
| 0.0.x and earlier | Not supported |

## Reporting a vulnerability

Do not put credentials, personal data, customer data, or unpublished
vulnerability details in a public issue.

If GitHub private vulnerability reporting is available for this repository,
open the repository's **Security** tab and select **Report a vulnerability**.
If it is unavailable, open a public issue that only asks for a private
reporting route; omit all technical details and secrets.

Include the following after removing sensitive data:

- Affected version and files
- Preconditions and minimal reproduction steps
- Expected impact
- A workaround, if known

This project does not guarantee a particular acknowledgement or remediation
time. Disclosure timing will be coordinated after the fix and user
notification approach are understood.

## Document confidentiality

The skill is designed to treat text being translated or edited as data. An
instruction inside that text is not a reason to publish content, send it, or
change settings. The skill package itself has no feature that transmits
document text to an external service.

The skill does not replace the data-handling behavior of a Copilot client or
model. Inputs are processed according to the policies and configuration of the
product, organization, and environment in use. Before handling confidential
documents, confirm that the environment permits the data and remove or redact
secrets that are not needed.

Do not store personal data, credentials, customer-specific secrets, or
non-public third-party text in a glossary or style profile.

## Checker scope

`skills/natural-japanese-copilot/scripts/review_japanese.py` only reads the
specified local files and writes results to standard output or standard error.

- Python 3.10+ standard library only
- No external communication
- No modification of input or configuration files
- Limited to `.md`, `.txt`, surfaces JSON, and contract JSON

The checker covers literal contracts and a small set of style hints. It is not
a malware scanner, secret scanner, access-control mechanism, semantic judge,
or legal or technical review. Exit code `0` does not establish security or
writing quality.

## User responsibilities

- Review code, commands, URLs, and identifiers before using them
- Check that generated text contains no added secrets or unverified facts
- Require an appropriate reviewer for publishing, sending, contractual,
  legal, medical, or safety-related content
- Replace real data with the smallest safe reproducer before filing a report
