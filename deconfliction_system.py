import math
from datetime import datetime, timedelta
# import matplotlib.pyplot as plt
# import numpy as np
# import imageio
from datetime import timedelta

def interpolate_path(waypoints, interval=1):
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
    # Add last waypoint if not included
    last_wp_time = datetime.fromisoformat(waypoints[-1]['time'])
    if path[-1]['time'] != last_wp_time:
        path.append({
            "x": waypoints[-1]['x'],
            "y": waypoints[-1]['y'],
            "z": waypoints[-1]['z'],
            "time": last_wp_time
        })
    return path


def euclidean_distance(p1, p2):
    dx = p1["x"] - p2["x"]
    dy = p1["y"] - p2["y"]
    dz = p1.get("z", 0) - p2.get("z", 0)
    return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

def detect_conflicts(primary_path, other_drones_paths, buffer_distance=5.0, debug=False, time_threshold=30):
    conflicts = []

    for drone in other_drones_paths:
        drone_id = drone['id']
        other_path = drone['path']

        # Iterate through each primary waypoint
        for p1 in primary_path:
            t1 = p1['time'] if isinstance(p1['time'], datetime) else datetime.fromisoformat(p1['time'])

            # Check for closest waypoint in other drone path within time_threshold
            for p2 in other_path:
                t2 = p2['time'] if isinstance(p2['time'], datetime) else datetime.fromisoformat(p2['time'])
                time_diff = abs((t1 - t2).total_seconds())
                
                if time_diff <= time_threshold:
                    dist = euclidean_distance(p1, p2)
                    if dist < buffer_distance:
                        conflicts.append({
                            "conflict_with": drone_id,
                            "location": {
                                "x": (p1['x'] + p2['x']) / 2,
                                "y": (p1['y'] + p2['y']) / 2,
                                "z": (p1['z'] + p2['z']) / 2
                            },
                            "time": t1.isoformat(),
                            "distance": dist
                        })
                        if debug:
                            print(f"Conflict with {drone_id} at time {t1.isoformat()} ±{time_threshold}s, dist={dist:.2f}m")
                    break  # Found a conflict for this primary waypoint, move to next

    return conflicts


def create_gif(primary_path, other_drones_paths, conflicts, gif_path):
    import matplotlib.pyplot as plt
    import numpy as np
    import imageio

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    primary_coords = np.array([[p['x'], p['y'], p['z']] for p in primary_path])
    primary_times = [p['time'] for p in primary_path]

    drones_data = []
    for drone in other_drones_paths:
        coords = np.array([[p['x'], p['y'], p['z']] for p in drone['path']])
        times = [p['time'] for p in drone['path']]
        drones_data.append((drone['id'], times, coords))

    conflict_points = np.array([[c['location']['x'], c['location']['y'], c['location']['z']] for c in conflicts]) if conflicts else np.empty((0,3))

    ax.plot(primary_coords[:, 0], primary_coords[:, 1], primary_coords[:, 2], label="Primary Drone", color='blue')
    for drone_id, times, coords in drones_data:
        ax.plot(coords[:, 0], coords[:, 1], coords[:, 2], label=drone_id, linestyle='--', alpha=0.6)
    if len(conflict_points) > 0:
        ax.scatter(conflict_points[:, 0], conflict_points[:, 1], conflict_points[:, 2], c='red', s=60, label='Conflicts')

    ax.legend()

    drone_markers = [ax.plot([], [], [], 'o')[0] for _ in drones_data]
    primary_marker, = ax.plot([], [], [], 'o', color='blue')

    images = []
    for frame_idx in range(len(primary_path)):
        current_time = primary_times[frame_idx]

        primary_marker.set_data([primary_coords[frame_idx, 0]], [primary_coords[frame_idx, 1]])
        primary_marker.set_3d_properties([primary_coords[frame_idx, 2]])

        for i, (drone_id, times, coords) in enumerate(drones_data):
            if frame_idx < len(coords):
                drone_markers[i].set_data([coords[frame_idx, 0]], [coords[frame_idx, 1]])
                drone_markers[i].set_3d_properties([coords[frame_idx, 2]])

        ax.set_title(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        buf.shape = (h, w, 4)
        buf = buf[:, :, [1, 2, 3, 0]]  # ARGB to RGBA
        image = buf[:, :, :3]  # Drop alpha channel
        images.append(image)

    imageio.mimsave(gif_path, images, fps=5, loop=0)
    plt.close(fig)


def generate_safe_path(primary_path, conflicts, climb_rate=5.0):
    safe_path = primary_path.copy()
    conflict_times = [datetime.fromisoformat(c['time']) for c in conflicts]
    climb_status = 0  # positive for climbing, negative for descending

    for i, wp in enumerate(safe_path):
        wp_time = wp['time'] if isinstance(wp['time'], datetime) else datetime.fromisoformat(wp['time'])
        in_conflict = any(abs((wp_time - ct).total_seconds()) <= 5 for ct in conflict_times)

        if in_conflict:
            climb_status = climb_rate  # start climbing
        elif climb_status > 0:
            climb_status = max(climb_status - 1, 0)  # slowly descend
        else:
            climb_status = 0

        safe_path[i]['z'] = primary_path[i]['z'] + climb_status

    return safe_path
