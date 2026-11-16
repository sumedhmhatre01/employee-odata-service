# Employee Management OData V2-Compatible API

A learning project built with Python, FastAPI, and JSON file storage. It
exposes employee CRUD endpoints using a **limited OData V2-compatible
interface** for SAP Cloud Integration (SAP CPI) practice.

> **Important:** This is not a fully OData V2 specification-compliant
> service. Validate compatibility with the SAP CPI OData V2 adapter
> before using it in an integration flow.

## Features

-   Retrieve all employees or one employee by ID.
-   Create, update, and delete employees.
-   Update salary using PATCH.
-   Filter employees by department.
-   API-key authentication for employee operations.
-   OData-style metadata and error responses.

## Technology

-   Python 3.12
-   FastAPI and Uvicorn
-   Pydantic
-   JSON file storage
-   python-dotenv
-   Render deployment

## Project structure

``` text
employee-odata-service/
├── app/
│   ├── main.py
│   ├── models/employee.py
│   ├── routes/employee_routes.py
│   ├── services/employee_service.py
│   ├── storage/employee_repository.py
│   └── utils/
│       ├── odata_response.py
│       └── odata_metadata.py
├── data/employees.json
├── requirements.txt
├── render.yaml
├── .env                 # Local secrets; do not commit
├── .gitignore
└── README.md
```

## Employee model

  Field          Type     Description
  -------------- -------- ----------------------------
  `EmployeeID`   String   Unique employee identifier
  `Name`         String   Employee name
  `Department`   String   Employee department
  `Salary`       Number   Employee salary

Example:

``` json
{
  "EmployeeID": "EMP1001",
  "Name": "Rahul",
  "Department": "IT",
  "Salary": 45000
}
```

## Deployed service

Base URL: https://employee-odata-service.onrender.com

Public endpoints:

  Method   Endpoint                Purpose
  -------- ----------------------- ------------------
  GET      `/`                     Service status
  GET      `/health`               Health check
  GET      `/odata/v2/`            Service document
  GET      `/odata/v2/$metadata`   Metadata XML

Employee endpoints require the API key.

## Authentication

Send this header with every employee CRUD request:

``` http
X-API-Key: YOUR_API_KEY
```

For JSON requests, also send:

``` http
Content-Type: application/json
Accept: application/json
```

The key is read from the `API_KEY` environment variable. Configure it in
Render's environment variables. For local development, create a `.env`
file:

``` env
API_KEY=replace_with_a_long_random_secret
```

Never commit `.env` or publish your API key. The home, health,
service-document, and metadata endpoints are public; employee CRUD
endpoints are protected.

## CRUD endpoints

All employee endpoints use the `/odata/v2` prefix.

  --------------------------------------------------------------------------------------------------
  Operation               Method                  Endpoint
  ----------------------- ----------------------- --------------------------------------------------
  Get all employees       GET                     `/odata/v2/Employees`

  Get employee by ID      GET                     `/odata/v2/Employees('EMP1001')`

  Create employee         POST                    `/odata/v2/Employees`

  Replace employee        PUT                     `/odata/v2/Employees('EMP1001')`
  details                                         

  Update salary           PATCH                   `/odata/v2/Employees('EMP1001')`

  Delete employee         DELETE                  `/odata/v2/Employees('EMP1001')`

  Filter by department    GET                     `/odata/v2/Employees?$filter=Department eq 'IT'`
  --------------------------------------------------------------------------------------------------

Replace `EMP1001` with the required employee ID.

### GET -- All employees

``` http
GET https://employee-odata-service.onrender.com/odata/v2/Employees
X-API-Key: YOUR_API_KEY
Accept: application/json
```

The collection response uses an OData-style `d.results` structure.

### GET -- One employee

``` http
GET https://employee-odata-service.onrender.com/odata/v2/Employees('EMP1001')
X-API-Key: YOUR_API_KEY
Accept: application/json
```

### POST -- Create employee

``` http
POST https://employee-odata-service.onrender.com/odata/v2/Employees
X-API-Key: YOUR_API_KEY
Content-Type: application/json
Accept: application/json
```

Body:

``` json
{
  "EmployeeID": "EMP1014",
  "Name": "Vikram",
  "Department": "IT",
  "Salary": 72000
}
```

Success returns `201 Created`. A duplicate EmployeeID returns
`409 Conflict`.

### PUT -- Update employee details

PUT requires all editable fields:

``` http
PUT https://employee-odata-service.onrender.com/odata/v2/Employees('EMP1014')
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

Body:

``` json
{
  "Name": "Vikram Patil",
  "Department": "Finance",
  "Salary": 75000
}
```

### PATCH -- Update salary

PATCH supports the Salary field:

``` http
PATCH https://employee-odata-service.onrender.com/odata/v2/Employees('EMP1014')
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

Body:

``` json
{
  "Salary": 80000
}
```

### DELETE -- Delete employee

``` http
DELETE https://employee-odata-service.onrender.com/odata/v2/Employees('EMP1014')
X-API-Key: YOUR_API_KEY
```

Success returns `204 No Content`.

### GET with filter -- IT employees

``` http
GET https://employee-odata-service.onrender.com/odata/v2/Employees?$filter=Department%20eq%20'IT'
X-API-Key: YOUR_API_KEY
Accept: application/json
```

The implemented filter supports the `Department eq 'value'` equality
pattern only. It does not implement the complete OData `$filter`
language.

## Error handling

  HTTP status   Meaning
  ------------- ----------------------------------------------------------------
  400           Invalid request data or unsupported/invalid DataServiceVersion
  401           Missing or invalid API key
  404           Employee not found
  409           Duplicate EmployeeID
  201           Employee created
  204           Employee deleted

Example error response:

``` json
{
  "error": {
    "code": "404",
    "message": {
      "lang": "en-US",
      "value": "Employee EMP9999 not found."
    }
  }
}
```

## Run locally

### 1. Clone the repository

``` bash
git clone https://github.com/sumedhmhatre01/employee-odata-service.git
cd employee-odata-service
```

### 2. Create and activate a virtual environment

Windows PowerShell:

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Git Bash:

``` bash
python -m venv venv
source venv/Scripts/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Create `.env`

``` env
API_KEY=replace_with_a_long_random_secret
```

### 5. Start the application

``` bash
python -m uvicorn app.main:app --reload
```

Local URLs:

-   Home: http://127.0.0.1:8000/
-   Health: http://127.0.0.1:8000/health
-   Swagger UI: http://127.0.0.1:8000/docs
-   Service document: http://127.0.0.1:8000/odata/v2/
-   Metadata: http://127.0.0.1:8000/odata/v2/\$metadata

In Swagger UI, use **Authorize** and enter the API key to call protected
employee endpoints.

## SAP CPI practice

The API is intended for practicing HTTP-to-OData integration concepts:

-   HTTP sender and receiver connectivity.
-   Sending the `X-API-Key` header.
-   CRUD methods and resource paths.
-   Department filtering with a query parameter.
-   Handling HTTP status codes and OData-style error payloads.

Because this is a simplified OData implementation, confirm that its
metadata, JSON payloads, filtering, and supported operations meet the
SAP CPI OData V2 adapter's expectations. If not, use an HTTP receiver
approach or extend the service.

## Storage and deployment limitations

Employee records are stored in a JSON file. This is suitable for
learning and local testing, not production use.

**Render Free services have an ephemeral filesystem.** Data written to
the JSON file may be lost when the service restarts, redeploys, or is
replaced. Do not rely on the deployed free service for durable employee
data. Recreate test records when needed, or use persistent storage for
data that must survive restarts.

The repository uses in-process locking for file operations; it is not
designed as a distributed or multi-instance data store.

## Security notes

-   Keep API keys in environment variables or a secret manager.
-   Never commit `.env`.
-   Use HTTPS for deployed API calls.
-   Do not log or share API keys.
-   This is a practice project, not a production-hardened employee
    system.

## License

Add a license before redistributing or reusing this project publicly.
