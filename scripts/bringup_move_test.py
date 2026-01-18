#!/usr/bin/env python3
"""
Mycosoft Embodiment - Bring-up Move Test Script
================================================
Simple test to prove basic control of myCobot 280 via pymycobot.

Tries multiple baud rates automatically if connection fails.

Usage:
    python scripts/bringup_move_test.py

Author: Mycosoft Labs
Date: January 2026
"""

import time
import sys

PORT = "COM8"
BAUD_RATES = [115200, 1000000, 9600]  # Try these in order


def try_connection(port, baud):
    """Try to connect and read angles at given baud rate."""
    # Try new import first (pymycobot 4.x), fallback to old
    try:
        from pymycobot import MyCobot280 as MyCobot
    except ImportError:
        try:
            from pymycobot import MyCobot
        except ImportError:
            from pymycobot.mycobot import MyCobot
    
    print(f"\n--- Trying {port} at {baud} baud ---")
    
    try:
        mc = MyCobot(port, baud)
        time.sleep(1)
        
        # Try power on
        try:
            mc.power_on()
            time.sleep(0.5)
        except:
            pass
        
        # Try to read angles
        for attempt in range(3):
            raw = mc.get_angles()
            if isinstance(raw, (list, tuple)) and len(raw) >= 6:
                return mc, list(raw), baud
            time.sleep(0.5)
        
        # Return mc even if angles failed - might still work
        return mc, None, baud
        
    except Exception as e:
        print(f"  Connection failed: {e}")
        return None, None, baud


def main():
    print("=" * 50)
    print("MYCOSOFT EMBODIMENT - Bring-up Move Test")
    print("=" * 50)
    
    # Try each baud rate
    mc = None
    angles = None
    working_baud = None
    
    for baud in BAUD_RATES:
        mc, angles, working_baud = try_connection(PORT, baud)
        if angles is not None:
            print(f"\n[SUCCESS] Connected at {baud} baud!")
            break
        elif mc is not None:
            print(f"  Connected but get_angles() returned invalid data")
    
    if angles is None:
        print("\n" + "=" * 50)
        print("[ERROR] Could not read joint angles at any baud rate.")
        print("=" * 50)
        print("\nTroubleshooting steps:")
        print("  1. Check robot base power LED is on (green)")
        print("  2. Press power button on robot base if needed")
        print("  3. Close myStudio or any other software using COM8")
        print("  4. Try running: python -m serial.tools.list_ports")
        print("  5. Check Windows Device Manager for COM8")
        print("\nThe robot-service can still run in MOCK mode!")
        print("Set mock_mode: true in config/settings.yaml")
        return 1
    
    print(f"\nCurrent angles: {angles}")
    print(f"  J1={angles[0]:.1f}  J2={angles[1]:.1f}  J3={angles[2]:.1f}")
    print(f"  J4={angles[3]:.1f}  J5={angles[4]:.1f}  J6={angles[5]:.1f}")

    # Small delta move: adjust joint1 by +5 degrees
    target = angles.copy()
    target[0] = target[0] + 5.0
    
    # Clamp to safe range
    target[0] = max(-165, min(165, target[0]))

    print(f"\nMoving J1 by +5 degrees...")
    print(f"  Target: {target}")
    
    try:
        mc.send_angles(target, 20)  # (angles, speed)
        print("  Move command sent. Waiting 3 seconds...")
        time.sleep(3)
    except Exception as e:
        print(f"  send_angles failed: {e}")
        return 1

    # Read position after move
    after_angles = mc.get_angles()
    print(f"  After move: {after_angles}")

    # Return to original
    print("\nReturning to original position...")
    try:
        mc.send_angles(angles, 20)
        time.sleep(3)
    except Exception as e:
        print(f"  Return failed: {e}")

    # Stop
    print("Sending stop command...")
    try:
        mc.stop()
    except Exception as e:
        print(f"  stop not available: {e}")

    # Final position
    final_angles = mc.get_angles()
    print(f"Final angles: {final_angles}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] BRING-UP TEST COMPLETE!")
    print("=" * 50)
    print(f"\nWorking configuration:")
    print(f"  Port: {PORT}")
    print(f"  Baud: {working_baud}")
    print("\nUpdate config/settings.yaml with these values.")
    print("You can now start the robot-service:")
    print("  cd robot-service && python app.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
