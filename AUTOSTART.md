# Start FluidSynthUI on Raspberry Pi

This guide covers running FluidSynthUI on your Raspberry Pi with systemd and a separate control daemon for physical Stream Deck start/stop actions.

## Architecture

Two independent systemd services:

1. **fluidsynthui-control.service** (Port 8081)
   - Lightweight Python HTTP server
   - Runs continuously, always available
   - Handles start/stop commands for the main service
   
2. **fluidsynthui.service** (Port 8080)
   - Django development server
   - Can be stopped/started via the control daemon

## Step 1: Switch to CLI Mode (Optional)

If you want the Pi to boot in CLI mode instead of GUI:

```bash
sudo raspi-config
```

Navigate to:
- System Options → Boot / Auto Login → Select "B1 Console" (CLI)

Or if using newer raspi-config:
- System Options → Boot Options → Console

Then reboot:
```bash
sudo reboot
```

## Step 2: Install systemd User Services

From the repository root, copy the service unit templates under `.config/systemd/user/` to the systemd user-unit directory:

```bash
mkdir -p ~/.config/systemd/user
cp .config/systemd/user/fluidsynthui.service ~/.config/systemd/user/
cp .config/systemd/user/fluidsynthui-control.service ~/.config/systemd/user/
```

The included units use `/home/charlie/fluidsynthui`. If your username or checkout path differs, edit `User`, `WorkingDirectory`, and the paths in `ExecStart` in both copied unit files.

Enable lingering so the user service manager can start these services at boot even before you log in:

```bash
sudo loginctl enable-linger "$USER"
```

Reload systemd and enable both services for automatic startup at boot:

```bash
systemctl --user daemon-reload
systemctl --user enable fluidsynthui-control.service fluidsynthui.service
```

If you want the main Django app to stay stopped until you start it from the physical Stream Deck, enable only the control daemon instead:

```bash
systemctl --user daemon-reload
systemctl --user enable fluidsynthui-control.service
systemctl --user disable --now fluidsynthui.service
```

## Step 3: Start the Control Daemon

The control daemon must be running first (it handles starting/stopping the main app):

```bash
systemctl --user start fluidsynthui-control.service
```

Check if it's running:

```bash
systemctl --user status fluidsynthui-control.service
```

If you enabled automatic startup for both services, start the main app now as well:

```bash
systemctl --user start fluidsynthui.service
```

## Step 4: Access Stream Deck

When `fluidsynthui.service` is running, access the web interface from another device:
```
http://<pi-ip>:8080
```

The web Stream Deck page is at `http://<pi-ip>:8080/stream-deck/`, and is available only while the Django service is running. To start a stopped Django service, configure the **physical** Stream Deck's START and STOP buttons to call the control daemon directly:

```
http://<pi-ip>:8081/service/start/
http://<pi-ip>:8081/service/stop/
```

The web page's service buttons currently call `localhost:8081`, which refers to the device running the browser. They work from the Pi itself, but not from a separate tablet/computer unless that browser is on the Pi.

## Step 5: Control via Stream Deck

The physical Stream Deck's START/STOP buttons can control the Django service while it is stopped because they call the independent control daemon on port 8081. The web Stream Deck page cannot be opened while the Django service is stopped.

The control daemon listens on all network interfaces and its start/stop endpoints do not require authentication. Keep it on a trusted local network and block port 8081 from untrusted networks with your firewall/router.

## Step 6: View Logs

To see service logs:

```bash
# Main app logs
journalctl --user -u fluidsynthui.service -f

# Control daemon logs
journalctl --user -u fluidsynthui-control.service -f

# Or check the log files directory
tail -f logs/server-*.log
```

## Troubleshooting

**Control daemon won't start:**
```bash
systemctl --user status fluidsynthui-control.service
journalctl --user -u fluidsynthui-control.service -n 50
```

**Main app won't start from Stream Deck:**
- Check if control daemon is running: `systemctl --user status fluidsynthui-control.service`
- Try starting manually: `systemctl --user start fluidsynthui.service`
- Check logs: `journalctl --user -u fluidsynthui.service -n 50`

**Port 8081 already in use:**
- Find what's using it: `lsof -i :8081`
- Stop the conflicting process or change the port argument in `fluidsynthui-control.service`'s `ExecStart` and update the physical Stream Deck URLs.

**Control daemon shows as failed:**
- Ensure Python 3 is installed: `which python3`
- Ensure the script has correct path: `cat ~/.config/systemd/user/fluidsynthui-control.service`
- Test the daemon directly from the project directory: `/usr/bin/python3 service_control.py 8081`
- `start_server.sh` starts Django, not the control daemon.

**Can't connect from network:**
- Check firewall: `sudo ufw status`
- Verify Django ALLOWED_HOSTS in `fluidsynthui/settings.py` includes your Pi's IP
- Confirm server is listening: `sudo ss -tuln | grep 8080`

**Port 8080 already in use:**
- Find what's using it: `sudo lsof -i :8080`
- Stop the conflicting process or change the host/port in `start_server.sh`, then update the web interface URL.
