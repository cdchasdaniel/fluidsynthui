# Start FluidSynthUI on Raspberry Pi

This guide covers starting FluidSynthUI on your Raspberry Pi using systemd with a separate control daemon (controlled via Stream Deck).

## Architecture

Two independent systemd services:

1. **fluidsynthui-control.service** (Port 8081)
   - Lightweight Python HTTP server
   - Runs continuously, always available
   - Handles start/stop commands for the main service
   
2. **fluidsynthui.service** (Port 8080)
   - Django development server
   - Can be stopped/started via the control daemon
   - Stops when you press the STOP button on stream deck

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

## Step 2: Set Up systemd Services

Create the systemd user service directory:

```bash
mkdir -p ~/.config/systemd/user
```

Service files are already created at:
- `.config/systemd/user/fluidsynthui.service` (main app)
- `.config/systemd/user/fluidsynthui-control.service` (control daemon)

Enable both services:

```bash
systemctl --user daemon-reload
systemctl --user enable fluidsynthui.service
systemctl --user enable fluidsynthui-control.service
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

## Step 4: Access Stream Deck

Once the control daemon is running, the Stream Deck interface is NOT immediately available. Use the START button on the Stream Deck to start the main Django application.

After pressing START, wait 2-3 seconds for the app to boot, then refresh the Stream Deck page.

Access the web interface from another device:
```
http://<pi-ip>:8080
```

## Step 5: Control via Stream Deck

Once the app is running:
- **START**: Starts the Django app (main service)
- **STOP**: Stops the Django app

The Stream Deck buttons always work because the control daemon (port 8081) stays running.

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
- Kill it or change the port in `service_control.py`

**Control daemon shows as failed:**
- Ensure Python 3 is installed: `which python3`
- Ensure the script has correct path: `cat ~/.config/systemd/user/fluidsynthui-control.service`
- Check permissions: `chmod +x /home/charlie/fluidsynthui/service_control.py`
- Run it directly and check the output: `./start_server.sh`

**Can't connect from network:**
- Check firewall: `sudo ufw status`
- Verify Django ALLOWED_HOSTS in `fluidsynthui/settings.py` includes your Pi's IP
- Confirm server is listening: `sudo ss -tuln | grep 8080`

**Port 8080 already in use:**
- Find what's using it: `sudo lsof -i :8080`
- Edit `start_server.sh` and change `0.0.0.0:8080` to a different port
