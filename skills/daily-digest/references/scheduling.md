# Scheduling Daily Digest

## macOS (launchd)

Create `~/Library/LaunchAgents/com.daily-digest.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.daily-digest</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/project && claude -p "跑一次 daily digest"</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/daily-digest.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/daily-digest.err</string>
</dict>
</plist>
```

Load/unload:
```bash
launchctl load ~/Library/LaunchAgents/com.daily-digest.plist
launchctl unload ~/Library/LaunchAgents/com.daily-digest.plist
```

## Linux (cron)

```bash
crontab -e
# Run at 8:00 AM daily:
0 8 * * * cd /path/to/project && claude -p "跑一次 daily digest" >> /tmp/daily-digest.log 2>&1
```

## Tips

- Adjust the hour to match when your content sources typically publish
- The pipeline is idempotent — running multiple times in a day is safe (dedup via state.json)
- Check `/tmp/daily-digest.log` for troubleshooting
- Make sure `claude` CLI is in the PATH for the scheduled user
