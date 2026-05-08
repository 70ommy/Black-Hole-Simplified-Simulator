# BlackHoleBOB - Control Reference

Complete guide to all controls and keyboard shortcuts in the BlackHoleBOB simulator.

## 🎮 Camera Controls

### Mouse Controls
| Control | Action |
|---------|--------|
| **Left Mouse Drag** | Rotate camera view (look around) |
| **Mouse Movement** | Change viewing direction while dragging |

### Keyboard Movement
| Key | Action | Description |
|-----|--------|-------------|
| **W** | Move Forward | Move camera in the direction you're looking |
| **S** | Move Backward | Move camera opposite to viewing direction |
| **A** | Move Left | Strafe left (perpendicular to view) |
| **D** | Move Right | Strafe right (perpendicular to view) |
| **Q** | Move Up | Move straight up (world Y-axis) |
| **E** | Move Down | Move straight down (world Y-axis) |
| **Shift + Movement** | Fast Mode | Hold Shift while moving for 4× speed |

### Camera Rotation
| Key | Action |
|-----|--------|
| **↑ (Up Arrow)** | Rotate view up (pitch up) |
| **↓ (Down Arrow)** | Rotate view down (pitch down) |
| **← (Left Arrow)** | Rotate view left (yaw left) |
| **→ (Right Arrow)** | Rotate view right (yaw right) |

## ⚙️ Simulation Controls

### Basic Controls
| Key | Action | Description |
|-----|--------|-------------|
| **Space** | Pause/Resume | Toggle simulation pause |
| **R** | Reset | Reset simulation to initial state |
| **ESC** | Quit | Exit the simulator |

### Time Controls
| Key | Action | Description |
|-----|--------|-------------|
| **+** or **=** | Speed Up | Increase simulation time speed |
| **-** or **_** | Slow Down | Decrease simulation time speed |

### Preset Configurations
| Key | Preset | Configuration |
|-----|--------|---------------|
| **1** | Default | Mass: 10.0, Bodies: 5, Disc: ON |
| **2** | Massive | Mass: 30.0, Bodies: 8, Disc: ON |
| **3** | Minimal | Mass: 5.0, Bodies: 3, Disc: ON |

## 📋 Configuration Menu

### Navigation
| Key | Action |
|-----|--------|
| **↑ (Up Arrow)** | Move selection up |
| **↓ (Down Arrow)** | Move selection down |
| **← (Left Arrow)** | Decrease value / Toggle OFF |
| **→ (Right Arrow)** | Increase value / Toggle ON |
| **Space** or **Enter** | Confirm / Start simulation |
| **ESC** | Quit to desktop |

### Configurable Options
1. **Black Hole Mass** (1.0 - 50.0)
   - Affects gravitational strength
   - Changes Schwarzschild radius
   - Impacts lensing intensity

2. **Orbiting Bodies** (0 - 15)
   - Number of planets/objects
   - Each has elliptical orbit
   - Random 3D inclinations

3. **Accretion Disc** (ON/OFF)
   - 5,000 particle disc
   - Temperature-based colors
   - Gravitational lensing effects

4. **Enable Orbiting Bodies** (ON/OFF)
   - Toggle orbital mechanics
   - Independent from disc

## 🎯 Camera Tips

### Best Viewing Angles for Lensing
1. **Edge-On View**: Position camera at disc height, look horizontally
2. **Slight Angle**: 15-30° above/below disc plane
3. **Close Proximity**: Move within 20-30 units of black hole
4. **Behind Disc**: View disc with black hole in foreground

### Navigation Techniques
- **Orbit Around**: Use A/D while rotating with mouse
- **Fly Through**: Use W/S with Q/E for vertical adjustment
- **Quick Reposition**: Use Shift for fast movement
- **Precise Control**: Release Shift for fine adjustments

## 🔍 Observation Guide

### What to Look For

**Einstein Ring**
- Bright ring around black hole edge
- Most visible from edge-on view
- Size: ~1.3× visual black hole radius

**Lensed Particles**
- Stretched and brightened disc particles
- Appear at black hole distance
- ~50-60% of particles affected

**Temperature Gradient**
- Blue-white: Inner hot regions (10,000K+)
- White-yellow: Middle regions (6,000K)
- Orange-red: Outer cool regions (3,000K)

**Orbital Motion**
- Elliptical paths of orbiting bodies
- 3D inclinations visible
- Faster motion closer to black hole

## 🎨 Visual Features

### Retro Elements
- **Grid Floor**: Cyan wireframe grid at y=-20
- **Bounding Box**: Simulation boundary visualization
- **Particle Trails**: Motion history for orbiting bodies
- **Starfield**: 1,500 background stars

### Color Coding
- **Black Hole**: Orange-red sphere
- **Accretion Disc**: Temperature gradient (blue→red)
- **Orbiting Bodies**: Random bright colors
- **Grid**: Cyan (0, 0.5, 0.5)
- **Stars**: Blue, white, yellow, orange-red

## ⚡ Performance Tips

### For Better Frame Rate
1. Reduce orbiting bodies (use 0-3)
2. Disable orbiting bodies toggle
3. Use lower black hole mass (5.0-10.0)
4. Close other applications
5. Ensure GPU drivers are updated

### For Better Visuals
1. Enable accretion disc
2. Use higher black hole mass (20.0-30.0)
3. Position camera for edge-on view
4. Adjust time speed for smooth motion

## 🐛 Troubleshooting

### Camera Issues
**Problem**: Camera moves in wrong direction
- **Solution**: Check if you're holding Shift accidentally
- **Solution**: Reset view with arrow keys

**Problem**: Can't see anything
- **Solution**: Press R to reset
- **Solution**: Move camera with Q/E to adjust height

### Simulation Issues
**Problem**: Nothing is moving
- **Solution**: Press Space to unpause
- **Solution**: Check time speed (press + to increase)

**Problem**: Lensing not visible
- **Solution**: Move closer to black hole
- **Solution**: View disc from edge-on angle
- **Solution**: Ensure disc is enabled in config

## 📊 UI Information Display

### On-Screen Information
- **FPS**: Frames per second (top-left)
- **Camera Position**: X, Y, Z coordinates
- **Time Speed**: Current simulation speed multiplier
- **Pause Status**: Displayed when paused
- **Particle Count**: Lensed vs normal particles (debug mode)

## 🎓 Learning Exercises

### Beginner
1. Orbit around the black hole using A/D + mouse
2. Observe Einstein ring from different angles
3. Watch temperature gradient on disc
4. Try different presets (1, 2, 3)

### Intermediate
1. Find optimal viewing angle for lensing
2. Observe how mass affects lensing strength
3. Track individual orbiting bodies
4. Experiment with time speed

### Advanced
1. Identify magnification effects on particles
2. Observe transition zones in lensing
3. Study orbital mechanics of bodies
4. Analyze temperature distribution

---

**Quick Reference Card**

```
MOVEMENT:  W/A/S/D + Q/E (Shift=Fast)
LOOK:      Mouse Drag + Arrow Keys
CONTROL:   Space=Pause  R=Reset  ESC=Quit
TIME:      +/- for speed
PRESETS:   1/2/3
```

**For detailed physics information, see LENSING.md**