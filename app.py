import streamlit as st
import json
from deconfliction_system import interpolate_path, detect_conflicts, create_gif, generate_safe_path
from datetime import datetime

@st.cache_data
def load_other_drones():
    with open('in_the_air_drones.json') as f:
        return json.load(f)

def display_mission_data(data):
    st.subheader("📍 Mission Details")
    start_time = data['waypoints'][0]['time']
    end_time = data['waypoints'][-1]['time']
    st.write(f"**Start Time:** {start_time}")
    st.write(f"**End Time:** {end_time}")
    st.write("**Waypoints:**")
    for i, wp in enumerate(data["waypoints"]):
        st.write(f"- Waypoint {i + 1}: (x={wp['x']}, y={wp['y']}, z={wp['z']}), time={wp['time']}")

def main():
    st.title("🚁 UAV Strategic Deconfliction System")

    other_drones = load_other_drones()

    uploaded_file = st.file_uploader("Upload Primary Drone Mission JSON", type=["json"])

    if uploaded_file:
        try:
            primary_drone = json.load(uploaded_file)
        except Exception as e:
            st.error(f"Error loading JSON: {e}")
            return

        display_mission_data(primary_drone)

        # Initialize session state variables to store data between reruns
        if 'conflicts' not in st.session_state:
            st.session_state.conflicts = None
        if 'primary_path' not in st.session_state:
            st.session_state.primary_path = None
        if 'other_drones_paths' not in st.session_state:
            st.session_state.other_drones_paths = None
        if 'safe_path' not in st.session_state:
            st.session_state.safe_path = None

        if st.button("🛡️ Check for Conflicts"):
            primary_path = interpolate_path(primary_drone['waypoints'], interval=1)
            other_drones_paths = []
            for drone in other_drones:
                interpolated = interpolate_path(drone['waypoints'], interval=1)
                other_drones_paths.append({"id": drone['id'], "path": interpolated})

            conflicts = detect_conflicts(primary_path, other_drones_paths, buffer_distance=5.0, debug=True)

            st.session_state.primary_path = primary_path
            st.session_state.other_drones_paths = other_drones_paths
            st.session_state.conflicts = conflicts
            st.session_state.safe_path = None  # reset safe path when checking conflicts again

        # Show conflict info if available
        if st.session_state.conflicts is not None and st.session_state.primary_path is not None:
            conflicts = st.session_state.conflicts
            primary_path = st.session_state.primary_path
            other_drones_paths = st.session_state.other_drones_paths

            if conflicts:
                st.error("Conflict Detected! ❌")
                for c in conflicts:
                    loc = c['location']
                    st.write(f"Conflict with **{c['conflict_with']}** at (x={loc['x']:.2f}, y={loc['y']:.2f}, z={loc['z']:.2f}) on {c['time']}, distance: {c['distance']:.2f}m")
            else:
                st.success("Mission is clear ✅")

            create_gif(primary_path, other_drones_paths, conflicts, "current_mission_simulation.gif")
            st.subheader("🎥 Current Mission Simulation")
            st.image("current_mission_simulation.gif", caption="Drone Mission Visualization (GIF)", use_container_width=True)

            # Show generate safe path button only if conflict detected
            if conflicts:
                if st.button("🛠️ Generate Safe Path"):
                    # Generate safe path and store in session state
                    safe_path = generate_safe_path(primary_path, conflicts)
                    st.session_state.safe_path = safe_path

        # If safe_path exists in session_state, show results
        if st.session_state.safe_path is not None:
            st.success("Safe path generated ✅")
            new_path = st.session_state.safe_path
            output_data = {
                "id": primary_drone.get('id', 'primary_drone') + "_safe",
                "waypoints": [
                    {"x": p['x'], "y": p['y'], "z": p['z'], "time": p['time'].isoformat()}
                    for p in new_path
                ]
            }
            json_data = json.dumps(output_data, indent=2)

            st.download_button(
                label="Download Safe Path JSON",
                data=json_data,
                file_name="new_primary_path.json",
                mime="application/json"
            )

            create_gif(new_path, st.session_state.other_drones_paths, st.session_state.conflicts, "safe_path_simulation.gif")
            st.subheader("🎥 Safe Path Simulation")
            st.image("safe_path_simulation.gif", caption="Safe Path Conflict Visualization (GIF)", use_container_width=True)

if __name__ == "__main__":
    main()
