# Language Learning Interface

## Overview

The Language Learning interface is a comprehensive system that allows users to learn new languages through personalized curricula, interactive lessons, and AI-powered assistance. This system is completely separate from the Computer Science learning section and uses its own dedicated storage and services.

## Features

### 1. Curriculum Generation
- **Personalized Learning Plans**: Users can specify the language they want to learn and provide details about their background, experience, and learning goals
- **Structured Curriculum**: AI generates a complete curriculum with 7 modules, each containing 10 submodules, and each submodule containing 10 lessons
- **Progressive Learning**: Curriculum is designed to be progressive and tailored to the user's background and challenges

### 2. Lesson Management
- **Lesson Expansion**: Each lesson can be expanded with detailed content, including learning objectives, grammar points, vocabulary, and practice exercises
- **YouTube Integration**: System automatically searches for relevant YouTube videos and downloads transcripts
- **Video Summaries**: AI generates summaries of video content in the context of the lesson

### 3. Interactive Learning Interface
- **Three-Column Layout**: 
  - Left: Lesson overview and learning assistant
  - Center: Story with target words highlighted
  - Right: Translations for each sentence
- **Real-time Assistance**: Users can ask questions during lessons without leaving the interface
- **Progress Tracking**: System tracks learning progress and stores user feedback

### 4. AI-Powered Features
- **RAG-Enhanced Responses**: Uses retrieval-augmented generation to provide personalized responses based on user history
- **Difficulty Tracking**: System stores and learns from user difficulties to suggest targeted resources
- **Contextual Learning**: AI considers user's learning history when generating new content

## Technical Architecture

### Services

#### LanguageService (`src/services/language_service.py`)
- **Curriculum Generation**: Creates personalized learning curricula
- **Lesson Expansion**: Expands basic lesson plans with detailed content
- **YouTube Integration**: Searches for and downloads relevant video content
- **Content Generation**: Creates stories, translations, and lesson materials

#### SimpleLanguageStore (`src/services/simple_language_store.py`)
- **Data Storage**: Stores user queries, learning history, difficulties, and lesson context
- **RAG Implementation**: Provides context-aware responses using user history
- **File-based Storage**: Uses JSON files to avoid ChromaDB compatibility issues

### Directory Structure

```
languages/
├── [language_name]/
│   ├── module_01_[module_title]/
│   │   ├── submodule_01_[submodule_title]/
│   │   │   ├── lesson_01_[lesson_title]/
│   │   │   │   ├── lesson_overview.txt
│   │   │   │   ├── expanded_lesson.json
│   │   │   │   ├── lesson_content.json
│   │   │   │   ├── video_transcripts/
│   │   │   │   └── video_summaries/
│   │   │   └── ...
│   │   └── ...
│   └── ...
```

```
languages_data/
├── queries/
│   └── [language].json
├── history/
│   └── [language].json
├── difficulties/
│   └── [language].json
└── context/
    └── [language].json
```

## User Interface

### Main Navigation
1. **Home Page**: Click "Learn Languages" to access the language learning interface
2. **Language Root**: View existing courses or create a new one
3. **New Course**: Specify language and learning background
4. **Curriculum View**: Browse and interact with lessons
5. **Lesson Workspace**: Interactive learning environment

### Lesson Workspace Features
- **Lesson Overview**: Detailed information about the current lesson
- **Story with Target Words**: Contextual learning with highlighted vocabulary
- **Translations**: Sentence-by-sentence translations
- **Learning Assistant**: Real-time Q&A with AI
- **Progress Tracking**: Mark lessons as completed and report difficulties

## API Integration

### Ollama Integration
- **Endpoint**: `YOUR_NGROK_ENDPOINT`
- **Curriculum Generation**: Creates structured learning plans
- **Lesson Expansion**: Generates detailed lesson content
- **Content Creation**: Produces stories and translations
- **Video Analysis**: Summarizes video transcripts

### YouTube Integration
- **API Key**: `YOUR_YOUTUBE_API_KEY`
- **Search**: Finds relevant educational videos
- **Transcript Download**: Uses `youtube-transcript-api`
- **Content Filtering**: Applies "medium" duration filter

## Data Flow

### 1. Curriculum Creation
```
User Input → AI Processing → JSON Response → Directory Structure → File Storage
```

### 2. Lesson Expansion
```
Lesson Overview → AI Processing → Detailed Content → YouTube Search → Transcript Download → Summary Generation
```

### 3. Interactive Learning
```
User Question → Context Retrieval → RAG Prompt → AI Response → Storage → Display
```

### 4. Progress Tracking
```
User Action → Data Storage → History Update → Future Context Enhancement
```

## Configuration

### Environment Variables
- `NGROK_OLLAMA_URL`: Ollama server endpoint
- `YOUTUBE_API_KEY`: YouTube Data API key
- `OLLAMA_MODEL`: AI model name (default: phi3:14b)

### Dependencies
- `streamlit`: Web interface
- `requests`: HTTP client
- `youtube-transcript-api`: Video transcript download
- `json`: Data serialization
- `os`: File system operations

## Usage Examples

### Creating a New Language Course
1. Navigate to "Learn Languages"
2. Click "Create New Language Course"
3. Enter language name (e.g., "Korean")
4. Describe your background and goals
5. Click "Generate Curriculum"

### Expanding a Lesson
1. Browse to a lesson in the curriculum
2. Click "Expand" button
3. System generates detailed content and finds relevant videos
4. Content is saved for future use

### Starting a Lesson
1. Click "Start Lesson" on any lesson
2. Review lesson overview in left panel
3. Read story with target words in center panel
4. Check translations in right panel
5. Ask questions using the learning assistant

### Tracking Progress
1. Complete lesson activities
2. Click "Mark as Completed"
3. Report any difficulties encountered
4. System stores progress for future personalization

## Error Handling

### Common Issues
- **AI Service Unavailable**: Graceful fallback with error messages
- **YouTube API Limits**: Continues without video content
- **File System Errors**: Creates directories as needed
- **Network Issues**: Retry mechanisms for API calls

### Debugging
- Check Ollama server status
- Verify YouTube API key
- Review file permissions
- Monitor network connectivity

## Future Enhancements

### Planned Features
- **Voice Integration**: Speech-to-text and text-to-speech
- **Advanced Analytics**: Learning progress visualization
- **Social Features**: Peer learning and discussion
- **Mobile Support**: Responsive design for mobile devices
- **Offline Mode**: Local content caching

### Technical Improvements
- **ChromaDB Integration**: Replace simple store with vector database
- **Caching Layer**: Improve response times
- **Batch Processing**: Efficient content generation
- **API Rate Limiting**: Prevent service overload

## Security Considerations

### Data Privacy
- User data stored locally
- No external data transmission beyond API calls
- Secure API key management
- Privacy-compliant data handling

### API Security
- HTTPS for all external communications
- API key rotation capabilities
- Rate limiting implementation
- Error message sanitization

## Support and Maintenance

### Troubleshooting
1. Check service connectivity
2. Verify file permissions
3. Review error logs
4. Test with simple examples

### Updates
- Regular dependency updates
- Security patches
- Feature enhancements
- Performance optimizations

## Contributing

### Development Guidelines
- Maintain separation from Computer Science section
- Follow existing code patterns
- Add comprehensive error handling
- Include unit tests for new features

### Testing
- Test curriculum generation
- Verify lesson expansion
- Check YouTube integration
- Validate data storage

---

This language learning interface provides a comprehensive, AI-powered learning experience while maintaining complete separation from the existing Computer Science functionality.
