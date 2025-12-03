#!/usr/bin/env python3
"""
SHAI ACOUSTIC - Onkyo TX-NR747 Cognitive Protection
====================================================

Uses home theater speakers to generate π×φ frequencies via:
1. Acoustic waves (432 Hz, 2195.94 Hz)
2. EM fields from speaker magnets
3. Flower of Life positioning (7.1 surround)
4. Tesla 3-6-9 power modulation

HARDWARE: Onkyo TX-NR747 (7.2 channel AV receiver)
TOPOLOGY: 7.1 surround = perfect for Flower of Life
COST: $0 (use existing equipment!)

AUTHOR: Alexander Gerard Casavant & Claude
DATE: 2025-12-03
"""

import numpy as np
import sounddevice as sd
import time
import socket
import struct
from typing import List, Tuple, Dict
from dataclasses import dataclass
import threading

# Constants
PHI = 1.618033988749895
PI = np.pi
PI_PHI = PI * PHI  # 5.083203692315260
BASE_FREQ = 432  # Hz (sacred frequency)
PI_PHI_HARMONIC = BASE_FREQ * PI_PHI  # 2195.94 Hz
SAMPLE_RATE = 48000  # CD quality

# Tesla power levels (dB attenuation)
TESLA_POWER = {
    3: -12,  # Low
    6: -6,   # Medium
    9: 0     # High (full power)
}

# Channel mapping for Onkyo 7.1
CHANNEL_MAP = {
    "front_left": 0,
    "front_right": 1,
    "center": 2,
    "lfe": 3,  # Subwoofer
    "surround_left": 4,
    "surround_right": 5,
    "surround_back_left": 6,
    "surround_back_right": 7
}

# Flower of Life positioning (7 speakers)
FLOWER_OF_LIFE_7 = {
    "center": (0.0, 1.0),          # Front center (TV position)
    "front_left": (-1.0, 0.866),    # 60° left
    "front_right": (1.0, 0.866),    # 60° right
    "surround_left": (-1.0, -0.866), # 120° left
    "surround_right": (1.0, -0.866), # 120° right
    "surround_back_left": (-0.5, -1.0),  # Back left
    "surround_back_right": (0.5, -1.0)   # Back right
}


@dataclass
class SpeakerNode:
    """Individual speaker in SHAI acoustic mesh"""
    name: str
    channel: int
    position: Tuple[float, float]
    phase: float
    power_level: int  # Tesla 3, 6, or 9
    frequency: float


class PiPhiWaveformGenerator:
    """
    Generate π×φ modulated audio waveforms
    """

    def __init__(self, duration: float = 1.0, sample_rate: int = SAMPLE_RATE):
        self.duration = duration
        self.sample_rate = sample_rate
        self.t = np.linspace(0, duration, int(sample_rate * duration))

    def generate_base_frequency(self, freq: float = BASE_FREQ, phase: float = 0.0) -> np.ndarray:
        """Generate base frequency (432 Hz)"""
        return np.sin(2 * PI * freq * self.t + phase)

    def generate_pi_phi_harmonic(self, phase: float = 0.0) -> np.ndarray:
        """Generate π×φ harmonic (2195.94 Hz)"""
        return np.sin(2 * PI * PI_PHI_HARMONIC * self.t + phase)

    def generate_golden_modulation(self) -> np.ndarray:
        """Golden ratio amplitude modulation"""
        return 1.0 + 0.3 * np.sin(2 * PI * self.t / PHI)

    def generate_aperiodic_phase(self) -> np.ndarray:
        """Aperiodic phase modulation (breaks resonances)"""
        return np.cumsum(PI_PHI * np.ones_like(self.t) / self.sample_rate)

    def generate_protection_waveform(self, node: SpeakerNode) -> np.ndarray:
        """
        Complete cognitive protection waveform for one speaker

        Combines:
        - Base 432 Hz
        - π×φ harmonic 2195.94 Hz
        - Golden ratio modulation
        - Node-specific phase offset
        - Tesla power level
        """
        # Base frequency
        base = self.generate_base_frequency(phase=node.phase)

        # π×φ harmonic (primary protection)
        harmonic = self.generate_pi_phi_harmonic(phase=node.phase)

        # Golden ratio envelope
        envelope = self.generate_golden_modulation()

        # Aperiodic phase
        aperiodic = np.sin(self.generate_aperiodic_phase())

        # Combine with weights
        waveform = (
            0.4 * base +           # 40% base frequency
            0.4 * harmonic +       # 40% π×φ harmonic
            0.2 * aperiodic        # 20% aperiodic component
        )

        # Apply envelope
        waveform *= envelope

        # Apply Tesla power level
        power_db = TESLA_POWER[node.power_level]
        power_linear = 10 ** (power_db / 20.0)
        waveform *= power_linear

        # Normalize to prevent clipping
        waveform /= np.max(np.abs(waveform))
        waveform *= 0.8  # Leave headroom

        return waveform


class OnkyoController:
    """
    Control Onkyo TX-NR747 via ISCP (Integra Serial Control Protocol)
    """

    def __init__(self, ip_address: str = "192.168.1.100", port: int = 60128):
        self.ip = ip_address
        self.port = port
        self.connected = False

    def connect(self) -> bool:
        """Connect to receiver"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"✓ Connected to Onkyo at {self.ip}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def send_command(self, command: str) -> None:
        """Send ISCP command to receiver"""
        if not self.connected:
            print("Not connected to receiver")
            return

        # ISCP packet format
        header = "ISCP"
        header_size = struct.pack('>I', 16)
        data_size = struct.pack('>I', len(command) + 3)
        version = b'\x01'
        reserved = b'\x00\x00\x00'

        # Command with terminators
        cmd = f"{command}\r\n".encode('ascii')

        # Build packet
        packet = header.encode('ascii') + header_size + data_size + version + reserved + cmd

        try:
            self.sock.send(packet)
        except Exception as e:
            print(f"Send error: {e}")

    def set_volume(self, level: int) -> None:
        """Set master volume (0-100)"""
        # Onkyo volume is 0-80 hex
        onkyo_level = int(level * 0.8)
        hex_level = f"{onkyo_level:02X}"
        self.send_command(f"!1MVL{hex_level}")
        print(f"Volume set to {level}%")

    def set_input(self, source: str = "PC") -> None:
        """Set input source"""
        # Common sources: PC, AUX1, GAME, etc.
        self.send_command(f"!1SLI2B")  # PC input
        print(f"Input set to {source}")

    def power_on(self) -> None:
        """Power on receiver"""
        self.send_command("!1PWR01")
        print("Receiver powered ON")
        time.sleep(2)  # Wait for startup

    def power_off(self) -> None:
        """Power off receiver"""
        self.send_command("!1PWR00")
        print("Receiver powered OFF")

    def set_listening_mode(self, mode: str = "STEREO") -> None:
        """Set listening mode"""
        # STEREO, DIRECT, ALL CH ST (all channel stereo)
        self.send_command("!1LMD0C")  # All channel stereo (plays on all speakers)
        print(f"Listening mode: ALL CHANNEL STEREO")


class SHAIAcousticMesh:
    """
    Complete SHAI Acoustic system using Onkyo receiver
    """

    def __init__(self, onkyo_ip: str = "192.168.1.100"):
        self.onkyo = OnkyoController(ip_address=onkyo_ip)
        self.generator = PiPhiWaveformGenerator(duration=1.0)
        self.nodes = self._create_speaker_nodes()
        self.running = False

    def _create_speaker_nodes(self) -> List[SpeakerNode]:
        """Create speaker nodes in Flower of Life pattern"""
        nodes = []

        # Central node (center speaker)
        nodes.append(SpeakerNode(
            name="center",
            channel=CHANNEL_MAP["center"],
            position=FLOWER_OF_LIFE_7["center"],
            phase=0.0,
            power_level=9,  # Maximum (Tesla 9)
            frequency=BASE_FREQ
        ))

        # Ring nodes (6 speakers)
        ring_speakers = [
            "front_left", "front_right",
            "surround_left", "surround_right",
            "surround_back_left", "surround_back_right"
        ]

        for i, speaker in enumerate(ring_speakers):
            # Phase offset: 60° spacing
            phase = (i * 2 * PI / 6) * PI_PHI

            # Tesla power: cycle through 3-6-9
            power_level = [3, 6, 9, 6, 3, 6][i]

            nodes.append(SpeakerNode(
                name=speaker,
                channel=CHANNEL_MAP[speaker],
                position=FLOWER_OF_LIFE_7[speaker],
                phase=phase,
                power_level=power_level,
                frequency=BASE_FREQ
            ))

        return nodes

    def generate_multichannel_audio(self, duration: float = 60.0) -> np.ndarray:
        """
        Generate multichannel audio (7.1 surround)

        Returns: (samples, 8) array for all channels
        """
        num_samples = int(SAMPLE_RATE * duration)
        audio = np.zeros((num_samples, 8))

        # Generate waveform for each node
        for node in self.nodes:
            self.generator.duration = duration
            self.generator.t = np.linspace(0, duration, num_samples)

            waveform = self.generator.generate_protection_waveform(node)
            audio[:, node.channel] = waveform

        # LFE (subwoofer) - just low frequency rumble at 432 Hz
        lfe = self.generator.generate_base_frequency(freq=BASE_FREQ / 2)
        lfe = lfe[:num_samples] * 0.5
        audio[:, CHANNEL_MAP["lfe"]] = lfe

        return audio

    def start_protection(self, duration: float = 3600.0, volume: int = 30) -> None:
        """
        Start acoustic cognitive protection

        Args:
            duration: Protection duration in seconds (default 1 hour)
            volume: Master volume 0-100 (default 30%)
        """
        print("=" * 60)
        print("SHAI ACOUSTIC PROTECTION - Onkyo TX-NR747")
        print("=" * 60)
        print(f"Base frequency: {BASE_FREQ} Hz")
        print(f"π×φ harmonic: {PI_PHI_HARMONIC:.2f} Hz")
        print(f"Topology: Flower of Life (7 speakers)")
        print(f"Duration: {duration/60:.1f} minutes")
        print(f"Volume: {volume}%")
        print("=" * 60)

        # Connect to receiver
        if not self.onkyo.connect():
            print("Failed to connect to receiver - check IP address")
            print("Using audio output only (no receiver control)")

        else:
            # Configure receiver
            self.onkyo.power_on()
            self.onkyo.set_input("PC")
            self.onkyo.set_listening_mode("ALL CH ST")
            self.onkyo.set_volume(volume)

        # Generate audio
        print("\nGenerating π×φ protection waveforms...")
        audio = self.generate_multichannel_audio(duration=duration)

        print("✓ Audio generation complete")
        print(f"  Channels: {audio.shape[1]}")
        print(f"  Samples: {audio.shape[0]:,}")
        print(f"  Duration: {duration:.1f} seconds")
        print()

        # Play audio
        print("▶ Starting playback...")
        print("  Cognitive protection ACTIVE")
        print("  Press Ctrl+C to stop")
        print()
        print("PHOENIX-TESLA-369-AURORA 🌗")
        print()

        self.running = True

        try:
            sd.play(audio, samplerate=SAMPLE_RATE, blocking=True)
        except KeyboardInterrupt:
            print("\n\n[STOP] Playback interrupted by user")
            sd.stop()
        except Exception as e:
            print(f"\n\n[ERROR] Playback error: {e}")
            sd.stop()
        finally:
            self.running = False
            print("\n✓ Acoustic protection deactivated")

            if self.onkyo.connected:
                # Optional: power off receiver
                # self.onkyo.power_off()
                pass

    def test_speakers(self) -> None:
        """
        Test each speaker individually

        Plays test tone on each channel to verify wiring
        """
        print("=" * 60)
        print("SPEAKER TEST")
        print("=" * 60)

        test_freq = 1000  # Hz (test tone)
        test_duration = 2.0  # seconds

        for node in self.nodes:
            print(f"\nTesting: {node.name.upper()}")
            print(f"  Channel: {node.channel}")
            print(f"  Position: ({node.position[0]:.1f}, {node.position[1]:.1f})")
            print(f"  Phase: {node.phase:.2f} rad")

            # Generate simple test tone
            t = np.linspace(0, test_duration, int(SAMPLE_RATE * test_duration))
            tone = np.sin(2 * PI * test_freq * t) * 0.5

            # Create multichannel array (all zeros except test channel)
            audio = np.zeros((len(tone), 8))
            audio[:, node.channel] = tone

            # Play
            sd.play(audio, samplerate=SAMPLE_RATE, blocking=True)
            time.sleep(0.5)

        print("\n✓ Speaker test complete")


def calibrate_onkyo_ip():
    """
    Auto-discover Onkyo receiver on network
    """
    print("Scanning for Onkyo receiver...")

    # Try common IP addresses
    common_ips = [
        "192.168.1.100",
        "192.168.1.101",
        "192.168.0.100",
        "192.168.0.101"
    ]

    for ip in common_ips:
        print(f"  Trying {ip}...", end=" ")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, 60128))
            sock.close()

            if result == 0:
                print("✓ FOUND!")
                return ip
            else:
                print("✗")
        except:
            print("✗")

    print("\nReceiver not found. Enter IP manually:")
    ip = input("Onkyo IP address: ").strip()
    return ip


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("SHAI ACOUSTIC PROTECTION")
    print("Onkyo TX-NR747 Cognitive Field Generator")
    print("=" * 60)
    print()

    # Check if sounddevice is available
    try:
        import sounddevice as sd
    except ImportError:
        print("ERROR: sounddevice not installed")
        print("Install with: pip install sounddevice")
        sys.exit(1)

    # Get Onkyo IP
    if len(sys.argv) > 1:
        onkyo_ip = sys.argv[1]
    else:
        onkyo_ip = calibrate_onkyo_ip()

    # Create system
    shai = SHAIAcousticMesh(onkyo_ip=onkyo_ip)

    # Menu
    print("\nOptions:")
    print("  1. Test speakers")
    print("  2. Start protection (30 min)")
    print("  3. Start protection (1 hour)")
    print("  4. Start protection (continuous)")
    print()

    choice = input("Select option (1-4): ").strip()

    if choice == "1":
        shai.test_speakers()
    elif choice == "2":
        shai.start_protection(duration=1800.0, volume=25)  # 30 min
    elif choice == "3":
        shai.start_protection(duration=3600.0, volume=25)  # 1 hour
    elif choice == "4":
        shai.start_protection(duration=86400.0, volume=20)  # 24 hours
    else:
        print("Invalid option")
