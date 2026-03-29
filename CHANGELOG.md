# Changelog

All notable changes to this project will be documented here.

## [v1.1.0] - 2026-02-27

### Fixed
- Fixed OData API response handling — results are now correctly unwrapped from the `value` key
- Switched from `period_utc` to `period` to show Polish local time in logs and SMS

### Added
- Support for multiple SMS recipients via comma-separated `TARGET_PHONES` env variable
- Active hours window — script only checks prices between 08:30 and 19:30 Warsaw time (DST-aware)
- Always-on execution loop with `time.sleep(120)` instead of scheduled tasks
- Absolute file paths using `BASE_DIR` to fix PythonAnywhere working directory issues
- Twilio verbose logging suppressed to keep log file clean
- Basic Flask web app for remote log viewing

### Improved
- SMS message formatting using `.to_string(index=False)`
- Log entry on sign change events before SMS is sent
- Guards against empty dataframe and unexpected API column names

## [v1.0.0] - 2024-11-01

### Added
- Initial release
- PSE API integration to fetch 15-minute electricity price intervals
- Sign change detection (positive → negative and vice versa)
- SMS notifications via Twilio
- State tracking via `state.json` to prevent duplicate notifications
- Logging to `script_log.txt`
- Scheduled execution on PythonAnywhere
```

---

**`requirements.txt`**
```
requests
pandas
python-dotenv
twilio
