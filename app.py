from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__, static_folder='cover')

# Global variables to store song data and aliases
songs_data = {}
alias_data = {}
import json
import os

# Global song queue
song_queue = []

QUEUE_FILE = 'queue.json'

def load_queue():
    global song_queue
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            try:
                song_queue = json.load(f)
            except json.JSONDecodeError:
                song_queue = []
    else:
        song_queue = []

# Load queue on startup
load_queue()

def save_queue():
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(song_queue, f, ensure_ascii=False, indent=4)

def load_data():
    global songs_data, alias_data
    try:
        with open(os.path.join(os.path.dirname(__file__), 'songs.json'), 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        with open(os.path.join(os.path.dirname(__file__), 'alias.json'), 'r', encoding='utf-8') as f:
            alias_data_list = json.load(f)

        # Convert alias_data_list to a dictionary for easier lookup
        alias_data = {item['id']: item for item in alias_data_list}

        # Merge song names from alias_data into songs_data
        for song in songs_data:
            song_id = song.get('id')
            if song_id and song_id in alias_data:
                song['name'] = alias_data[song_id].get('name', song.get('name', '未知歌曲'))

        print("Data loaded successfully!")
    except FileNotFoundError:
        print("Error: songs.json or alias.json not found.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from songs.json or alias.json.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def song_list():
    return render_template('list.html', queue=song_queue)

@app.route('/display')
def display():
    return render_template('display.html', queue=song_queue)

@app.route('/debug')
def debug():
    return render_template('debug.html', songs=songs_data, aliases=alias_data, queue=song_queue)

@app.route('/add_to_queue', methods=['POST'])
def add_to_queue():
    song_id = request.json.get('song_id')
    if song_id:
        # Check if the song is already in the queue
        if any(s.get('id') == song_id for s in song_queue):
            return jsonify({'success': False, 'message': 'Song already in queue.'}), 400

        song = next((s for s in songs_data if s.get('id') == song_id), None)
        if song:
            # Ensure the song object has all necessary fields before adding to queue
            queued_song = {
                'id': song.get('id'),
                'name': song.get('name', '未知歌曲'),
                'artist': song.get('artist', '未知曲师'),
                'type': song.get('type', '未知类型'),
                'ds': song.get('ds', [])
            }
            song_queue.append(queued_song)
            save_queue() # Save queue after adding a song
            return jsonify({'success': True, 'message': 'Song added to queue.'})
    return jsonify({'success': False, 'message': 'Failed to add song to queue.'}), 400

@app.route('/remove_from_queue', methods=['POST'])
def remove_from_queue():
    song_index = request.json.get('index')
    if song_index is not None and 0 <= song_index < len(song_queue):
            del song_queue[song_index]
            save_queue() # Save queue after removing a song
            return jsonify({'success': True, 'message': 'Song removed from queue.'})
    return jsonify({'success': False, 'message': 'Failed to remove song from queue.'}), 400

@app.route('/move_queue_item', methods=['POST'])
def move_queue_item():
    index = request.json.get('index')
    direction = request.json.get('direction') # 'up' or 'down'

    if index is not None and 0 <= index < len(song_queue):
        if direction == 'up' and index > 0:
            song_queue[index], song_queue[index - 1] = song_queue[index - 1], song_queue[index]
            save_queue() # Save queue after moving a song
            return jsonify({'success': True, 'message': 'Song moved up.'})
        elif direction == 'down' and index < len(song_queue) - 1:
            song_queue[index], song_queue[index + 1] = song_queue[index + 1], song_queue[index]
            save_queue() # Save queue after moving a song
            return jsonify({'success': True, 'message': 'Song moved down.'})
    return jsonify({'success': False, 'message': 'Failed to move song.'}), 400

@app.route('/get_queue', methods=['GET'])
def get_queue():
    print(f"Current song_queue: {song_queue}") # Debug print
    return jsonify(song_queue)

@app.route('/get_current_song', methods=['GET'])
def get_current_song():
    if song_queue:
        current_song = song_queue[0]
        # Ensure the current_song object has all necessary fields for display
        display_song = {
            'id': current_song.get('id'),
            'name': current_song.get('name', '未知歌曲'),
            'artist': current_song.get('artist', '未知曲师'),
            'type': current_song.get('type', '未知类型'),
            'ds': current_song.get('ds', [])
        }
        return jsonify(display_song)
    return jsonify({'message': 'No song in queue.'}), 404

@app.route('/search', methods=['GET'])
def search_songs():
    query = request.args.get('query', '').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 30)) # Default to 10 songs per page

    filtered_songs = []
    if query:
        for song_info in songs_data:
            song_id = song_info.get('id')
            if not song_id:
                continue

            # Check song name
            if query in song_info.get('name', '').lower():
                filtered_songs.append(song_info)
                continue

            # Check alias
            # alias_data is a dictionary where key is song_id and value is an object containing 'id', 'name', 'alias'
            alias_entry = alias_data.get(song_id)
            if alias_entry and 'alias' in alias_entry:
                for alias_name in alias_entry['alias'].split(','):
                    if query in alias_name.strip().lower():
                        filtered_songs.append(song_info)
                        break # Found in aliases, no need to check other aliases for this song
                if song_info in filtered_songs: # If already added by alias, continue to next song
                    continue

            # Check artist
            if query in song_info.get('artist', '').lower():
                filtered_songs.append(song_info)
                continue

            # Check difficulty (ds)
            for difficulty in song_info.get('ds', []):
                if query in str(difficulty).lower():
                    filtered_songs.append(song_info)
                    break # Found in difficulties, no need to check other difficulties for this song
    else:
        filtered_songs = songs_data # If no query, show all songs paginated

    total_songs = len(filtered_songs)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_songs = filtered_songs[start:end]

    return jsonify({
        'songs': paginated_songs,
        'total_songs': total_songs,
        'total_pages': (total_songs + per_page - 1) // per_page,
        'current_page': page
    })


if __name__ == '__main__':
    load_data()
    app.run(port=1145, debug=True)