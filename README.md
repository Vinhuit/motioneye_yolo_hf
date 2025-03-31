# MotionEye Telegram Notifier

This project integrates [MotionEye](https://github.com/ccrisan/motioneye) with Telegram notifications, using the Hugging Face YOLOS model to detect "person" and "car" objects in snapshots. When motion is detected, it processes the latest `.jpg` image from a specified camera (e.g., `Camera4`), annotates detected objects with red rectangles, and sends the result to a Telegram chat.

Designed for low-resource devices like the Allwinner H616 (2GB RAM) running Python 2.7, this script uses a Flask webhook to handle MotionEye events and includes a lightweight health check endpoint.

## Features
- **Webhook Trigger**: Responds to MotionEye motion events (e.g., `http://<ip>:5000/motion_detected?camera=Camera4`).
- **Object Detection**: Uses Hugging Face YOLOS (`hustvl/yolos-base`) with retry logic for reliability.
- **Image Annotation**: Draws single-pixel red rectangles around detected "person" and "car" objects (Python 2.7 compatibility).
- **Telegram Alerts**: Sends annotated images to a specified Telegram chat.
- **Lightweight Health Check**: Handles `/api/stats` requests from MotionEye with minimal overhead.

## Requirements
- **Hardware**: Allwinner H616 or similar (2GB RAM recommended).
- **OS**: Debian/Armbian with Python 2.7.
- **Dependencies**:
  - `flask==0.12.2`
  - `requests==2.18.4`
  - `pillow==5.4.1`
  - MotionEye 0.42.1 (Python 2.7 compatible).
- **Network**: Internet access for Hugging Face API and Telegram.
- **Credentials**:
  - Telegram Bot Token and Chat ID.
  - Hugging Face API Token.
Replace **TELEGRAM_TOKEN** with your bot token.
Replace **TELEGRAM_CHAT_ID** with your chat ID.
Replace **HF_API_TOKEN** with your Hugging Face token.
Adjust **MOTION_BASE_DIR** if MotionEye uses a different path (default: `/var/lib/motion



