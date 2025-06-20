FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 libasound2 libxcomposite1 libxrandr2 libgbm1 libgtk-3-0 wget curl fonts-liberation libappindicator3-1 xdg-utils lsb-release

RUN python -m playwright install --with-deps

CMD ["python", "app.py"]