"""
BlackHoleBOB - 3D Particle-Based Black Hole and Star Simulator
A retro 90s-style 3D simulation of gravitational physics with GR effects
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math
import sys
from dataclasses import dataclass

# Constants (using geometric units where G/c^2 ≈ 7.42e-28 m/kg)
G = 6.67430e-11  # Gravitational constant
C = 299792458    # Speed of light
G_OVER_C2 = G / (C * C)  # Conversion factor for mass to meters

@dataclass
class OrbitalElements:
    """Keplerian orbital elements for elliptical orbits"""
    semi_major_axis: float  # a
    eccentricity: float     # e (0 = circular, <1 = elliptical)
    inclination: float      # i (radians)
    longitude_ascending: float  # Ω (radians)
    argument_periapsis: float   # ω (radians)
    true_anomaly: float     # ν (radians)


class Camera:
    """Free-flying 3D Camera with full movement controls"""
    def __init__(self):
        self.position = np.array([0.0, 20.0, 50.0], dtype=float)
        self.rotation_x = 0.0  # Pitch
        self.rotation_y = 0.0  # Yaw
        self.mouse_sensitivity = 0.3
        self.move_speed = 0.5
        self.fast_move_speed = 2.0
        
    def apply(self):
        """Apply camera transformations"""
        glLoadIdentity()
        glRotatef(-self.rotation_x, 1, 0, 0)
        glRotatef(-self.rotation_y, 0, 1, 0)
        glTranslatef(-self.position[0], -self.position[1], -self.position[2])
    
    def handle_mouse_motion(self, dx, dy, buttons):
        """Handle mouse movement for camera rotation"""
        if buttons[0]:  # Left mouse button
            self.rotation_y += dx * self.mouse_sensitivity
            self.rotation_x += dy * self.mouse_sensitivity
            self.rotation_x = max(-89, min(89, self.rotation_x))
    
    def handle_mouse_wheel(self, y):
        """Handle mouse wheel for speed adjustment"""
        self.move_speed += y * 0.1
        self.move_speed = max(0.1, min(5.0, self.move_speed))
    
    def handle_keyboard(self, keys):
        """Handle keyboard input for FPS-style camera movement"""
        # Calculate movement speed (hold SHIFT for faster movement)
        speed = self.fast_move_speed if (keys[K_LSHIFT] or keys[K_RSHIFT]) else self.move_speed
        
        # Convert rotation to radians
        yaw_rad = math.radians(self.rotation_y)
        pitch_rad = math.radians(self.rotation_x)
        
        # Calculate backward vector (direction camera is looking, projected on XZ plane for W/S)
        backward = np.array([
            math.sin(yaw_rad),
            0,  # Keep horizontal for W/S movement
            math.cos(yaw_rad)
        ])
        backward = backward / np.linalg.norm(backward)  # Normalize
        
        # Calculate left vector (perpendicular to backward on XZ plane)
        left = np.array([
            -math.cos(yaw_rad),
            0,
            math.sin(yaw_rad)
        ])
        
        # Calculate true up vector relative to camera (for Q/E)
        camera_up = np.array([
            math.sin(yaw_rad) * math.sin(pitch_rad),
            math.cos(pitch_rad),
            -math.cos(yaw_rad) * math.sin(pitch_rad)
        ])
        
        # WASD movement (horizontal plane relative to camera direction)
        if keys[K_w]:
            self.position -= backward * speed
        if keys[K_s]:
            self.position += backward * speed
        if keys[K_a]:
            self.position += left * speed
        if keys[K_d]:
            self.position -= left * speed
        
        # Q/E for up/down movement along world Y-axis (true vertical)
        world_up = np.array([0, 1, 0])  # Always move straight up/down
        if keys[K_q]:
            self.position += world_up * speed
        if keys[K_e]:
            self.position -= world_up * speed
        
        # Arrow keys for rotation (alternative to mouse)
        if keys[K_LEFT]:
            self.rotation_y -= self.mouse_sensitivity * 2
        if keys[K_RIGHT]:
            self.rotation_y += self.mouse_sensitivity * 2
        if keys[K_UP]:
            self.rotation_x += self.mouse_sensitivity * 2
            self.rotation_x = max(-89, min(89, self.rotation_x))
        if keys[K_DOWN]:
            self.rotation_x -= self.mouse_sensitivity * 2
            self.rotation_x = max(-89, min(89, self.rotation_x))
    
    def get_position(self):
        """Get camera position for physics calculations"""
        return self.position.copy()


class Particle:
    """Represents a particle in the simulation"""
    def __init__(self, position, velocity, mass, color, is_central=False, orbital_elements=None):
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.mass = mass
        self.color = color
        self.is_central = is_central
        self.trail = []
        self.max_trail_length = 150
        self.orbital_elements = orbital_elements
        
    def update_trail(self):
        """Update particle trail for visualization"""
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)


class Photon:
    """Represents a light ray/photon for gravitational lensing"""
    def __init__(self, position, direction, color=(1.0, 1.0, 0.0)):
        self.position = np.array(position, dtype=float)
        self.direction = np.array(direction, dtype=float)
        self.direction = self.direction / np.linalg.norm(self.direction)  # Normalize
        self.color = color
        self.trail = []
        self.max_trail_length = 200
        self.active = True
        
    def update_trail(self):
        """Update photon trail"""
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)


class Starfield:
    """Background starfield for scenic effect"""
    def __init__(self, num_stars=50000, radius=200):
        self.stars = []
        self.generate_stars(num_stars, radius)
    
    def generate_stars(self, num_stars, radius):
        """Generate random stars in a sphere around the scene"""
        for _ in range(num_stars):
            # Random position on sphere
            theta = np.random.uniform(0, 2 * math.pi)
            phi = np.random.uniform(0, math.pi)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            # Random brightness and slight color variation
            brightness = np.random.uniform(0.3, 2.0)
            color_temp = np.random.uniform(0, 1)
            
            # Star colors: blue-white (hot) to red-orange (cool)
            if color_temp > 0.8:  # Blue stars (rare)
                color = (0.7 * brightness, 0.8 * brightness, 1.0 * brightness)
            elif color_temp > 0.5:  # White stars (common)
                color = (0.9 * brightness, 0.9 * brightness, 1.0 * brightness)
            elif color_temp > 0.2:  # Yellow-white stars
                color = (1.0 * brightness, 0.95 * brightness, 0.7 * brightness)
            else:  # Orange-red stars
                color = (1.0 * brightness, 0.6 * brightness, 0.4 * brightness)
            
            # Random size
            size = np.random.uniform(1.0, 3.0)
            
            self.stars.append({
                'position': np.array([x, y, z]),
                'color': color,
                'size': size
            })


class AccretionDisc:
    """Accretion disc around black hole with gravitational lensing"""
    def __init__(self, inner_radius, outer_radius, num_particles=1200):
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.particles = []
        self.generate_particles(num_particles)
        
    def generate_particles(self, num_particles, black_hole_pos=None):
        """Generate disc particles with enhanced brightness"""
        if black_hole_pos is None:
            black_hole_pos = np.array([0.0, 0.0, 0.0])
        
        for i in range(num_particles):
            # Bias towards inner regions for better visibility
            r_normalized = np.random.beta(2, 5)  # Beta distribution biased to inner disc
            r = self.inner_radius + r_normalized * (self.outer_radius - self.inner_radius)
            theta = np.random.uniform(0, 2 * math.pi)
            
            # Position in disc plane (thinner disc) RELATIVE TO BLACK HOLE
            x = black_hole_pos[0] + r * math.cos(theta)
            z = black_hole_pos[2] + r * math.sin(theta)
            y = black_hole_pos[1] + np.random.normal(0, 0.15)  # Thinner disc
            
            # Temperature-based color (inner = hot = blue/white, outer = cooler = red/orange)
            temp_factor = 1.0 - (r - self.inner_radius) / (self.outer_radius - self.inner_radius)
            temp_factor = temp_factor ** 0.7  # Non-linear for more dramatic effect
            
            # Blackbody radiation colors based on temperature
            # Inner disc: ~10,000K+ (blue-white), Outer disc: ~3,000K (red-orange)
            if temp_factor > 0.7:  # Very hot inner region - blue-white
                color = (
                    0.7 + 0.3 * temp_factor,  # Red
                    0.8 + 0.2 * temp_factor,  # Green
                    1.0,                       # Blue - maximum
                )
            elif temp_factor > 0.4:  # Hot middle region - white-yellow
                t = (temp_factor - 0.4) / 0.3
                color = (
                    1.0,                       # Red - maximum
                    0.9 + 0.1 * t,            # Green
                    0.6 + 0.4 * t,            # Blue
                )
            else:  # Cooler outer region - orange-red
                t = temp_factor / 0.4
                color = (
                    1.0,                       # Red - maximum
                    0.4 + 0.5 * t,            # Green
                    0.1 + 0.5 * t,            # Blue
                )
            
            # Brightness/intensity for rendering
            intensity = 0.7 + 0.3 * temp_factor
            
            self.particles.append({
                'position': np.array([x, y, z]),
                'angle': theta,
                'radius': r,
                'color': color,
                'intensity': intensity,
                'lensed_position': np.array([x, y, z]),  # Will be updated with lensing
                'lensed_scale': 1.0,  # Scale factor for stretched appearance
                'y_offset': np.random.normal(0, 0.15)  # Store y offset for updates
            })
    
    def update(self, central_mass, dt, black_hole_pos=None):
        """Update disc particle positions (static disc for performance)"""
        # Disc is now static - no rotation for better performance
        # Particles maintain their initial positions
        pass
    
    def apply_gravitational_lensing(self, black_hole_pos, black_hole_mass, camera_pos):
        """
        Apply gravitational lensing ONLY to particles that are actually obscured by the black hole.
        Uses proper lens equation but only when BH blocks the line of sight.
        """
        schwarzschild_radius = 2 * black_hole_mass
        # Visual radius of black hole (what we see as blocking)
        visual_bh_radius = schwarzschild_radius * 0.5  # Match the rendered size
        
        # IMPORTANT: Reset all particles to not lensed at start of each frame
        for particle in self.particles:
            particle['is_lensed'] = False
        
        for particle in self.particles:
            true_pos = particle['position']
            
            # Vectors from camera
            cam_to_bh = black_hole_pos - camera_pos
            cam_to_particle = true_pos - camera_pos
            
            D_L = np.linalg.norm(cam_to_bh)
            D_S = np.linalg.norm(cam_to_particle)
            
            if D_L < 0.1 or D_S < 0.1:
                # Too close - no lensing (already set to False above)
                continue
            
            # Direction from camera to BH
            cam_bh_dir = cam_to_bh / D_L
            
            # Project particle position onto camera-BH line
            projection_length = np.dot(cam_to_particle, cam_bh_dir)
            
            # Check if the ray from camera to particle actually passes through the BH
            # Use proper ray-sphere intersection test
            cam_particle_dir = cam_to_particle / D_S
            
            # Closest point on ray to BH center: t = dot(cam_to_bh, cam_particle_dir)
            t_closest = np.dot(cam_to_bh, cam_particle_dir)
            
            # Only check if closest point is between camera and particle
            if t_closest <= 0 or t_closest >= D_S:
                # BH is not between camera and particle - no lensing
                particle['is_lensed'] = False
                continue
            
            # Additional check: particle must be on the far side of BH from camera
            # Compare distances: particle should be farther than BH
            if D_S <= D_L:
                # Particle is closer than or at same distance as BH - no lensing
                particle['is_lensed'] = False
                continue
            
            # Find closest point on ray to BH center
            closest_point_on_ray = camera_pos + cam_particle_dir * t_closest
            distance_to_ray = np.linalg.norm(black_hole_pos - closest_point_on_ray)
            
            # SMOOTH TRANSITION: Extended lensing zone for smoother appearance
            # Wider transition zone with intensity decreasing with distance
            # This creates a more diffuse, natural-looking Einstein ring
            lensing_start_radius = visual_bh_radius * 4.0  # Extended outer radius
            lensing_full_radius = visual_bh_radius * 0.6   # Tighter inner radius
            
            if distance_to_ray > lensing_start_radius:
                # Ray is too far - no lensing effect
                particle['is_lensed'] = False
                continue
            
            # Calculate lensing strength based on impact parameter
            # Intensity decreases smoothly with distance from BH center
            if distance_to_ray <= lensing_full_radius:
                lensing_strength = 1.0  # Full lensing at center
            else:
                # Smooth falloff using smoothstep
                # This creates a gradual decrease in lensing intensity
                t = (lensing_start_radius - distance_to_ray) / (lensing_start_radius - lensing_full_radius)
                # Use smoothstep for C¹ continuity
                lensing_strength = t * t * (3.0 - 2.0 * t)
                
                # Additional falloff for very distant particles
                # This makes the outer edge even smoother
                if distance_to_ray > lensing_start_radius * 0.7:
                    outer_t = (lensing_start_radius - distance_to_ray) / (lensing_start_radius * 0.3)
                    lensing_strength *= outer_t * outer_t
            
            # Store lensing strength for blending
            particle['lensing_strength'] = lensing_strength
            
            # BLACK HOLE AFFECTS THIS PARTICLE - Apply lensing
            
            # Calculate Einstein radius
            D_LS = np.linalg.norm(true_pos - black_hole_pos)
            einstein_angle = np.sqrt(4 * black_hole_mass * D_LS / (D_L * D_S))
            einstein_radius = einstein_angle * D_L
            
            # Calculate source angular position β
            # β is the angular separation of the TRUE source from the optical axis
            # Measure perpendicular distance from source to optical axis
            cam_particle_dir = cam_to_particle / D_S
            # Project true position perpendicular to line of sight
            projection_on_los = np.dot(cam_to_particle, cam_bh_dir)
            point_on_los = camera_pos + cam_bh_dir * projection_on_los
            source_offset_vector = true_pos - point_on_los
            beta_physical = np.linalg.norm(source_offset_vector)
            beta = beta_physical / D_S  # Angular position of source
            
            # Solve lens equation: θ = (β + √(β² + 4θ_E²)) / 2
            theta_E_sq = einstein_angle ** 2
            discriminant = beta ** 2 + 4 * theta_E_sq
            
            if discriminant < 0:
                particle['lensed_position'] = true_pos
                particle['lensed_scale'] = 1.0
                particle['magnification'] = 1.0
                continue
            
            sqrt_disc = np.sqrt(discriminant)
            theta_image = (beta + sqrt_disc) / 2  # Primary (outer) image angular position
            
            # The lensed image appears at angular position θ from optical axis
            # At the SOURCE distance D_S (we see it where the source is)
            # Physical radius from optical axis at source distance
            image_radius = theta_image * D_S
            
            # Direction for lensed image (perpendicular to line of sight)
            if beta_physical > 0.01:
                # Use source offset direction (normalized)
                image_direction = source_offset_vector / beta_physical
            else:
                # Perfect alignment - create Einstein ring
                angle = particle.get('ring_angle', np.random.uniform(0, 2 * np.pi))
                particle['ring_angle'] = angle
                # Create perpendicular direction in camera's reference frame
                up = np.array([0, 1, 0])
                right = np.cross(cam_bh_dir, up)
                if np.linalg.norm(right) < 0.01:
                    right = np.array([1, 0, 0])
                right = right / np.linalg.norm(right)
                up = np.cross(right, cam_bh_dir)
                up = up / np.linalg.norm(up)
                image_direction = np.cos(angle) * right + np.sin(angle) * up
            
            # Calculate lensed position
            # Lensed images appear at the BLACK HOLE distance D_L (contouring the BH)
            # Keep ring tightly centered around BH, just slightly larger than visual radius
            image_radius_at_bh = theta_image * D_L
            
            # Maximum radius: slightly larger than before to reduce compression
            # But still tightly centered around the black hole
            max_ring_radius = visual_bh_radius * 1.3  # Just 30% larger than BH visual radius
            
            # Clamp the lensed image to stay near the BH edge
            if image_radius_at_bh > max_ring_radius:
                image_radius_at_bh = max_ring_radius
            
            lensed_pos = camera_pos + cam_bh_dir * D_L + image_direction * image_radius_at_bh
            
            # Calculate magnification
            if beta > 0.001:
                magnification = theta_image / beta
            else:
                magnification = 10.0  # Einstein ring - very bright
            
            # Mark particle as lensed and store lensed properties
            particle['is_lensed'] = True
            particle['lensed_position'] = lensed_pos
            
            # Apply magnification effects
            # Stretching (tangential magnification)
            particle['lensed_scale'] = 1.0 + min(2.0, magnification * 0.3)
            
            # Brightness magnification
            particle['magnification'] = min(3.0, magnification)


class PhysicsEngine:
    """Handles gravitational physics calculations"""
    def __init__(self, use_relativistic=False):
        self.use_relativistic = use_relativistic
        
    def orbital_elements_to_state(self, elements, central_mass):
        """Convert orbital elements to position and velocity"""
        a = elements.semi_major_axis
        e = elements.eccentricity
        i = elements.inclination
        Omega = elements.longitude_ascending
        omega = elements.argument_periapsis
        nu = elements.true_anomaly
        
        # Distance from focus
        r = a * (1 - e * e) / (1 + e * math.cos(nu))
        
        # Position in orbital plane
        x_orb = r * math.cos(nu)
        y_orb = r * math.sin(nu)
        
        # Velocity in orbital plane (vis-viva equation)
        v = math.sqrt(central_mass * (2/r - 1/a))
        v_x_orb = -v * math.sin(nu) / math.sqrt(1 - e*e)
        v_y_orb = v * (e + math.cos(nu)) / math.sqrt(1 - e*e)
        
        # Rotation matrices for 3D orientation
        # Rotate by argument of periapsis
        cos_omega = math.cos(omega)
        sin_omega = math.sin(omega)
        x_peri = x_orb * cos_omega - y_orb * sin_omega
        y_peri = x_orb * sin_omega + y_orb * cos_omega
        vx_peri = v_x_orb * cos_omega - v_y_orb * sin_omega
        vy_peri = v_x_orb * sin_omega + v_y_orb * cos_omega
        
        # Rotate by inclination
        cos_i = math.cos(i)
        sin_i = math.sin(i)
        x_incl = x_peri
        y_incl = y_peri * cos_i
        z_incl = y_peri * sin_i
        vx_incl = vx_peri
        vy_incl = vy_peri * cos_i
        vz_incl = vy_peri * sin_i
        
        # Rotate by longitude of ascending node
        cos_Omega = math.cos(Omega)
        sin_Omega = math.sin(Omega)
        x = x_incl * cos_Omega - y_incl * sin_Omega
        y = x_incl * sin_Omega + y_incl * cos_Omega
        z = z_incl
        vx = vx_incl * cos_Omega - vy_incl * sin_Omega
        vy = vx_incl * sin_Omega + vy_incl * cos_Omega
        vz = vz_incl
        
        return np.array([x, y, z]), np.array([vx, vy, vz])
        
    def calculate_acceleration(self, particle, central_mass, central_pos):
        """
        Calculate gravitational acceleration
        Using Newtonian approximation
        """
        r_vec = central_pos - particle.position
        r = np.linalg.norm(r_vec)
        
        if r < 0.1:  # Prevent singularity
            return np.array([0.0, 0.0, 0.0])
        
        # Newtonian gravity: a = GM/r^2
        a_magnitude = central_mass / (r * r)
        a_vec = a_magnitude * (r_vec / r)
        
        return a_vec
    
    def calculate_photon_deflection(self, photon, central_mass, central_pos):
        """
        ENHANCED gravitational lensing with DRAMATIC light bending
        Uses strong-field approximation for visible Einstein ring
        """
        r_vec = central_pos - photon.position
        r = np.linalg.norm(r_vec)
        
        schwarzschild_radius = 2 * central_mass
        photon_sphere = 3 * central_mass
        
        # Capture photons inside event horizon
        if r <= schwarzschild_radius * 1.02:
            photon.active = False
            return np.array([0.0, 0.0, 0.0])
        
        # MUCH STRONGER deflection for visible lensing
        # The closer to the black hole, the stronger the bending
        
        # Distance factor - increases dramatically near photon sphere
        if r < photon_sphere * 2:
            # Very strong deflection near photon sphere
            # This creates the Einstein ring effect
            deflection_strength = 20.0 * central_mass / (r * r)
        elif r < photon_sphere * 4:
            # Strong deflection
            deflection_strength = 10.0 * central_mass / (r * r)
        else:
            # Moderate deflection
            deflection_strength = 5.0 * central_mass / (r * r)
        
        # Direction towards black hole
        r_unit = r_vec / r
        
        # Apply deflection - bend light towards black hole
        deflection = deflection_strength * r_unit
        
        return deflection
    
    def calculate_particle_lensing(self, particle_pos, black_hole_pos, black_hole_mass, camera_pos):
        """
        Calculate gravitational lensing effect for a single particle
        Returns lensed position and lensing strength
        """
        # Distance from camera to particle
        D_S = np.linalg.norm(particle_pos - camera_pos)
        
        # Distance from camera to black hole
        D_L = np.linalg.norm(black_hole_pos - camera_pos)
        
        # Particle must be behind black hole for lensing
        if D_S <= D_L:
            return particle_pos, 0.0
        
        # Direction vectors
        cam_particle_dir = (particle_pos - camera_pos) / D_S
        cam_to_bh = black_hole_pos - camera_pos
        cam_bh_dir = cam_to_bh / D_L
        
        # Ray-sphere intersection test
        t_closest = np.dot(cam_to_bh, cam_particle_dir)
        if t_closest <= 0 or t_closest >= D_S:
            return particle_pos, 0.0
        
        closest_point_on_ray = camera_pos + cam_particle_dir * t_closest
        distance_to_ray = np.linalg.norm(black_hole_pos - closest_point_on_ray)
        
        # Lensing parameters
        schwarzschild_radius = 2 * black_hole_mass
        visual_bh_radius = schwarzschild_radius * 0.5
        lensing_start_radius = visual_bh_radius * 4.0
        lensing_full_radius = visual_bh_radius * 0.6
        
        # Calculate lensing strength with extended smooth falloff for ultra-smooth transitions
        if distance_to_ray < lensing_full_radius:
            t = 1.0
        elif distance_to_ray > lensing_start_radius:
            # Extended smooth falloff beyond lensing zone (2x longer range)
            extended_falloff_range = lensing_start_radius * 1.0  # Double the falloff distance
            t = max(0.0, 1.0 - (distance_to_ray - lensing_start_radius) / extended_falloff_range)
            t = t * t * t  # Cubic falloff for even smoother transition
        else:
            t = (lensing_start_radius - distance_to_ray) / (lensing_start_radius - lensing_full_radius)
            t = max(0.0, min(1.0, t))
        
        lensing_strength = t * t * (3.0 - 2.0 * t)  # Smoothstep
        
        # If lensing is too weak, return original position but keep small non-zero strength
        if lensing_strength < 0.001:
            return particle_pos, 0.0
        
        # Einstein radius calculation
        D_LS = D_S - D_L
        theta_E_squared = (4.0 * G_OVER_C2 * black_hole_mass) * D_LS / (D_L * D_S)
        theta_E = math.sqrt(max(0, theta_E_squared))
        
        # Source position (angular)
        beta = np.linalg.norm(particle_pos - black_hole_pos) / D_S
        
        # Solve lens equation for image position
        theta_image = (beta + math.sqrt(beta * beta + 4 * theta_E * theta_E)) / 2.0
        
        # Convert to physical position at black hole distance
        image_radius_at_bh = theta_image * D_L
        
        # Clamp to maximum ring size
        max_ring_radius = visual_bh_radius * 1.3
        if image_radius_at_bh > max_ring_radius:
            image_radius_at_bh = max_ring_radius
        
        # Calculate lensed position
        bh_to_particle = particle_pos - black_hole_pos
        tangent = bh_to_particle - np.dot(bh_to_particle, cam_bh_dir) * cam_bh_dir
        tangent_norm = np.linalg.norm(tangent)
        
        if tangent_norm > 0.001:
            image_direction = tangent / tangent_norm
        else:
            image_direction = np.array([1.0, 0.0, 0.0])
        
        lensed_pos = camera_pos + cam_bh_dir * D_L + image_direction * image_radius_at_bh
        
        return lensed_pos, lensing_strength
    
    def update_particles(self, particles, dt):
        """Update particles with simple Newtonian gravity"""
        if len(particles) < 2:
            return
            
        central = particles[0]  # First particle is the central body
        
        for particle in particles[1:]:
            if particle.is_central:
                continue
            
            # Calculate acceleration
            acc = self.calculate_acceleration(particle, central.mass, central.position)
            
            # Simple Verlet integration
            particle.position += particle.velocity * dt + 0.5 * acc * dt * dt
            particle.velocity += acc * dt
            
            # Update trail
            particle.update_trail()
    
    def update_photons(self, photons, central_mass, central_pos, dt):
        """Update photon trajectories with gravitational lensing"""
        speed_of_light = 1.0  # In our units
        
        for photon in photons:
            if not photon.active:
                continue
            
            # Calculate deflection
            deflection = self.calculate_photon_deflection(photon, central_mass, central_pos)
            
            # Update direction (bend the light)
            photon.direction += deflection * dt
            photon.direction = photon.direction / np.linalg.norm(photon.direction)
            
            # Move photon
            photon.position += photon.direction * speed_of_light * dt
            photon.update_trail()
            
            # Deactivate if too far
            if np.linalg.norm(photon.position) > 100:
                photon.active = False


class Renderer:
    """Handles all rendering with retro 90s aesthetic"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid_size = 100
        self.grid_spacing = 5
        
    def setup_perspective(self):
        """Setup 3D perspective"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.width / self.height, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        
    def draw_starfield(self, starfield):
        """Draw background stars"""
        glDisable(GL_DEPTH_TEST)  # Draw stars behind everything
        glPointSize(1.0)
        
        glBegin(GL_POINTS)
        for star in starfield.stars:
            glColor3f(*star['color'])
            glVertex3f(*star['position'])
        glEnd()
        
        # Draw some larger stars
        for star in starfield.stars[::10]:  # Every 10th star
            glPointSize(star['size'])
            glBegin(GL_POINTS)
            glColor3f(*star['color'])
            glVertex3f(*star['position'])
            glEnd()
        
        glEnable(GL_DEPTH_TEST)  # Re-enable depth test
        glPointSize(1.0)  # Reset point size
    
    def draw_curved_spacetime_grid(self, black_hole_pos, black_hole_mass):
        """Draw curved spacetime grid showing gravitational warping"""
        glColor3f(0.0, 0.5, 0.5)
        
        # Schwarzschild radius for warping calculation
        schwarzschild_radius = 2 * black_hole_mass
        warp_strength = schwarzschild_radius * 3.0  # Adjust for visual effect
        
        half_size = self.grid_size / 2
        grid_y = -20  # Base grid height
        
        # Draw lines parallel to X axis (running along Z direction)
        for i in range(-int(half_size), int(half_size) + 1, self.grid_spacing):
            glBegin(GL_LINE_STRIP)
            for z in range(-int(half_size), int(half_size) + 1, 2):
                x = float(i)
                z_pos = float(z)
                
                # Calculate distance from black hole (in XZ plane)
                dx = x - black_hole_pos[0]
                dz = z_pos - black_hole_pos[2]
                distance = math.sqrt(dx * dx + dz * dz)
                
                # Apply gravitational warping (depression in spacetime)
                if distance > 0.1:  # Avoid division by zero
                    # Warping falls off with distance
                    warp = -warp_strength / (1.0 + distance * 0.5)
                    y = grid_y + warp
                else:
                    y = grid_y - warp_strength * 2  # Maximum depression at center
                
                glVertex3f(x, y, z_pos)
            glEnd()
        
        # Draw lines parallel to Z axis (running along X direction)
        for z in range(-int(half_size), int(half_size) + 1, self.grid_spacing):
            glBegin(GL_LINE_STRIP)
            for i in range(-int(half_size), int(half_size) + 1, 2):
                x = float(i)
                z_pos = float(z)
                
                # Calculate distance from black hole (in XZ plane)
                dx = x - black_hole_pos[0]
                dz = z_pos - black_hole_pos[2]
                distance = math.sqrt(dx * dx + dz * dz)
                
                # Apply gravitational warping (depression in spacetime)
                if distance > 0.1:  # Avoid division by zero
                    warp = -warp_strength / (1.0 + distance * 0.5)
                    y = grid_y + warp
                else:
                    y = grid_y - warp_strength * 2  # Maximum depression at center
                
                glVertex3f(x, y, z_pos)
            glEnd()
    
    def draw_grid(self):
        """Draw retro grid floor (legacy method, kept for compatibility)"""
        glColor3f(0.0, 0.5, 0.5)
        glBegin(GL_LINES)
        
        half_size = self.grid_size / 2
        for i in range(-int(half_size), int(half_size) + 1, self.grid_spacing):
            # Lines parallel to X axis
            glVertex3f(i, -20, -half_size)
            glVertex3f(i, -20, half_size)
            # Lines parallel to Z axis
            glVertex3f(-half_size, -20, i)
            glVertex3f(half_size, -20, i)
        
        glEnd()
    
    def draw_solid_sphere(self, radius, slices=20, stacks=15):
        """Draw solid sphere (for black hole event horizon)"""
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = radius * math.sin(lat0)
            zr0 = radius * math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = radius * math.sin(lat1)
            zr1 = radius * math.cos(lat1)
            
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glVertex3f(x * zr0, z0, y * zr0)
                glVertex3f(x * zr1, z1, y * zr1)
            glEnd()
    
    def draw_wireframe_sphere(self, radius, slices=12, stacks=8):
        """Draw wireframe sphere for retro look"""
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = radius * math.sin(lat0)
            zr0 = radius * math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = radius * math.sin(lat1)
            zr1 = radius * math.cos(lat1)
            
            glBegin(GL_LINE_LOOP)
            for j in range(slices):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glVertex3f(x * zr0, z0, y * zr0)
            glEnd()
            
            glBegin(GL_LINE_LOOP)
            for j in range(slices):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glVertex3f(x * zr1, z1, y * zr1)
            glEnd()
    
    def draw_lensed_wireframe_sphere_world_space(self, radius, particle_pos, black_hole_pos, lensing_strength, slices=12, stacks=8):
        """Draw wireframe sphere with gravitational lensing distortion in world space (no matrix transforms)"""
        # DEBUG: Print distortion info once per frame
        if not hasattr(self, '_debug_frame_count'):
            self._debug_frame_count = 0
        self._debug_frame_count += 1
        
        debug_this_frame = False
        if self._debug_frame_count % 60 == 0:  # Print every 60 frames
            dist_particle_to_bh = np.linalg.norm(particle_pos - black_hole_pos)
            print(f"DEBUG DISTORTION: particle_pos={particle_pos}, bh_pos={black_hole_pos}, dist={dist_particle_to_bh:.2f}, lensing_strength={lensing_strength:.3f}")
            debug_this_frame = True
        
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = radius * math.sin(lat0)
            zr0 = radius * math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = radius * math.sin(lat1)
            zr1 = radius * math.cos(lat1)
            
            # Draw latitude rings with distortion IN WORLD SPACE
            glBegin(GL_LINE_LOOP)
            for j in range(slices):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                # Local vertex position (relative to particle center)
                local_vertex = np.array([x * zr0, z0, y * zr0])
                # World position of this vertex (undistorted)
                world_vertex = particle_pos + local_vertex
                
                # Calculate distance from this vertex to black hole
                to_bh = black_hole_pos - world_vertex
                dist_to_bh = np.linalg.norm(to_bh)
                
                if dist_to_bh > 0.1:
                    # Apply differential lensing - TANGENTIAL stretching (perpendicular to radial direction)
                    # This simulates how gravitational lensing stretches objects around the mass
                    direction_to_bh = to_bh / dist_to_bh
                    
                    # Calculate tangential direction (perpendicular to radial)
                    # Use cross product with a reference vector to get perpendicular direction
                    up_vector = np.array([0.0, 1.0, 0.0])
                    tangent1 = np.cross(direction_to_bh, up_vector)
                    tangent1_mag = np.linalg.norm(tangent1)
                    if tangent1_mag > 0.01:
                        tangent1 = tangent1 / tangent1_mag
                    else:
                        # If direction_to_bh is parallel to up, use different reference
                        tangent1 = np.cross(direction_to_bh, np.array([1.0, 0.0, 0.0]))
                        tangent1 = tangent1 / np.linalg.norm(tangent1)
                    
                    # Get second tangent perpendicular to both
                    tangent2 = np.cross(direction_to_bh, tangent1)
                    tangent2 = tangent2 / np.linalg.norm(tangent2)
                    
                    # Distortion strength increases closer to black hole
                    vertex_lensing = lensing_strength * (radius * 8.0) / (dist_to_bh * 0.2)
                    vertex_lensing = min(vertex_lensing, 3.0)
                    
                    # Apply TANGENTIAL distortion (stretching perpendicular to radial direction)
                    # Project local vertex onto tangent plane and amplify
                    tangent_component1 = np.dot(local_vertex, tangent1)
                    tangent_component2 = np.dot(local_vertex, tangent2)
                    
                    distortion = (tangent1 * tangent_component1 + tangent2 * tangent_component2) * vertex_lensing * 0.5
                    distorted_world_vertex = world_vertex + distortion
                    
                    if debug_this_frame and j == 0 and i == 0:
                        distortion_mag = np.linalg.norm(distortion)
                        print(f"  Vertex: dist_to_bh={dist_to_bh:.2f}, vertex_lensing={vertex_lensing:.3f}, distortion_mag={distortion_mag:.3f}, tangential stretch")
                    
                    # Draw in world space
                    glVertex3f(*distorted_world_vertex)
                else:
                    glVertex3f(*world_vertex)
            glEnd()
            
            # Second ring
            glBegin(GL_LINE_LOOP)
            for j in range(slices):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                local_vertex = np.array([x * zr1, z1, y * zr1])
                world_vertex = particle_pos + local_vertex
                
                to_bh = black_hole_pos - world_vertex
                dist_to_bh = np.linalg.norm(to_bh)
                
                if dist_to_bh > 0.1:
                    direction_to_bh = to_bh / dist_to_bh
                    
                    # Calculate tangential directions
                    up_vector = np.array([0.0, 1.0, 0.0])
                    tangent1 = np.cross(direction_to_bh, up_vector)
                    tangent1_mag = np.linalg.norm(tangent1)
                    if tangent1_mag > 0.01:
                        tangent1 = tangent1 / tangent1_mag
                    else:
                        tangent1 = np.cross(direction_to_bh, np.array([1.0, 0.0, 0.0]))
                        tangent1 = tangent1 / np.linalg.norm(tangent1)
                    
                    tangent2 = np.cross(direction_to_bh, tangent1)
                    tangent2 = tangent2 / np.linalg.norm(tangent2)
                    
                    vertex_lensing = lensing_strength * (radius * 8.0) / (dist_to_bh * 0.2)
                    vertex_lensing = min(vertex_lensing, 3.0)
                    
                    # Tangential distortion
                    tangent_component1 = np.dot(local_vertex, tangent1)
                    tangent_component2 = np.dot(local_vertex, tangent2)
                    distortion = (tangent1 * tangent_component1 + tangent2 * tangent_component2) * vertex_lensing * 0.5
                    distorted_world_vertex = world_vertex + distortion
                    glVertex3f(*distorted_world_vertex)
                else:
                    glVertex3f(*world_vertex)
            glEnd()
    
    def draw_particle(self, particle, lensed_pos=None, lensing_strength=0.0, black_hole_pos=None):
        """Draw a particle with its trail, optionally with gravitational lensing and shape distortion"""
        # Determine rendering position
        if lensed_pos is not None and lensing_strength > 0.0:
            # Blend between original and lensed position
            render_pos = particle.position * (1.0 - lensing_strength) + lensed_pos * lensing_strength
        else:
            render_pos = particle.position
        
        # Draw particle
        if particle.is_central:
            glPushMatrix()
            glTranslatef(*render_pos)
            
            # Draw BLACK HOLE as solid black sphere (event horizon)
            # Using realistic scaling: r_s = 2M, but scale for visibility
            schwarzschild_radius = 2 * particle.mass
            # Scale down for better visualization (realistic BH would be tiny)
            visual_radius = schwarzschild_radius * 0.5  # Half size for better proportions
            
            # Disable lighting and draw solid black sphere
            glDisable(GL_BLEND)
            glColor3f(0.0, 0.0, 0.0)  # Pure black
            self.draw_solid_sphere(visual_radius, slices=32, stacks=24)
            glEnable(GL_BLEND)
            
            # Draw subtle wireframe at actual Schwarzschild radius for reference
            glColor4f(0.3, 0.0, 0.0, 0.2)  # Very dark red, barely visible
            self.draw_wireframe_sphere(schwarzschild_radius, slices=24, stacks=18)
            
            glPopMatrix()
        else:
            # Always apply lensing (with smooth blending from 0 to full strength)
            if black_hole_pos is not None:
                # Magnification effect - brighter when lensed
                brightness_boost = 1.0 + lensing_strength * 0.5
                color = tuple(min(1.0, c * brightness_boost) for c in particle.color)
                glColor3f(*color)
                # Slightly larger when lensed
                size = 0.5 * (1.0 + lensing_strength * 0.3)
                # Draw with shape distortion at the LENSED position (render_pos)
                # This ensures the shape follows the lensed center smoothly
                # Use particle.position for distortion calculation (where it actually is)
                self.draw_lensed_wireframe_sphere_world_space(size, render_pos, black_hole_pos, lensing_strength, slices=8, stacks=6)
            else:
                # Fallback if no black hole position provided
                glPushMatrix()
                glTranslatef(*render_pos)
                glColor3f(*particle.color)
                self.draw_wireframe_sphere(0.5, slices=8, stacks=6)
                glPopMatrix()
        
        # Draw trail - apply same lensing offset to trail if particle is lensed
        if len(particle.trail) > 1:
            # Apply brightness boost to trail if lensed
            if lensing_strength > 0.0:
                brightness_boost = 1.0 + lensing_strength * 0.3
                r = min(1.0, particle.color[0] * brightness_boost)
                g = min(1.0, particle.color[1] * brightness_boost)
                b = min(1.0, particle.color[2] * brightness_boost)
                alpha = 0.5 + lensing_strength * 0.2
                glColor4f(r, g, b, alpha)
                
                # Calculate lensing offset to apply to trail
                lensing_offset = (lensed_pos - particle.position) * lensing_strength
            else:
                glColor4f(particle.color[0], particle.color[1], particle.color[2], 0.5)
                lensing_offset = np.array([0.0, 0.0, 0.0])
            
            glBegin(GL_LINE_STRIP)
            for pos in particle.trail:
                # Apply the same lensing offset to each trail position
                lensed_trail_pos = pos + lensing_offset
                glVertex3f(*lensed_trail_pos)
            glEnd()
    
    def draw_accretion_disc(self, disc):
        """Draw accretion disc - show lensed OR original position, never both"""
        # Use additive blending for maximum glow effect
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        
        # DEBUG: Count lensed vs non-lensed particles
        lensed_count = sum(1 for p in disc.particles if p.get('is_lensed', False))
        total_count = len(disc.particles)
        if lensed_count > 0:
            print(f"DEBUG: Rendering {lensed_count} lensed, {total_count - lensed_count} normal particles")
        
        # Draw particles - blend between original and lensed position based on lensing_strength
        for particle in disc.particles:
            is_lensed = particle.get('is_lensed', False)
            lensing_strength = particle.get('lensing_strength', 0.0)
            
            if is_lensed and lensing_strength > 0.0:
                # Blend between original and lensed position
                original_pos = particle['position']
                lensed_pos = particle['lensed_position']
                
                # Interpolate position based on lensing strength
                pos = original_pos * (1.0 - lensing_strength) + lensed_pos * lensing_strength
                
                scale = particle.get('lensed_scale', 1.0)
                magnification = particle.get('magnification', 1.0)
                intensity = particle.get('intensity', 1.0)
                
                # Brightness increases with magnification and lensing strength
                brightness = min(1.0, intensity * magnification * 0.3 * lensing_strength)
                
                # Point size scales with lensing strength
                point_size = 5.0 * (1.0 + (scale - 1.0) * lensing_strength)
                glPointSize(point_size)
                
                glBegin(GL_POINTS)
                # Color gets brighter with magnification, scaled by lensing strength
                base_brightness = 1.0 + brightness
                r = min(1.0, particle['color'][0] * base_brightness)
                g = min(1.0, particle['color'][1] * base_brightness)
                b = min(1.0, particle['color'][2] * base_brightness)
                glColor4f(r, g, b, 1.0)
                glVertex3f(*pos)
                glEnd()
            else:
                # Draw normal (non-lensed) particle
                pos = particle['position']
                intensity = particle.get('intensity', 1.0)
                
                point_size = 5.0
                glPointSize(point_size)
                
                glBegin(GL_POINTS)
                glColor4f(particle['color'][0], particle['color'][1], particle['color'][2], 1.0)
                glVertex3f(*pos)
                glEnd()
        
        # Second layer for extra brightness (ALL particles)
        for particle in disc.particles:
            is_lensed = particle.get('is_lensed', False)
            lensing_strength = particle.get('lensing_strength', 0.0)
            
            if is_lensed and lensing_strength > 0.0:
                magnification = particle.get('magnification', 1.0)
                if magnification > 1.5:
                    # Blend position for second layer too
                    original_pos = particle['position']
                    lensed_pos = particle['lensed_position']
                    pos = original_pos * (1.0 - lensing_strength) + lensed_pos * lensing_strength
                    
                    scale = particle.get('lensed_scale', 1.0)
                    point_size = 3.5 * (1.0 + (scale - 1.0) * lensing_strength)
                    glPointSize(point_size)
                    
                    glBegin(GL_POINTS)
                    # Alpha scales with lensing strength
                    alpha = min(1.0, lensing_strength)
                    glColor4f(1.0, 1.0, 1.0, alpha)
                    glVertex3f(*pos)
                    glEnd()
            else:
                # Normal particles also get second layer
                pos = particle['position']
                point_size = 3.5
                glPointSize(point_size)
                
                glBegin(GL_POINTS)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                glVertex3f(*pos)
                glEnd()
        
        # Third layer for glow (ALL particles)
        for particle in disc.particles:
            is_lensed = particle.get('is_lensed', False)
            lensing_strength = particle.get('lensing_strength', 0.0)
            
            if is_lensed and lensing_strength > 0.0:
                magnification = particle.get('magnification', 1.0)
                if magnification > 1.2:
                    # Blend position for third layer too
                    original_pos = particle['position']
                    lensed_pos = particle['lensed_position']
                    pos = original_pos * (1.0 - lensing_strength) + lensed_pos * lensing_strength
                    
                    scale = particle.get('lensed_scale', 1.0)
                    point_size = 2.0 * (1.0 + (scale * magnification * 0.5 - 1.0) * lensing_strength)
                    glPointSize(point_size)
                    
                    glBegin(GL_POINTS)
                    # Alpha scales with both magnification and lensing strength
                    alpha = min(0.9, 0.5 * magnification * lensing_strength)
                    glColor4f(1.0, 1.0, 1.0, alpha)
                    glVertex3f(*pos)
                    glEnd()
            else:
                # Normal particles also get third layer
                pos = particle['position']
                point_size = 2.0
                glPointSize(point_size)
                
                glBegin(GL_POINTS)
                glColor4f(1.0, 1.0, 1.0, 0.9)
                glVertex3f(*pos)
                glEnd()
        
        glPointSize(1.0)
        # Restore normal blending
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    def draw_photon(self, photon):
        """Draw photon trail"""
        if len(photon.trail) > 1:
            glColor4f(*photon.color, 0.8)
            glLineWidth(2.0)
            glBegin(GL_LINE_STRIP)
            for pos in photon.trail:
                glVertex3f(*pos)
            glEnd()
            glLineWidth(1.5)
    
    def draw_bounding_box(self, size=30):
        """Draw simulation bounding box"""
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        
        # Bottom square
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        
        glVertex3f(-size, -size, size)
        glVertex3f(-size, -size, -size)
        
        # Top square
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        
        glVertex3f(size, size, -size)
        glVertex3f(size, size, size)
        
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        
        glVertex3f(-size, size, size)
        glVertex3f(-size, size, -size)
        
        # Vertical lines
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        
        glVertex3f(size, -size, -size)
        glVertex3f(size, size, -size)
        
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        
        glVertex3f(-size, -size, size)
        glVertex3f(-size, size, size)
        
        glEnd()


class UI:
    """User interface for simulation controls"""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
    def draw_text(self, text, x, y, color=(0, 255, 0)):
        """Draw text on screen"""
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))
    
    def draw_small_text(self, text, x, y, color=(0, 255, 0)):
        """Draw small text on screen"""
        surface = self.small_font.render(text, True, color)
        self.screen.blit(surface, (x, y))
    
    def draw_panel(self, sim_state):
        """Draw control panel with time dilation info"""
        panel_height = 200
        panel_rect = pygame.Rect(0, 0, self.screen.get_width(), panel_height)
        
        # Semi-transparent background
        s = pygame.Surface((panel_rect.width, panel_rect.height))
        s.set_alpha(200)
        s.fill((0, 0, 20))
        self.screen.blit(s, (0, 0))
        
        # Title
        self.draw_text("BOB's Black Hole - Simplified Gravitational Simulator", 10, 10, (0, 255, 255))
        
        # Controls
        y_offset = 40
        self.draw_small_text("Controls:", 10, y_offset)
        y_offset += 20
        self.draw_small_text("  Mouse Drag: Look | WASD: Move | Q/E: Up/Down | SHIFT: Fast", 10, y_offset, (200, 200, 200))
        y_offset += 18
        self.draw_small_text("  R: Reset | 1/2/3: Presets | SPACE: Pause", 10, y_offset, (200, 200, 200))
        y_offset += 18
        self.draw_small_text("  Arrow Keys: Rotate | +/-: Time speed", 10, y_offset, (200, 200, 200))
        y_offset += 18
        self.draw_small_text("  Gravitational lensing: Always active on disc", 10, y_offset, (100, 255, 100))
        
        # Status
        status_x = 500
        self.draw_small_text(f"Status: {'PAUSED' if sim_state['paused'] else 'RUNNING'}",
                           status_x, 40, (255, 255, 0) if sim_state['paused'] else (0, 255, 0))
        self.draw_small_text(f"Particles: {sim_state['particle_count']}", status_x, 60)
        self.draw_small_text(f"Photons: {sim_state['photon_count']}", status_x, 80)
        self.draw_small_text(f"Central Mass: {sim_state['central_mass']:.1f}", status_x, 100)
        self.draw_small_text(f"Time Step: {sim_state['dt']:.3f}", status_x, 120)
        self.draw_small_text(f"Disc: {'ON' if sim_state['disc_visible'] else 'OFF'}", status_x, 140)

class ConfigMenu:
    """Startup configuration menu"""
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("BOB's Black Hole - Configuration")
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.clock = pygame.time.Clock()
        
        # Configuration options
        self.mass = 10.0
        self.num_orbiting = 5
        self.with_disc = True
        self.with_orbiting = True
        
        # UI state
        self.selected_option = 0
        self.options = ['mass', 'orbiting', 'disc', 'bodies', 'start']
        
    def draw_text(self, text, x, y, font, color=(0, 255, 0)):
        """Draw text centered at position"""
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(x, y))
        self.screen.blit(surface, rect)
    
    def draw_text_left(self, text, x, y, font, color=(0, 255, 0)):
        """Draw text left-aligned"""
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))
    
    def run(self):
        """Run configuration menu and return settings"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    
                    elif event.key == K_UP:
                        self.selected_option = (self.selected_option - 1) % len(self.options)
                    
                    elif event.key == K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(self.options)
                    
                    elif event.key == K_LEFT:
                        self.adjust_option(-1)
                    
                    elif event.key == K_RIGHT:
                        self.adjust_option(1)
                    
                    elif event.key == K_RETURN or event.key == K_SPACE:
                        if self.options[self.selected_option] == 'start':
                            return {
                                'mass': self.mass,
                                'num_orbiting': self.num_orbiting,
                                'with_disc': self.with_disc,
                                'with_orbiting': self.with_orbiting
                            }
                        elif self.options[self.selected_option] == 'disc':
                            self.with_disc = not self.with_disc
                        elif self.options[self.selected_option] == 'bodies':
                            self.with_orbiting = not self.with_orbiting
            
            self.render()
            self.clock.tick(30)
    
    def adjust_option(self, direction):
        """Adjust selected option value"""
        option = self.options[self.selected_option]
        
        if option == 'mass':
            self.mass = max(1.0, min(50.0, self.mass + direction * 2.0))
        elif option == 'orbiting':
            self.num_orbiting = max(0, min(15, self.num_orbiting + direction))
        elif option == 'disc':
            self.with_disc = not self.with_disc
        elif option == 'bodies':
            self.with_orbiting = not self.with_orbiting
    
    def render(self):
        """Render configuration menu"""
        self.screen.fill((0, 0, 10))
        
        # Title
        self.draw_text("BOB's Black Hole", self.width // 2, 60, self.font_large, (0, 255, 255))
        self.draw_text("Gravitational Simulator Configuration", self.width // 2, 110, self.font_small, (100, 200, 255))
        
        y_start = 180
        y_spacing = 70
        
        # Mass option
        y = y_start
        color = (255, 255, 0) if self.selected_option == 0 else (150, 150, 150)
        self.draw_text_left("Black Hole Mass:", 100, y, self.font_medium, color)
        self.draw_text(f"{self.mass:.1f}", 550, y + 15, self.font_medium, (0, 255, 0))
        if self.selected_option == 0:
            self.draw_text_left("← →  to adjust", 100, y + 35, self.font_small, (200, 200, 0))
        
        # Number of orbiting bodies
        y += y_spacing
        color = (255, 255, 0) if self.selected_option == 1 else (150, 150, 150)
        self.draw_text_left("Orbiting Bodies:", 100, y, self.font_medium, color)
        self.draw_text(f"{self.num_orbiting}", 550, y + 15, self.font_medium, (0, 255, 0))
        if self.selected_option == 1:
            self.draw_text_left("← →  to adjust", 100, y + 35, self.font_small, (200, 200, 0))
        
        # Accretion disc toggle
        y += y_spacing
        color = (255, 255, 0) if self.selected_option == 2 else (150, 150, 150)
        self.draw_text_left("Accretion Disc:", 100, y, self.font_medium, color)
        disc_text = "ON" if self.with_disc else "OFF"
        disc_color = (0, 255, 0) if self.with_disc else (255, 100, 100)
        self.draw_text(disc_text, 550, y + 15, self.font_medium, disc_color)
        if self.selected_option == 2:
            self.draw_text_left("SPACE to toggle", 100, y + 35, self.font_small, (200, 200, 0))
        
        # Orbiting bodies toggle
        y += y_spacing
        color = (255, 255, 0) if self.selected_option == 3 else (150, 150, 150)
        self.draw_text_left("Enable Orbiting Bodies:", 100, y, self.font_medium, color)
        bodies_text = "ON" if self.with_orbiting else "OFF"
        bodies_color = (0, 255, 0) if self.with_orbiting else (255, 100, 100)
        self.draw_text(bodies_text, 550, y + 15, self.font_medium, bodies_color)
        if self.selected_option == 3:
            self.draw_text_left("SPACE to toggle", 100, y + 35, self.font_small, (200, 200, 0))
        
        # Start button
        y += y_spacing + 20
        color = (0, 255, 0) if self.selected_option == 4 else (100, 100, 100)
        button_rect = pygame.Rect(self.width // 2 - 100, y, 200, 50)
        pygame.draw.rect(self.screen, color, button_rect, 3)
        self.draw_text("START SIMULATION", self.width // 2, y + 25, self.font_medium, color)
        
        # Instructions
        self.draw_text("↑↓ Navigate  |  ←→ Adjust  |  SPACE/ENTER Start  |  ESC Quit", 
                      self.width // 2, self.height - 30, self.font_small, (100, 100, 100))
        
        pygame.display.flip()



class Simulation:
    """Main simulation class"""
    def __init__(self, width=1200, height=800, config=None):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("BOB's Black Hole - Simplified Gravitational Simulator")
        
        # Setup OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.5)
        
        # Initialize components
        self.camera = Camera()
        self.renderer = Renderer(width, height)
        self.physics = PhysicsEngine()
        self.ui = UI(self.screen)
        self.starfield = Starfield(num_stars=1500, radius=250)  # Create starfield
        
        # Simulation state
        self.particles = []
        self.photons = []
        self.accretion_disc = None
        self.disc_visible = True
        self.paused = False
        self.dt = 0.1
        self.clock = pygame.time.Clock()
        
        # Initialize simulation with config or defaults
        if config:
            self.reset_simulation(
                central_mass=config['mass'],
                num_orbiting=config['num_orbiting'],
                with_disc=config['with_disc'],
                with_orbiting=config['with_orbiting']
            )
        else:
            self.reset_simulation()
        
    def reset_simulation(self, central_mass=10.0, num_orbiting=5, with_disc=True, with_orbiting=True):
        """Reset simulation with new parameters"""
        self.particles = []
        self.photons = []
        
        # Create central body (black hole)
        central = Particle(
            position=[0, 0, 0],
            velocity=[0, 0, 0],
            mass=central_mass,
            color=(1.0, 0.3, 0.0),  # Orange/red for black hole
            is_central=True
        )
        self.particles.append(central)
        
        # Create accretion disc if requested
        self.accretion_disc = None
        if with_disc:
            schwarzschild_radius = 2 * central_mass
            # Accretion disc VERY close to black hole for dramatic lensing effect
            self.accretion_disc = AccretionDisc(
                inner_radius=schwarzschild_radius * 1.2,   # Very close to event horizon!
                outer_radius=schwarzschild_radius * 4.0,   # Compact, tight disc
                num_particles=5000  # Very dense for bright lensing
            )
            self.disc_visible = True
        
        # Create orbiting bodies with elliptical orbits and inclinations (if requested)
        if with_orbiting:
            schwarzschild_radius = 2 * central_mass
            
            for i in range(num_orbiting):
                # Orbital parameters - ensure periapsis is outside event horizon
                # Periapsis distance = a(1-e), must be > schwarzschild_radius
                semi_major = 15 + (i * 4)
                
                # Limit eccentricity to ensure periapsis stays outside event horizon
                # periapsis = a(1-e) > r_s  =>  e < 1 - r_s/a
                max_eccentricity = min(0.6, 1.0 - (schwarzschild_radius * 1.5) / semi_major)
                eccentricity = np.random.uniform(0.1, max(0.1, max_eccentricity))
                
                inclination = np.random.uniform(-math.pi/6, math.pi/6)  # ±30 degrees
                long_asc = np.random.uniform(0, 2 * math.pi)
                arg_peri = np.random.uniform(0, 2 * math.pi)
                true_anom = np.random.uniform(0, 2 * math.pi)
                
                elements = OrbitalElements(
                    semi_major_axis=semi_major,
                    eccentricity=eccentricity,
                    inclination=inclination,
                    longitude_ascending=long_asc,
                    argument_periapsis=arg_peri,
                    true_anomaly=true_anom
                )
                
                # Convert to position and velocity
                position, velocity = self.physics.orbital_elements_to_state(elements, central_mass)
                
                # Verify position is outside event horizon
                distance_from_bh = np.linalg.norm(position)
                if distance_from_bh <= schwarzschild_radius:
                    # Skip this particle if it starts inside event horizon
                    print(f"Warning: Skipping particle {i} - starts inside event horizon")
                    continue
                
                # Random color for each particle
                color = (
                    np.random.uniform(0.5, 1.0),
                    np.random.uniform(0.5, 1.0),
                    np.random.uniform(0.5, 1.0)
                )
                
                particle = Particle(position, velocity, 0.1, color, orbital_elements=elements)
                self.particles.append(particle)
    
    def launch_photons(self, num_photons=50):
        """Launch photons to demonstrate Einstein ring gravitational lensing"""
        central_mass = self.particles[0].mass
        schwarzschild_radius = 2 * central_mass
        photon_sphere = 3 * central_mass
        
        # Launch photons in multiple rings at different impact parameters
        # This creates visible Einstein ring effects
        
        for ring in range(3):  # Multiple rings
            ring_distance = 30 + ring * 10
            photons_in_ring = num_photons // 3
            
            for i in range(photons_in_ring):
                angle = (2 * math.pi * i) / photons_in_ring
                
                # Start position in a ring
                start_pos = np.array([
                    ring_distance * math.cos(angle),
                    0,  # Keep in plane for better ring visibility
                    ring_distance * math.sin(angle)
                ])
                
                # Direction: aim slightly off-center for grazing trajectories
                # This creates the Einstein ring effect
                target_offset = np.array([
                    np.random.uniform(-photon_sphere, photon_sphere),
                    np.random.uniform(-2, 2),
                    np.random.uniform(-photon_sphere, photon_sphere)
                ])
                
                direction = target_offset - start_pos
                
                # Color varies by ring
                if ring == 0:
                    color = (1.0, 1.0, 0.3)  # Yellow
                elif ring == 1:
                    color = (0.3, 1.0, 1.0)  # Cyan
                else:
                    color = (1.0, 0.5, 1.0)  # Magenta
                
                photon = Photon(start_pos, direction, color=color)
                self.photons.append(photon)
        
        # Add some photons passing very close for dramatic bending
        for i in range(10):
            angle = (2 * math.pi * i) / 10
            distance = 25
            
            start_pos = np.array([
                distance * math.cos(angle),
                np.random.uniform(-1, 1),
                distance * math.sin(angle)
            ])
            
            # Aim to graze the photon sphere
            direction = np.array([
                -start_pos[0] + np.random.uniform(-photon_sphere*0.5, photon_sphere*0.5),
                -start_pos[1],
                -start_pos[2] + np.random.uniform(-photon_sphere*0.5, photon_sphere*0.5)
            ])
            
            photon = Photon(start_pos, direction, color=(1.0, 0.8, 0.0))
            self.photons.append(photon)
    
    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return False
                elif event.key == K_SPACE:
                    self.paused = not self.paused
                elif event.key == K_r:
                    self.reset_simulation()
                elif event.key == K_1:
                    self.reset_simulation(central_mass=5.0, num_orbiting=3)
                elif event.key == K_2:
                    self.reset_simulation(central_mass=10.0, num_orbiting=5)
                elif event.key == K_3:
                    self.reset_simulation(central_mass=20.0, num_orbiting=8)
                elif event.key == K_EQUALS or event.key == K_PLUS:
                    self.dt = min(0.5, self.dt * 1.2)
                elif event.key == K_MINUS:
                    self.dt = max(0.01, self.dt / 1.2)
            
            elif event.type == MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    self.camera.handle_mouse_motion(event.rel[0], event.rel[1],
                                                    pygame.mouse.get_pressed())
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.camera.handle_mouse_wheel(1)
                elif event.button == 5:  # Scroll down
                    self.camera.handle_mouse_wheel(-1)
        
        # Handle continuous keyboard input for camera movement
        keys = pygame.key.get_pressed()
        self.camera.handle_keyboard(keys)
        
        return True
    
    def update(self):
        """Update simulation"""
        if not self.paused:
            # Update particles with simple physics
            self.physics.update_particles(self.particles, self.dt)
            
            # Check for event horizon collisions and remove particles
            if self.particles:
                black_hole = self.particles[0]
                schwarzschild_radius = 2 * black_hole.mass
                
                # Filter out particles that have fallen into the event horizon
                particles_to_keep = [black_hole]  # Always keep the black hole
                
                for particle in self.particles[1:]:
                    distance_from_bh = np.linalg.norm(particle.position - black_hole.position)
                    
                    if distance_from_bh <= schwarzschild_radius:
                        # Particle has crossed event horizon - remove it
                        print(f"Particle absorbed by black hole at distance {distance_from_bh:.2f} (r_s = {schwarzschild_radius:.2f})")
                    else:
                        # Particle is safe - keep it
                        particles_to_keep.append(particle)
                
                # Update particle list
                self.particles = particles_to_keep
            
            # Get camera position for lensing
            observer_position = self.camera.get_position()
            
            # Update accretion disc with gravitational lensing
            if self.accretion_disc:
                central_mass = self.particles[0].mass
                central_pos = self.particles[0].position
                camera_pos = self.camera.get_position()
                
                # Update orbital motion (disc follows black hole)
                self.accretion_disc.update(central_mass, self.dt, central_pos)
                
                # Apply gravitational lensing effect
                self.accretion_disc.apply_gravitational_lensing(central_pos, central_mass, camera_pos)
            
            # Update photons
            if self.photons:
                central_mass = self.particles[0].mass
                central_pos = self.particles[0].position
                self.physics.update_photons(self.photons, central_mass, central_pos, self.dt)
                
                # Remove inactive photons
                self.photons = [p for p in self.photons if p.active]
    
    def render(self):
        """Render the scene"""
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.0, 0.0, 0.02, 1.0)  # Very dark background for stars
        
        # Setup 3D view
        self.renderer.setup_perspective()
        self.camera.apply()
        
        # Draw starfield first (background)
        self.renderer.draw_starfield(self.starfield)
        
        # Draw 3D elements with curved spacetime grid
        if self.particles:
            black_hole_pos = self.particles[0].position
            black_hole_mass = self.particles[0].mass
            self.renderer.draw_curved_spacetime_grid(black_hole_pos, black_hole_mass)
        else:
            self.renderer.draw_grid()  # Fallback to flat grid
        
        self.renderer.draw_bounding_box()
        
        # Draw accretion disc
        if self.accretion_disc and self.disc_visible:
            self.renderer.draw_accretion_disc(self.accretion_disc)
        
        # Draw particles with gravitational lensing
        if self.particles:
            black_hole = self.particles[0]
            camera_pos = self.camera.get_position()
            
            for particle in self.particles:
                if particle.is_central:
                    # Draw black hole normally (no lensing on itself)
                    self.renderer.draw_particle(particle)
                else:
                    # Calculate lensing for orbiting particles
                    lensed_pos, lensing_strength = self.physics.calculate_particle_lensing(
                        particle.position,
                        black_hole.position,
                        black_hole.mass,
                        camera_pos
                    )
                    # Draw with lensing effect and shape distortion
                    self.renderer.draw_particle(particle, lensed_pos, lensing_strength, black_hole.position)
        else:
            # No particles, shouldn't happen but handle gracefully
            for particle in self.particles:
                self.renderer.draw_particle(particle)
        
        # Draw photons
        for photon in self.photons:
            self.renderer.draw_photon(photon)
        
        # Switch to 2D for UI
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        
        # Draw UI - simplified without time dilation
        sim_state = {
            'paused': self.paused,
            'particle_count': len(self.particles),
            'photon_count': len(self.photons),
            'central_mass': self.particles[0].mass if self.particles else 0,
            'dt': self.dt,
            'disc_visible': self.disc_visible
        }
        self.ui.draw_panel(sim_state)
        
        glEnable(GL_DEPTH_TEST)
        
        # Restore 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        pygame.display.flip()
    
    def run(self):
        """Main simulation loop"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point"""
    print("Starting Simulator...")
    
    # Show configuration menu
    config_menu = ConfigMenu()
    config = config_menu.run()
    
    print("\nSimulation Configuration:")
    print(f"  Black Hole Mass: {config['mass']}")
    print(f"  Orbiting Bodies: {config['num_orbiting']}")
    print(f"  Accretion Disc: {'Enabled' if config['with_disc'] else 'Disabled'}")
    print(f"  Orbiting Bodies: {'Enabled' if config['with_orbiting'] else 'Disabled'}")
    print("\nControls:")
    print("  - Mouse drag: Look around")
    print("  - WASD: Move camera (SHIFT for fast movement)")
    print("  - Q/E: Move up/down")
    print("  - Arrow keys: Rotate view")
    print("  - SPACE: Pause/resume")
    print("  - R: Reset simulation")
    print("  - 1/2/3: Different presets")
    print("  - +/-: Adjust time speed")
    print("  - ESC: Quit")
    print("\nGravitational lensing is automatically applied to the accretion disc!")
    
    # Start simulation with configuration
    sim = Simulation(config=config)
    sim.run()


if __name__ == "__main__":
    main()

# Made with Bob's help
