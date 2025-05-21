import json
from datetime import datetime, timedelta
import math
import matplotlib.pyplot as plt
import numpy as np


# Load the JSON Files
with open('primary_drone.json') as f:
    primary_drone = json.load(f)

with open('in_the_air_drones.json') as f:
    other_drones = json.load(f)


# Interpolate Drone Paths
# We'll generate positions every second between waypoints
# Interpolate positions between waypoints at fixed intervals (seconds)
# Returns a list of dicts with {x, y, z, time}
def interpolate_path(waypoints, interval=60):
    path = []
    for i in range(len(waypoints) - 1):
        wp1, wp2 = waypoints[i], waypoints[i+1]
        t1 = datetime.fromisoformat(wp1['time'])
        t2 = datetime.fromisoformat(wp2['time'])
        total_seconds = int((t2 - t1).total_seconds())

        steps = total_seconds // interval
        for step in range(steps + 1):
            ratio = step / steps if steps else 0
            x = wp1['x'] + (wp2['x'] - wp1['x']) * ratio
            y = wp1['y'] + (wp2['y'] - wp1['y']) * ratio
            z = wp1.get('z', 0) + (wp2.get('z', 0) - wp1.get('z', 0)) * ratio
            t = t1 + timedelta(seconds=step * interval)
            path.append({"x": x, "y": y, "z": z, "time": t})
    return path


def euclidean_distance(p1, p2):
    dx = p1["x"] - p2["x"]
    dy = p1["y"] - p2["y"]
    dz = p1.get("z", 0) - p2.get("z", 0)
    return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)


# Conflict Detection with minimum distance threshold as 5m
def detect_conflicts(primary_path, other_drones_paths, buffer_distance=5.0):
    conflicts = []
    for drone in other_drones_paths:
        drone_id = drone['id']
        path = drone['path']
        for p1 in primary_path:
            for p2 in path:
                # Check whether the drones come at the same position within 5 seconds
                if abs((p1['time'] - p2['time']).total_seconds()) <= 5:
                    dist = euclidean_distance(p1, p2)
                    # Check whether the distance of the drones are less than 5m
                    if dist < buffer_distance:
                        conflicts.append({
                            "conflict_with": drone_id,
                            "location": {"x": (p1['x'] + p2['x']) / 2,
                                         "y": (p1['y'] + p2['y']) / 2,
                                         "z": (p1['z'] + p2['z']) / 2},
                            "time": p1['time'].isoformat(),
                            "distance": dist
                        })
    return conflicts


# Convert Path to NumPy Arrays for smoother animation
def path_to_array(path):
    times = [p['time'] for p in path]
    coords = np.array([[p['x'], p['y'], p['z']] for p in path])
    return times, coords


# Simulation of the drones to show the positions where they collide
def animate_simulation(primary_path, other_drones_paths, conflicts):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("4D UAV Deconfliction Simulation (3D + Time)", fontsize=14)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # Plot static paths
    primary_times, primary_coords = path_to_array(primary_path)
    ax.plot(primary_coords[:, 0], primary_coords[:, 1], primary_coords[:, 2], label="Primary Drone", color='blue')

    drones_data = []
    for drone in other_drones_paths:
        times, coords = path_to_array(drone['path'])
        drones_data.append((drone['id'], times, coords))
        ax.plot(coords[:, 0], coords[:, 1], coords[:, 2], label=drone['id'], linestyle='--', alpha=0.6)

    conflict_points = np.array([[c['location']['x'], c['location']['y'], c['location']['z']] for c in conflicts])
    if len(conflict_points) > 0:
        ax.scatter(conflict_points[:, 0], conflict_points[:, 1], conflict_points[:, 2], c='red', s=60, label='Conflicts')

    ax.legend()

    # Animate drone movement over time
    drone_markers = [ax.plot([], [], [], 'o', label=id)[0] for id, _, _ in drones_data]
    primary_marker, = ax.plot([], [], [], 'o', color='blue')

    def update(frame_idx):
        current_time = primary_times[frame_idx]
        primary_marker.set_data([primary_coords[frame_idx, 0]], [primary_coords[frame_idx, 1]])
        primary_marker.set_3d_properties([primary_coords[frame_idx, 2]])

        for i, (id, times, coords) in enumerate(drones_data):
            if frame_idx < len(coords):
                drone_markers[i].set_data([coords[frame_idx, 0]], [coords[frame_idx, 1]])
                drone_markers[i].set_3d_properties([coords[frame_idx, 2]])
        ax.set_title(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return [primary_marker] + drone_markers


primary_path = interpolate_path(primary_drone['waypoints'])

other_drones_paths = []
for drone in other_drones:
    interpolated = interpolate_path(drone['waypoints'])
    other_drones_paths.append({"id": drone['id'], "path": interpolated})

conflicts = detect_conflicts(primary_path, other_drones_paths)

# if conflicts:
#     print("Conflict Detected! ❌")
#     for c in conflicts:
#         print(f"Conflict with {c['conflict_with']} at {c['location']} on {c['time']}, distance: {c['distance']:.2f}m")
# else:
#     print("Mission is clear ✅")

# animate_simulation(primary_path, other_drones_paths, conflicts)
