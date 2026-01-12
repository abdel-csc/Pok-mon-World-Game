"""
Manual Firebase Sync Script
Run this to upload your existing game data to the leaderboard
"""

import sqlite3
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Configuration
DATABASE_FILE = "pokemon_game.db"
FIREBASE_CONFIG_FILE = "firebase-credentials.json"
FIREBASE_DB_URL = "https://pokemonworld-5dacd-default-rtdb.firebaseio.com/"

try:
    # Initialize Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })

    db_ref = db.reference()

    # Connect to local database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Get all players
    cursor.execute('SELECT player_id, name, total_catches FROM players')
    players = cursor.fetchall()

    if not players:
        print("❌ No players found in database!")
        exit()

    print(f"Found {len(players)} player(s) in local database\n")

    # Sync each player
    for player_id, name, total_catches in players:
        # Get shiny count
        cursor.execute('''
            SELECT COUNT(*) FROM caught_pokemon
            WHERE player_id = ? AND is_shiny = 1
        ''', (player_id,))
        shiny_catches = cursor.fetchone()[0]

        # Upload to Firebase
        player_data = {
            'name': name,
            'total_catches': total_catches,
            'shiny_catches': shiny_catches,
            'last_updated': datetime.now().isoformat()
        }

        db_ref.child('leaderboard').child(str(player_id)).set(player_data)

        print(f"✓ Synced: {name}")
        print(f"  - Total Catches: {total_catches}")
        print(f"  - Shiny Catches: {shiny_catches}")
        print()

    conn.close()

    print("🎉 All players synced to Firebase!")
    print("Refresh the leaderboard in your game to see the updates.")

except FileNotFoundError as e:
    print(f"❌ Error: Could not find file - {e}")
    print("\nMake sure you have:")
    print("1. pokemon_game.db (your save file)")
    print("2. firebase-credentials.json (your Firebase config)")

except Exception as e:
    print(f"❌ Error syncing to Firebase: {e}")
    print("\nMake sure you have installed: pip install firebase-admin")
