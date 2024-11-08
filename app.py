from flask import Flask, jsonify
from bs4 import BeautifulSoup
from urllib.parse import quote
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import json
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

cache = Cache(config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': 'cache',
    'CACHE_THRESHOLD': 100000 # number of 'files' before start auto-delete (~2gb)
})
cache.init_app(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memcached://localhost:11211",
    default_limits=["100 per day", "20 per hour"],
    strategy="fixed-window", # or "moving-window"
)

# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["100 per day", "20 per hour"]
# )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_dictionary_entry(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    entries = []
    
    # Find all entry blocks
    for entry_div in soup.find_all('div', class_='entry_v2'):
        entry_data = {
            'word': '',
            'pronunciations': [],
            'part_of_speech': '',
            'definitions': [],
            'examples': [],
            'notes': []
        }
        
        # Get word and homograph number
        hw_txt = entry_div.find('span', class_='hw_txt')
        if hw_txt:
            entry_data['word'] = hw_txt.text.strip()
            homograph = hw_txt.find('sup', class_='homograph')
            if homograph:
                entry_data['homograph'] = homograph.text.strip()
        
        # Get pronunciations
        for pron in entry_div.find_all('span', class_='hpron_word'):
            entry_data['pronunciations'].append(pron.text.strip())
        
        # Get part of speech
        fl = entry_div.find('span', class_='fl')
        if fl:
            entry_data['part_of_speech'] = fl.text.strip()
        
        # Get grammar info
        gram = entry_div.find('span', class_='gram')
        if gram:
            entry_data['grammar'] = gram.text.strip('[]')
        
        # Get style labels
        sl = entry_div.find('span', class_='sl')
        if sl:
            entry_data['style_label'] = sl.text.strip()
        
        # Get definitions and examples
        for sense in entry_div.find_all('div', class_='sense'):
            definition = {
                'text': '',
                'examples': []
            }
            
            # Get definition text
            def_text = sense.find('span', class_='def_text')
            if def_text:
                definition['text'] = def_text.text.strip()
            
            # Get examples
            for vi in sense.find_all('div', class_='vi_content'):
                definition['examples'].append(vi.text.strip())
            
            if definition['text'] or definition['examples']:
                entry_data['definitions'].append(definition)
        
        # Get usage notes
        for note in entry_div.find_all('span', class_='snote'):
            if note.text.strip():
                entry_data['notes'].append(note.text.strip())
        
        entries.append(entry_data)
    
    return entries

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Dictionary API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Dictionary API</h1>
            <p>Use this API by making a GET request to <code>/x/{word}</code></p>
            <p>Example: <code>/x/stat</code> will return the definition of "stat"</p>
            <p>The response will be in JSON format.</p>
        </body>
    </html>
    '''

@app.route('/x/<word>')
@cache.memoize(300)  # Cache for 5 minutes XXX
def get_word(word):
    try:
        # URL encode the word to handle special characters
        encoded_word = quote(word.lower().strip())
        url = f"https://www.britannica.com/dictionary/{encoded_word}"
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Fetching definition for word: {word}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            entries = parse_dictionary_entry(response.text)
            if entries:
                return jsonify(entries)
            else:
                return jsonify({"error": "No definition found"}), 404
        else:
            logger.error(f"Failed to fetch definition. Status code: {response.status_code}")
            return jsonify({"error": f"Failed to fetch definition. Status code: {response.status_code}"}), response.status_code
            
    except requests.Timeout:
        logger.error("Request timed out")
        return jsonify({"error": "Request timed out"}), 504
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return jsonify({"error": f"Failed to fetch definition: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)