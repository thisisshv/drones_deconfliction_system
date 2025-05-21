import streamlit as st
import json
import tempfile
from deconfliction_system import interpolate_path, detect_conflicts
import matplotlib.pyplot as plt
import numpy as np
import imageio

# Load the other drones JSON once here
with open('in_the_air_drones.json') as f:
    other_drones = json.load(f)

def parse_uploaded_file(uploaded_file):
    try:
        data = json.load(uploaded_file)
        return data
    except Exception as e:
        st.error(f"Error parsing JSON file: {e}")
        return None

def display_mission_data(data):
    st.subheader("📍 Mission Details")
    # Since primary_drone.json has waypoints only (no start_time/end_time), infer from first/last waypoints
    start_time = data['waypoints'][0]['time']
    end_time = data['waypoints'][-1]['time']
    st.write(f"**Start Time:** {start_time}")
    st.write(f"**End Time:** {end_time}")
    st.write("**Waypoints:**")
    for i, wp in enumerate(data["waypoints"]):
        st.write(f"- Waypoint {i + 1}: (x={wp['x']}, y={wp['y']}, z={wp['z']}), time={wp['time']}")

def create_gif(primary_path, other_drones_paths, conflicts, gif_path):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    primary_times = [p['time'] for p in primary_path]
    primary_coords = np.array([[p['x'], p['y'], p['z']] for p in primary_path])

    drones_data = []
    for drone in other_drones_paths:
        times = [p['time'] for p in drone['path']]
        coords = np.array([[p['x'], p['y'], p['z']] for p in drone['path']])
        drones_data.append((drone['id'], times, coords))

    conflict_points = np.array([[c['location']['x'], c['location']['y'], c['location']['z']] for c in conflicts]) if conflicts else np.empty((0,3))

    # Draw static paths
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

        # Draw the canvas and convert to image
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        buf.shape = (h, w, 4)
        # Convert ARGB to RGBA
        buf = buf[:, :, [1, 2, 3, 0]]
        # Convert to RGB (drop alpha)
        image = buf[:, :, :3]
        images.append(image)

    # Save images as GIF
    imageio.mimsave(gif_path, images, fps=5, loop=0)

    plt.close(fig)

def main():
    st.title("🚁 UAV Strategic Deconfliction System")
    st.write("Upload the primary drone mission JSON file (`primary_drone.json`). The system will automatically load other airborne drones' data.")

    uploaded_file = st.file_uploader("Upload Primary Drone Mission JSON", type=["json"])

    if uploaded_file:
        primary_drone = parse_uploaded_file(uploaded_file)
        if primary_drone:
            display_mission_data(primary_drone)

            if st.button("🛡️ Check for Conflicts"):
                # Interpolate paths
                primary_path = interpolate_path(primary_drone['waypoints'])

                other_drones_paths = []
                for drone in other_drones:
                    interpolated = interpolate_path(drone['waypoints'])
                    other_drones_paths.append({"id": drone['id'], "path": interpolated})

                conflicts = detect_conflicts(primary_path, other_drones_paths)

                if conflicts:
                    st.error("Conflict Detected! ❌")
                    for c in conflicts:
                        st.write(f"Conflict with **{c['conflict_with']}** at {c['location']} on {c['time']}, distance: {c['distance']:.2f}m")
                else:
                    st.success("Mission is clear ✅")

                # Create GIF and display
                with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as tmp_gif:
                    create_gif(primary_path, other_drones_paths, conflicts, tmp_gif.name)
                    st.subheader("🎥 4D UAV Deconfliction Simulation")
                    st.image(tmp_gif.name, caption="Drone Mission Conflict Visualization (GIF)", use_container_width=True)


if __name__ == "__main__":
    main()
