# secrets/

This directory holds Docker secret files.
**These files are NOT committed to Git** (excluded by `.gitignore`).

## Files

| File | Content | Used for |
|------|---------|----------|
| `smtp_pass` | Your SMTP password or app-specific password | Email alerts |
| `alert_to`  | Destination email address for alerts | Email alerts |

## Setup

```bash
# Fill in real values before running docker compose
echo "your_real_smtp_password"     > secrets/smtp_pass
echo "you@yourcompany.com"         > secrets/alert_to
```

## How Docker secrets work

Docker Compose mounts each file into the container at `/run/secrets/<name>`.
The application reads the value from the file at startup using the `_read_secret()`
helper function — the password never appears in environment variables, `docker inspect`
output, or image layers.
