# Use Playwright official Python image (has browser & deps installed)
FROM mcr.microsoft.com/playwright/python:v1.35.0-focal

# Set working directory inside the container
WORKDIR /app

# Copy all your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install

# Default command to run your bot
CMD ["python", "bot.py"]
