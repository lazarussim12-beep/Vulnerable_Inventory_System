# Vulnerable Inventory Management System

> **Warning:** This project is intentionally vulnerable. Do not deploy it on the public internet.

This mini Flask application mimics an inventory management portal that a small warehouse team might use.  

## Features (and Intentional Flaws)

- User registration and login that store passwords as plaintext and allow SQL injection.
- Hard-coded Flask secret key, debug mode, and weak JWT configuration.
- Any logged-in user can alter any record.
- Admin dashboard that is exposed without authentication.
- Unsafe search & export endpoints that concatenate user input into SQL statements.
- Insecure file upload area that stores executable files.
- No CSRF protection, no rate limiting, no logging, no input validation.

## Quick start

```bash
pip install -r requirements.txt
python setup_db.py   # run once to create inventory.db with demo data
python app.py        # start the vulnerable server on http://localhost:7000
```

Default demo credentials are listed in `setup_db.py`.

## Educational use only


