

### Quantum Job Tracker

-----

### **Overview**

The Quantum Job Tracker is a web application designed to help users and researchers manage and monitor their quantum computing jobs on the IBM Quantum Platform. The platform provides a professional dashboard with real-time insights, analytics, and powerful features to streamline the quantum workflow.

-----

### **Features**

  * **Real-time Job Tracking**: The application allows you to monitor the status of your quantum jobs with live updates on completion, running, and queued tasks.
  * **User & Researcher Modes**: It offers different levels of access, with a personalized dashboard for regular users and aggregated data for researchers.
  * **Backend Heatmap**: This feature visualizes the real-time status and load of all available IBM Quantum backends.
  * **Smart Notifications**: Users receive instant alerts on job status changes, such as completion or failure.
  * **Quantum Failure Doctor**: A diagnostic tool that analyzes job failures and provides actionable recommendations to fix common issues.
  * **Time Predictor**: Get an estimated start and completion time for your queued or running jobs.
  * **Backend Comparator**: This feature compares different quantum backends based on key metrics like pending jobs, error rates, and uptime.
  * **Chat Assistant**: A simple, rule-based chatbot answers common questions about backends, job status, and quantum computing.
  * **User Leaderboard**: A gamified feature that ranks users based on their job activity.

-----

### **Project Structure**

The project structure is organized to separate the frontend, backend, and documentation. The `.venv` and `__pycache__` folders are intentionally not tracked by version control, as they contain temporary and environment-specific files.

```
quantum-job-tracker/
├── .venv/
├── __pycache__/
├── frontend/
│   └── final.html
├── backend/
│   ├── main.py
│   ├── requirements.txt
└── README.md
```

  * **`frontend/`**: Contains the single-page web application (`final.html`) built with HTML, CSS, and JavaScript. It handles the user interface and communicates with the backend API.
  * **`backend/`**: This directory houses the FastAPI server (`main.py`) and a `requirements.txt` file listing all necessary Python packages. This is the core logic that connects to the IBM Quantum Platform to process requests and provide data to the frontend.
  * **`.venv`**: This directory is where your Python virtual environment is stored. A virtual environment isolates the Python packages required for your project from other projects. It contains a Python interpreter and the specific libraries (like FastAPI and Qiskit) listed in your `requirements.txt` file. You should never commit this folder to your Git repository. To prevent this, add `.venv/` to your `.gitignore` file.
  * **`__pycache__`**: This folder is automatically created by the Python interpreter to store compiled bytecode files with a `.pyc` extension. These files help Python run faster by skipping the compilation step on subsequent runs. Since these are temporary, generated files, you should also add `__pycache__/` to your `.gitignore` file to keep your repository clean.
 * **`README.md`**: The file you're currently reading.
-----

### **Getting Started**

Follow these steps to set up and run the project locally.

#### **Prerequisites**

  * **Python 3.8+**: Ensure you have a compatible version of Python installed.
  * **IBM Quantum Account**: You'll need an IBM Quantum account with an API key and an instance URL to connect to the service.

#### **Backend Setup**

1.  Navigate to the `backend/` directory in your terminal.
    `cd backend/`
2.  Install the required Python packages from `requirements.txt`.
    `pip install -r requirements.txt`
3.  Open `main.py` and replace the placeholder API keys and instance URLs with your own.
4.  Run the FastAPI server.
    `uvicorn main:app --reload`
    The server will start at `http://localhost:8000`.

#### **Frontend Setup**

The frontend is a static HTML file and does not require a dedicated server.

1.  Navigate to the `frontend/` directory.
2.  Open the `final.html` file in your preferred web browser (e.g., Chrome, Firefox, Edge).
3.  The application will automatically connect to the backend running on `localhost:8000`.

-----

### **Usage**

  * **Select User Type**: On the home page, choose between `User` or `Researcher` mode.
  * **Connect**: As a user, select your name from the dropdown. As a researcher, click "Access Research Dashboard".
  * **Explore**: Once connected, you can explore the dashboard's features for monitoring your quantum jobs.

-----

### **Acknowledgments**

  * **Qiskit IBM Runtime**: The project is built on the Qiskit SDK to interact with the IBM Quantum Platform.
  * **FastAPI**: Used for building the efficient and robust backend API.
  * **Chart.js**: Utilized for creating data visualizations in the dashboard.