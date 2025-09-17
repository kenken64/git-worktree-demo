from flask import Flask, request, jsonify
import sqlite3
import hashlib
import zlib
import base64
from datetime import datetime
import os

app = Flask(__name__)

DATABASE = 'prompts.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS compressed_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_hash TEXT UNIQUE NOT NULL,
            compressed_data TEXT NOT NULL,
            original_size INTEGER NOT NULL,
            compressed_size INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def compress_prompt(prompt):
    compressed = zlib.compress(prompt.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')

def generate_prompt_hash(prompt):
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

@app.route('/save-prompt', methods=['POST'])
def save_compressed_prompt():
    try:
        data = request.get_json()

        if not data or 'prompt' not in data:
            return jsonify({'error': 'Prompt is required'}), 400

        prompt = data['prompt']

        if not prompt.strip():
            return jsonify({'error': 'Prompt cannot be empty'}), 400

        prompt_hash = generate_prompt_hash(prompt)
        compressed_data = compress_prompt(prompt)
        original_size = len(prompt.encode('utf-8'))
        compressed_size = len(compressed_data.encode('utf-8'))

        conn = get_db_connection()

        try:
            conn.execute('''
                INSERT INTO compressed_prompts (prompt_hash, compressed_data, original_size, compressed_size)
                VALUES (?, ?, ?, ?)
            ''', (prompt_hash, compressed_data, original_size, compressed_size))
            conn.commit()

            cursor = conn.execute('SELECT last_insert_rowid()')
            prompt_id = cursor.fetchone()[0]

            return jsonify({
                'message': 'Prompt saved successfully',
                'id': prompt_id,
                'hash': prompt_hash,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round(compressed_size / original_size, 3)
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Prompt already exists'}), 409

        finally:
            conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-prompt/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    try:
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT prompt_hash, compressed_data, original_size, compressed_size, created_at
            FROM compressed_prompts WHERE id = ?
        ''', (prompt_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return jsonify({'error': 'Prompt not found'}), 404

        compressed_bytes = base64.b64decode(row['compressed_data'])
        original_prompt = zlib.decompress(compressed_bytes).decode('utf-8')

        return jsonify({
            'id': prompt_id,
            'hash': row['prompt_hash'],
            'prompt': original_prompt,
            'original_size': row['original_size'],
            'compressed_size': row['compressed_size'],
            'created_at': row['created_at']
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list-prompts', methods=['GET'])
def list_prompts():
    try:
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT id, prompt_hash, original_size, compressed_size, created_at
            FROM compressed_prompts
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        prompts = []
        for row in rows:
            prompts.append({
                'id': row['id'],
                'hash': row['prompt_hash'],
                'original_size': row['original_size'],
                'compressed_size': row['compressed_size'],
                'compression_ratio': round(row['compressed_size'] / row['original_size'], 3),
                'created_at': row['created_at']
            })

        return jsonify({'prompts': prompts}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)