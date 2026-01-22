import bge
import csv
import os
import math

def main():
    controller = bge.logic.getCurrentController()
    owner = controller.owner
    
    # Access the Sound Actuator attached to the object
    sound_actuator = controller.actuators.get('Sound')

    # 1. Initialization Phase
    if "initialized" not in owner:
        initialize_logic(owner, sound_actuator)

    # 2. Per-Frame Update Phase
    if owner.get("speed_data"):
        update_frame(owner, sound_actuator)

def initialize_logic(owner, sound_actuator):
    """Initializes properties and loads RPM data from the CSV file."""
    # Expand path to find Speed.csv in the same directory as the .blend file
    csv_path = bge.logic.expandPath("//Speed.csv")
    owner["speed_data"] = []
    owner["index"] = 0
    owner["smooth_speed"] = 0.0
    
    try:
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip the header row
                for row in reader:
                    if len(row) > 1:
                        # Store speed values as floats
                        owner["speed_data"].append(float(row[1]))
        else:
            print(f"File Error: {csv_path} not found.")
    except Exception as e:
        print(f"Load Error: {e}")

    # Activate sound actuator and set initial volume to 0
    if sound_actuator:
        bge.logic.getCurrentController().activate(sound_actuator)
        sound_actuator.volume = 0.0
    
    owner["initialized"] = True

def update_frame(owner, sound_actuator):
    """Calculates rotation and sound dynamics based on current RPM."""
    data = owner["speed_data"]
    idx = owner["index"]
    
    # Retrieve target RPM from the current data index
    target_rpm = data[idx] if idx < len(data) else 0.0
    
    # Speed Smoothing (Interpolation)
    # Higher lerp_factor (e.g., 0.2) follows the CSV data more strictly
    lerp_factor = 0.2 
    owner["smooth_speed"] += (target_rpm - owner["smooth_speed"]) * lerp_factor
    current_rpm = owner["smooth_speed"]
    
    # Increment index to move to the next CSV row in the next frame
    if idx < len(data) - 1:
        owner["index"] += 1

    # --- Time-Synchronized Rotation Calculation ---
    # Get the real-time Logic Tick Rate (FPS) to ensure speed matches real time
    logic_fps = bge.logic.getLogicTicRate() 
    
    # Formula: Convert RPM to Radians per Frame
    # (RPM / 60) = Revolutions per Second
    # (Revolutions per Second / FPS) = Revolutions per Frame
    # Multiply by 2*PI to get Radians per Frame
    rotation_per_frame = (current_rpm / 60.0) / logic_fps * (2 * math.pi)

    # Apply rotation. Adjust index [X, Y, Z] based on your object's axis.
    # Currently set to Y-axis (middle value).
    owner.applyRotation([0, rotation_per_frame, 0], True)

    # --- Dynamic Sound Logic ---
    if sound_actuator:
        # Max volume threshold (1.0 is full volume)
        max_volume = 1.0 
        
        # Max expected RPM for normalization (Adjust this to match your CSV max)
        reference_rpm = 3000.0 
        
        # Calculate target volume based on current speed percentage
        target_vol = (abs(current_rpm) / reference_rpm) * max_volume
        
        # Smooth volume transitions (Fade Speed)
        fade_speed = 0.1
        sound_actuator.volume += (target_vol - sound_actuator.volume) * fade_speed
        
        # Adjust Pitch: Base pitch 0.5 + dynamic increase based on RPM
        sound_actuator.pitch = 0.5 + (abs(current_rpm) / reference_rpm) * 1.5

        # Cut sound completely if the object is nearly stationary
        if abs(current_rpm) < 0.1:
            sound_actuator.volume = 0.0

if __name__ == "__main__":
    main()