# UAV Strategic Deconfliction System

This system detects and visualizes **spatio-temporal conflicts** between UAV (Unmanned Aerial Vehicle) missions in **shared airspace**. It checks whether a new (primary) mission plan is safe to execute by comparing it against other UAVs already in flight.

## 🚀 Features

- ✅ **Spatio-Temporal Conflict Detection**: Identifies conflicts when drones come within 5 meters and 5 seconds of each other.
- ✅ **3D Visualization**: Animated 3D trajectory visualization using `matplotlib`, with conflict points highlighted.
- ✅ **Streamlit UI**: User-friendly interface for uploading files, detecting conflicts, and displaying results.
- ✅ **GIF Export**: Generates an animated `.gif` of drone movements with conflict points for easy sharing and review.

---

## 📁 Input Format

### 1. Primary Drone Mission (`primary_drone.json`)

```json
[
  {
    "time": "2024-06-01T12:00:00",
    "x": 0,
    "y": 0,
    "z": 10
  },
  ...
]
```

- `time`: ISO 8601 timestamp
- `x`, `y`, `z`: Position coordinates in meters

### 2. Other Active Missions (`in_the_air_drones.json`)

```json
[
  {
    "drone_id": "Drone_A",
    "path": [
      {
        "time": "2024-06-01T11:59:57",
        "x": 3,
        "y": 2,
        "z": 10
      },
      ...
    ]
  },
  ...
]
```

- `drone_id`: Unique identifier for each drone
- `path`: List of time-stamped coordinates

---

## ⚙️ How It Works

1. Paths are **interpolated** at fixed intervals for smoother analysis.
2. Each point in the primary drone’s path is compared to nearby points in other drones’ paths.
3. If a point is found within **5 meters and 5 seconds** of another, it is flagged as a conflict.
4. All drones' paths and conflict points are visualized in a **3D animated simulation**.

---

## 🧪 How to Use

### 🖥️ Local Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/thisisshv/uav-deconfliction-system.git
   cd uav-deconfliction-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

4. Upload your `primary_drone.json` via the interface and hit **Run Conflict Detection**.

---

## 📷 Sample Output

- Textual conflict report listing drone IDs and timestamps
- Animated 3D `.gif` showing:
  - All drone paths
  - Highlighted conflict points (in red)

---

## 🧩 Dependencies

- `streamlit`
- `matplotlib`
- `numpy`
- `imageio`

(See `requirements.txt`)

---

## 👨‍💻 Author

**Shivanshu Kumar**  
Data Science | Data Engineer | Big Data
