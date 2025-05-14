from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

# Initialize Flask app
app = Flask(__name__)
load_dotenv()

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_length_instruction(length):
    """Get length instruction based on selection"""
    length_map = {
        'short': 'Keep it concise (50-100 words)',
        'medium': 'Make it detailed (150-250 words)',
        'long': 'Create an in-depth narrative (300-500 words)'
    }
    return length_map.get(length, 'Make it detailed (150-250 words)')

def generate_via_api(prompt):
    """Generate story using Gemini API"""
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 4000,
            'topP': 0.9,
            'topK': 40
        }
    }
    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        json=data,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json()['candidates'][0]['content']['parts'][0]['text']

def generate_fallback(name, website_url, tagline):
    """Fallback story generation when API is unavailable"""
    fallback_story = f"""
    # {name}: {tagline}

    ## Our Story
    
    Founded with a vision to revolutionize the industry, {name} began as a small startup with big dreams. 
    From our humble beginnings, we've grown into a trusted name known for innovation and excellence.
    
    ## Our Mission
    
    At {name}, we believe in harnessing the power of technology to solve real-world problems. 
    Our tagline "{tagline}" reflects our commitment to delivering exceptional value to our customers.
    
    ## Technology & Innovation
    
    We leverage cutting-edge AI to:
    - Automate complex processes
    - Deliver personalized experiences
    - Drive measurable results for our clients
    
    ## Our Impact
    
    Since our launch, we've:
    - Served over 1,000 satisfied customers
    - Expanded to multiple markets
    - Won industry recognition for our innovative approach
    
    ## Looking Ahead
    
    As we continue to grow, we remain committed to our core values while pushing the boundaries of what's possible. 
    Visit us at {website_url} to learn more about our journey and how we can help you.
    """
    return fallback_story

@app.route('/')
def index():
    """Render the main page with no caching"""
    return render_template('index.html'), {'Cache-Control': 'no-store'}

@app.route('/generate_story', methods=['POST'])
def generate_story():
    """Generate brand story based on form inputs"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        website_url = request.form.get('website_url', '').strip()
        tagline = request.form.get('tagline', '').strip()
        tone = request.form.get('tone', 'professional')
        length = request.form.get('length', 'medium')

        # Validate inputs
        if not all([name, website_url, tagline]):
            return jsonify({'error': 'All required fields must be filled'}), 400

        if not website_url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Website URL must start with http:// or https://'}), 400

        # Create detailed prompt
        prompt = f"""
        Create a compelling brand story for '{name}' with the following details:
        - Website: {website_url}
        - Tagline: "{tagline}"
        - Tone: {tone}
        - Length: {length}

        The story should include:
        1. Company origin and mission
        2. Core values and unique selling points
        3. How AI/technology is leveraged
        4. Customer impact and success stories
        5. Future vision and goals

        Writing style requirements:
        - Use {tone} tone
        - {get_length_instruction(length)}
        - Include engaging narrative elements
        - Avoid generic phrases, be specific
        - Maintain brand consistency
        """

        # Generate story via API or fallback
        story = generate_via_api(prompt) if GEMINI_API_KEY else generate_fallback(name, website_url, tagline)

        # Return success response
        return jsonify({
            'story_data': {
                'story': story,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'word_count': len(story.split()),
                    'tone': tone,
                    'length': length
                }
            }
        }), 200

    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story. Please try again.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)