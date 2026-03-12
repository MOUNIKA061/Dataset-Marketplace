# Dataset Marketplace

A **cloud-based dataset marketplace** that allows users to upload, search, download, and visualize datasets.
The platform integrates **Flask APIs, MySQL database, AWS S3 storage, and interactive data visualization**.

Users can explore datasets, view statistics through charts, and receive simple **AI-based dataset recommendations** based on tag similarity.

---

# Features

### User Authentication

* Register and login system
* Role-based access control ( Owner / User)

<img width="2624" height="1497" alt="image" src="https://github.com/user-attachments/assets/12884dcd-aa6a-4447-8a1f-f9635405c585" />


### Dataset Upload

* Upload CSV or JSON datasets
* Files stored securely in **AWS S3**
* Metadata stored in **MySQL database**

<img width="2699" height="1511" alt="image" src="https://github.com/user-attachments/assets/3c1bf27c-45d1-4160-9a85-ae000c5020c0" />


### Search & Filtering

* Search datasets using **tags and keywords**
* Dataset listing with preview information

### AI Dataset Recommendations

* Suggests related datasets based on **tag similarity**

<img width="2618" height="1500" alt="image" src="https://github.com/user-attachments/assets/5bec0966-74fd-4446-897c-e6c019d34f4d" />


### Dataset Visualization

* Interactive charts using **Chart.js**
* Dataset statistics such as:

  * Mean
  * Median
  * Minimum
  * Maximum
 
  ### Download Analytics

* Tracks dataset downloads
* Admin dashboard showing popular datasets

---

 <img width="2454" height="1484" alt="image" src="https://github.com/user-attachments/assets/5b72f840-7d90-4c3a-af3f-2cc7dcf743c9" />
 <img width="2268" height="1504" alt="image" src="https://github.com/user-attachments/assets/7f15916a-333a-40c9-b966-10963c7a2f71" />



# Tech Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

## Backend

* Python
* Flask REST API

## Database

* MySQL

## Cloud

* AWS S3 (dataset storage)
* AWS RDS (optional MySQL hosting)

## Other

* JWT Authentication
* REST APIs

---

# Project Architecture

```
User (Browser)
      │
      ▼
Frontend (HTML / CSS / JS)
      │
      ▼
Flask Backend API
      │
 ┌────┴───────────┐
 ▼                ▼
MySQL          AWS S3
Metadata       Dataset Files
```

---

# Project Structure

```
dataset-marketplace/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── auth.py
│   ├── models.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── dataset_routes.py
│   │   └── analytics_routes.py
│   └── services/
│       ├── s3_service.py
│       ├── recommendation_service.py
│       └── stats_service.py
│
├── database/
│   └── schema.sql
│
├── frontend/
│   ├── index.html
│   ├── upload.html
│   ├── search.html
│   ├── dataset.html
│   ├── admin.html
│   ├── register.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── api.js
│       ├── auth.js
│       ├── search.js
│       ├── upload.js
│       ├── dataset.js
│       └── admin.js
│
└── README.md
```

---

# Example Datasets

Example datasets for testing the platform:

* `sales_data.csv` – monthly product sales
* `weather_data.json` – temperature and humidity records
* `student_scores.csv` – exam performance dataset

These datasets can be uploaded and visualized inside the application.

---

# How the System Works

1. User registers or logs into the system.
2. User uploads a dataset (CSV or JSON).
3. Dataset file is stored in **AWS S3**.
4. Dataset metadata is saved in **MySQL**.
5. Users search datasets using tags.
6. Platform recommends related datasets.
7. Dataset statistics are visualized using charts.

---

# Local Development Setup

## 1. Clone the Repository

```
git clone https://github.com/your-username/dataset-marketplace.git
cd dataset-marketplace
```

---

## 2. Create Python Virtual Environment

```
python -m venv venv
```

Activate environment

Windows

```
venv\Scripts\activate
```

Linux / macOS

```
source venv/bin/activate
```

Install dependencies

```
pip install -r backend/requirements.txt
```

---

# Database Setup

Create database in MySQL

```
CREATE DATABASE dataset_marketplace;
USE dataset_marketplace;
SOURCE database/schema.sql;
```

---

# Running the Backend

```
cd backend
python app.py
```

Backend runs at:

```
http://localhost:5000
```

---

# Running the Frontend

```
cd frontend
python -m http.server 8080
```

Open browser

```
http://localhost:8080
```

---

# AWS S3 Setup

1. Create an S3 bucket
2. Create IAM user with S3 access
3. Add credentials in `.env`

Example `.env` file

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=dataset-marketplace
```

---

# API Endpoints

### Authentication

| Method | Endpoint      | Description   |
| ------ | ------------- | ------------- |
| POST   | /api/register | Register user |
| POST   | /api/login    | Login         |

### Dataset

| Method | Endpoint             | Description        |
| ------ | -------------------- | ------------------ |
| POST   | /api/upload-dataset  | Upload dataset     |
| GET    | /api/search-datasets | Search datasets    |
| GET    | /api/download/<id>   | Download dataset   |
| GET    | /api/visualize/<id>  | Dataset statistics |

### Recommendations

| Method | Endpoint             | Description                |
| ------ | -------------------- | -------------------------- |
| GET    | /api/recommendations | AI dataset recommendations |

### Analytics

| Method | Endpoint       | Description     |
| ------ | -------------- | --------------- |
| GET    | /api/analytics | Admin analytics |

---

# Free Tier Limits (AWS)

To avoid costs:

* **S3 Storage:** 5GB
* **RDS Storage:** 20GB
* **EC2 usage:** 750 hours/month

Recommended dataset size:

```
< 5 MB per dataset
```

---

# Future Improvements

* Dataset rating system
* Dataset commenting system
* Advanced ML recommendations
* Public dataset sharing
* Dataset versioning

---

# License

MIT License

---

# Author

Built as a **full-stack cloud project for learning and portfolio purposes.**
