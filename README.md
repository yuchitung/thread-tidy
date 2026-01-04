# 🧵 ThreadTidy

**Personal Threads Saved Posts Organization Tool**

A personal tool for fetching, classifying, and browsing Threads saved posts. Automatically classify posts with OpenAI and provides a clean web interface for viewing and filtering.

## 🚀 Features

- **Auto Fetch Saved Posts**: Use Playwright automation to scrape Threads saved posts
- **AI Smart Classification**: Use OpenAI to automatically classify posts and generate keyword tags
- **Responsive Interface**: Beautiful React + Tailwind CSS interface, supports mobile and desktop
- **Tag Filtering**: Support category and keyword filtering, quickly find desired posts
- **Search Function**: Support post content and author name search
- **Statistics**: Display post count and filter status

## 🛠️ Tech Stack

### Backend (Python)
- **Python 3.11**
- **Playwright** - Browser automation
- **OpenAI SDK** - Post classification and keyword generation

### Frontend (React)
- **React 19** 
- **TypeScript** 
- **Tailwind CSS v4** 
- **Vite** 

### Data Storage
- **JSON** - Lightweight data storage
- **Static Deployment** 

## 📦 Installation & Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies
```bash
npm install
```

### 3. Setup Environment Variables
Create `.env` file from example:
```bash
cp .env.example .env
```
Then edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Prepare Threads Login Info
Save Threads cookies to `cookies.json` (refer to `cookies.example.json`)

## 🚀 Usage

### Step 1: Fetch Saved Posts
```bash
python scripts/fetch_saved_posts.py
```

### Step 2: Classify Posts
```bash
python scripts/classify.py
```

### Step 3: Start Frontend
```bash
npm run dev
```

Frontend will start at http://localhost:3000

### Using Docker

```bash
# Start all services
docker-compose up

# Or run scripts separately
docker-compose run python-scripts python scripts/fetch_saved_posts.py
docker-compose run python-scripts python scripts/classify.py
```

## 📁 Project Structure

```
thread-tidy/
├── scripts/
│   ├── fetch_saved_posts.py      # Fetch saved posts
│   ├── classify.py               # AI classify posts
│   ├── classification_prompt.py  # Classification prompt templates
│   └── estimate_cost.py          # Estimate classification costs
├── src/
│   ├── App.jsx                   # Main React component
│   ├── main.tsx                  # React entry point
│   └── index.css                 # Style file
├── public/
│   ├── posts.json               # Posts data (gitignored)
│   └── posts.example.json       # Data format example
├── cookies.json                 # Threads login info (gitignored)
├── cookies.example.json         # Login info example
├── package.json                 # Node.js dependencies
├── requirements.txt             # Python dependencies
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
└── README.md                    # Project documentation
```

## 📊 Data Format

Post data is stored in `public/posts.json` with the following format:

```json
[
  {
    "post_id": "abc123",
    "url": "https://www.threads.net/post/abc123",
    "author": {
      "username": "myname",
      "display_name": "My Name"
    },
    "content": "I tried a new ramen shop, it was great!",
    "media": [
      {"type": "image", "url": "https://..."}
    ],
    "timestamp": "2024-06-01T15:00:00Z",
    "saved_at": "2024-06-05T10:20:00Z",
    "categories": ["Food", "Travel"],
    "keywords": ["ramen", "Taipei"]
  }
]
```

## 🎨 Interface Features

### Main Features
- **Search Box**: Search post content and authors
- **Tag Filtering**:
  - 📂 Category tags
  - 🏷️ Keyword tags
- **Post Display**:
  - Author info and time
  - Post content
  - Category and keyword tags

### Filter Features
- Click tags to filter
- Support multiple filters
- One-click clear all filters
- Keyword tags display toggle

## 🔧 Development Commands

```bash
# Development mode
npm run dev

# Build
npm run build

# Preview build
npm run preview
```


## 🤝 Contributing

This is a personal project developed with assistance from Claude AI. Suggestions and improvements are welcome.

## 📄 License

MIT License

---

**Happy using!** 🎉