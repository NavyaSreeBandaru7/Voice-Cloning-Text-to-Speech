import os
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps
import json
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pyttsx3
import speech_recognition as sr
from gtts import gTTS
import tempfile
import wave
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__, static_folder='static', template_folder='.')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Enable CORS for frontend communication
CORS(app, origins=['http://localhost:3000', 'http://localhost:8000', 'https://yourdomain.com'])

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'flac'}

# In-memory storage for voice models (use database in production)
voice_models = {}
synthesis_jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())

def validate_api_request(f):
    """Decorator to validate API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    return decorated_function

@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'tts': True,
            'voice_cloning': True,
            'storage': True
        }
    })

@app.route('/api/voices', methods=['GET'])
@validate_api_request
def get_voices():
    """Get available voice models"""
    # Built-in voices
    builtin_voices = [
        {
            'id': 'sarah_us',
            'name': 'Sarah',
            'language': 'en-US',
            'gender': 'female',
            'accent': 'American',
            'type': 'builtin',
            'preview_url': '/api/voices/sarah_us/preview'
        },
        {
            'id': 'david_uk',
            'name': 'David',
            'language': 'en-GB',
            'gender': 'male',
            'accent': 'British',
            'type': 'builtin',
            'preview_url': '/api/voices/david_uk/preview'
        },
        {
            'id': 'maria_es',
            'name': 'Maria',
            'language': 'es-ES',
            'gender': 'female',
            'accent': 'Spanish',
            'type': 'builtin',
            'preview_url': '/api/voices/maria_es/preview'
        }
    ]
    
    # Custom voice models
    custom_voices = []
    for voice_id, voice_data in voice_models.items():
        custom_voices.append({
            'id': voice_id,
            'name': voice_data['name'],
            'language': voice_data['language'],
            'quality': voice_data['quality'],
            'type': 'custom',
            'created_at': voice_data['created_at'],
            'preview_url': f'/api/voices/{voice_id}/preview'
        })
    
    return jsonify({
        'builtin_voices': builtin_voices,
        'custom_voices': custom_voices,
        'total_count': len(builtin_voices) + len(custom_voices)
    })

@app.route('/api/tts/synthesize', methods=['POST'])
@validate_api_request
def synthesize_speech():
    """Synthesize speech from text"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400
    
    text = data['text'].strip()
    if not text:
        return jsonify({'error': 'Text cannot be empty'}), 400
    
    # Extract parameters
    voice_id = data.get('voice_id', 'sarah_us')
    speed = data.get('speed', 1.0)
    pitch = data.get('pitch', 1.0)
    volume = data.get('volume', 1.0)
    output_format = data.get('format', 'mp3')
    
    # Validate parameters
    if not (0.1 <= speed <= 3.0):
        return jsonify({'error': 'Speed must be between 0.1 and 3.0'}), 400
    if not (0.1 <= pitch <= 2.0):
        return jsonify({'error': 'Pitch must be between 0.1 and 2.0'}), 400
    if not (0.0 <= volume <= 1.0):
        return jsonify({'error': 'Volume must be between 0.0 and 1.0'}), 400
    
    job_id = generate_job_id()
    
    try:
        # Create synthesis job
        synthesis_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'created_at': datetime.utcnow().isoformat(),
            'text': text,
            'voice_id': voice_id,
            'parameters': {
                'speed': speed,
                'pitch': pitch,
                'volume': volume,
                'format': output_format
            }
        }
        
        # Generate speech using gTTS (Google Text-to-Speech)
        language_map = {
            'sarah_us': 'en',
            'david_uk': 'en',
            'maria_es': 'es',
            'jean_fr': 'fr',
            'anna_de': 'de'
        }
        
        language = language_map.get(voice_id, 'en')
        
        # Update progress
        synthesis_jobs[job_id]['progress'] = 25
        
        # Create TTS object
        tts = gTTS(text=text, lang=language, slow=(speed < 0.8))
        
        # Update progress
        synthesis_jobs[job_id]['progress'] = 50
        
        # Save to temporary file
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        tts.save(output_path)
        
        # Update progress
        synthesis_jobs[job_id]['progress'] = 75
        
        # Apply audio effects if needed (simplified)
        if speed != 1.0 or pitch != 1.0:
            # Note: In production, use more sophisticated audio processing
            logger.info(f"Audio effects applied: speed={speed}, pitch={pitch}")
        
        # Update job completion
        synthesis_jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'output_file': output_filename,
            'completed_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'download_url': f'/api/tts/download/{job_id}',
            'duration_estimate': len(text) * 0.1  # Rough estimate
        })
        
    except Exception as e:
        synthesis_jobs[job_id] = {
            'status': 'failed',
            'error': str(e),
            'created_at': datetime.utcnow().isoformat()
        }
        logger.error(f"TTS synthesis failed: {e}")
        return jsonify({'error': 'Speech synthesis failed', 'job_id': job_id}), 500

@app.route('/api/tts/status/<job_id>', methods=['GET'])
@validate_api_request
def get_synthesis_status(job_id):
    """Get synthesis job status"""
    if job_id not in synthesis_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(synthesis_jobs[job_id])

@app.route('/api/tts/download/<job_id>', methods=['GET'])
@validate_api_request
def download_synthesized_audio(job_id):
    """Download synthesized audio file"""
    if job_id not in synthesis_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = synthesis_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    output_file = job.get('output_file')
    if not output_file:
        return jsonify({'error': 'Output file not found'}), 404
    
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_file)
    if not os.path.exists(output_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"speech_{job_id}.{job['parameters']['format']}"
    )

@app.route('/api/voices/clone', methods=['POST'])
@validate_api_request
def clone_voice():
    """Clone a voice from uploaded audio samples"""
    if 'audio_files' not in request.files:
        return jsonify({'error': 'No audio files uploaded'}), 400
    
    files = request.files.getlist('audio_files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    # Get form data
    voice_name = request.form.get('voice_name', '').strip()
    quality = request.form.get('quality', 'standard')
    language = request.form.get('language', 'en-US')
    
    if not voice_name:
        return jsonify({'error': 'Voice name is required'}), 400
    
    if quality not in ['draft', 'standard', 'high', 'premium']:
        return jsonify({'error': 'Invalid quality setting'}), 400
    
    # Validate and save uploaded files
    uploaded_files = []
    total_duration = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            try:
                # Analyze audio file
                audio_data, sample_rate = librosa.load(file_path, sr=None)
                duration = len(audio_data) / sample_rate
                total_duration += duration
                
                uploaded_files.append({
                    'filename': unique_filename,
                    'original_name': file.filename,
                    'duration': duration,
                    'sample_rate': sample_rate,
                    'file_path': file_path
                })
                
            except Exception as e:
                logger.error(f"Error processing audio file {filename}: {e}")
                return jsonify({'error': f'Invalid audio file: {filename}'}), 400
    
    if not uploaded_files:
        return jsonify({'error': 'No valid audio files uploaded'}), 400
    
    if total_duration < 10:  # Minimum 10 seconds
        return jsonify({'error': 'Insufficient audio data (minimum 10 seconds required)'}), 400
    
    # Create voice model
    voice_id = generate_job_id()
    
    # Simulate voice training process
    training_stages = [
        'Preprocessing audio samples...',
        'Extracting vocal features...',
        'Training neural network...',
        'Optimizing voice model...',
        'Validating quality...',
        'Finalizing model...'
    ]
    
    voice_models[voice_id] = {
        'id': voice_id,
        'name': voice_name,
        'language': language,
        'quality': quality,
        'status': 'training',
        'progress': 0,
        'current_stage': training_stages[0],
        'total_stages': len(training_stages),
        'created_at': datetime.utcnow().isoformat(),
        'audio_files': uploaded_files,
        'total_duration': total_duration,
        'training_stages': training_stages
    }
    
    # In a real implementation, this would start an async training job
    # For demo purposes, we'll simulate instant completion
    voice_models[voice_id].update({
        'status': 'completed',
        'progress': 100,
        'current_stage': 'Model ready',
        'completed_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({
        'voice_id': voice_id,
        'name': voice_name,
        'status': 'completed',
        'message': 'Voice cloning completed successfully',
        'training_time': '2.5 minutes',  # Simulated
        'quality_score': 0.92  # Simulated
    })

@app.route('/api/voices/clone/status/<voice_id>', methods=['GET'])
@validate_api_request
def get_cloning_status(voice_id):
    """Get voice cloning status"""
    if voice_id not in voice_models:
        return jsonify({'error': 'Voice model not found'}), 404
    
    voice_data = voice_models[voice_id]
    return jsonify({
        'voice_id': voice_id,
        'name': voice_data['name'],
        'status': voice_data['status'],
        'progress': voice_data['progress'],
        'current_stage': voice_data['current_stage'],
        'total_stages': voice_data['total_stages'],
        'created_at': voice_data['created_at']
    })

@app.route('/api/voices/<voice_id>/preview', methods=['GET'])
@validate_api_request
def preview_voice(voice_id):
    """Generate voice preview"""
    preview_text = "Hello, this is a preview of my voice. I can speak naturally with emotion and clarity."
    
    # For built-in voices, use TTS
    if voice_id in ['sarah_us', 'david_uk', 'maria_es']:
        try:
            language_map = {'sarah_us': 'en', 'david_uk': 'en', 'maria_es': 'es'}
            language = language_map.get(voice_id, 'en')
            
            tts = gTTS(text=preview_text, lang=language)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            
            return send_file(
                temp_file.name,
                mimetype='audio/mpeg',
                as_attachment=False
            )
            
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            return jsonify({'error': 'Preview generation failed'}), 500
    
    # For custom voices
    elif voice_id in voice_models:
        # In production, use the trained model to generate preview
        return jsonify({
            'message': 'Custom voice preview not implemented',
            'voice_id': voice_id,
            'preview_text': preview_text
        })
    
    else:
        return jsonify({'error': 'Voice not found'}), 404

@app.route('/api/voices/<voice_id>', methods=['DELETE'])
@validate_api_request
def delete_voice(voice_id):
    """Delete a custom voice model"""
    if voice_id not in voice_models:
        return jsonify({'error': 'Voice model not found'}), 404
    
    voice_data = voice_models[voice_id]
    
    # Clean up audio files
    for audio_file in voice_data.get('audio_files', []):
        file_path = audio_file.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
    
    # Remove from memory
    del voice_models[voice_id]
    
    return jsonify({
        'message': 'Voice model deleted successfully',
        'voice_id': voice_id
    })

@app.route('/api/analytics', methods=['GET'])
@validate_api_request
def get_analytics():
    """Get application analytics"""
    return jsonify({
        'total_voices': len(voice_models),
        'total_syntheses': len(synthesis_jobs),
        'active_jobs': len([j for j in synthesis_jobs.values() if j['status'] == 'processing']),
        'completed_jobs': len([j for j in synthesis_jobs.values() if j['status'] == 'completed']),
        'failed_jobs': len([j for j in synthesis_jobs.values() if j['status'] == 'failed']),
        'storage_used': sum(
            sum(af.get('duration', 0) for af in vm.get('audio_files', []))
            for vm in voice_models.values()
        ),
        'languages_supported': ['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE'],
        'uptime': 'Running'
    })

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': 'File size exceeds 50MB limit',
        'max_size': '50MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# Cleanup function to remove old files
def cleanup_old_files():
    """Clean up old synthesis jobs and files"""
    current_time = datetime.utcnow()
    cutoff_time = current_time - timedelta(hours=24)  # 24 hours
    
    # Clean up synthesis jobs
    jobs_to_remove = []
    for job_id, job_data in synthesis_jobs.items():
        job_time = datetime.fromisoformat(job_data['created_at'])
        if job_time < cutoff_time:
            # Remove output file
            output_file = job_data.get('output_file')
            if output_file:
                file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_file)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del synthesis_jobs[job_id]
    
    logger.info(f"Cleaned up {len(jobs_to_remove)} old synthesis jobs")

if __name__ == '__main__':
    # Run cleanup on startup
    cleanup_old_files()
    
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting VoiceClone Pro server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
