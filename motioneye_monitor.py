from flask import Flask, request
import requests
from PIL import Image, ImageDraw
import io
import json
import os
import time

app = Flask(__name__)

# Telegram settings
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"  # Replace with your bot token
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"  # Replace with your chat ID
TELEGRAM_API_URL = "https://api.telegram.org/bot%s/sendPhoto" % TELEGRAM_TOKEN

# Hugging Face settings
HF_API_TOKEN = "HF_API_TOKEN"  # Your token
HF_API_URL = "https://api-inference.huggingface.co/models/hustvl/yolos-base"
headers = {"Authorization": "Bearer %s" % HF_API_TOKEN, "Content-Type": "application/json"}

# MotionEye base directory
MOTION_BASE_DIR = "/var/lib/motioneye"

# Convert image to bytes for API
def image_to_bytes(image_path):
    img = Image.open(image_path)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    return img_byte_arr.getvalue()

# Query Hugging Face API with retry logic
def query_hugging_face(image_path):
    max_attempts = 3
    delay_seconds = 2
    
    image_data = image_to_bytes(image_path)
    for attempt in range(max_attempts):
        response = requests.post(HF_API_URL, headers=headers, data=image_data)
        if response.status_code == 200:
            result = json.loads(response.content)
            return [d for d in result if d["label"] in ["person", "car"]]
        else:
            print "HF API Error on attempt %d: %d - %s" % (attempt + 1, response.status_code, response.text)
            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)
    print "Failed to get valid response from Hugging Face after %d attempts" % max_attempts
    return []

# Draw rectangles on image (single-pixel outline for Python 2.7)
def annotate_image(image_path, detections):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    for detection in detections:
        box = detection["box"]
        draw.rectangle(
            [(box["xmin"], box["ymin"]), (box["xmax"], box["ymax"])],
            outline="red"
        )
        draw.text((box["xmin"], box["ymin"] - 10), detection["label"], fill="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    return img_byte_arr.getvalue()

# Send image via Telegram
def send_telegram_photo(photo_bytes, caption):
    files = {"photo": ("snapshot.jpg", photo_bytes, "image/jpeg")}
    payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    response = requests.post(TELEGRAM_API_URL, data=payload, files=files)
    if response.status_code == 200:
        print "Image sent successfully!"
    else:
        print "Telegram error: %d - %s" % (response.status_code, response.text)

# Get the latest .jpg file from the camera's dated directory
def get_latest_image(camera_id):
    # Use current date (e.g., 2025-03-31)
    today = time.strftime("%Y-%m-%d")
    snapshot_dir = os.path.join(MOTION_BASE_DIR, camera_id, today)
    
    if not os.path.exists(snapshot_dir):
        print "Snapshot directory %s not found" % snapshot_dir
        return None
    
    # List all .jpg files and sort by modification time
    jpg_files = [f for f in os.listdir(snapshot_dir) if f.endswith(".jpg")]
    if not jpg_files:
        print "No .jpg files found in %s" % snapshot_dir
        return None
    
    latest_file = max(jpg_files, key=lambda f: os.path.getmtime(os.path.join(snapshot_dir, f)))
    return os.path.join(snapshot_dir, latest_file)

# Flask route for MotionEye webhook with query parameter
@app.route('/motion_detected', methods=['POST', 'GET'])
def motion_detected():
    # Get camera ID from query parameter (e.g., ?camera=Camera4)
    camera_id = request.args.get("camera", "Camera1")  # Default to Camera1
    timestamp = time.ctime()
    
    # Get the latest image for the camera
    snapshot_path = get_latest_image(camera_id)
    
    if not snapshot_path:
        print "No snapshot available for %s" % camera_id
        return "No snapshot available for %s" % camera_id, 404
    
    print "Processing snapshot: %s" % snapshot_path
    
    # Detect objects with Hugging Face
    detections = query_hugging_face(snapshot_path)
    
    if detections:
        # Annotate image with detections
        annotated_image = annotate_image(snapshot_path, detections)
        labels = ", ".join([d["label"] for d in detections])
        caption = "Motion on %s at %s: %s" % (camera_id, timestamp, labels)
        send_telegram_photo(annotated_image, caption)
        print "Sent notification for %s on %s" % (labels, camera_id)
    else:
        print "No person or car detected on %s" % camera_id
    
    return "OK", 200

if __name__ == "__main__":
    if not os.path.exists(MOTION_BASE_DIR):
        print "Error: MotionEye base directory %s not found." % MOTION_BASE_DIR
    else:
        app.run(host="0.0.0.0", port=5000)
