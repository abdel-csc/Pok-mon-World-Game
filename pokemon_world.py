import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk, ImageDraw
import requests
import random
import sqlite3
import os
from io import BytesIO
from datetime import datetime, timedelta
<<<<<<< Updated upstream
=======
import threading
import time

# Audio imports - mixer only to avoid tkinter conflicts
try:
    import pygame.mixer
    # Initialize ONLY the mixer, not pygame.init()
    pygame.mixer.init(44100, -16, 2, 512)
    AUDIO_AVAILABLE = True
    print("✅ Audio system initialized")
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ Warning: pygame not installed. Audio will be disabled.")
    print("Install with: pip install pygame")
except Exception as e:
    AUDIO_AVAILABLE = False
    print(f"⚠️ Warning: Could not initialize audio: {e}")

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Warning: Firebase not installed. Leaderboards will be disabled.")
    print("Install with: pip install firebase-admin")
>>>>>>> Stashed changes

# Configuration
DATABASE_FILE = "pokemon_game.db"
PLAYER_SPRITE_FILE = "player_sprite.png"
<<<<<<< Updated upstream
SHINY_CHANCE = 1/10
ENCOUNTER_CHANCE = 0.15
# 5% chance to flee after Poké Ball The 20% is way too high after testing.
=======
FIREBASE_CONFIG_FILE = "firebase-credentials.json"
FIREBASE_DB_URL = "https://pokemonworld-5dacd-default-rtdb.firebaseio.com/"
SHINY_CHANCE = 1/100
# 8% chance per step 10% is way to much in my opinion. reminds me of the zubats in the caves
ENCOUNTER_CHANCE = 0.08
>>>>>>> Stashed changes
FLEE_CHANCE_POKEBALL = 0.05

# Audio file paths - updated to support MP3 and one Wav  file since it worked better for that
AUDIO_FILES = {
    'walk': 'grass.mp3',
    'encounter_normal': 'normal.mp3',
    'encounter_legendary': 'legendary.mp3',
    'encounter_shiny': 'shiny.mp3',
    'catch_success': 'catch_success.mp3',      # FIXED - removed 'sounds/' folder
    # Wav was more convenient here. Mp3s were used for others. Should note that the mp3s were
    'pokeball_throw': 'pokeball_throw.wav'
    # royalty free. Don't think they had anything to do with p-mon itself.
}
# Legendary Pokémon IDs (Gen 1-8)
LEGENDARY_IDS = {
    144, 145, 146, 150, 151,
    243, 244, 245, 249, 250, 251,
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386,
    480, 481, 482, 483, 484, 485, 487, 488, 489, 490, 491, 492, 493, 494,
    638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649,
    716, 717, 718, 719, 720, 721,
    772, 773,
    785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809,
    888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898
}

# Badge milestones
BADGE_MILESTONES = {
    'first_shiny': {'name': '✨ First Shiny', 'requirement': 1, 'type': 'shiny'},
    'shiny_10': {'name': '✨ Shiny Collector', 'requirement': 10, 'type': 'shiny'},
    'shiny_100': {'name': '✨ Shiny Master', 'requirement': 100, 'type': 'shiny'},
    'catch_500': {'name': '🏆 Pokémon Trainer', 'requirement': 500, 'type': 'total'},
    'catch_1000': {'name': '🏆 Pokémon Master', 'requirement': 1000, 'type': 'total'},
    'catch_10000': {'name': '👑 LEGENDARY TRAINER', 'requirement': 10000, 'type': 'total'}
}

<<<<<<< Updated upstream
=======
if 'catch_10000' in BADGE_MILESTONES:
    SHINY_CHANCE = 1/50
# Biome configurations for different exploration areas
BIOMES = {
    'forest': {'bg': '#90EE90', 'shades': ['#90EE90', '#7CCD7C', '#A8E6A3'], 'tree_color': 'darkgreen', 'name': '🌲 Forest'},
    'desert': {'bg': '#F4A460', 'shades': ['#F4A460', '#DEB887', '#D2B48C'], 'tree_color': '#8B7355', 'name': '🏜️ Desert'},
    'snow': {'bg': '#F0F8FF', 'shades': ['#F0F8FF', '#E6F2FF', '#D4E9FF'], 'tree_color': '#B0C4DE', 'name': '❄️ Snow'},
    'beach': {'bg': '#FFE4B5', 'shades': ['#FFE4B5', '#FFDEAD', '#F5DEB3'], 'tree_color': '#8B7355', 'name': '🏖️ Beach'},
    'cave': {'bg': '#696969', 'shades': ['#696969', '#778899', '#808080'], 'tree_color': '#2F4F4F', 'name': '🗻 Cave'}
}


class FirebaseManager:
    """Handle Firebase Realtime Database operations for leaderboards - FIXED VERSION"""

    def __init__(self):
        self.firebase_initialized = False
        self.db_ref = None
        self.last_sync_time = 0
        self.sync_cooldown = 10  # Only sync every 10 seconds to avoid rate limits

        if not FIREBASE_AVAILABLE:
            print("❌ Firebase library not available")
            return

        try:
            if os.path.exists(FIREBASE_CONFIG_FILE):
                # Check if already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': FIREBASE_DB_URL
                    })

                self.db_ref = db.reference()
                self.firebase_initialized = True
                print("✅ Firebase connected successfully!")

                # Test the connection
                try:
                    test_data = self.db_ref.child('leaderboard').get()
                    print(
                        f"✅ Firebase test successful - found {len(test_data) if test_data else 0} players")
                except Exception as e:
                    print(f"⚠️ Firebase connection test failed: {e}")
            else:
                print(
                    f"⚠️ Firebase config file not found: {FIREBASE_CONFIG_FILE}")
                print("Leaderboards will be disabled.")
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            self.firebase_initialized = False

    def update_leaderboard(self, player_id, player_name, total_catches, shiny_catches):
        """Update player's leaderboard entry in background with rate limiting"""
        if not self.firebase_initialized:
            return False

        # Rate limiting - only sync every 10 seconds
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_cooldown:
            print(
                f"⏳ Skipping Firebase sync (cooldown: {self.sync_cooldown}s)")
            return False

        self.last_sync_time = current_time

        def _update():
            try:
                # Use milliseconds timestamp for rate limiting
                import time
                timestamp_ms = int(time.time() * 1000)

                player_data = {
                    'name': player_name,
                    'total_catches': total_catches,
                    'shiny_catches': shiny_catches,
                    'last_updated': timestamp_ms  # Milliseconds timestamp for rate limiting
                }

                self.db_ref.child('leaderboard').child(
                    str(player_id)).set(player_data)
                print(
                    f"✅ Synced to Firebase: {player_name} ({total_catches} catches, {shiny_catches} shinies)")
            except Exception as e:
                print(f"❌ Error updating leaderboard: {e}")

        # Run in background thread to avoid blocking game
        thread = threading.Thread(target=_update, daemon=True)
        thread.start()
        return True

    def get_top_total_catches(self, limit=100):
        """Get top players by total catches - FIXED FOR LIST FORMAT"""
        if not self.firebase_initialized:
            print("❌ Firebase not initialized")
            return []

        try:
            print("🔄 Fetching total catches leaderboard from Firebase...")
            ref = self.db_ref.child('leaderboard')
            data = ref.order_by_child(
                'total_catches').limit_to_last(limit).get()

            print(f"📊 Firebase returned data type: {type(data)}")
            print(f"📊 Firebase data: {data}")

            # Check if we got valid data
            if data is None:
                print("⚠️ Firebase returned None - no data yet")
                return []

            leaderboard = []

            # Firebase can return either a dict OR a list depending on how data is stored
            if isinstance(data, dict):
                print("✅ Processing as dictionary")
                for player_id, player_data in data.items():
                    if not isinstance(player_data, dict):
                        print(
                            f"⚠️ Skipping invalid player data for ID {player_id}")
                        continue

                    leaderboard.append({
                        'player_id': player_id,
                        'name': player_data.get('name', 'Unknown'),
                        'total_catches': player_data.get('total_catches', 0),
                        'shiny_catches': player_data.get('shiny_catches', 0)
                    })

            elif isinstance(data, list):
                print("✅ Processing as list")
                for index, player_data in enumerate(data):
                    # Skip None entries
                    if player_data is None:
                        continue

                    if not isinstance(player_data, dict):
                        print(
                            f"⚠️ Skipping invalid player data at index {index}")
                        continue

                    leaderboard.append({
                        'player_id': index,  # Use list index as player_id
                        'name': player_data.get('name', 'Unknown'),
                        'total_catches': player_data.get('total_catches', 0),
                        'shiny_catches': player_data.get('shiny_catches', 0)
                    })
            else:
                print(f"⚠️ Firebase returned unexpected type: {type(data)}")
                return []

            # Sort by total catches descending
            leaderboard.sort(key=lambda x: x['total_catches'], reverse=True)
            print(f"✅ Loaded {len(leaderboard)} players from leaderboard")
            return leaderboard

        except Exception as e:
            print(f"❌ Error getting total catches leaderboard: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_top_shiny_catches(self, limit=100):
        """Get top players by shiny catches - FIXED FOR LIST FORMAT"""
        if not self.firebase_initialized:
            print("❌ Firebase not initialized")
            return []

        try:
            print("🔄 Fetching shiny catches leaderboard from Firebase...")
            ref = self.db_ref.child('leaderboard')
            data = ref.order_by_child(
                'shiny_catches').limit_to_last(limit).get()

            print(f"📊 Firebase returned data type: {type(data)}")

            # Check if we got valid data
            if data is None:
                print("⚠️ Firebase returned None - no data yet")
                return []

            leaderboard = []

            # Firebase can return either a dict OR a list depending on how data is stored
            if isinstance(data, dict):
                print("✅ Processing as dictionary")
                for player_id, player_data in data.items():
                    if not isinstance(player_data, dict):
                        print(
                            f"⚠️ Skipping invalid player data for ID {player_id}")
                        continue

                    shiny_count = player_data.get('shiny_catches', 0)
                    # Only include players with at least 1 shiny
                    if shiny_count > 0:
                        leaderboard.append({
                            'player_id': player_id,
                            'name': player_data.get('name', 'Unknown'),
                            'total_catches': player_data.get('total_catches', 0),
                            'shiny_catches': shiny_count
                        })

            elif isinstance(data, list):
                print("✅ Processing as list")
                for index, player_data in enumerate(data):
                    # Skip None entries
                    if player_data is None:
                        continue

                    if not isinstance(player_data, dict):
                        print(
                            f"⚠️ Skipping invalid player data at index {index}")
                        continue

                    shiny_count = player_data.get('shiny_catches', 0)
                    # Only include players with at least 1 shiny
                    if shiny_count > 0:
                        leaderboard.append({
                            'player_id': index,  # Use list index as player_id
                            'name': player_data.get('name', 'Unknown'),
                            'total_catches': player_data.get('total_catches', 0),
                            'shiny_catches': shiny_count
                        })
            else:
                print(f"⚠️ Firebase returned unexpected type: {type(data)}")
                return []

            # Sort by shiny catches descending
            leaderboard.sort(key=lambda x: x['shiny_catches'], reverse=True)
            print(
                f"✅ Loaded {len(leaderboard)} players with shinies from leaderboard")
            return leaderboard

        except Exception as e:
            print(f"❌ Error getting shiny catches leaderboard: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_player_rank(self, player_id, category='total'):
        """Get player's rank in specified category"""
        if not self.firebase_initialized:
            return None

        try:
            if category == 'total':
                leaderboard = self.get_top_total_catches(limit=10000)
            else:
                leaderboard = self.get_top_shiny_catches(limit=10000)

            for rank, player in enumerate(leaderboard, 1):
                if str(player['player_id']) == str(player_id):
                    return rank

            return None
        except Exception as e:
            print(f"❌ Error getting player rank: {e}")
            return None

>>>>>>> Stashed changes

class AudioManager:
    """Handle all game audio with volume control - supports both WAV and MP3"""

    def __init__(self):
        self.audio_enabled = True
        self.volume = 0.7  # 0.0 to 1.0 - default to 70% volume
        self.sounds = {}
        self.audio_available = AUDIO_AVAILABLE

        if not self.audio_available:
            print("⚠️ Audio system not available - install pygame: pip install pygame")
            return

        # Load sound effects
        self.load_sounds()

    def load_sounds(self):
        """Load all sound files (supports WAV and MP3)"""
        if not self.audio_available:
            return

        print("\n🔊 Loading audio files...")
        loaded = 0

        for sound_name, filepath in AUDIO_FILES.items():
            try:
                if os.path.exists(filepath):
                    # Load the sound
                    sound = pygame.mixer.Sound(filepath)
                    sound.set_volume(self.volume)
                    self.sounds[sound_name] = sound
                    print(f"   ✅ {sound_name}: {filepath}")
                    loaded += 1
                else:
                    print(f"   ⚠️ {sound_name}: FILE NOT FOUND ({filepath})")
            except Exception as e:
                print(f"   ❌ {sound_name}: Error - {e}")

        print(
            f"🔊 Audio System Ready: {loaded}/{len(AUDIO_FILES)} sounds loaded\n")

        if loaded == 0:
            print("⚠️ No audio files found! Game will run without sound.")

    def play(self, sound_name):
        """Play a sound effect"""
        if not self.audio_available:
            return

        if not self.audio_enabled:
            return

        if sound_name in self.sounds:
            try:
                # Stop the sound first if it's already playing (for walk sounds)
                if sound_name == 'walk':
                    self.sounds[sound_name].stop()
                # Play the sound
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"❌ Error playing {sound_name}: {e}")
        else:
            # Don't spam warnings for missing optional sounds
            if sound_name not in ['catch_success', 'pokeball_throw']:
                print(f"⚠️ Sound '{sound_name}' not loaded")

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

        if self.audio_available:
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
            print(f"🔊 Volume set to {int(self.volume * 100)}%")

    def toggle_audio(self):
        """Toggle audio on/off"""
        self.audio_enabled = not self.audio_enabled
        status = "ON" if self.audio_enabled else "OFF"
        print(f"🔊 Audio toggled {status}")
        return self.audio_enabled

    def is_enabled(self):
        """Check if audio is enabled"""
        return self.audio_enabled and self.audio_available


class Database:
    """Handle all database operations"""

    def __init__(self, db_file):
        self.db_file = db_file
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_played TEXT NOT NULL,
                total_steps INTEGER DEFAULT 0,
                total_encounters INTEGER DEFAULT 0,
                total_catches INTEGER DEFAULT 0,
                total_playtime INTEGER DEFAULT 0
            )
        ''')

        # Caught Pokémon table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS caught_pokemon (
                catch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                pokemon_id INTEGER NOT NULL,
                pokemon_name TEXT NOT NULL,
                is_shiny BOOLEAN NOT NULL,
                is_legendary BOOLEAN NOT NULL,
                caught_at TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
            )
        ''')

        # Badges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS badges (
                badge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                badge_key TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                earned_at TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
                UNIQUE(player_id, badge_key)
            )
        ''')

        # Battle history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battles (
                battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                pokemon_id INTEGER NOT NULL,
                pokemon_name TEXT NOT NULL,
                is_shiny BOOLEAN NOT NULL,
                is_legendary BOOLEAN NOT NULL,
                result TEXT NOT NULL,
                attempts INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    def create_player(self, name):
        """Create a new player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO players (name, created_at, last_played)
            VALUES (?, ?, ?)
        ''', (name, now, now))

        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return player_id

    def get_player(self, player_id):
        """Get player data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM players WHERE player_id = ?', (player_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'player_id': row[0],
                'name': row[1],
                'created_at': datetime.fromisoformat(row[2]),
                'last_played': datetime.fromisoformat(row[3]),
                'total_steps': row[4],
                'total_encounters': row[5],
                'total_catches': row[6],
                'total_playtime': row[7]
            }
        return None

    def get_latest_player(self):
        """Get the most recently played player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT player_id FROM players ORDER BY last_played DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()

        if row:
            return self.get_player(row[0])
        return None

    def update_player(self, player_id, **kwargs):
        """Update player stats"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['total_steps', 'total_encounters', 'total_catches', 'total_playtime', 'last_played']:
                fields.append(f"{key} = ?")
                if key == 'last_played' and isinstance(value, datetime):
                    values.append(value.isoformat())
                else:
                    values.append(value)

        if fields:
            values.append(player_id)
            query = f"UPDATE players SET {', '.join(fields)} WHERE player_id = ?"
            cursor.execute(query, values)
            conn.commit()

        conn.close()

    def delete_player(self, player_id):
        """Delete a player and all their data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM players WHERE player_id = ?', (player_id,))
        conn.commit()
        conn.close()

    def add_caught_pokemon(self, player_id, pokemon_id, pokemon_name, is_shiny, is_legendary):
        """Add a caught Pokémon"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO caught_pokemon
            (player_id, pokemon_id, pokemon_name,
             is_shiny, is_legendary, caught_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_id, pokemon_id, pokemon_name, is_shiny, is_legendary, now))

        conn.commit()
        conn.close()

    def get_caught_pokemon(self, player_id):
        """Get all caught Pokémon for a player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT pokemon_id, pokemon_name, is_shiny, is_legendary, caught_at
            FROM caught_pokemon
            WHERE player_id = ?
            ORDER BY caught_at DESC
        ''', (player_id,))

        pokemon = []
        for row in cursor.fetchall():
            pokemon.append({
                'pokemon_id': row[0],
                'pokemon_name': row[1],
                'is_shiny': bool(row[2]),
                'is_legendary': bool(row[3]),
                'caught_at': row[4]
            })

        conn.close()
        return pokemon

    def get_shiny_count(self, player_id):
        """Get count of shiny Pokémon"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM caught_pokemon
            WHERE player_id = ? AND is_shiny = 1
        ''', (player_id,))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_legendary_count(self, player_id):
        """Get count of legendary Pokémon"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM caught_pokemon
            WHERE player_id = ? AND is_legendary = 1
        ''', (player_id,))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def add_badge(self, player_id, badge_key, badge_name):
        """Award a badge to a player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT INTO badges (player_id, badge_key, badge_name, earned_at)
                VALUES (?, ?, ?, ?)
            ''', (player_id, badge_key, badge_name, now))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Badge already exists
            conn.close()
            return False

    def get_badges(self, player_id):
        """Get all badges for a player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT badge_key, badge_name, earned_at
            FROM badges
            WHERE player_id = ?
            ORDER BY earned_at
        ''', (player_id,))

        badges = []
        for row in cursor.fetchall():
            badges.append({
                'badge_key': row[0],
                'badge_name': row[1],
                'earned_at': row[2]
            })

        conn.close()
        return badges

    def add_battle(self, player_id, pokemon_id, pokemon_name, is_shiny, is_legendary, result, attempts=1):
        """Record a battle"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO battles
            (player_id, pokemon_id, pokemon_name, is_shiny,
             is_legendary, result, attempts, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, pokemon_id, pokemon_name, is_shiny, is_legendary, result, attempts, now))

        conn.commit()
        conn.close()

    def get_battle_stats(self, player_id):
        """Get battle statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total battles
        cursor.execute(
            'SELECT COUNT(*) FROM battles WHERE player_id = ?', (player_id,))
        total_battles = cursor.fetchone()[0]

        # Caught
        cursor.execute(
            'SELECT COUNT(*) FROM battles WHERE player_id = ? AND result = "caught"', (player_id,))
        caught = cursor.fetchone()[0]

        # Fled
        cursor.execute(
            'SELECT COUNT(*) FROM battles WHERE player_id = ? AND result = "fled"', (player_id,))
        fled = cursor.fetchone()[0]

        # Fainted
        cursor.execute(
            'SELECT COUNT(*) FROM battles WHERE player_id = ? AND result = "fainted"', (player_id,))
        fainted = cursor.fetchone()[0]

        conn.close()

        return {
            'total_battles': total_battles,
            'caught': caught,
            'fled': fled,
            'fainted': fainted,
            'catch_rate': (caught / total_battles * 100) if total_battles > 0 else 0
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

        self.grid = [["white" for _ in range(
            self.grid_size)] for _ in range(self.grid_size)]

        tk.Label(self.window, text="Create Your Pixel Art Character",
                 font=("Arial", 16, "bold")).pack(pady=10)

        canvas_size = self.grid_size * self.pixel_size
        self.canvas = tk.Canvas(self.window, width=canvas_size, height=canvas_size,
                                bg="white", highlightthickness=2, highlightbackground="black")
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.paint_pixel)
        self.canvas.bind("<B1-Motion>", self.paint_pixel)

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

        tk.Button(self.window, text="🎨 Custom Color",
                  command=self.choose_custom_color).pack(pady=5)

        self.color_label = tk.Label(self.window, text="Current Color",
                                    bg=self.current_color, width=20, height=2)
        self.color_label.pack(pady=5)

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
        self.grid = [["white" for _ in range(
            self.grid_size)] for _ in range(self.grid_size)]

    def save(self):
        img = Image.new("RGBA", (self.grid_size, self.grid_size))
        pixels = img.load()

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                color = self.grid[y][x]
                if color == "white":
                    pixels[x, y] = (255, 255, 255, 0)
                else:
                    color = color.lstrip('#')
                    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                    pixels[x, y] = rgb + (255,)

        img.save(PLAYER_SPRITE_FILE, "PNG")
        self.callback()
        self.window.destroy()
        messagebox.showinfo("Success", "Character created!")


class PokemonCatchingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon Catching Game")
        self.root.geometry("800x900")

        # Initialize database
        self.db = Database(DATABASE_FILE)

<<<<<<< Updated upstream
=======
        # Initialize Firebase
        self.firebase = FirebaseManager()

        # Initialize Audio
        self.audio = AudioManager()

>>>>>>> Stashed changes
        # Load or create player
        self.player = self.db.get_latest_player()
        if not self.player:
            self.create_profile()
        else:
            self.player_id = self.player['player_id']

        # Game state
        self.current_pokemon = None
        self.pokemon_health = 100
        self.max_health = 100
        self.bait_used = 0
        self.in_battle = False
        self.steps = 0
        self.session_start = datetime.now()
        self.player_x = 200
        self.player_y = 200
        self.catch_attempts = 0

        # Load player sprite
        self.player_sprite = self.load_player_sprite()

        # UI Elements
        self.setup_ui()

        # Start in exploration mode
        self.exploration_mode()

<<<<<<< Updated upstream
=======
        # Sync to Firebase on startup
        self.sync_to_firebase()

    def sync_to_firebase(self):
        """Sync player stats to Firebase leaderboard"""
        if self.firebase.firebase_initialized:
            total_catches = self.player['total_catches']
            shiny_catches = self.db.get_shiny_count(self.player_id)
            print(
                f"🔄 Syncing to Firebase: {self.player['name']} - {total_catches} catches, {shiny_catches} shinies")
            self.firebase.update_leaderboard(
                self.player_id,
                self.player['name'],
                total_catches,
                shiny_catches
            )

>>>>>>> Stashed changes
    def create_profile(self):
        """Create new player profile"""
        name = simpledialog.askstring(
            "New Profile", "Enter your trainer name:")
        if not name:
            name = "Trainer"

        self.player_id = self.db.create_player(name)
        self.player = self.db.get_player(self.player_id)

        response = messagebox.askquestion("Player Sprite",
                                          "Would you like to create your character?\n\n"
                                          "Yes - Create pixel art character\n"
                                          "No - Upload an image instead")

        if response == 'yes':
            self.create_pixel_character()
        else:
            if messagebox.askyesno("Upload Sprite", "Upload an image for your character?"):
                self.upload_player_sprite()

    def switch_profile(self):
        """Switch to a different profile or create new one"""
        response = messagebox.askyesno(
            "Switch Profile",
            "Do you want to create a NEW profile?\n\n"
            "Yes - Create new profile\n"
            "No - Cancel"
        )

        if response:
            session_time = (datetime.now() - self.session_start).seconds
            new_playtime = self.player['total_playtime'] + session_time
            self.db.update_player(
                self.player_id,
                total_playtime=new_playtime,
                last_played=datetime.now()
            )

            self.create_profile()

            self.steps = 0
            self.session_start = datetime.now()
            self.update_profile_display()
            self.update_stats()
            self.exploration_mode()

            messagebox.showinfo("Profile Switched",
                                f"Welcome, Trainer {self.player['name']}!")

    def delete_profile(self):
        """Delete current profile and all data"""
        response = messagebox.askyesno(
            "⚠️ Delete Profile",
            f"Are you SURE you want to delete Trainer {self.player['name']}'s profile?\n\n"
            "This will delete:\n"
            "- All caught Pokémon\n"
            "- All badges\n"
            "- All battle history\n"
            "- All progress\n\n"
            "THIS CANNOT BE UNDONE!"
        )

        if response:
            confirm = messagebox.askyesno(
                "⚠️ FINAL WARNING",
                "This is your LAST CHANCE!\n\n"
                "Delete everything and start over?"
            )

            if confirm:
                try:
                    self.db.delete_player(self.player_id)

                    if os.path.exists(PLAYER_SPRITE_FILE):
                        os.remove(PLAYER_SPRITE_FILE)

                    messagebox.showinfo("Profile Deleted",
                                        "All data has been deleted.")

                    self.create_profile()

                    self.steps = 0
                    self.session_start = datetime.now()
                    self.player_sprite = self.load_player_sprite()
                    self.update_profile_display()
                    self.update_stats()
                    self.exploration_mode()

                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Could not delete profile: {e}")

    def create_pixel_character(self):
        """Open pixel art creator"""
        PixelArtCreator(self.root, self.reload_player_sprite)

    def reload_player_sprite(self):
        """Reload player sprite after creation"""
        self.player_sprite = self.load_player_sprite()

    def load_player_sprite(self):
        """Load player sprite or use default"""
        if os.path.exists(PLAYER_SPRITE_FILE):
            try:
                img = Image.open(PLAYER_SPRITE_FILE)
                img = img.resize((64, 64), Image.NEAREST)
                return ImageTk.PhotoImage(img)
            except:
                pass

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
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")

    def setup_ui(self):
        """Create the game interface"""
        self.title_label = tk.Label(self.root,
                                    text=f"Trainer {self.player['name']}'s Adventure",
                                    font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        self.profile_label = tk.Label(self.root, text="", font=("Arial", 11))
        self.profile_label.pack()
        self.update_profile_display()

        stats_frame = tk.Frame(self.root)
        stats_frame.pack(pady=5)

        caught_count = len(self.db.get_caught_pokemon(self.player_id))
        self.stats_label = tk.Label(stats_frame,
                                    text=f"Pokédex: {caught_count} | Steps: 0",
                                    font=("Arial", 14, "bold"))
        self.stats_label.pack()

        self.main_frame = tk.Frame(
            self.root, width=600, height=500, bg="lightblue")
        self.main_frame.pack(pady=20)
        self.main_frame.pack_propagate(False)

        self.content_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        self.message_label = tk.Label(self.root, text="Press WASD or Arrow keys to walk!",
                                      font=("Arial", 12, "italic"),
                                      fg="blue", wraplength=700)
        self.message_label.pack(pady=10)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="📖 Pokédex",
                  font=("Arial", 10),
                  command=self.show_pokedex,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="👤 Profile",
                  font=("Arial", 10),
                  command=self.show_profile,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="🏅 Badges",
                  font=("Arial", 10),
                  command=self.show_badges,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="📊 Stats",
                  font=("Arial", 10),
                  command=self.show_stats,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="🎨 Create",
                  font=("Arial", 10),
                  command=self.create_pixel_character,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="🔄 Switch",
                  font=("Arial", 10),
                  command=self.switch_profile,
                  width=9).pack(side=tk.LEFT, padx=2)

        tk.Button(bottom_frame, text="🗑️ Delete",
                  font=("Arial", 10),
                  command=self.delete_profile,
                  bg="#FF6B6B",
                  width=9).pack(side=tk.LEFT, padx=2)

<<<<<<< Updated upstream
=======
        tk.Button(row2, text="🏆 Leaderboard",
                  font=("Arial", 10),
                  command=self.show_leaderboards,
                  bg="#F7E168",
                  width=11).pack(side=tk.LEFT, padx=2)

        # Third row - Audio controls
        row3 = tk.Frame(bottom_frame)
        row3.pack(pady=2)

        self.audio_button = tk.Button(row3, text="🔊 Audio: ON",
                                      font=("Arial", 10),
                                      command=self.toggle_audio,
                                      bg="#90EE90",
                                      width=12)
        self.audio_button.pack(side=tk.LEFT, padx=2)

        # Update audio button text based on current state
        self.update_audio_button()

        tk.Button(row3, text="🔧 Settings",
                  font=("Arial", 10),
                  command=self.show_settings,
                  width=12).pack(side=tk.LEFT, padx=2)

>>>>>>> Stashed changes
        self.root.bind('<KeyPress>', self.handle_keypress)

    def toggle_audio(self):
        """Toggle audio on/off"""
        is_enabled = self.audio.toggle_audio()
        self.update_audio_button()

        status = "ON" if is_enabled else "OFF"
        self.show_message(f"🔊 Audio {status}")

    def update_audio_button(self):
        """Update audio button appearance"""
        if self.audio.is_enabled():
            self.audio_button.config(text="🔊 Audio: ON", bg="#90EE90")
        else:
            self.audio_button.config(text="🔇 Audio: OFF", bg="#FFB6B6")

    def show_settings(self):
        """Show settings window with volume control"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("400x400")

        tk.Label(settings_window, text="⚙️ Game Settings",
                 font=("Arial", 18, "bold")).pack(pady=20)

        # Audio settings frame
        audio_frame = tk.Frame(
            settings_window, relief=tk.RAISED, borderwidth=2, bg="lightblue")
        audio_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(audio_frame, text="🔊 Audio Settings",
                 font=("Arial", 14, "bold"), bg="lightblue").pack(pady=10)

        # Audio toggle
        audio_status = "✅ Enabled" if self.audio.is_enabled() else "❌ Disabled"
        audio_label = tk.Label(audio_frame, text=f"Status: {audio_status}",
                               font=("Arial", 11), bg="lightblue")
        audio_label.pack(pady=5)

        def toggle_and_update():
            self.toggle_audio()
            new_status = "✅ Enabled" if self.audio.is_enabled() else "❌ Disabled"
            audio_label.config(text=f"Status: {new_status}")

        tk.Button(audio_frame, text="Toggle Audio On/Off",
                  command=toggle_and_update,
                  font=("Arial", 11)).pack(pady=5)

        # Test sound button
        def test_sound():
            if 'walk' in self.audio.sounds:
                self.audio.play('walk')
                messagebox.showinfo(
                    "Test", "Playing grass sound!\nDid you hear it?")
            else:
                messagebox.showwarning("Test", "No sounds loaded to test!")

        tk.Button(audio_frame, text="🔊 Test Sound",
                  command=test_sound,
                  bg="#90EE90",
                  font=("Arial", 11)).pack(pady=5)

        # Volume slider
        tk.Label(audio_frame, text="Volume:",
                 font=("Arial", 11), bg="lightblue").pack(pady=5)

        volume_var = tk.DoubleVar(value=self.audio.volume * 100)

        def update_volume(val):
            self.audio.set_volume(float(val) / 100)

        volume_slider = tk.Scale(audio_frame, from_=0, to=100,
                                 orient=tk.HORIZONTAL,
                                 variable=volume_var,
                                 command=update_volume,
                                 length=250,
                                 bg="lightblue")
        volume_slider.pack(pady=5)

        # Audio file info
        info_frame = tk.Frame(
            settings_window, relief=tk.RAISED, borderwidth=2, bg="lightyellow")
        info_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        tk.Label(info_frame, text="📁 Audio Files Status",
                 font=("Arial", 12, "bold"), bg="lightyellow").pack(pady=5)

        loaded_count = len(self.audio.sounds)
        total_count = len(AUDIO_FILES)

        tk.Label(info_frame, text=f"Loaded: {loaded_count}/{total_count} sound files",
                 font=("Arial", 10, "bold"), bg="lightyellow").pack(pady=5)

        # Show which files are loaded
        for sound_name, filepath in AUDIO_FILES.items():
            status = "✅" if sound_name in self.audio.sounds else "❌"
            display_name = sound_name.replace('_', ' ').title()
            tk.Label(info_frame, text=f"{status} {display_name}: {filepath}",
                     font=("Arial", 9), bg="lightyellow", anchor="w").pack(padx=20, pady=2)

    def update_profile_display(self):
        """Update profile info display"""
        playtime = timedelta(seconds=self.player['total_playtime'])
        hours = int(playtime.total_seconds() // 3600)
        minutes = int((playtime.total_seconds() % 3600) // 60)

        badges = self.db.get_badges(self.player_id)
        badge_count = len(badges)

        self.profile_label.config(
            text=f"Playtime: {hours}h {minutes}m | Encounters: {self.player['total_encounters']} | Catches: {self.player['total_catches']} | Badges: {badge_count}"
        )

        self.title_label.config(
            text=f"Trainer {self.player['name']}'s Adventure")

    def handle_keypress(self, event):
        """Handle keyboard input for movement"""
        if self.in_battle:
            return

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
        new_steps = self.player['total_steps'] + 1
        self.db.update_player(self.player_id, total_steps=new_steps)
        self.player['total_steps'] = new_steps
        self.update_stats()

        # Play walking sound
        self.audio.play('walk')

        if hasattr(self, 'exploration_canvas'):
            self.exploration_canvas.coords(
                self.player_sprite_id, self.player_x, self.player_y)

        if random.random() < ENCOUNTER_CHANCE:
            self.encounter_pokemon()
        else:
            self.show_message(f"Step {self.steps}... Keep exploring!")

    def exploration_mode(self):
        """Show exploration UI with walking player"""
        self.in_battle = False

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.content_frame.config(bg="lightgreen")

        self.exploration_canvas = tk.Canvas(
            self.content_frame, width=600, height=500, bg="#90EE90")
        self.exploration_canvas.pack(fill=tk.BOTH, expand=True)

        for i in range(0, 600, 40):
            for j in range(0, 500, 40):
                shade = random.choice(["#90EE90", "#7CCD7C", "#A8E6A3"])
                self.exploration_canvas.create_rectangle(
                    i, j, i+40, j+40, fill=shade, outline="")

        for _ in range(15):
            x = random.randint(50, 550)
            y = random.randint(50, 450)
            size = random.randint(20, 40)
            self.exploration_canvas.create_oval(x-size, y-size, x+size, y+size,
                                                fill="darkgreen", outline="")

        self.exploration_canvas.create_text(300, 30,
                                            text="🌳 Use WASD or Arrows to explore! 🌳",
                                            font=("Arial", 16, "bold"),
                                            fill="white")

        self.player_sprite_id = self.exploration_canvas.create_image(
            self.player_x, self.player_y,
            image=self.player_sprite
        )

        self.show_message("Keep walking to find wild Pokémon!")

    def encounter_pokemon(self):
        """Trigger a Pokémon encounter"""
        self.in_battle = True
        self.catch_attempts = 0

        new_encounters = self.player['total_encounters'] + 1
        self.db.update_player(self.player_id, total_encounters=new_encounters)
        self.player['total_encounters'] = new_encounters

        self.pokemon_health = self.max_health
        self.bait_used = 0

        pokemon_id = random.randint(1, 898)
        is_shiny = random.random() < SHINY_CHANCE
        is_legendary = pokemon_id in LEGENDARY_IDS

        # Play encounter sound - priority: Shiny > Legendary > Normal
        if is_shiny:
            self.audio.play('encounter_shiny')
        elif is_legendary:
            self.audio.play('encounter_legendary')
        else:
            self.audio.play('encounter_normal')

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

        if self.current_pokemon['is_legendary']:
            bg_color = "#2D1B4E"
        else:  # creating a selection of random lighter colors that can be picked on random when other pokemon appear
            lighter_colors = ["#FFFACD", "#FFEBB7",
                              "#FFFFE0", "#F0E68C", "#9F663B"]
            bg_color = random.choice(lighter_colors)

        self.content_frame.config(bg=bg_color)

        top_frame = tk.Frame(self.content_frame, bg=bg_color)
        top_frame.pack(pady=10)

        self.pokemon_label = tk.Label(top_frame,
                                      text=f"{self.current_pokemon['name']}",
                                      font=("Arial", 20, "bold"),
                                      bg=bg_color,
                                      fg="white" if self.current_pokemon['is_legendary'] else "black")
        self.pokemon_label.pack()

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

        health_frame = tk.Frame(self.content_frame, bg=bg_color)
        health_frame.pack(pady=10)

        tk.Label(health_frame, text="HP:", font=("Arial", 12, "bold"),
                 bg=bg_color,
                 fg="white" if self.current_pokemon['is_legendary'] else "black").pack(side=tk.LEFT)

        self.health_bar = tk.Canvas(
            health_frame, width=300, height=25, bg="white", highlightthickness=1)
        self.health_bar.pack(side=tk.LEFT, padx=5)

        self.health_text = tk.Label(health_frame, text="100/100",
                                    font=("Arial", 12), bg=bg_color,
                                    fg="white" if self.current_pokemon['is_legendary'] else "black")
        self.health_text.pack(side=tk.LEFT)

        self.update_health_bar()

        actions_frame = tk.Frame(self.content_frame, bg=bg_color)
        actions_frame.pack(pady=20)

        row1 = tk.Frame(actions_frame, bg=bg_color)
        row1.pack(pady=5)

        tk.Button(row1, text="🎁 Use Bait",
                  font=("Arial", 13),
                  bg="#90EE90",
                  command=self.use_bait,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

        tk.Button(row1, text="🪨 Throw Rock",
                  font=("Arial", 13),
                  bg="#D3D3D3",
                  command=self.throw_rock,
                  width=15, height=2).pack(side=tk.LEFT, padx=10)

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
            f"🎁 Used Bait! {self.current_pokemon['name']} gained 20 HP and feels calmer.")

    def throw_rock(self):
        """Throw rock to damage Pokémon, with flee chance"""
        if not self.current_pokemon:
            return

        damage = int(self.max_health * 0.20)
        self.pokemon_health = max(0, self.pokemon_health - damage)

        self.update_health_bar()

        if self.pokemon_health <= 0:
            self.show_message(f"💀 {self.current_pokemon['name']} fainted!")
            messagebox.showinfo("Fainted!",
                                f"{self.current_pokemon['name']} has fainted!\n\nYou cannot catch a fainted Pokémon.")

            self.db.add_battle(
                self.player_id,
                self.current_pokemon['id'],
                self.current_pokemon['name'],
                self.current_pokemon['is_shiny'],
                self.current_pokemon['is_legendary'],
                'fainted',
                self.catch_attempts
            )

            self.root.after(1500, self.exploration_mode)
            return

        flee_chance = 1/3
        flee_reduction = self.bait_used * 0.1
        actual_flee_chance = max(0.05, flee_chance - flee_reduction)

        if random.random() < actual_flee_chance:
            self.show_message(
                f"🪨 Threw a rock! {self.current_pokemon['name']} took {damage} damage and fled! 💨")
            messagebox.showwarning(
                "Fled!", f"{self.current_pokemon['name']} was scared and ran away!")

            self.db.add_battle(
                self.player_id,
                self.current_pokemon['id'],
                self.current_pokemon['name'],
                self.current_pokemon['is_shiny'],
                self.current_pokemon['is_legendary'],
                'fled',
                self.catch_attempts
            )

            self.root.after(1500, self.exploration_mode)
        else:
            self.show_message(
                f"🪨 Threw a rock! {self.current_pokemon['name']} took {damage} damage but stayed!")

    def calculate_catch_rate(self):
        """Calculate current catch probability - LOWER HEALTH = EASIER CATCH"""
        base_rate = self.current_pokemon['base_catch_rate']

        health_pct = self.pokemon_health / self.max_health
        health_modifier = 1 + (1 - health_pct) * 1.0

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

        self.catch_attempts += 1

        if self.pokemon_health <= 0:
            messagebox.showerror("Cannot Catch",
                                 f"{self.current_pokemon['name']} has fainted!\n\nYou cannot catch a fainted Pokémon.")
            return

        catch_rate = self.calculate_catch_rate()
        catch_roll = random.random()

        # Play pokeball throw sound
        self.audio.play('pokeball_throw')

        self.show_message("🔴 The Pokéball wobbles...")
        self.root.update()
        self.root.after(800)

        if catch_roll < catch_rate:
            self.catch_success()
        else:
            flee_reduction = self.bait_used * 0.05
            actual_flee_chance = max(
                0.05, FLEE_CHANCE_POKEBALL - flee_reduction)

            if random.random() < actual_flee_chance:
                self.show_message(
                    f"💥 {self.current_pokemon['name']} broke free and fled! 💨")
                messagebox.showwarning("Fled!",
                                       f"{self.current_pokemon['name']} broke out of the Pokéball and ran away!")

                self.db.add_battle(
                    self.player_id,
                    self.current_pokemon['id'],
                    self.current_pokemon['name'],
                    self.current_pokemon['is_shiny'],
                    self.current_pokemon['is_legendary'],
                    'fled',
                    self.catch_attempts
                )

                self.root.after(1500, self.exploration_mode)
            else:
                self.show_message(
                    f"💥 {self.current_pokemon['name']} broke free! Try weakening it. (Catch rate: {catch_rate*100:.1f}%)")

    def catch_success(self):
        """Handle successful catch"""
        # Play catch success sound
        self.audio.play('catch_success')

        self.db.add_caught_pokemon(
            self.player_id,
            self.current_pokemon['id'],
            self.current_pokemon['name'],
            self.current_pokemon['is_shiny'],
            self.current_pokemon['is_legendary']
        )

        new_catches = self.player['total_catches'] + 1
        self.db.update_player(self.player_id, total_catches=new_catches)
        self.player['total_catches'] = new_catches

        self.db.add_battle(
            self.player_id,
            self.current_pokemon['id'],
            self.current_pokemon['name'],
            self.current_pokemon['is_shiny'],
            self.current_pokemon['is_legendary'],
            'caught',
            self.catch_attempts
        )

        special_text = ""
        if self.current_pokemon['is_shiny']:
            special_text += " ✨SHINY✨"
        if self.current_pokemon['is_legendary']:
            special_text += " ⚡LEGENDARY⚡"

        self.show_message(
            f"🎉 Gotcha! {self.current_pokemon['name']} was caught!{special_text}")

        caught_count = len(self.db.get_caught_pokemon(self.player_id))
        messagebox.showinfo("Success!",
                            f"Gotcha! {self.current_pokemon['name']} was caught!{special_text}\n\n"
                            f"Pokédex: {caught_count}")

        self.check_and_award_badges()
        self.update_profile_display()
        self.update_stats()

        self.exploration_mode()

    def check_and_award_badges(self):
        """Check if player earned any new badges"""
        total_catches = self.player['total_catches']
        shiny_catches = self.db.get_shiny_count(self.player_id)

        new_badges = []

        for badge_id, badge_info in BADGE_MILESTONES.items():
            if badge_info['type'] == 'shiny' and shiny_catches >= badge_info['requirement']:
                if self.db.add_badge(self.player_id, badge_id, badge_info['name']):
                    new_badges.append(badge_info['name'])
            elif badge_info['type'] == 'total' and total_catches >= badge_info['requirement']:
                if self.db.add_badge(self.player_id, badge_id, badge_info['name']):
                    new_badges.append(badge_info['name'])

        if new_badges:
            badge_text = "\n".join(new_badges)
            messagebox.showinfo("🎉 Badge Earned! 🎉",
                                f"Congratulations! You earned:\n\n{badge_text}")

    def run_away(self):
        """Run away from battle"""
        self.show_message("You got away safely!")
        self.exploration_mode()

    def show_message(self, message):
        """Display a message to the player"""
        self.message_label.config(text=message)

    def update_stats(self):
        """Update stats display"""
        caught_count = len(self.db.get_caught_pokemon(self.player_id))
        self.stats_label.config(
            text=f"Pokédex: {caught_count} | Steps: {self.steps}")

    def show_pokedex(self):
        """Show caught Pokémon"""
        caught_pokemon = self.db.get_caught_pokemon(self.player_id)

        if not caught_pokemon:
            messagebox.showinfo(
                "Pokédex", "You haven't caught any Pokémon yet!")
            return

        pokedex_window = tk.Toplevel(self.root)
        pokedex_window.title("Pokédex")
        pokedex_window.geometry("500x600")

        tk.Label(pokedex_window, text="Your Pokédex",
                 font=("Arial", 18, "bold")).pack(pady=10)

        total = len(caught_pokemon)
        shinies = self.db.get_shiny_count(self.player_id)
        legendaries = self.db.get_legendary_count(self.player_id)

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

        for pokemon in sorted(caught_pokemon, key=lambda x: x['pokemon_id']):
            markers = ""
            if pokemon['is_shiny']:
                markers += "✨"
            if pokemon['is_legendary']:
                markers += "⚡"

            entry_text = f"#{pokemon['pokemon_id']:03d} - {pokemon['pokemon_name']} {markers}"
            tk.Label(scrollable_frame, text=entry_text,
                     font=("Arial", 12)).pack(pady=2, anchor="w", padx=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_badges(self):
        """Show earned badges"""
        badges_window = tk.Toplevel(self.root)
        badges_window.title("Badge Collection")
        badges_window.geometry("500x600")

        tk.Label(badges_window, text="🏅 Your Badges 🏅",
                 font=("Arial", 18, "bold")).pack(pady=10)

        total_catches = self.player['total_catches']
        shiny_catches = self.db.get_shiny_count(self.player_id)
        earned_badges = self.db.get_badges(self.player_id)
        earned_keys = [b['badge_key'] for b in earned_badges]

        tk.Label(badges_window,
                 text=f"Total Catches: {total_catches} | Shiny Catches: {shiny_catches}",
                 font=("Arial", 11)).pack(pady=5)

        canvas = tk.Canvas(badges_window)
        scrollbar = tk.Scrollbar(
            badges_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for badge_id, badge_info in BADGE_MILESTONES.items():
            earned = badge_id in earned_keys

            frame = tk.Frame(scrollable_frame, relief=tk.RAISED if earned else tk.SUNKEN,
                             borderwidth=2, bg="gold" if earned else "lightgray")
            frame.pack(pady=5, padx=20, fill=tk.X)

            badge_text = f"{badge_info['name']}"
            if badge_info['type'] == 'shiny':
                progress_text = f"({shiny_catches}/{badge_info['requirement']} Shinies)"
            else:
                progress_text = f"({total_catches}/{badge_info['requirement']} Total)"

            status = "✓ EARNED" if earned else "🔒 LOCKED"

            tk.Label(frame, text=f"{badge_text} {status}",
                     font=("Arial", 12, "bold"),
                     bg="gold" if earned else "lightgray").pack(pady=5)

            tk.Label(frame, text=progress_text,
                     font=("Arial", 10),
                     bg="gold" if earned else "lightgray").pack(pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_stats(self):
        """Show analytics and statistics"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Statistics & Analytics")
        stats_window.geometry("600x700")

        tk.Label(stats_window, text="📊 Your Statistics",
                 font=("Arial", 18, "bold")).pack(pady=10)

        battle_stats = self.db.get_battle_stats(self.player_id)
        caught_pokemon = self.db.get_caught_pokemon(self.player_id)

        canvas = tk.Canvas(stats_window)
        scrollbar = tk.Scrollbar(
            stats_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Battle Statistics
        battle_frame = tk.Frame(
            scrollable_frame, relief=tk.RAISED, borderwidth=2, bg="lightblue")
        battle_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(battle_frame, text="⚔️ Battle Statistics",
                 font=("Arial", 14, "bold"), bg="lightblue").pack(pady=5)

        tk.Label(battle_frame, text=f"Total Battles: {battle_stats['total_battles']}",
                 font=("Arial", 11), bg="lightblue").pack(anchor="w", padx=10)
        tk.Label(battle_frame, text=f"Caught: {battle_stats['caught']}",
                 font=("Arial", 11), bg="lightblue", fg="green").pack(anchor="w", padx=10)
        tk.Label(battle_frame, text=f"Fled: {battle_stats['fled']}",
                 font=("Arial", 11), bg="lightblue", fg="orange").pack(anchor="w", padx=10)
        tk.Label(battle_frame, text=f"Fainted: {battle_stats['fainted']}",
                 font=("Arial", 11), bg="lightblue", fg="red").pack(anchor="w", padx=10)
        tk.Label(battle_frame, text=f"Catch Rate: {battle_stats['catch_rate']:.1f}%",
                 font=("Arial", 11, "bold"), bg="lightblue").pack(anchor="w", padx=10, pady=5)

        # Collection Statistics
        collection_frame = tk.Frame(
            scrollable_frame, relief=tk.RAISED, borderwidth=2, bg="lightgreen")
        collection_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(collection_frame, text="📚 Collection Statistics",
                 font=("Arial", 14, "bold"), bg="lightgreen").pack(pady=5)

        total_pokemon = len(caught_pokemon)
        shiny_count = self.db.get_shiny_count(self.player_id)
        legendary_count = self.db.get_legendary_count(self.player_id)
        unique_species = len(set(p['pokemon_id'] for p in caught_pokemon))

        tk.Label(collection_frame, text=f"Total Pokémon: {total_pokemon}",
                 font=("Arial", 11), bg="lightgreen").pack(anchor="w", padx=10)
        tk.Label(collection_frame, text=f"Unique Species: {unique_species}",
                 font=("Arial", 11), bg="lightgreen").pack(anchor="w", padx=10)
        tk.Label(collection_frame, text=f"Shinies: {shiny_count} ({shiny_count/max(1, total_pokemon)*100:.1f}%)",
                 font=("Arial", 11), bg="lightgreen").pack(anchor="w", padx=10)
        tk.Label(collection_frame, text=f"Legendaries: {legendary_count} ({legendary_count/max(1, total_pokemon)*100:.1f}%)",
                 font=("Arial", 11), bg="lightgreen").pack(anchor="w", padx=10, pady=5)

        # Player Statistics
        player_frame = tk.Frame(
            scrollable_frame, relief=tk.RAISED, borderwidth=2, bg="lightyellow")
        player_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(player_frame, text="👤 Player Statistics",
                 font=("Arial", 14, "bold"), bg="lightyellow").pack(pady=5)

        playtime = timedelta(seconds=self.player['total_playtime'])
        hours = int(playtime.total_seconds() // 3600)
        minutes = int((playtime.total_seconds() % 3600) // 60)

        tk.Label(player_frame, text=f"Total Steps: {self.player['total_steps']:,}",
                 font=("Arial", 11), bg="lightyellow").pack(anchor="w", padx=10)
        tk.Label(player_frame, text=f"Total Playtime: {hours}h {minutes}m",
                 font=("Arial", 11), bg="lightyellow").pack(anchor="w", padx=10)
        tk.Label(player_frame, text=f"Encounters: {self.player['total_encounters']:,}",
                 font=("Arial", 11), bg="lightyellow").pack(anchor="w", padx=10)

        badges_earned = len(self.db.get_badges(self.player_id))
        tk.Label(player_frame, text=f"Badges Earned: {badges_earned}/{len(BADGE_MILESTONES)}",
                 font=("Arial", 11), bg="lightyellow").pack(anchor="w", padx=10, pady=5)

        # Recent Catches
        if caught_pokemon:
            recent_frame = tk.Frame(
                scrollable_frame, relief=tk.RAISED, borderwidth=2, bg="lavender")
            recent_frame.pack(pady=10, padx=20, fill=tk.X)

            tk.Label(recent_frame, text="🕐 Recent Catches (Last 10)",
                     font=("Arial", 14, "bold"), bg="lavender").pack(pady=5)

            for pokemon in caught_pokemon[:10]:
                markers = ""
                if pokemon['is_shiny']:
                    markers += "✨"
                if pokemon['is_legendary']:
                    markers += "⚡"

                date_str = datetime.fromisoformat(
                    pokemon['caught_at']).strftime("%m/%d %I:%M%p")
                text = f"{date_str} - {pokemon['pokemon_name']} {markers}"
                tk.Label(recent_frame, text=text,
                         font=("Arial", 10), bg="lavender").pack(anchor="w", padx=10, pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_profile(self):
        """Show player profile"""
        created = self.player['created_at'].strftime("%Y-%m-%d")
        last_played = self.player['last_played'].strftime("%Y-%m-%d %H:%M")

        session_time = (datetime.now() - self.session_start).seconds
        total_time = self.player['total_playtime'] + session_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)

        shiny_catches = self.db.get_shiny_count(self.player_id)
        badge_count = len(self.db.get_badges(self.player_id))
        caught_count = len(self.db.get_caught_pokemon(self.player_id))

        info = f"""
Trainer Name: {self.player['name']}
Created: {created}
Last Played: {last_played}

Total Playtime: {hours}h {minutes}m
Total Steps: {self.player['total_steps']:,}
Total Encounters: {self.player['total_encounters']:,}
Total Catches: {self.player['total_catches']:,}

Pokémon Caught: {caught_count}
Shiny Pokémon: {shiny_catches}
Badges Earned: {badge_count}/{len(BADGE_MILESTONES)}
Catch Rate: {(self.player['total_catches'] / max(1, self.player['total_encounters']) * 100):.1f}%
        """

        messagebox.showinfo("Trainer Profile", info)


if __name__ == "__main__":
    root = tk.Tk()
    game = PokemonCatchingGame(root)

    def on_closing():
        session_time = (datetime.now() - game.session_start).seconds
        new_playtime = game.player['total_playtime'] + session_time
        game.db.update_player(
            game.player_id,
            total_playtime=new_playtime,
            last_played=datetime.now()
        )
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
