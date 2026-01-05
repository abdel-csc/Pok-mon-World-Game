import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk, ImageDraw
import requests
import random
import json
import os
from io import BytesIO
from datetime import datetime, timedelta

# Configuration
POKEDEX_FILE = "caught_pokemon.json"
PROFILE_FILE = "player_profile.json"
PLAYER_SPRITE_FILE = "player_sprite.png"
SHINY_CHANCE = 1/100
ENCOUNTER_CHANCE = 0.15  # 15% chance per step
FLEE_CHANCE_POKEBALL = 0.20  # 20% chance to flee when pokeball fails

# Legendary Pokémon IDs (Gen 1-8)
LEGENDARY_IDS = {
    144, 145, 146, 150, 151,  # Gen 1
    243, 244, 245, 249, 250, 251,  # Gen 2
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386,  # Gen 3
    480, 481, 482, 483, 484, 487, 488, 489, 490, 491, 492, 493,  # Gen 4
    494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649,  # Gen 5
    716, 717, 718, 719, 720, 721,  # Gen 6
    772, 773, 785, 786, 787, 788, 789, 790, 791, 792, 800, 801, 802, 807, 808, 809,  # Gen 7
    888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898  # Gen 8
}


class PixelArtCreator:
    """Popup window for creating pixel art character"""

    def __init__(self, parent, callback):
        self.callback = callback
        self.window = tk.Toplevel(parent)
        self.window.title("Create Your Character")
        self.window.geometry("600x700")

        self.grid_size = 16
        self.pixel_size = 20
        self.current_color = "#0000FF"

        self.grid = [["white" for _ in range(self.grid_size)]
                     for _ in range(self.grid_size)]

        # Title
        tk.Label(self.window, text="Create Your Pixel Art Character",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # Canvas
        canvas_size = self.grid_size * self.pixel_size
        self.canvas = tk.Canvas(self.window, width=canvas_size,
                                height=canvas_size, bg="white",
                                highlightthickness=2, highlightbackground="black")
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.paint_pixel)
        self.canvas.bind("<B1-Motion>", self.paint_pixel)

        # Color palette (common colors)
        palette_frame = tk.Frame(self.window)
        palette_frame.pack(pady=10)

        tk.Label(palette_frame, text="Quick Colors:",
                 font=("Arial", 12)).pack()

        colors_frame = tk.Frame(palette_frame)
        colors_frame.pack()

        common_colors = [
            ("Skin", "#FFD1A3"), ("Hair", "#8B4513"), ("Black", "#000000"),
            ("White", "#FFFFFF"), ("Red", "#FF0000"), ("Blue", "#0000FF"),
            ("Green", "#00FF00"), ("Yellow", "#FFFF00"), ("Purple", "#800080"),
            ("Orange", "#FFA500"), ("Pink", "#FFC0CB"), ("Gray", "#808080")
        ]

        for i, (name, color) in enumerate(common_colors):
            btn = tk.Button(colors_frame, bg=color, width=3, height=1,
                            command=lambda c=color: self.set_color(c))
            btn.grid(row=i//6, column=i % 6, padx=2, pady=2)

        # Custom color picker
        tk.Button(self.window, text="🎨 Custom Color",
                  command=self.choose_custom_color).pack(pady=5)

        # Current color indicator
        self.color_label = tk.Label(self.window, text="Current Color",
                                    bg=self.current_color, width=20, height=2)
        self.color_label.pack(pady=5)

        # Action buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Clear", command=self.clear,
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save & Use", command=self.save,
                  bg="green", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.window.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

    def paint_pixel(self, event):
        x = event.x // self.pixel_size
        y = event.y // self.pixel_size

        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            self.grid[y][x] = self.current_color
            self.draw_pixel(x, y, self.current_color)

    def draw_pixel(self, x, y, color):
        x1 = x * self.pixel_size
        y1 = y * self.pixel_size
        x2 = x1 + self.pixel_size
        y2 = y1 + self.pixel_size
        self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=color, outline="gray")

    def set_color(self, color):
        self.current_color = color
        self.color_label.config(bg=color)

    def choose_custom_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor()[1]
        if color:
            self.set_color(color)

    def clear(self):
        self.canvas.delete("all")
        self.grid = [["white" for _ in range(self.grid_size)]
                     for _ in range(self.grid_size)]

    def save(self):
        # Create image from grid
        img = Image.new("RGBA", (self.grid_size, self.grid_size))
        pixels = img.load()

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                color = self.grid[y][x]
                if color == "white":
                    pixels[x, y] = (255, 255, 255, 0)  # Transparent
                else:
                    # Convert hex to RGB
                    color = color.lstrip('#')
                    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                    pixels[x, y] = rgb + (255,)

        # Save and callback
        img.save(PLAYER_SPRITE_FILE, "PNG")
        self.callback()
        self.window.destroy()
        messagebox.showinfo("Success", "Character created!")


class PokemonCatchingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon Catching Game")
        self.root.geometry("800x900")

        # Load or create profile
        self.profile = self.load_profile()
        if not self.profile:
            self.create_profile()

        # Game state
        self.current_pokemon = None
        self.pokemon_health = 100
        self.max_health = 100
        self.bait_used = 0
        self.caught_pokemon = self.load_pokedex()
        self.in_battle = False
        self.steps = 0
        self.session_start = datetime.now()
        self.player_x = 200
        self.player_y = 200

        # Load player sprite
        self.player_sprite = self.load_player_sprite()

        # UI Elements
        self.setup_ui()

        # Start in exploration mode
        self.exploration_mode()

    def load_profile(self):
        """Load player profile"""
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, 'r') as f:
                profile = json.load(f)
                profile['created_at'] = datetime.fromisoformat(
                    profile['created_at'])
                profile['last_played'] = datetime.fromisoformat(
                    profile['last_played'])
                return profile
        return None

    def save_profile(self):
        """Save player profile"""
        self.profile['last_played'] = datetime.now()
        profile_copy = self.profile.copy()
        profile_copy['created_at'] = profile_copy['created_at'].isoformat()
        profile_copy['last_played'] = profile_copy['last_played'].isoformat()

        with open(PROFILE_FILE, 'w') as f:
            json.dump(profile_copy, f, indent=2)

    def create_profile(self):
        """Create new player profile"""
        name = simpledialog.askstring(
            "New Profile", "Enter your trainer name:")
        if not name:
            name = "Trainer"

        self.profile = {
            'name': name,
            'created_at': datetime.now(),
            'last_played': datetime.now(),
            'total_steps': 0,
            'total_encounters': 0,
            'total_catches': 0,
            'total_playtime': 0
        }
        self.save_profile()

        # Ask about sprite
        response = messagebox.askquestion("Player Sprite",
                                          "Would you like to create your character?\n\n"
                                          "Yes - Create pixel art character\n"
                                          "No - Upload an image instead")

        if response == 'yes':
            self.create_pixel_character()
        else:
            if messagebox.askyesno("Upload Sprite", "Upload an image for your character?"):
                self.upload_player_sprite()

    def create_pixel_character(self):
        """Open pixel art creator"""
        PixelArtCreator(self.root, self.reload_player_sprite)

    def reload_player_sprite(self):
        """Reload player sprite after creation"""
        self.player_sprite = self.load_player_sprite()
        if hasattr(self, 'player_sprite_label'):
            self.player_sprite_label.config(image=self.player_sprite)

    def load_player_sprite(self):
        """Load player sprite or use default"""
        if os.path.exists(PLAYER_SPRITE_FILE):
            try:
                img = Image.open(PLAYER_SPRITE_FILE)
                img = img.resize((64, 64), Image.NEAREST)
                return ImageTk.PhotoImage(img)
            except:
                pass

        # Create default sprite (simple circle)
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill='blue', outline='darkblue', width=3)
        return ImageTk.PhotoImage(img)

    def upload_player_sprite(self):
        """Upload custom player sprite"""
        filename = filedialog.askopenfilename(
            title="Select your player sprite",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )

        if filename:
            try:
                img = Image.open(filename)
                img = img.resize((64, 64), Image.NEAREST)
                img.save(PLAYER_SPRITE_FILE, "PNG")
                self.player_sprite = ImageTk.PhotoImage(img)
                messagebox.showinfo("Success", "Player sprite uploaded!")
                if hasattr(self, 'player_sprite_label'):
                    self.player_sprite_label.config(image=self.player_sprite)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")

    def setup_ui(self):
        """Create the game interface"""
        # Title with player name
        self.title_label = tk.Label(self.root,
                                    text=f"Trainer {self.profile['name']}'s Adventure",
                                    font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        # Profile stats
        self.profile_label = tk.Label(self.root, text="", font=("Arial", 11))
        self.profile_label.pack()
        self.update_profile_display()

        # Stats frame
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(pady=5)

        self.stats_label = tk.Label(stats_frame,
                                    text=f"Pokédex: {len(self.caught_pokemon)} | Steps: 0",
                                    font=("Arial", 14, "bold"))
        self.stats_label.pack()

        # Main display area
        self.main_frame = tk.Frame(
            self.root, width=600, height=500, bg="lightblue")
        self.main_frame.pack(pady=20)
        self.main_frame.pack_propagate(False)

        # This will hold either exploration or battle content
        self.content_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        # Message log
        self.message_label = tk.Label(self.root, text="Press WASD or Arrow keys to walk!",
                                      font=("Arial", 12, "italic"),
                                      fg="blue", wraplength=700)
        self.message_label.pack(pady=10)

        # Bottom buttons (always visible)
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="📖 Pokédex",
                  font=("Arial", 11),
                  command=self.show_pokedex,
                  width=12).pack(side=tk.LEFT, padx=3)

        tk.Button(bottom_frame, text="👤 Profile",
                  font=("Arial", 11),
                  command=self.show_profile,
                  width=12).pack(side=tk.LEFT, padx=3)

        tk.Button(bottom_frame, text="🎨 Create Sprite",
                  font=("Arial", 11),
                  command=self.create_pixel_character,
                  width=12).pack(side=tk.LEFT, padx=3)

        tk.Button(bottom_frame, text="📤 Upload Sprite",
                  font=("Arial", 11),
                  command=self.upload_player_sprite,
                  width=12).pack(side=tk.LEFT, padx=3)

        # Bind movement keys
        self.root.bind('<KeyPress>', self.handle_keypress)

    def update_profile_display(self):
        """Update profile info display"""
        playtime = timedelta(seconds=self.profile['total_playtime'])
        hours = int(playtime.total_seconds() // 3600)
        minutes = int((playtime.total_seconds() % 3600) // 60)

        self.profile_label.config(
            text=f"Playtime: {hours}h {minutes}m | Encounters: {self.profile['total_encounters']} | Catches: {self.profile['total_catches']}"
        )

    def handle_keypress(self, event):
        """Handle keyboard input for movement"""
        if self.in_battle:
            return

        # WASD or Arrow keys
        move_distance = 20
        if event.keysym in ['w', 'W', 'Up']:
            self.player_y = max(32, self.player_y - move_distance)
            self.take_step()
        elif event.keysym in ['s', 'S', 'Down']:
            self.player_y = min(468, self.player_y + move_distance)
            self.take_step()
        elif event.keysym in ['a', 'A', 'Left']:
            self.player_x = max(32, self.player_x - move_distance)
            self.take_step()
        elif event.keysym in ['d', 'D', 'Right']:
            self.player_x = min(568, self.player_x + move_distance)
            self.take_step()

    def take_step(self):
        """Player takes a step, chance to encounter Pokémon"""
        self.steps += 1
        self.profile['total_steps'] += 1
        self.update_stats()

        # Update player position on canvas
        if hasattr(self, 'exploration_canvas'):
            self.exploration_canvas.coords(self.player_sprite_id,
                                           self.player_x, self.player_y)

        # Check for encounter
        if random.random() < ENCOUNTER_CHANCE:
            self.encounter_pokemon()
        else:
            self.show_message(f"Step {self.steps}... Keep exploring!")

    def exploration_mode(self):
        """Show exploration UI with walking player"""
        self.in_battle = False

        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.content_frame.config(bg="lightgreen")

        # Create canvas for the overworld
        self.exploration_canvas = tk.Canvas(self.content_frame,
                                            width=600, height=500,
                                            bg="#90EE90")
        self.exploration_canvas.pack(fill=tk.BOTH, expand=True)

        # Draw grass pattern
        for i in range(0, 600, 40):
            for j in range(0, 500, 40):
                shade = random.choice(["#90EE90", "#7CCD7C", "#A8E6A3"])
                self.exploration_canvas.create_rectangle(i, j, i+40, j+40,
                                                         fill=shade, outline="")

        # Add some trees/bushes
        for _ in range(15):
            x = random.randint(50, 550)
            y = random.randint(50, 450)
            size = random.randint(20, 40)
            self.exploration_canvas.create_oval(x-size, y-size, x+size, y+size,
                                                fill="darkgreen", outline="")

        # Instructions
        self.exploration_canvas.create_text(300, 30,
                                            text="🌳 Use WASD or Arrows to explore! 🌳",
                                            font=("Arial", 16, "bold"),
                                            fill="white")

        # Draw player sprite
        self.player_sprite_id = self.exploration_canvas.create_image(
            self.player_x, self.player_y,
            image=self.player_sprite
        )

        self.show_message("Keep walking to find wild Pokémon!")

    def encounter_pokemon(self):
        """Trigger a Pokémon encounter"""
        self.in_battle = True
        self.profile['total_encounters'] += 1
        self.pokemon_health = self.max_health
        self.bait_used = 0

        pokemon_id = random.randint(1, 898)
        is_shiny = random.random() < SHINY_CHANCE
        is_legendary = pokemon_id in LEGENDARY_IDS

        try:
            response = requests.get(
                f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
            data = response.json()

            self.current_pokemon = {
                'id': pokemon_id,
                'name': data['name'].title(),
                'is_shiny': is_shiny,
                'is_legendary': is_legendary,
                'sprite_url': data['sprites']['versions']['generation-v']['black-white']['animated']['front_default'] if not is_shiny
                else data['sprites']['versions']['generation-v']['black-white']['animated']['front_shiny'],
                'base_catch_rate': self.calculate_base_catch_rate(data, is_legendary)
            }

            if not self.current_pokemon['sprite_url']:
                self.current_pokemon['sprite_url'] = data['sprites']['front_default'] if not is_shiny else data['sprites']['front_shiny']

            self.show_battle_ui()
            self.show_message(
                f"⚔️ A wild {self.current_pokemon['name']} appeared!")

        except Exception as e:
            print(f"Error spawning Pokémon: {e}")
            self.exploration_mode()

    def show_battle_ui(self):
        """Show battle UI with legendary background"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Different background for legendary
        if self.current_pokemon['is_legendary']:
            bg_color = "#2D1B4E"  # Dark purple for legendary
        else:
            bg_color = "#FFFACD"  # Light yellow for normal

        self.content_frame.config(bg=bg_color)

        # Top section - Pokemon info
        top_frame = tk.Frame(self.content_frame, bg=bg_color)
        top_frame.pack(pady=10)

        self.pokemon_label = tk.Label(top_frame,
                                      text=f"{self.current_pokemon['name']}",
                                      font=("Arial", 20, "bold"),
                                      bg=bg_color,
                                      fg="white" if self.current_pokemon['is_legendary'] else "black")
        self.pokemon_label.pack()

        # Legendary/Shiny indicators
        indicators_frame = tk.Frame(top_frame, bg=bg_color)
        indicators_frame.pack()

        self.legendary_label = tk.Label(indicators_frame, text="",
                                        font=("Arial", 12, "bold"),
                                        fg="gold", bg=bg_color)
        self.legendary_label.pack(side=tk.LEFT, padx=5)

        if self.current_pokemon['is_legendary']:
            self.legendary_label.config(text="⚡ LEGENDARY ⚡")

        self.shiny_label = tk.Label(indicators_frame, text="",
                                    font=("Arial", 12, "bold"),
                                    fg="cyan", bg=bg_color)
        self.shiny_label.pack(side=tk.LEFT, padx=5)

        if self.current_pokemon['is_shiny']:
            self.shiny_label.config(text="✨ SHINY ✨")

        # Add sparkles for legendary background
        if self.current_pokemon['is_legendary']:
            sparkle_canvas = tk.Canvas(self.content_frame, width=600, height=50,
                                       bg=bg_color, highlightthickness=0)
            sparkle_canvas.pack()

            for _ in range(20):
                x = random.randint(50, 550)
                y = random.randint(5, 45)
                size = random.randint(2, 5)
                color = random.choice(["white", "yellow", "gold"])
                sparkle_canvas.create_oval(
                    x-size, y-size, x+size, y+size, fill=color, outline="")

        # Sprite
        sprite_frame = tk.Frame(self.content_frame, bg=bg_color)
        sprite_frame.pack(pady=10)

        self.sprite_label = tk.Label(sprite_frame, bg=bg_color)
        self.sprite_label.pack()

        try:
            sprite_response = requests.get(self.current_pokemon['sprite_url'])
            img = Image.open(BytesIO(sprite_response.content))
            img = img.resize((200, 200), Image.NEAREST)
            photo = ImageTk.PhotoImage(img)

            self.sprite_label.config(image=photo)
            self.sprite_label.image = photo
        except Exception as e:
            print(f"Error loading sprite: {e}")

        # Health bar
        health_frame = tk.Frame(self.content_frame, bg=bg_color)
        health_frame.pack(pady=10)

        tk.Label(health_frame, text="HP:", font=("Arial", 12, "bold"),
                 bg=bg_color,
                 fg="white" if self.current_pokemon['is_legendary'] else "black").pack(side=tk.LEFT)

        self.health_bar = tk.Canvas(health_frame, width=300, height=25,
                                    bg="white", highlightthickness=1)
        self.health_bar.pack(side=tk.LEFT, padx=5)

        self.health_text = tk.Label(health_frame, text="100/100",
                                    font=("Arial", 12), bg=bg_color,
                                    fg="white" if self.current_pokemon['is_legendary'] else "black")
        self.health_text.pack(side=tk.LEFT)

        self.update_health_bar()

        # Action buttons
        actions_frame = tk.Frame(self.content_frame, bg=bg_color)
        actions_frame.pack(pady=20)

        # Row 1: Bait and Rock
        row1 = tk.Frame(actions_frame, bg=bg_color)
        row1.pack(pady=5)

        tk.Button(row1, text="🍎 Use Bait",
                  font=("Arial", 13),
                  bg="#90EE90",
                  command=self.use_bait,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

        tk.Button(row1, text="🪨 Throw Rock",
                  font=("Arial", 13),
                  bg="#D3D3D3",
                  command=self.throw_rock,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

        # Row 2: Pokeball and Run
        row2 = tk.Frame(actions_frame, bg=bg_color)
        row2.pack(pady=5)

        tk.Button(row2, text="🔴 Throw Pokéball",
                  font=("Arial", 14, "bold"),
                  bg="#FF0000", fg="white",
                  command=self.attempt_catch,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

        tk.Button(row2, text="🏃 Run Away",
                  font=("Arial", 13),
                  bg="#FFE4B5",
                  command=self.run_away,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

        # Tips
        tips_frame = tk.Frame(self.content_frame, bg=bg_color)
        tips_frame.pack(pady=10)

        tk.Label(tips_frame,
                 text="💡 Lower HP = Easier catch | Bait reduces flee chance | Pokémon may flee!",
                 font=("Arial", 9, "italic"), bg=bg_color,
                 fg="lightgray" if self.current_pokemon['is_legendary'] else "gray").pack()

    def calculate_base_catch_rate(self, data, is_legendary):
        """Calculate base catch probability"""
        base_rate = 0.40
        if is_legendary:
            base_rate = 0.10
        return base_rate

    def update_health_bar(self):
        """Update the health bar display"""
        self.health_bar.delete("all")

        health_pct = min(self.pokemon_health / self.max_health, 1.5)
        bar_width = int(300 * health_pct)

        if self.pokemon_health > self.max_health:
            color = "gold"
        elif self.pokemon_health > 50:
            color = "green"
        elif self.pokemon_health > 20:
            color = "orange"
        else:
            color = "red"

        self.health_bar.create_rectangle(
            0, 0, bar_width, 25, fill=color, outline="")
        self.health_text.config(
            text=f"{self.pokemon_health}/{self.max_health}")

    def use_bait(self):
        """Use bait to heal Pokémon and reduce flee chance"""
        if not self.current_pokemon:
            return

        self.pokemon_health += 20
        self.bait_used += 1

        self.update_health_bar()
        self.show_message(
            f"🍎 Used Bait! {self.current_pokemon['name']} gained 20 HP and feels calmer.")

    def throw_rock(self):
        """Throw rock to damage Pokémon, with flee chance"""
        if not self.current_pokemon:
            return

        damage = int(self.max_health * 0.20)
        self.pokemon_health = max(0, self.pokemon_health - damage)

        self.update_health_bar()

        flee_chance = 1/3
        flee_reduction = self.bait_used * 0.1
        actual_flee_chance = max(0.05, flee_chance - flee_reduction)

        if random.random() < actual_flee_chance:
            self.show_message(
                f"🪨 Threw a rock! {self.current_pokemon['name']} took {damage} damage and fled! 💨")
            messagebox.showwarning(
                "Fled!", f"{self.current_pokemon['name']} was scared and ran away!")
            self.root.after(1500, self.exploration_mode)
        else:
            self.show_message(
                f"🪨 Threw a rock! {self.current_pokemon['name']} took {damage} damage but stayed!")

    def calculate_catch_rate(self):
        """Calculate current catch probability"""
        base_rate = self.current_pokemon['base_catch_rate']

        health_pct = self.pokemon_health / self.max_health
        health_modifier = 1 + (1 - health_pct) * 0.5

        bait_penalty = self.bait_used * 0.05

        overheal_penalty = 0
        if self.pokemon_health > self.max_health:
            overheal_penalty = (self.pokemon_health - self.max_health) * 0.01

        final_rate = base_rate * health_modifier - bait_penalty - overheal_penalty
        return max(0.05, min(0.95, final_rate))

    def attempt_catch(self):
        """Attempt to catch the Pokémon"""
        if not self.current_pokemon:
            return

        catch_rate = self.calculate_catch_rate()
        catch_roll = random.random()

        self.show_message("🔴 The Pokéball wobbles...")
        self.root.update()
        self.root.after(800)

        if catch_roll < catch_rate:
            self.catch_success()
        else:
            # Failed catch - check if Pokémon flees
            flee_reduction = self.bait_used * 0.05  # Bait reduces flee chance
            actual_flee_chance = max(
                0.05, FLEE_CHANCE_POKEBALL - flee_reduction)

            if random.random() < actual_flee_chance:
                self.show_message(
                    f"💥 {self.current_pokemon['name']} broke free and fled! 💨")
                messagebox.showwarning("Fled!",
                                       f"{self.current_pokemon['name']} broke out of the Pokéball and ran away!")
                self.root.after(1500, self.exploration_mode)
            else:
                self.show_message(
                    f"💥 {self.current_pokemon['name']} broke free! Try weakening it. (Catch rate: {catch_rate*100:.1f}%)")

    def catch_success(self):
        """Handle successful catch"""
        pokemon_key = f"{self.current_pokemon['id']}"
        if self.current_pokemon['is_shiny']:
            pokemon_key += "_shiny"

        self.caught_pokemon[pokemon_key] = {
            'name': self.current_pokemon['name'],
            'id': self.current_pokemon['id'],
            'is_shiny': self.current_pokemon['is_shiny'],
            'is_legendary': self.current_pokemon['is_legendary']
        }

        self.save_pokedex()
        self.profile['total_catches'] += 1
        self.save_profile()

        special_text = ""
        if self.current_pokemon['is_shiny']:
            special_text += " ✨SHINY✨"
        if self.current_pokemon['is_legendary']:
            special_text += " ⚡LEGENDARY⚡"

        self.show_message(
            f"🎉 Gotcha! {self.current_pokemon['name']} was caught!{special_text}")

        messagebox.showinfo("Success!",
                            f"Gotcha! {self.current_pokemon['name']} was caught!{special_text}\n\n"
                            f"Pokédex: {len(self.caught_pokemon)}")

        self.exploration_mode()

    def run_away(self):
        """Run away from battle"""
        self.show_message("You got away safely!")
        self.exploration_mode()

    def show_message(self, message):
        """Display a message to the player"""
        self.message_label.config(text=message)

    def update_stats(self):
        """Update stats display"""
        self.stats_label.config(
            text=f"Pokédex: {len(self.caught_pokemon)} | Steps: {self.steps}"
        )

    def load_pokedex(self):
        """Load caught Pokémon from file"""
        if os.path.exists(POKEDEX_FILE):
            with open(POKEDEX_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_pokedex(self):
        """Save caught Pokémon to file"""
        with open(POKEDEX_FILE, 'w') as f:
            json.dump(self.caught_pokemon, f, indent=2)

    def show_pokedex(self):
        """Show caught Pokémon"""
        if not self.caught_pokemon:
            messagebox.showinfo(
                "Pokédex", "You haven't caught any Pokémon yet!")
            return

        pokedex_window = tk.Toplevel(self.root)
        pokedex_window.title("Pokédex")
        pokedex_window.geometry("500x600")

        tk.Label(pokedex_window, text="Your Pokédex",
                 font=("Arial", 18, "bold")).pack(pady=10)

        total = len(self.caught_pokemon)
        shinies = sum(1 for p in self.caught_pokemon.values()
                      if p.get('is_shiny'))
        legendaries = sum(1 for p in self.caught_pokemon.values()
                          if p.get('is_legendary'))

        tk.Label(pokedex_window,
                 text=f"Total: {total} | Shinies: {shinies} | Legendaries: {legendaries}",
                 font=("Arial", 12)).pack(pady=5)

        canvas = tk.Canvas(pokedex_window)
        scrollbar = tk.Scrollbar(
            pokedex_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for key, pokemon in sorted(self.caught_pokemon.items(), key=lambda x: x[1]['id']):
            markers = ""
            if pokemon.get('is_shiny'):
                markers += "✨"
            if pokemon.get('is_legendary'):
                markers += "⚡"

            entry_text = f"#{pokemon['id']:03d} - {pokemon['name']} {markers}"
            tk.Label(scrollable_frame, text=entry_text,
                     font=("Arial", 12)).pack(pady=2, anchor="w", padx=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_profile(self):
        """Show player profile"""
        created = self.profile['created_at'].strftime("%Y-%m-%d")
        last_played = self.profile['last_played'].strftime("%Y-%m-%d %H:%M")

        session_time = (datetime.now() - self.session_start).seconds
        total_time = self.profile['total_playtime'] + session_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)

        info = f"""
Trainer Name: {self.profile['name']}
Created: {created}
Last Played: {last_played}

Total Playtime: {hours}h {minutes}m
Total Steps: {self.profile['total_steps']}
Total Encounters: {self.profile['total_encounters']}
Total Catches: {self.profile['total_catches']}

Pokémon Caught: {len(self.caught_pokemon)}
Catch Rate: {(self.profile['total_catches'] / max(1, self.profile['total_encounters']) * 100):.1f}%
        """

        messagebox.showinfo("Trainer Profile", info)


if __name__ == "__main__":
    root = tk.Tk()
    game = PokemonCatchingGame(root)

    def on_closing():
        session_time = (datetime.now() - game.session_start).seconds
        game.profile['total_playtime'] += session_time
        game.save_profile()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
