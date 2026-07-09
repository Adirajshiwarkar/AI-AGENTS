import os
import sys
import warnings
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient


# Ensure current directory is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils.logger import logger

client = TestClient(app)

def test_example_1_chatbot():
    logger.info("=========================================")
    logger.info("TESTING EXAMPLE 1: AI Chatbot Proposal")
    logger.info("=========================================")
    
    payload = {
        "request": "Generate a project proposal for implementing an AI chatbot for customer support."
    }
    
    response = client.post("/agent", json=payload)
    
    logger.info(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    logger.info(f"Response JSON keys: {list(data.keys())}")
    logger.info(f"Execution Time: {data.get('execution_time')}")
    logger.info(f"Document Saved At: {data.get('document_path')}")
    
    # Assertions
    assert data["status"] == "success"
    assert "summary" in data
    assert len(data["execution_plan"]) > 0
    assert len(data["completed_tasks"]) > 0
    assert len(data["assumptions"]) > 0
    assert "reflection_result" in data
    assert os.path.exists(data["document_path"])
    assert os.path.getsize(data["document_path"]) > 0
    logger.info("Example 1 passed successfully.\n")


def test_example_2_erp_migration():
    logger.info("=========================================")
    logger.info("TESTING EXAMPLE 2: ERP Legacy Migration")
    logger.info("=========================================")
    
    payload = {
        "request": "We need a technical implementation plan for migrating our legacy monolithic ERP to microservices in six months with a small engineering team and uncertain budget. Make reasonable assumptions."
    }
    
    response = client.post("/agent", json=payload)
    
    logger.info(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    logger.info(f"Response JSON keys: {list(data.keys())}")
    logger.info(f"Execution Time: {data.get('execution_time')}")
    logger.info(f"Document Saved At: {data.get('document_path')}")
    logger.info(f"Generated Assumptions: {data.get('assumptions')}")
    
    # Assertions
    assert data["status"] == "success"
    assert len(data["assumptions"]) > 0
    assert os.path.exists(data["document_path"])
    assert os.path.getsize(data["document_path"]) > 0
    logger.info("Example 2 passed successfully.\n")


def test_validation_errors():
    logger.info("=========================================")
    logger.info("TESTING VALIDATION RULES")
    logger.info("=========================================")
    
    # Test Empty request
    payload_empty = {"request": ""}
    res_empty = client.post("/agent", json=payload_empty)
    logger.info(f"Empty request status (expected 422): {res_empty.status_code}")
    assert res_empty.status_code == 422
    
    # Test Short request
    payload_short = {"request": "short"}
    res_short = client.post("/agent", json=payload_short)
    logger.info(f"Short request status (expected 422): {res_short.status_code}")
    assert res_short.status_code == 422
    logger.info("Validation tests passed successfully.\n")


if __name__ == "__main__":
    try:
        test_validation_errors()
        test_example_1_chatbot()
        test_example_2_erp_migration()
        logger.info("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        logger.error(f"Test Assertion Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test Error: {e}", exc_info=True)
        sys.exit(1)
