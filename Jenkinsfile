pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run Containers') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Continue"
                    docker rm -f inventory-mongodb inventory-api inventory-prometheus inventory-grafana 2>$null
                    docker builder prune -f 2>$null
                    docker compose build --no-cache
                    docker compose up -d
                '''
            }
        }

        stage('Wait for API') {
            steps {
                powershell '''
                    Write-Host "Waiting for API to be ready..."
                    for ($i = 1; $i -le 30; $i++) {
                        try {
                            $r = Invoke-WebRequest -Uri "http://localhost:8000/getAll" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                            if ($r.StatusCode -eq 200) {
                                Write-Host "API is ready"
                                exit 0
                            }
                        } catch {}
                        Write-Host "Attempt $i - waiting 5 seconds..."
                        Start-Sleep -Seconds 5
                    }
                    Write-Host "ERROR: API did not become ready in time"
                    exit 1
                '''
            }
        }

        stage('Load Data') {
            steps {
                powershell 'docker compose exec -T api python3 scripts/load_products.py'
            }
        }

        stage('Run Newman Tests') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Continue"
                    docker run --rm --network assignment1-pipeline_default -v "${PWD}:/collection" -w /collection postman/newman run postman/Inventory_API_Tests.postman_collection.json --env-var baseUrl=http://api:8000 --reporters cli
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                '''
            }
        }

        stage('Run Python Unit Tests') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Continue"
                    docker compose exec -T api pip3 install pytest pytest-asyncio mongomock --quiet
                    docker compose exec -T api python3 -m pytest tests/ -v
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                '''
            }
        }

        stage('Create README') {
            steps {
                powershell '''
                    @"
Inventory Management API - Endpoints Reference
==============================================

Base URL: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

ENDPOINTS:
---------

1. GET /getSingleProduct
   Parameters: product_id (int, required) - Product ID number
   Returns: Single product details in JSON

2. GET /getAll
   Parameters: None
   Returns: All inventory in JSON format

3. POST /addNew
   Body (JSON): ProductID (int), Name (str), UnitPrice (float), StockQuantity (int), Description (str)
   Returns: Confirmation message

4. DELETE /deleteOne
   Parameters: product_id (int, required) - Product ID to delete
   Returns: Confirmation message

5. GET /startsWith
   Parameters: letter (str, required) - Single letter (e.g. "s")
   Returns: Products whose names start with the letter

6. GET /paginate
   Parameters: start_id (int), end_id (int) - Product ID range
   Returns: Batch of up to 10 products in range

7. GET /convert
   Parameters: product_id (int, required) - Product ID
   Returns: Price in EUR (uses live exchange rate API)

8. GET /metrics
   Parameters: None
   Returns: Prometheus metrics for API monitoring

FastAPI Documentation: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
"@ | Out-File -FilePath README.txt -Encoding utf8
                '''
            }
        }

        stage('Stop Containers') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Continue"
                    docker compose down
                '''
            }
        }

        stage('Create Zip') {
            steps {
                powershell '''
                    $timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
                    $zipName = "complete-$timestamp.zip"
                    $items = @("app", "scripts", "tests", "postman", "products.csv", "requirements.txt", "Dockerfile", "docker-compose.yml", "prometheus.yml", "Jenkinsfile", "README.txt")
                    Compress-Archive -Path $items -DestinationPath $zipName -Force
                    Write-Host "Created $zipName"
                '''
                archiveArtifacts artifacts: 'complete-*.zip', fingerprint: true
            }
        }
    }

    post {
        always {
            powershell '''
                $ErrorActionPreference = "Continue"
                docker compose down 2>$null
            '''
        }
    }
}
