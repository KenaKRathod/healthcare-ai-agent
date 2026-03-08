# Healthcare AI Agent 🩺🤖

A simple AI-powered healthcare assistant that helps users track medications and receive basic health guidance.

## Features

* 💊 Medication reminder system
* 📊 Health data storage using SQLite
* 🤖 Basic health chatbot
* 🌐 Streamlit web interface

## Tech Stack

* Python
* Streamlit
* SQLite
* Pandas
* LangChain

## Project Structure

```
healthcare-ai-agent
│
└── backend
    │
    ├── app.py
    ├── chatbot.py
    ├── database.py
    ├── requirements.txt
    │
    └── data
```

## How to Run

1. Install dependencies

```
pip install -r requirements.txt
```

2. Run the app

```
streamlit run app.py
```

3. Open in browser

```
http://localhost:8501
```

## Demo

The system allows users to:

* Add medication reminders
* View scheduled medications
* Ask basic health-related questions to the chatbot

## Future Improvements

* AI-based symptom analysis
* Smart medication alerts
* Health analytics dashboard
* Integration with wearable health devices
