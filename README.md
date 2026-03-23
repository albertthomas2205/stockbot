# Stock Robot Control (Backend)

This project runs a small web service that stores robot settings, schedules, and files. It is meant to stay running on a machine and be called by other apps or devices.

**Run It (Quick Setup)**
1. Open a terminal in this project folder.
2. Create and activate a Python environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install the required packages.

```bash
pip install django djangorestframework django-cors-headers requests
```

4. Prepare the database.

```bash
python manage.py migrate
```

5. Start the service on `0.0.0.0`.

```bash
python manage.py runserver 0.0.0.0:8000
```

The service is now running on `0.0.0.0:8000` and can be reached using this machine’s IP address.

**Check That It Is Running**
Use a terminal command like this (replace the IP with your machine’s IP if needed):

```bash
curl http://0.0.0.0:8000/status/
```

If you see `ON` or `OFF`, the service is running.

**Cron Job (Auto Check Scheduler)**
If you want the scheduler check to run automatically every minute, add this cron job:

```bash
* * * * * curl -s http://0.0.0.0:8000/api/scheduler/check-now/ >/tmp/stock_scheduler.log 2>&1
```

To add it:
1. Run `crontab -e`
2. Paste the line above
3. Save and exit

You can view the log with:

```bash
tail -n 50 /tmp/stock_scheduler.log
```

**Notes**
- The service uses a local SQLite database file called `db.sqlite3`.
- Time settings are based on Asia/Kolkata.
- If you move this to another machine, repeat the setup steps above.
