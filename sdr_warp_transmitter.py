#!/usr/bin/env python3
"""
SDR Warp Drive Transmitter
PHOENIX-TESLA-369-AURORA 🌗

Generates dual-frequency EM field (2.4 GHz + 5.0 GHz) with π×φ amplitude modulation
using Software-Defined Radio (HackRF One, LimeSDR, USRP, etc.)

This provides FULL control over the waveform for precise spacetime coupling.

HARDWARE REQUIRED:
    - HackRF One, LimeSDR, USRP, or compatible SDR
    - Antenna or connection to toroidal cavity

DEPENDENCIES:
    pip install numpy scipy

GNU Radio version available in sdr_warp_gnuradio.py

USAGE:
    python3 sdr_warp_transmitter.py [--device hackrf|limesdr|usrp]
"""

import numpy as np
import math
import argparse
import sys
import time

try:
    import SoapySDR
    from SoapySDR import SOAPY_SDR_TX, SOAPY_SDR_CF32
except ImportError:
    print("[!] ERROR: SoapySDR not installed")
    print("[!] Install with: pip install SoapySDR")
    sys.exit(1)

# CONSTANTS
PI = math.pi
PHI = (1 + math.sqrt(5)) / 2
MODULATION_FREQ = PI * PHI  # 5.083203692315260 Hz

# SDR Configuration
SAMPLE_RATE = 20e6      # 20 MHz sample rate
FREQ_1 = 2.4e9          # 2.4 GHz carrier
FREQ_2 = 5.0e9          # 5.0 GHz carrier
CENTER_FREQ = 3.7e9     # Center between the two
GAIN = 14               # TX gain (dBm) - adjust based on hardware
BUFFER_SIZE = 16384     # Samples per buffer

class WarpDriveTransmitter:
    """
    Dual-frequency transmitter with π×φ amplitude modulation
    """

    def __init__(self, device_type='hackrf'):
        """
        Initialize SDR device

        Args:
            device_type: 'hackrf', 'limesdr', or 'usrp'
        """
        self.device_type = device_type
        self.sdr = None
        self.stream = None
        self.running = False

        print(f"[*] Initializing {device_type.upper()}...")
        self._init_sdr()

    def _init_sdr(self):
        """Initialize SDR hardware"""
        try:
            # Create device
            if self.device_type == 'hackrf':
                self.sdr = SoapySDR.Device({'driver': 'hackrf'})
            elif self.device_type == 'limesdr':
                self.sdr = SoapySDR.Device({'driver': 'lime'})
            elif self.device_type == 'usrp':
                self.sdr = SoapySDR.Device({'driver': 'uhd'})
            else:
                raise ValueError(f"Unknown device: {self.device_type}")

            # Configure
            self.sdr.setSampleRate(SOAPY_SDR_TX, 0, SAMPLE_RATE)
            self.sdr.setFrequency(SOAPY_SDR_TX, 0, CENTER_FREQ)
            self.sdr.setGain(SOAPY_SDR_TX, 0, GAIN)

            print(f"[+] {self.device_type.upper()} initialized")
            print(f"[+] Sample rate: {SAMPLE_RATE/1e6:.1f} MHz")
            print(f"[+] Center frequency: {CENTER_FREQ/1e9:.2f} GHz")
            print(f"[+] TX gain: {GAIN} dB")

        except Exception as e:
            print(f"[!] ERROR initializing SDR: {e}")
            print(f"[!] Available devices:")
            for dev in SoapySDR.Device.enumerate():
                print(f"    {dev}")
            sys.exit(1)

    def generate_waveform(self, duration=1.0):
        """
        Generate dual-frequency waveform with π×φ modulation

        Args:
            duration: Waveform duration in seconds

        Returns:
            Complex numpy array of IQ samples
        """
        num_samples = int(SAMPLE_RATE * duration)
        t = np.arange(num_samples) / SAMPLE_RATE

        # Carrier 1: 2.4 GHz (relative to center freq)
        offset_1 = FREQ_1 - CENTER_FREQ
        carrier_1 = np.exp(2j * PI * offset_1 * t)

        # Carrier 2: 5.0 GHz (relative to center freq)
        offset_2 = FREQ_2 - CENTER_FREQ
        carrier_2 = np.exp(2j * PI * offset_2 * t)

        # π×φ amplitude modulation envelope
        envelope = 0.5 + 0.5 * np.sin(2 * PI * MODULATION_FREQ * t)

        # Apply envelope to both carriers
        signal_1 = envelope * carrier_1
        signal_2 = envelope * carrier_2

        # Combine (superposition)
        combined = (signal_1 + signal_2) / 2.0  # Normalize

        # Convert to complex64 (CF32 format)
        return combined.astype(np.complex64)

    def transmit(self, duration=60.0):
        """
        Transmit warp drive signal

        Args:
            duration: Total transmission duration in seconds (0 = infinite)
        """
        print()
        print("[*] Starting transmission...")
        print(f"[*] Modulation frequency: {MODULATION_FREQ:.15f} Hz")
        print(f"[*] Carrier 1: {FREQ_1/1e9:.3f} GHz")
        print(f"[*] Carrier 2: {FREQ_2/1e9:.3f} GHz")
        print(f"[*] Beat frequency: {abs(FREQ_2-FREQ_1)/1e9:.3f} GHz")
        print(f"[*] Duration: {duration:.1f}s" if duration > 0 else "[*] Duration: Infinite (Ctrl+C to stop)")
        print()

        # Setup stream
        self.stream = self.sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
        self.sdr.activateStream(self.stream)

        self.running = True
        start_time = time.time()
        samples_sent = 0

        try:
            while self.running:
                # Check duration
                elapsed = time.time() - start_time
                if duration > 0 and elapsed >= duration:
                    break

                # Generate waveform chunk (1 second)
                waveform = self.generate_waveform(duration=1.0)

                # Transmit
                sr = self.sdr.writeStream(self.stream, [waveform], len(waveform))

                if sr.ret < 0:
                    print(f"[!] Stream error: {sr.ret}")
                    break

                samples_sent += sr.ret

                # Status
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    cycles = elapsed * MODULATION_FREQ
                    print(f"[{elapsed:7.2f}s] Samples: {samples_sent/1e6:.2f}M | Cycles: {cycles:.1f}")

        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")

        finally:
            # Cleanup
            self.sdr.deactivateStream(self.stream)
            self.sdr.closeStream(self.stream)
            self.running = False

            elapsed = time.time() - start_time
            print()
            print(f"[+] Transmission complete")
            print(f"[+] Total time: {elapsed:.2f}s")
            print(f"[+] Total samples: {samples_sent/1e6:.2f}M")
            print(f"[+] Modulation cycles: {elapsed * MODULATION_FREQ:.1f}")

    def close(self):
        """Close SDR device"""
        if self.sdr:
            self.sdr = None
            print("[+] SDR closed")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='SDR Warp Drive Transmitter')
    parser.add_argument('--device', choices=['hackrf', 'limesdr', 'usrp'],
                       default='hackrf', help='SDR device type')
    parser.add_argument('--duration', type=float, default=0,
                       help='Transmission duration in seconds (0 = infinite)')

    args = parser.parse_args()

    print("=" * 60)
    print("SDR WARP DRIVE TRANSMITTER")
    print("PHOENIX-TESLA-369-AURORA 🌗")
    print("=" * 60)

    tx = WarpDriveTransmitter(device_type=args.device)

    try:
        tx.transmit(duration=args.duration)
    finally:
        tx.close()

    print("=" * 60)

if __name__ == '__main__':
    main()
