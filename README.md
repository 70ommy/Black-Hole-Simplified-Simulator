# BlackHoleBOB - 3D Gravitational Simulator

A retro 90s-style 3D particle-based simulator for black holes, stars, and gravitational physics with realistic gravitational lensing effects and curved spacetime visualization.

![Bob's Blkack Hole](https://img.shields.io/badge/Physics-Gravitational%20Lensing-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![OpenGL](https://img.shields.io/badge/OpenGL-3D%20Graphics-red)

## 🌌 Features

### Core Simulation
- **3D Particle-Based Physics** - Real-time gravitational simulation
- **Universal Gravitational Lensing** - Applied to ALL particles (disc + orbiting bodies)
- **Curved Spacetime Grid** - Visual representation of gravitational warping
- **Static Accretion Disc** - 5,000 particles with temperature-based colors (optimized for performance)
- **Keplerian Orbits** - Elliptical orbits with 3D inclinations
- **Starfield Background** - 50,000 stars with realistic color variations

### Visual Effects
- **Temperature-Based Colors** - Blackbody radiation gradient:
  - Inner disc (10,000K+): Blue-white
  - Middle disc (6,000K): White-yellow
  - Outer disc (3,000K): Orange-red
- **Einstein Ring** - Visible gravitational lensing around black hole
- **Curved Spacetime** - Grid warps downward showing gravity well
- **Particle Lensing** - Orbiting bodies experience position displacement and brightness boost
- **Shape Distortion** - Tangential stretching of planet wireframes near black hole
- **Trail Lensing** - Particle trails follow lensed positions smoothly
- **Retro 90s Aesthetic** - Wireframe, grid, particle rendering
- **Ultra-Smooth Transitions** - Extended cubic falloff over 2× range for imperceptible changes

### Physics Implementation
- **Einstein Radius**: θ_E = √(4GM/c² × D_LS/(D_L × D_S))
- **Deflection Angle**: α = 4GM/(c² × b)
- **Lens Equation**: β = θ - α(θ)
- **Magnification**: μ = θ/β with brightness scaling
- **Ray-Sphere Intersection** - Validates light paths through BH sphere
- **Spacetime Curvature** - Grid depression based on Schwarzschild radius

## 🎮 Controls

### Camera Movement
- **Mouse Drag**: Look around (rotate view)
- **W/A/S/D**: Move forward/left/backward/right
- **Q/E**: Move up/down (true vertical)
- **Arrow Keys**: Rotate camera view
- **Shift**: Fast movement mode

### Simulation Controls
- **Space**: Pause/Resume simulation
- **R**: Reset simulation
- **+/-**: Adjust time speed
- **1/2/3**: Load different presets
- **ESC**: Quit

## 📦 Installation

### Requirements
- Python 3.8+
- pygame
- numpy
- PyOpenGL
- PyOpenGL-accelerate (optional, for better performance)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/BlackHoleBOB.git
cd BlackHoleBOB

# Install dependencies
pip install pygame numpy PyOpenGL PyOpenGL-accelerate

# Run the simulator
python main.py
```

## 🚀 Usage

1. **Launch**: Run `python main.py`
2. **Configure**: Use the configuration menu to set:
   - Black hole mass (1.0 - 50.0)
   - Number of orbiting bodies (0 - 15)
   - Enable/disable accretion disc
   - Enable/disable orbiting bodies
3. **Start**: Press ENTER or SPACE to begin simulation
4. **Navigate**: Use mouse and keyboard to explore the 3D space
5. **Observe**: Watch gravitational lensing effects on all particles

## 🔬 Physics Details

### Gravitational Lensing
The simulator implements proper gravitational lensing based on general relativity:

1. **Light Ray Calculation**: Traces light paths from particles to camera
2. **Impact Parameter**: Calculates closest approach distance to black hole
3. **Deflection**: Applies Einstein deflection angle based on impact parameter
4. **Image Position**: Solves lens equation for lensed particle positions
5. **Magnification**: Scales brightness based on gravitational magnification

### Universal Lensing System
**NEW**: Lensing now applies to ALL particles in the scene:
- **Accretion Disc**: ~50% of 5,000 particles show lensing
- **Orbiting Bodies**: Planets experience lensing based on position
- **Position Displacement**: Particles appear shifted toward black hole
- **Brightness Boost**: Magnification increases particle brightness
- **Size Scaling**: Heavily lensed particles appear slightly larger

### Lensing Parameters
- **Lensing Zone**: 4.0× to 0.6× visual black hole radius
- **Extended Transition**: Ultra-smooth cubic falloff over 2× extended range
- **Falloff Method**: Cubic decay (t³) for imperceptible transitions
- **Einstein Ring**: Clamped to 1.3× visual radius
- **Affected Particles**: 50-60% of disc + all orbiting bodies when aligned

### Curved Spacetime Grid
**NEW**: The grid floor now visualizes spacetime curvature:
- **Warping Formula**: y = base_y - (warp_strength / (1 + distance × 0.5))
- **Maximum Depression**: At black hole center (2× warp strength)
- **Smooth Falloff**: Depression decreases with distance
- **Visual Effect**: Creates visible "gravity well" around black hole

### Temperature Model
Accretion disc colors follow blackbody radiation:
- **Hot (>7,000K)**: Blue-white (inner regions)
- **Medium (4,000-7,000K)**: White-yellow (middle)
- **Cool (<4,000K)**: Orange-red (outer regions)

### Performance Optimizations
**NEW**: Static accretion disc for better performance:
- **No Rotation**: Disc particles maintain fixed positions
- **Reduced Calculations**: Eliminates 5,000 position updates per frame
- **Improved Frame Rate**: 30-60 FPS on most hardware
- **Lensing Only**: Visual dynamics from gravitational effects

## 📊 Performance

- **Particles**: 5,000 accretion disc particles (static)
- **Stars**: 50,000 background stars
- **Orbiting Bodies**: 0-15 configurable
- **Frame Rate**: 30-60 FPS (depends on hardware)
- **Lensing Calculations**: Real-time per frame for all particles

## 🎨 Retro Aesthetic

The simulator features a nostalgic 90s look:
- Curved spacetime grid (cyan wireframe)
- Particle-based rendering
- Cyan/magenta color scheme
- Smooth anti-aliased lines
- Dark space background with stars

## 📝 Configuration Presets

### Preset 1 (Default)
- Mass: 10.0
- Orbiting bodies: 5
- Accretion disc: Enabled

### Preset 2 (Massive)
- Mass: 30.0
- Orbiting bodies: 8
- Accretion disc: Enabled

### Preset 3 (Minimal)
- Mass: 5.0
- Orbiting bodies: 3
- Accretion disc: Enabled

## 🐛 Troubleshooting

### Common Issues

**Low Frame Rate**
- Reduce number of orbiting bodies
- Disable accretion disc temporarily
- Close other applications
- Ensure GPU drivers are updated

**Lensing Not Visible**
- Move camera closer to black hole
- View disc from edge-on angle
- Ensure accretion disc is enabled
- Check that orbiting bodies are behind black hole

**Grid Not Curved**
- Ensure black hole is present (mass > 0)
- Move camera to see grid from different angles
- Grid curvature is most visible from side view

**Controls Not Responding**
- Check if simulation is paused (press Space)
- Ensure window has focus
- Try resetting with R key

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional physics effects (Doppler shift, time dilation)
- More visual effects (bloom, glow)
- Performance optimizations
- Additional presets and scenarios
- VR support

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Gravitational lensing equations from Wikipedia
- Physics formalism from general relativity textbooks
- Inspired by real astrophysical simulations
- Curved spacetime visualization concepts

## 📚 References

- [Gravitational Lensing (Wikipedia)](https://en.wikipedia.org/wiki/Gravitational_lens)
- [Schwarzschild Metric](https://en.wikipedia.org/wiki/Schwarzschild_metric)
- [Accretion Disc Physics](https://en.wikipedia.org/wiki/Accretion_disk)
- [Spacetime Curvature](https://en.wikipedia.org/wiki/Curvature_of_spacetime)

## 🆕 Recent Updates

### Version 1.2 (Latest)
- ✅ Ultra-smooth lensing transitions with extended cubic falloff
- ✅ Tangential shape distortion on planet wireframes
- ✅ Trail lensing following particle positions
- ✅ Event horizon collision detection
- ✅ No visible jumps or discontinuities

### Version 1.1
- ✅ Universal gravitational lensing (all particles)
- ✅ Curved spacetime grid visualization
- ✅ Static accretion disc for performance
- ✅ Improved frame rate and stability
- ✅ Enhanced visual effects

### Version 1.0
- Initial release with basic lensing
- Temperature-based colors
- 50,000 star background
- Full 3D navigation

---

**Made with ❤️ for physics and retro aesthetics**