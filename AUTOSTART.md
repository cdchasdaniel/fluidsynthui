# Start FluidSynthUI on Raspberry Pi

This guide covers starting FluidSynthUI when your Raspberry Pi boots, in CLI mode (no desktop), using `start_server.sh` (no systemd service).

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

## Step 2: Start the Server

From the project directory:

```bash
cd /home/charlie/fluidsynthui
./start_server.sh
```

If you want this to run on boot, add the command to your preferred startup mechanism (for example, your user's shell profile or a boot script). This project no longer uses systemd services.

## Step 3: Verify It's Running

Check if the server is listening on port 8000:
```bash
netstat -tuln | grep 8000
```

Access the web interface from another device:
```
http://<pi-ip>:8000
```

## Troubleshooting

**Script fails to start:**
- Ensure `start_server.sh` is executable: `chmod +x /home/charlie/fluidsynthui/start_server.sh`
- Run it directly and check the output: `./start_server.sh`

**Can't connect from network:**
- Check firewall: `sudo ufw status`
- Verify Django ALLOWED_HOSTS in `fluidsynthui/settings.py` includes your Pi's IP
- Confirm server is listening: `sudo ss -tuln | grep 8000`

**Port 8000 already in use:**
- Edit `start_server.sh` and change `0.0.0.0:8000` to a different port like `0.0.0.0:8080`
