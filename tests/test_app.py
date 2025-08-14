"""
Test suite for VoiceClone Pro application
"""

import os
import json
import tempfile
import pytest
from io import BytesIO
import wave
import numpy as np

# Import the app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, voice_models, synthesis_jobs
from config import TestingConfig

class TestVoiceClonePro:
    """Test cases for VoiceClone Pro application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config.from_object(TestingConfig)
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing"""
        # Generate a simple sine wave
        sample_rate = 44100
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_file.name
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'services' in data
    
    def test_get_voices(self, client):
        """Test getting available voices"""
        response = client.get('/api/voices')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'builtin_voices' in data
        assert 'custom_voices' in data
        assert 'total_count' in data
        assert len(data['builtin_voices']) > 0
    
    def test_synthesize_speech_success(self, client):
        """Test successful speech synthesis"""
        payload = {
            'text': 'Hello, this is a test.',
            'voice_id': 'sarah_us',
            'speed': 1.0,
            'pitch': 1.0,
            'volume': 1.0,
            'format': 'mp3'
        }
        
        response = client.post('/api/tts/synthesize', 
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'job_id' in data
        assert data['status'] == 'completed'
        assert 'download_url' in data
    
    def test_synthesize_speech_missing_text(self, client):
        """Test speech synthesis with missing text"""
        payload = {
            'voice_id': 'sarah_us'
        }
        
        response = client.post('/api/tts/synthesize',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_synthesize_speech_empty_text(self, client):
        """Test speech synthesis with empty text"""
        payload = {
            'text': '',
            'voice_id': 'sarah_us'
        }
        
        response = client.post('/api/tts/synthesize',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_synthesize_speech_invalid_parameters(self, client):
        """Test speech synthesis with invalid parameters"""
        payload = {
            'text': 'Hello world',
            'voice_id': 'sarah_us',
            'speed': 5.0,  # Invalid speed
            'pitch': 1.0,
            'volume': 1.0
        }
        
        response = client.post('/api/tts/synthesize',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_synthesis_status_not_found(self, client):
        """Test getting status for non-existent job"""
        response = client.get('/api/tts/status/nonexistent-job-id')
        assert response.status_code == 404
    
    def test_clone_voice_success(self, client, sample_audio_file):
        """Test successful voice cloning"""
        with open(sample_audio_file, 'rb') as f:
            data = {
                'voice_name': 'Test Voice',
                'quality': 'standard',
                'language': 'en-US'
            }
            
            response = client.post('/api/voices/clone',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'audio_files': (f, 'test.wav')})
        
        # Clean up
        os.unlink(sample_audio_file)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'voice_id' in data
        assert data['status'] == 'completed'
        assert data['name'] == 'Test Voice'
    
    def test_clone_voice_no_files(self, client):
        """Test voice cloning with no files"""
        data = {
            'voice_name': 'Test Voice',
            'quality': 'standard',
            'language': 'en-US'
        }
        
        response = client.post('/api/voices/clone',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_clone_voice_missing_name(self, client, sample_audio_file):
        """Test voice cloning with missing name"""
        with open(sample_audio_file, 'rb') as f:
            data = {
                'quality': 'standard',
                'language': 'en-US'
            }
            
            response = client.post('/api/voices/clone',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'audio_files': (f, 'test.wav')})
        
        # Clean up
        os.unlink(sample_audio_file)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_clone_voice_invalid_quality(self, client, sample_audio_file):
        """Test voice cloning with invalid quality"""
        with open(sample_audio_file, 'rb') as f:
            data = {
                'voice_name': 'Test Voice',
                'quality': 'invalid',
                'language': 'en-US'
            }
            
            response = client.post('/api/voices/clone',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'audio_files': (f, 'test.wav')})
        
        # Clean up
        os.unlink(sample_audio_file)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_cloning_status_not_found(self, client):
        """Test getting cloning status for non-existent voice"""
        response = client.get('/api/voices/clone/status/nonexistent-voice-id')
        assert response.status_code == 404
    
    def test_delete_voice_not_found(self, client):
        """Test deleting non-existent voice"""
        response = client.delete('/api/voices/nonexistent-voice-id')
        assert response.status_code == 404
    
    def test_preview_voice_builtin(self, client):
        """Test previewing built-in voice"""
        response = client.get('/api/voices/sarah_us/preview')
        assert response.status_code == 200
        assert response.mimetype == 'audio/mpeg'
    
    def test_preview_voice_not_found(self, client):
        """Test previewing non-existent voice"""
        response = client.get('/api/voices/nonexistent-voice/preview')
        assert response.status_code == 404
    
    def test_get_analytics(self, client):
        """Test getting analytics"""
        response = client.get('/api/analytics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_voices' in data
        assert 'total_syntheses' in data
        assert 'active_jobs' in data
        assert 'completed_jobs' in data
        assert 'failed_jobs' in data
        assert 'languages_supported' in data
    
    def test_file_too_large_error(self, client):
        """Test file too large error handling"""
        # This test simulates the error condition
        large_data = b'x' * (51 * 1024 * 1024)  # 51MB
        
        response = client.post('/api/voices/clone',
                             data={'voice_name': 'Test'},
                             content_type='multipart/form-data',
                             files={'audio_files': (BytesIO(large_data), 'large.wav')})
        
        assert response.status_code == 413
    
    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Not found'
    
    def test_index_route(self, client):
        """Test main application route"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'VoiceClone Pro' in response.data

class TestVoiceEngine:
    """Test cases for voice engine functionality"""
    
    def test_audio_processor_initialization(self):
        """Test audio processor initialization"""
        from voice_engine import AudioProcessor
        
        processor = AudioProcessor(sample_rate=22050)
        assert processor.sample_rate == 22050
    
    def test_voice_cloning_engine_initialization(self):
        """Test voice cloning engine initialization"""
        from voice_engine import VoiceCloningEngine
        
        engine = VoiceCloningEngine(model_dir="test_models")
        assert engine.model_dir.name == "test_models"
        assert hasattr(engine, 'audio_processor')
        assert hasattr(engine, 'training_jobs')

class TestConfig:
    """Test configuration settings"""
    
    def test_development_config(self):
        """Test development configuration"""
        from config import DevelopmentConfig
        
        config = DevelopmentConfig()
        assert config.DEBUG == True
        assert config.LOG_LEVEL == 'DEBUG'
    
    def test_testing_config(self):
        """Test testing configuration"""
        from config import TestingConfig
        
        config = TestingConfig()
        assert config.TESTING == True
        assert config.DEBUG == True
        assert 'memory' in config.SQLALCHEMY_DATABASE_URI
    
    def test_production_config(self):
        """Test production configuration"""
        from config import ProductionConfig
        
        config = ProductionConfig()
        assert config.DEBUG == False

# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config.from_object(TestingConfig)
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    def test_complete_tts_workflow(self, client):
        """Test complete text-to-speech workflow"""
        # Step 1: Synthesize speech
        payload = {
            'text': 'This is a complete workflow test.',
            'voice_id': 'sarah_us',
            'speed': 1.0,
            'pitch': 1.0,
            'volume': 1.0,
            'format': 'mp3'
        }
        
        response = client.post('/api/tts/synthesize',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        job_id = data['job_id']
        
        # Step 2: Check status
        response = client.get(f'/api/tts/status/{job_id}')
        assert response.status_code == 200
        
        # Step 3: Download audio
        response = client.get(f'/api/tts/download/{job_id}')
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__])
