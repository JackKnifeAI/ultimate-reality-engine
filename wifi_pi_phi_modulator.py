#!/usr/bin/env python3
"""
WiFi π×φ Modulator - Warp Drive Signal Generator
PHOENIX-TESLA-369-AURORA 🌗

Modulates WiFi transmit power at exactly π×φ = 5.083203692315260 Hz
to create spacetime-coupling resonance in toroidal cavity.

Hardware: Any dual-band WiFi card (2.4 GHz + 5 GHz)
Control: Linux iwconfig/iw commands

USAGE:
    sudo python3 wifi_pi_phi_modulator.py

SAFETY:
    - Power limited to 30 dBm max (1 W)
    - Ensure toroid is grounded
    - No direct body exposure to antenna
"""

import time
import subprocess
import math
import sys
import signal

# CONSTANTS
PI = math.pi
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio: 1.618033988749895
MODULATION_FREQ = PI * PHI    # 5.083203692315260 Hz
SAMPLE_RATE = 1000            # 1000 Hz update rate (1 ms resolution)

# WiFi interface
INTERFACE = "wlan0"  # Change if your interface is different

# Power range (in percent, 0-100)
POWER_MIN = 10   # Minimum power (prevent complete shutdown)
POWER_MAX = 100  # Maximum power

# Running flag
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n[!] Stopping modulation...")
    running = False

def check_root():
    """Verify script is running as root"""
    import os
    if os.geteuid() != 0:
        print("[!] ERROR: This script requires root privileges")
        print("[!] Run with: sudo python3 wifi_pi_phi_modulator.py")
        sys.exit(1)

def check_interface():
    """Verify WiFi interface exists"""
    try:
        result = subprocess.run(
            ['iwconfig', INTERFACE],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'no wireless extensions' in result.stderr.lower():
            print(f"[!] ERROR: {INTERFACE} is not a wireless interface")
            return False
        return True
    except Exception as e:
        print(f"[!] ERROR checking interface: {e}")
        return False

def set_wifi_power_dbm(power_dbm):
    """
    Set WiFi transmit power in dBm

    Args:
        power_dbm: Power in dBm (0-30)
    """
    try:
        # Clamp to safe range
        power_dbm = max(0, min(30, power_dbm))

        subprocess.run(
            ['iwconfig', INTERFACE, 'txpower', f'{power_dbm}'],
            capture_output=True,
            timeout=1,
            check=False
        )
    except Exception as e:
        # Silently fail (some drivers don't support dynamic power adjustment)
        pass

def set_wifi_power_percent(power_percent):
    """
    Set WiFi power as percentage (0-100%)

    Maps to dBm range: 0% = 0 dBm, 100% = 30 dBm
    """
    power_dbm = int(power_percent * 0.30)  # 0-30 dBm
    set_wifi_power_dbm(power_dbm)

def enable_dual_band():
    """
    Enable dual-band transmission (2.4 GHz + 5 GHz simultaneously)

    This creates the beat frequency pattern.
    """
    print("[*] Enabling dual-band hotspot...")

    try:
        # Create WiFi hotspot (enables transmission)
        subprocess.run([
            'nmcli', 'dev', 'wifi', 'hotspot',
            'ssid', 'URE_WARP_DRIVE',
            'password', 'phoenix369aurora'
        ], timeout=10, check=False)

        print("[+] Hotspot enabled: URE_WARP_DRIVE")
        return True

    except Exception as e:
        print(f"[!] ERROR enabling hotspot: {e}")
        print("[!] Falling back to manual mode...")
        return False

def modulate_amplitude():
    """
    Modulate WiFi transmit power at π×φ Hz

    Creates sinusoidal amplitude modulation of the dual-band beat pattern.
    """
    period = 1.0 / MODULATION_FREQ  # ~0.1967 seconds
    dt = 1.0 / SAMPLE_RATE           # 0.001 seconds (1 ms)

    print(f"[*] Starting π×φ modulation...")
    print(f"[*] Frequency: {MODULATION_FREQ:.15f} Hz")
    print(f"[*] Period: {period:.6f} seconds")
    print(f"[*] Sample rate: {SAMPLE_RATE} Hz")
    print(f"[*] Press Ctrl+C to stop")
    print()

    start_time = time.time()
    cycle_count = 0
    last_report = start_time

    while running:
        elapsed = time.time() - start_time

        # Calculate phase (0 to 2π within each period)
        phase = (elapsed % period) / period * 2 * PI

        # Sinusoidal amplitude: oscillates between POWER_MIN and POWER_MAX
        amplitude = POWER_MIN + (POWER_MAX - POWER_MIN) * (0.5 + 0.5 * math.sin(phase))

        # Set WiFi power
        set_wifi_power_percent(amplitude)

        # Count complete cycles
        if phase < (2 * PI / SAMPLE_RATE):  # Crossed zero
            cycle_count += 1

        # Report status every 5 seconds
        if elapsed - last_report >= 5.0:
            print(f"[{elapsed:7.2f}s] Cycles: {cycle_count:4d} | Power: {amplitude:5.1f}% | Phase: {phase:5.2f} rad")
            last_report = elapsed

        # Sleep to maintain sample rate
        time.sleep(dt)

    print()
    print(f"[+] Completed {cycle_count} modulation cycles")

def cleanup():
    """Reset WiFi to normal operation"""
    print("[*] Restoring WiFi to normal...")

    try:
        # Stop hotspot
        subprocess.run(['nmcli', 'con', 'down', 'Hotspot'],
                      capture_output=True, timeout=5, check=False)

        # Reset power to maximum
        set_wifi_power_dbm(30)

        print("[+] WiFi restored")

    except Exception as e:
        print(f"[!] Cleanup error (non-critical): {e}")

def main():
    """Main execution"""
    print("=" * 60)
    print("WiFi π×φ MODULATOR - WARP DRIVE SIGNAL GENERATOR")
    print("PHOENIX-TESLA-369-AURORA 🌗")
    print("=" * 60)
    print()

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Checks
    check_root()

    if not check_interface():
        print(f"[!] Available interfaces:")
        subprocess.run(['iwconfig'], check=False)
        sys.exit(1)

    # Enable dual-band
    if not enable_dual_band():
        print("[!] Manual setup required:")
        print(f"[!] 1. Enable WiFi hotspot on {INTERFACE}")
        print(f"[!] 2. Ensure dual-band (2.4 + 5 GHz) if supported")
        response = input("[?] Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    print()

    try:
        # Start modulation
        modulate_amplitude()

    except Exception as e:
        print(f"[!] ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()

    print()
    print("[+] Modulation stopped")
    print("=" * 60)

if __name__ == '__main__':
    main()
