
import os
import requests
import base64
import json
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv # For loading environment variables from .env file
load_dotenv()

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main") # Default to 'main'
GITHUB_API_BASE_URL = "https://api.github.com/repos"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
def retry_request(func, *args, **kwargs):
    max_retries = 5
    base_delay = 1 
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)
                print(f"Request failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise 

def get_github_contents(repo_path):
    url = f"{GITHUB_API_BASE_URL}/{repo_path}?ref={GITHUB_BRANCH}"
    response = retry_request(requests.get, url, headers=GITHUB_HEADERS)
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()

def create_github_file(repo_path, file_path, content, commit_message):
    url = f"{GITHUB_API_BASE_URL}/{repo_path}/contents/{file_path}"
    sha = None
    try:
        existing_file_info = retry_request(requests.get, url, headers=GITHUB_HEADERS)
        if existing_file_info.status_code == 200:
            sha = existing_file_info.json().get('sha')
    except requests.exceptions.RequestException as e:
        print(f"Could not get SHA for {file_path}: {e}. Assuming new file.")

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha # Include SHA for updating existing file

    response = retry_request(requests.put, url, headers=GITHUB_HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

async def generate_ai_lesson_content(prompt, gemini_api_key):
    if not gemini_api_key:
        raise ValueError("Gemini API key is required for content generation.")

    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "text/plain" # We want plain text HTML
        }
    }

    response = retry_request(requests.post, f"{GEMINI_API_URL}?key={gemini_api_key}", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception("Failed to generate content from AI model.")

def wrap_html_content(lesson_content_html, lesson_title, course_id, current_lesson_filename, github_repo_path_for_js):
    about_us_path = "../../about.html"
    contact_us_path = "../../contact.html"
    index_courses_path = "../../../index.html"

    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lesson_title} - Jokkulabs</title>
    <!-- Google Fonts - Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <!-- Modular CSS Files -->
    <link rel="stylesheet" href="../../../styles/landingpage/base.css">
    <link rel="stylesheet" href="../../../styles/landingpage/header.css">
    <link rel="stylesheet" href="../../../styles/landingpage/footer.css">
    <link rel="stylesheet" href="../../../styles/course-page.css">
    <link rel="stylesheet" href="../../../styles/lesson/lesson-content.css">
    <link rel="stylesheet" href="../../../styles/lesson/code.css">
    <link rel="stylesheet" href="../../../styles/lesson/output.css">
</head>
<body>
    <!-- Header Section -->
    <header>
        <div class="logo">
            <svg class="logo-icon" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a8 8 0 100 16 8 8 0 000-16zM5 9a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 4a1 1 0 100 2h6a1 1 0 100-2H6z" />
            </svg>
            <h1>jokkulabs</h1>
        </div>
        <nav>
            <ul>
                <li><a href="{index_courses_path}">Courses</a></li>
                <li><a href="{about_us_path}">About Us</a></li>
                <li><a href="{contact_us_path}">Contact</a></li>
            </ul>
        </nav>
    </header>

    <main class="lesson-content-container">
        <!-- Back to Course Content button at the top -->
        <a href="../index.html" class="btn-secondary back-to-course-btn">&#8592; Back to Course Content</a>

        {lesson_content_html}

        <div class="navigation-buttons">
            <a id="prev-lesson-button" href="#" class="btn-secondary" style="display:none;">&#8592; Previous Lesson</a>
            <a id="next-lesson-button" href="#" class="btn-secondary" style="display:none;">Next Lesson &#8594;</a>
        </div>
    </main>

    <!-- Footer Section -->
    <footer>
        <p>&copy; 2025 jokkulabs. All rights reserved.</p>
        <p>Designed with passion by Joel for jokkulabs.</p>
    </footer>

    <!-- JavaScript for lesson navigation -->
    <script src="../../../scripts/course-listing.js"></script>
    <script>
        // GitHub API path for this course's contents folder, used by JS for navigation
        const githubApiPathForCourseContents = '{github_repo_path_for_js}';

        document.addEventListener('DOMContentLoaded', () => {
    setupLessonNavigation(
        'python', 
        '01 - Introduction to Python & History.html',
        'prev-lesson-button',
        'next-lesson-button',
        'Jokku-gamma/JokkuLabs/contents/courses/python/contents?ref=main'
    )
})      ;
    </script>
</body>
</html>
    """
    return full_html

# --- API Endpoints ---

@app.route('/')
def index():
    return "Jokkulabs Backend is running!"

@app.route('/list_course_contents/<course_id>', methods=['GET'])
def list_course_contents(course_id):
    """
    API endpoint to list HTML files in a specific course's contents folder on GitHub.
    Example: GET /list_course_contents/python
    """
    if not GITHUB_USERNAME or not GITHUB_REPO_NAME:
        return jsonify({"error": "GitHub username or repository name not configured."}), 500

    # Construct the GitHub API path for the specific course's contents
    # e.g., Jokku-gamma/JokkuLabs/contents/courses/python/contents
    github_api_path = f"{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/contents/courses/{course_id}/contents"

    try:
        contents = get_github_contents(github_api_path)
        
        # Filter for HTML files and extract their names
        html_files = sorted([item['name'] for item in contents if item['type'] == 'file' and item['name'].endswith('.html')])
        
        return jsonify({"course_id": course_id, "files": html_files}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to list GitHub contents: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_and_add_lesson', methods=['POST'])
async def generate_and_add_lesson():
    data = request.get_json()
    course_id = data.get('course_id')
    lesson_topic = data.get('lesson_topic')
    ai_prompt_details = data.get('ai_prompt_details')
    target_directory = data.get('target_directory')
    gemini_api_key = data.get('gemini_api_key') # New: Get Gemini API key from request

    if not all([course_id, lesson_topic, ai_prompt_details, target_directory, gemini_api_key]):
        return jsonify({"error": "Missing required parameters: course_id, lesson_topic, ai_prompt_details, target_directory, gemini_api_key"}), 400
    
    if not GITHUB_USERNAME or not GITHUB_REPO_NAME or not GITHUB_TOKEN:
        return jsonify({"error": "Backend GitHub configuration missing (username, repo, or token)."}), 500

    try:
        github_api_path_for_listing = f"{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/contents/{target_directory}"
        existing_contents = get_github_contents(github_api_path_for_listing)
        
        existing_html_files = sorted([item['name'] for item in existing_contents if item['type'] == 'file' and item['name'].endswith('.html')])
        
        next_index = 1
        if existing_html_files:
            last_file_name = existing_html_files[-1]
            try:
                import re
                match = re.match(r'^(\d+)', last_file_name)
                if match:
                    current_max_index = int(match.group(1))
                    next_index = current_max_index + 1
                else:
                    next_index = len(existing_html_files) + 1 
            except ValueError:
                next_index = len(existing_html_files) + 1 
        formatted_lesson_topic = lesson_topic.replace(' ', '-').replace('/', '-').replace('\\', '-') 
        new_filename = f"{str(next_index).zfill(2)} - {formatted_lesson_topic}.html"
        full_file_path_in_repo = f"{target_directory}/{new_filename}"
        ai_prompt = f"""
Generate the main content for an HTML lesson page on the topic: "{lesson_topic}".
The content should be well-structured with appropriate HTML tags (h1, h2, h3, p, ul, ol, pre, code, strong, table, thead, tbody, tr, th, td).
Include relevant code examples and expected output blocks.
The overall tone should be educational and engaging for a beginner to intermediate audience.
Focus on explaining concepts clearly and concisely.
Do NOT include the full HTML boilerplate (head, body, html tags, doctype, script, link, meta, title, header, footer, main, navigation buttons).
Only provide the content that would go inside the `<main class="lesson-content-container">` tag, starting with an `<h1>` for the lesson title.
For code examples, use `<pre><code class="language-python">...</code></pre>`.
For expected output, use `<div class="output-block"><strong>Expected Output:</strong><pre><code>...</code></pre></div>`.
Here are some additional details for the content: {ai_prompt_details}
"""
        lesson_content_html = await generate_ai_lesson_content(ai_prompt, gemini_api_key) # Pass the key here
        github_api_path_for_js = f"{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/contents/{target_directory}?ref={GITHUB_BRANCH}"
        
        final_html_content = wrap_html_content(
            lesson_content_html,
            lesson_topic,
            course_id,
            new_filename, 
            github_api_path_for_js
        )
        commit_message = f"Add new lesson: {new_filename} (Generated by AI)"
        github_response = create_github_file(
            f"{GITHUB_USERNAME}/{GITHUB_REPO_NAME}", 
            full_file_path_in_repo,
            final_html_content,
            commit_message
        )
        
        return jsonify({
            "message": "Lesson generated and added to GitHub successfully!",
            "filename": new_filename,
            "github_url": github_response.get('content', {}).get('html_url'),
            "commit_url": github_response.get('commit', {}).get('html_url')
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"GitHub API request failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000) 