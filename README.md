# ProfAI MIT - AI-Powered Learning Platform

https://github.com/markknoffler/ProfAI-MIT-Learning-Platform/blob/main/resources_imgs/ProfAI_1.png

An intelligent, AI-driven learning platform that creates personalized educational experiences with integrated YouTube video content and ChromaDB knowledge retrieval.

## 🚀 Features

### Core Learning Features
- **AI-Generated Course Structures**: Automatically creates 7x10x10 course structures (7 modules, 10 submodules each, 10 lessons each)
- **Intelligent Lesson Expansion**: AI-powered detailed lesson plans with comprehensive learning objectives
- **Interactive Code Editor**: Built-in code editor with syntax highlighting for Python, C, and C++
- **Real-time Code Evaluation**: AI-powered code analysis and guidance without revealing solutions
- **Voice-Based Learning Assessment**: Record verbal summaries for AI evaluation of understanding

### YouTube Integration (NEW!)
- **Smart Video Discovery**: AI generates 3 search prompts based on lesson content
- **YouTube Video Search**: Finds relevant educational videos using YouTube Data API
- **Automatic Transcription**: Downloads and transcribes video content
- **AI-Generated Summaries**: Creates concise summaries of video content
- **Relevance Explanations**: AI explains why each video is relevant to the lesson
- **Seamless UI Integration**: Videos displayed alongside lesson content

### Knowledge Management
- **ChromaDB Integration**: Intelligent knowledge retrieval for personalized learning
- **Progress Tracking**: Comprehensive progress monitoring and analytics
- **Adaptive Learning**: Course adaptation based on student performance

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **AI Models**: Ollama (via ngrok endpoint)
- **Knowledge Base**: ChromaDB
- **Video Processing**: YouTube Data API + youtube-transcript-api
- **Code Editor**: Streamlit-Ace
- **Storage**: Local file system with JSON metadata

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd primary_code_hackathon
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env file with your actual API keys
   # You'll need:
   # - ElevenLabs API key for voice features
   # - YouTube Data API key for video integration
   # - ngrok endpoint for Ollama server
   ```

4. **Run the setup script** (optional):
   ```bash
   python setup.py
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 🎯 Usage

### Creating a New Course
1. Navigate to "Create Course" in the main menu
2. Enter your learning topic (e.g., "learn C++", "learn web development")
3. The AI will generate a comprehensive course structure
4. Review and customize the generated content

### Taking a Course
1. Select a course from the course map
2. Click "Expand" on any lesson to generate detailed content
3. **NEW**: YouTube videos will automatically be processed and displayed
4. Use the interactive code editor to practice
5. Record voice summaries for AI evaluation

### YouTube Video Features
- Videos are automatically discovered based on lesson content
- Each video includes:
  - AI-generated summary
  - Relevance explanation
  - Direct YouTube link
  - Channel information
- Videos are displayed in both course map and lesson workspace views

## 🔧 Configuration

### API Keys Required
- **YouTube Data API**: For video search functionality
- **Ollama Endpoint**: For AI model interactions (via ngrok)

### ChromaDB Setup
The system uses ChromaDB for intelligent knowledge retrieval. Ensure ChromaDB is properly configured for optimal performance.

## 📁 Project Structure

```
primary_code_hackathon/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── src/
│   ├── services/
│   │   ├── course_service.py       # Course generation and management
│   │   ├── course_storage.py       # File system storage operations
│   │   ├── lesson_expander.py      # AI lesson plan expansion
│   │   ├── youtube_service.py      # YouTube video processing (NEW!)
│   │   ├── ollama_client.py        # AI model communication
│   │   ├── chroma_store.py         # ChromaDB knowledge retrieval
│   │   └── language_service.py     # Language-specific utilities
│   └── utils/                      # Utility functions
└── courses/                        # Generated course content (gitignored)
```

## 🎬 YouTube Integration Details

### How It Works
1. **Lesson Expansion**: When a lesson is expanded, the AI generates 3 search prompts
2. **Video Discovery**: YouTube Data API searches for videos matching each prompt
3. **Content Processing**: Videos are transcribed and summarized by AI
4. **Storage**: All data is saved locally with the lesson content
5. **Display**: Videos appear in the UI with summaries and explanations

### Video Processing Pipeline
```
Lesson Plan → AI Search Prompts → YouTube Search → Transcription → AI Summary → UI Display
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Streamlit** for the amazing web framework
- **Ollama** for local AI model hosting
- **ChromaDB** for vector database capabilities
- **YouTube Data API** for video discovery
- **youtube-transcript-api** for video transcription

## 🆕 Recent Updates

### YouTube Video Integration (Latest)
- ✅ AI-powered video discovery based on lesson content
- ✅ Automatic video transcription and summarization
- ✅ Seamless UI integration with lesson content
- ✅ Relevance explanations for each video
- ✅ Local storage of video metadata and transcripts

---

**Made with ❤️ for AI-powered education**


