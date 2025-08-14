/**
 * VoiceClone Pro - API Client
 * Handles all communication with the backend Flask API
 */

class VoiceCloneAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.endpoints = {
            health: '/api/health',
            voices: '/api/voices',
            synthesize: '/api/tts/synthesize',
            synthesisStatus: '/api/tts/status',
            download: '/api/tts/download',
            cloneVoice: '/api/voices/clone',
            cloneStatus: '/api/voices/clone/status',
            deleteVoice: '/api/voices',
            previewVoice: '/api/voices',
            analytics: '/api/analytics'
        };
    }

    /**
     * Make HTTP request with error handling
     */
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(this.baseURL + url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle different response types
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else if (contentType && contentType.includes('audio/')) {
                return response; // Return response object for audio
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    /**
     * Health check
     */
    async healthCheck() {
        return await this.request(this.endpoints.health);
    }

    /**
     * Get available voices
     */
    async getVoices() {
        return await this.request(this.endpoints.voices);
    }

    /**
     * Synthesize speech from text
     */
    async synthesizeSpeech(params) {
        const {
            text,
            voiceId = 'sarah_us',
            speed = 1.0,
            pitch = 1.0,
            volume = 1.0,
            format = 'mp3'
        } = params;

        if (!text || text.trim().length === 0) {
            throw new Error('Text is required for speech synthesis');
        }

        const payload = {
            text: text.trim(),
            voice_id: voiceId,
            speed: Math.max(0.1, Math.min(3.0, speed)),
            pitch: Math.max(0.1, Math.min(2.0, pitch)),
            volume: Math.max(0.0, Math.min(1.0, volume)),
            format: format
        };

        return await this.request(this.endpoints.synthesize, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Get synthesis job status
     */
    async getSynthesisStatus(jobId) {
        if (!jobId) {
            throw new Error('Job ID is required');
        }
        return await this.request(`${this.endpoints.synthesisStatus}/${jobId}`);
    }

    /**
     * Download synthesized audio
     */
    async downloadAudio(jobId) {
        if (!jobId) {
            throw new Error('Job ID is required');
        }
        return await this.request(`${this.endpoints.download}/${jobId}`);
    }

    /**
     * Clone voice from audio files
     */
    async cloneVoice(params) {
        const {
            audioFiles,
            voiceName,
            quality = 'standard',
            language = 'en-US'
        } = params;

        if (!audioFiles || audioFiles.length === 0) {
            throw new Error('Audio files are required for voice cloning');
        }

        if (!voiceName || voiceName.trim().length === 0) {
            throw new Error('Voice name is required');
        }

        const formData = new FormData();
        
        // Add audio files
        for (let i = 0; i < audioFiles.length; i++) {
            formData.append('audio_files', audioFiles[i]);
        }

        // Add parameters
        formData.append('voice_name', voiceName.trim());
        formData.append('quality', quality);
        formData.append('language', language);

        return await this.request(this.endpoints.cloneVoice, {
            method: 'POST',
            headers: {
                // Don't set Content-Type for FormData, let browser set it
            },
            body: formData
        });
    }

    /**
     * Get voice cloning status
     */
    async getCloneStatus(voiceId) {
        if (!voiceId) {
            throw new Error('Voice ID is required');
        }
        return await this.request(`${this.endpoints.cloneStatus}/${voiceId}`);
    }

    /**
     * Delete voice model
     */
    async deleteVoice(voiceId) {
        if (!voiceId) {
            throw new Error('Voice ID is required');
        }
        return await this.request(`${this.endpoints.deleteVoice}/${voiceId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Preview voice
     */
    async previewVoice(voiceId) {
        if (!voiceId) {
            throw new Error('Voice ID is required');
        }
        return await this.request(`${this.endpoints.previewVoice}/${voiceId}/preview`);
    }

    /**
     * Get analytics data
     */
    async getAnalytics() {
        return await this.request(this.endpoints.analytics);
    }

    /**
     * Upload file with progress tracking
     */
    async uploadWithProgress(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            formData.append('file', file);

            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable && onProgress) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    onProgress(percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid JSON response'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', this.baseURL + '/api/upload');
            xhr.send(formData);
        });
    }

    /**
     * Validate audio file
     */
    validateAudioFile(file) {
        const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/mp4', 'audio/flac'];
        const maxSize = 50 * 1024 * 1024; // 50MB

        if (!allowedTypes.includes(file.type)) {
            throw new Error(`Unsupported file type: ${file.type}. Allowed types: WAV, MP3, OGG, M4A, FLAC`);
        }

        if (file.size > maxSize) {
            throw new Error(`File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum size: 50MB`);
        }

        return true;
    }

    /**
     * Get audio file duration
     */
    async getAudioDuration(file) {
        return new Promise((resolve, reject) => {
            const audio = new Audio();
            const url = URL.createObjectURL(file);

            audio.addEventListener('loadedmetadata', () => {
                URL.revokeObjectURL(url);
                resolve(audio.duration);
            });

            audio.addEventListener('error', () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load audio file'));
            });

            audio.src = url;
        });
    }

    /**
     * Batch process multiple files
     */
    async batchProcess(files, processor, onProgress) {
        const results = [];
        const total = files.length;

        for (let i = 0; i < files.length; i++) {
            try {
                const result = await processor(files[i], i);
                results.push({ success: true, result, file: files[i] });
            } catch (error) {
                results.push({ success: false, error: error.message, file: files[i] });
            }

            if (onProgress) {
                onProgress((i + 1) / total * 100, i + 1, total);
            }
        }

        return results;
    }

    /**
     * Retry failed requests
     */
    async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await requestFn();
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
                
                console.warn(`Request attempt ${attempt} failed, retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
            }
        }
    }

    /**
     * Poll for job completion
     */
    async pollJobStatus(jobId, statusGetter, interval = 1000, timeout = 300000) {
        const startTime = Date.now();

        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await statusGetter(jobId);
                    
                    if (status.status === 'completed') {
                        resolve(status);
                        return;
                    }
                    
                    if (status.status === 'failed') {
                        reject(new Error(status.error || 'Job failed'));
                        return;
                    }

                    if (Date.now() - startTime > timeout) {
                        reject(new Error('Job timeout'));
                        return;
                    }

                    setTimeout(poll, interval);
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }
}

/**
 * Error handling utilities
 */
class APIError extends Error {
    constructor(message, status, details) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
}

/**
 * Response cache for API requests
 */
class APICache {
    constructor(maxAge = 300000) { // 5 minutes default
        this.cache = new Map();
        this.maxAge = maxAge;
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > this.maxAge) {
            this.cache.delete(key);
            return null;
        }

        return item.data;
    }

    set(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    clear() {
        this.cache.clear();
    }
}

/**
 * Event emitter for API events
 */
class APIEventEmitter {
    constructor() {
        this.events = {};
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    off(event, callback) {
        if (!this.events[event]) return;
        this.events[event] = this.events[event].filter(cb => cb !== callback);
    }

    emit(event, data) {
        if (!this.events[event]) return;
        this.events[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('Event callback error:', error);
            }
        });
    }
}

/**
 * Enhanced API client with caching and events
 */
class EnhancedVoiceCloneAPI extends VoiceCloneAPI {
    constructor(baseURL = '') {
        super(baseURL);
        this.cache = new APICache();
        this.events = new APIEventEmitter();
        this.activeRequests = new Map();
    }

    async request(url, options = {}) {
        const requestId = `${options.method || 'GET'}_${url}`;
        
        // Emit request start event
        this.events.emit('requestStart', { url, options });

        try {
            // Check cache for GET requests
            if (!options.method || options.method === 'GET') {
                const cached = this.cache.get(url);
                if (cached) {
                    this.events.emit('cacheHit', { url });
                    return cached;
                }
            }

            // Prevent duplicate requests
            if (this.activeRequests.has(requestId)) {
                return await this.activeRequests.get(requestId);
            }

            const requestPromise = super.request(url, options);
            this.activeRequests.set(requestId, requestPromise);

            const result = await requestPromise;

            // Cache successful GET requests
            if (!options.method || options.method === 'GET') {
                this.cache.set(url, result);
            }

            this.events.emit('requestSuccess', { url, result });
            return result;

        } catch (error) {
            this.events.emit('requestError', { url, error });
            throw error;
        } finally {
            this.activeRequests.delete(requestId);
            this.events.emit('requestEnd', { url });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        VoiceCloneAPI,
        EnhancedVoiceCloneAPI,
        APIError,
        APICache,
        APIEventEmitter
    };
} else {
    // Browser environment
    window.VoiceCloneAPI = VoiceCloneAPI;
    window.EnhancedVoiceCloneAPI = EnhancedVoiceCloneAPI;
    window.APIError = APIError;
}
