# Use official Python 3.11 image (or 3.14 if available)
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    wget \
    unzip \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy bot code
COPY . .

# Set environment variables (optional, can also set in Render)
# ENV TELEGRAM_BOT_TOKEN=your_bot_token_here

# Run bot
CMD ["python", "bot.py"]
