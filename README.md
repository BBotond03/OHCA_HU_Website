# 🩺 OHCA Prediction Dashboard — Hungary

An interactive web dashboard for visualizing predicted Out-of-Hospital Cardiac Arrest (OHCA) cases across the counties of Hungary. This application uses a machine learning model (served via a separate backend) to provide daily predictions and displays them on a color-coded, interactive map.

## 📸 Preview

*(You should replace this with a screenshot or GIF of your running application)*




## ✨ Features

-   **Interactive Map**: A map of Hungary divided by counties, built with Folium.
-   **Risk-Level Coloring**: Counties are color-coded (green, orange, red) based on the predicted number of OHCA cases, indicating low, moderate, or high risk.
-   **Detailed Sidebar**: Clicking on a county highlights it and displays detailed information in the sidebar, including:
    -   Weather data (Temperature, Humidity)
    -   Case statistics (Yesterday's cases, Predicted cases)
    -   Predicted mortality rate
-   **Dynamic Data Fetching**: The dashboard fetches the latest predictions from a backend API on startup or when the "Refresh" button is clicked.
-   **Responsive Layout**: The `layout="wide"` setting in Streamlit provides a good user experience on larger screens.

## 🏗️ Architecture & Tech Stack

This project consists of a frontend dashboard that communicates with a backend prediction service.

-   **Frontend (This Repository)**:
    -   **Framework**: [Streamlit](https://streamlit.io/)
    -   **Mapping**: [Folium](https://python-visualization.github.io/folium/) & [Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium)
    -   **Geospatial**: [Shapely](https://shapely.readthedocs.io/) for point-in-polygon checks.
    -   **HTTP Requests**: [Requests](https://requests.readthedocs.io/)
    -   **Environment Management**: [python-dotenv](https://pypi.org/project/python-dotenv/)

-   **Backend**:
    -   The application is designed to connect to a REST API (e.g., built with FastAPI, Flask).
    -   This backend is responsible for running the ML model, fetching weather data, and serving the predictions via an endpoint.

## 🚀 Getting Started

Follow these instructions to set up and run the dashboard on your local machine.

### Prerequisites

-   Python 3.8+
-   A running instance of the backend prediction service.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ohca-dashboard.git
cd ohca-dashboard
```

### 2. Set Up the Backend

This dashboard requires a separate backend service. The backend must expose a `GET` endpoint that returns a JSON array of objects, where each object has the following structure:

**Expected Endpoint:** `/predict_all`

**Expected JSON Response:**
```json
[
  {
    "county": "Bács-Kiskun",
    "prediction": {
      "predicted_cases": 55,
      "yesterday_cases": 52,
      "mortality_rate": 0.91
    },
    "weather": {
      "temperature": 15.4,
      "humidity": 78
    }
  },
  {
    "county": "Pest",
    "prediction": { "...etc" },
    "weather": { "...etc" }
  }
]
```

### 3. Set Up the Frontend

**A. Create a Virtual Environment**

It's highly recommended to use a virtual environment.

```bash
# For Unix/macOS
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\\venv\\Scripts\\activate
```

**B. Install Dependencies**

Create a `requirements.txt` file with the following content:

```txt
streamlit
folium
streamlit-folium
requests
python-dotenv
shapely
```

Then, install the packages:

```bash
pip install -r requirements.txt
```

**C. Configure Environment Variables**

Create a file named `.env` in the root directory of the project. This file will hold the URL for your backend.

```
# .env
BACKEND_URL="http://127.0.0.1:8000/predict_all"
```
Update the URL if your backend is running on a different address or port.

**D. Ensure GeoJSON Data is Present**

The map requires a GeoJSON file defining the county boundaries. Make sure `hu.json` is located in a `data/` directory: `./data/hu.json`.

### 4. Run the Application

Once your backend service is running, start the Streamlit dashboard with the following command:

```bash
streamlit run app.py
```

Open your web browser and navigate to `http://localhost:8501`.

## 📂 Project Structure

```
.
├── data/
│   └── hu.json           # GeoJSON file with county boundaries
├── .env                  # Environment variables (backend URL)
├── .gitignore            # Standard Python gitignore
├── app.py                # The main Streamlit application script
├── README.md             # You are here!
└── requirements.txt      # Python dependencies
```

## 📜 License

This project is licensed under the MIT License.