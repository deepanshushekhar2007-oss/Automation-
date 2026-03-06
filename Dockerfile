# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
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

# Copy requirements.txt first (Docker layer caching)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with dependencies
RUN playwright install --with-deps

# Copy bot code
COPY . .

# Expose port if needed (optional, for webhooks)
# EXPOSE 8080

# Set environment variables (can also set in Render)
# ENV TELEGRAM_BOT_TOKEN=your_bot_token_here

# Run the bot
CMD ["python", "bot.py"]
