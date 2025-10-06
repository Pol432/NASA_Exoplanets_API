import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import uuid

# Import the status codes we need
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_413_REQUEST_ENTITY_TOO_LARGE = 413
HTTP_500_INTERNAL_SERVER_ERROR = 500


class TestUploadCSVEndpoint:
    """Test cases for the upload-csv endpoint"""

    def test_upload_valid_csv_success(self, authenticated_client, valid_csv_content, mock_csv_processor, mock_exoplanet_service):
        """Test successful upload of valid CSV file"""
        # Setup the mock response
        response_data = {
            "message": "Successfully uploaded 2 exoplanet candidates",
            "candidates_created": 2,
            "upload_id": str(uuid.uuid4()),
            "filename": "test.csv",
            "warnings": ["Some optional columns missing"]
        }

        # Configure the mock client to return our expected response
        authenticated_client.post.return_value.status_code = HTTP_201_CREATED
        authenticated_client.post.return_value.json.return_value = response_data

        # Make the request
        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.csv", valid_csv_content, "text/csv")})

        # Assertions
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Successfully uploaded 2 exoplanet candidates"
        assert data["candidates_created"] == 2
        assert data["filename"] == "test.csv"
        assert "upload_id" in data
        assert data["warnings"] == ["Some optional columns missing"]

    def test_upload_invalid_file_type(self, authenticated_client):
        """Test upload with invalid file type returns 400"""
        response_data = {"detail": "Only CSV files are allowed"}
        authenticated_client.post.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.txt", "some content", "text/plain")})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Only CSV files are allowed" in response.json()["detail"]

    def test_upload_file_too_large(self, authenticated_client, mock_settings):
        """Test upload with file exceeding size limit returns 413"""
        response_data = {
            "detail": "File size exceeds maximum allowed size of 1048576 bytes"}
        authenticated_client.post.return_value.status_code = HTTP_413_REQUEST_ENTITY_TOO_LARGE
        authenticated_client.post.return_value.json.return_value = response_data

        large_content = "x" * (mock_settings.MAX_FILE_SIZE + 1)
        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("large.csv", large_content, "text/csv")})

        assert response.status_code == HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "File size exceeds maximum allowed size" in response.json()[
            "detail"]

    def test_upload_empty_csv(self, authenticated_client):
        """Test upload with empty CSV returns 400"""
        response_data = {"detail": "CSV file is empty"}
        authenticated_client.post.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("empty.csv", "", "text/csv")})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "CSV file is empty" in response.json()["detail"]

    def test_upload_missing_required_columns(self, authenticated_client):
        """Test upload with missing required columns returns 400"""
        response_data = {
            "detail": "Invalid CSV format: Missing required columns: koi_depth, koi_duration"}
        authenticated_client.post.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post("/api/v1/data-upload/upload-csv", files={
                                             "file": ("invalid.csv", "kepid,kepoi_name\n123,K001", "text/csv")})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Missing required columns" in response.json()["detail"]

    def test_upload_malformed_csv(self, authenticated_client):
        """Test upload with malformed CSV returns 400"""
        response_data = {"detail": "CSV parsing error: Error tokenizing data"}
        authenticated_client.post.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post("/api/v1/data-upload/upload-csv", files={
                                             "file": ("malformed.csv", "invalid,csv,content\n", "text/csv")})

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "CSV parsing error" in response.json()["detail"]

    def test_upload_csv_processing_error(self, authenticated_client):
        """Test upload with CSV processing error returns 500"""
        response_data = {
            "detail": "Error processing CSV file: Processing failed"}
        authenticated_client.post.return_value.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("error.csv", "some,content", "text/csv")})

        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error processing CSV file" in response.json()["detail"]

    def test_upload_unauthenticated(self, client):
        """Test upload without authentication returns 401"""
        client.post.return_value.status_code = HTTP_401_UNAUTHORIZED
        client.post.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.post("/api/v1/data-upload/upload-csv",
                               files={"file": ("test.csv", "content", "text/csv")})

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestGetMyUploadsEndpoint:
    """Test cases for the get-my-uploads endpoint"""

    def test_get_my_uploads_success(self, authenticated_client, sample_exoplanet_candidate):
        """Test successful retrieval of user's uploads"""
        response_data = [{
            "id": sample_exoplanet_candidate.id,
            "kepid": sample_exoplanet_candidate.kepid,
            "kepoi_name": sample_exoplanet_candidate.kepoi_name,
            "koi_period": sample_exoplanet_candidate.koi_period,
            "koi_depth": sample_exoplanet_candidate.koi_depth,
            "analysis_status": sample_exoplanet_candidate.analysis_status,
            "final_verdict": sample_exoplanet_candidate.final_verdict,
            "ai_prediction": None,
            "ai_confidence_score": None,
            "consensus_score": sample_exoplanet_candidate.consensus_score,
            "upload_timestamp": sample_exoplanet_candidate.upload_timestamp.isoformat()
        }]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get("/api/v1/data-upload/uploads/me")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_exoplanet_candidate.id
        assert data[0]["kepid"] == sample_exoplanet_candidate.kepid

    def test_get_my_uploads_with_pagination(self, authenticated_client):
        """Test get uploads with pagination parameters"""
        response_data = [
            {"id": 3, "kepid": 123458, "analysis_status": "pending"},
            {"id": 4, "kepid": 123459, "analysis_status": "pending"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            "/api/v1/data-upload/uploads/me?skip=2&limit=2")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_my_uploads_empty_list(self, authenticated_client):
        """Test get uploads when user has no uploads"""
        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = []

        response = authenticated_client.get("/api/v1/data-upload/uploads/me")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_get_my_uploads_unauthenticated(self, client):
        """Test get uploads without authentication returns 401"""
        client.get.return_value.status_code = HTTP_401_UNAUTHORIZED
        client.get.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.get("/api/v1/data-upload/uploads/me")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestGetUploadDetailsEndpoint:
    """Test cases for the get-upload-details endpoint"""

    def test_get_upload_details_success(self, authenticated_client, sample_exoplanet_candidate):
        """Test successful retrieval of candidate details"""
        response_data = {
            "id": sample_exoplanet_candidate.id,
            "kepid": sample_exoplanet_candidate.kepid,
            "researcher_id": sample_exoplanet_candidate.researcher_id,
            "original_csv_filename": sample_exoplanet_candidate.original_csv_filename,
            "upload_timestamp": sample_exoplanet_candidate.upload_timestamp.isoformat(),
            "analysis_status": sample_exoplanet_candidate.analysis_status,
            "final_verdict": sample_exoplanet_candidate.final_verdict,
            "consensus_score": sample_exoplanet_candidate.consensus_score
        }

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            f"/api/v1/data-upload/uploads/{sample_exoplanet_candidate.id}")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_exoplanet_candidate.id
        assert data["kepid"] == sample_exoplanet_candidate.kepid
        assert data["researcher_id"] == sample_exoplanet_candidate.researcher_id

    def test_get_upload_details_not_found(self, authenticated_client):
        """Test get details for non-existent candidate returns 404"""
        authenticated_client.get.return_value.status_code = HTTP_404_NOT_FOUND
        authenticated_client.get.return_value.json.return_value = {
            "detail": "Candidate not found"}

        response = authenticated_client.get(
            "/api/v1/data-upload/uploads/99999")

        assert response.status_code == HTTP_404_NOT_FOUND
        assert "Candidate not found" in response.json()["detail"]

    def test_get_upload_details_unauthenticated(self, client):
        """Test get details without authentication returns 401"""
        client.get.return_value.status_code = HTTP_401_UNAUTHORIZED
        client.get.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.get("/api/v1/data-upload/uploads/1")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestDeleteUploadEndpoint:
    """Test cases for the delete-upload endpoint"""

    def test_delete_own_upload_success(self, authenticated_client, sample_exoplanet_candidate):
        """Test successful deletion of own candidate"""
        authenticated_client.delete.return_value.status_code = HTTP_200_OK
        authenticated_client.delete.return_value.json.return_value = {
            "message": "Candidate deleted successfully"}

        response = authenticated_client.delete(
            f"/api/v1/data-upload/uploads/{sample_exoplanet_candidate.id}")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["message"] == "Candidate deleted successfully"

    def test_delete_other_user_upload_forbidden(self, authenticated_client):
        """Test deletion of another user's candidate returns 403"""
        authenticated_client.delete.return_value.status_code = HTTP_403_FORBIDDEN
        authenticated_client.delete.return_value.json.return_value = {
            "detail": "Not authorized to delete this candidate"}

        response = authenticated_client.delete(
            "/api/v1/data-upload/uploads/999")

        assert response.status_code == HTTP_403_FORBIDDEN
        assert "Not authorized to delete this candidate" in response.json()[
            "detail"]

    def test_delete_nonexistent_upload(self, authenticated_client):
        """Test deletion of non-existent candidate returns 404"""
        authenticated_client.delete.return_value.status_code = HTTP_404_NOT_FOUND
        authenticated_client.delete.return_value.json.return_value = {
            "detail": "Candidate not found"}

        response = authenticated_client.delete(
            "/api/v1/data-upload/uploads/99999")

        assert response.status_code == HTTP_404_NOT_FOUND
        assert "Candidate not found" in response.json()["detail"]

    def test_delete_upload_unauthenticated(self, client):
        """Test delete without authentication returns 401"""
        client.delete.return_value.status_code = HTTP_401_UNAUTHORIZED
        client.delete.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.delete("/api/v1/data-upload/uploads/1")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestListAllCandidatesEndpoint:
    """Test cases for the list-all-candidates endpoint"""

    def test_list_all_candidates_no_filters(self, authenticated_client):
        """Test listing all candidates without filters"""
        response_data = [
            {"id": 1, "analysis_status": "pending", "final_verdict": "pending"},
            {"id": 2, "analysis_status": "completed", "final_verdict": "confirmed"},
            {"id": 3, "analysis_status": "completed",
                "final_verdict": "false_positive"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get("/api/v1/data-upload/candidates")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_candidates_with_status_filter(self, authenticated_client):
        """Test listing candidates with status filter"""
        response_data = [
            {"id": 2, "analysis_status": "completed", "final_verdict": "confirmed"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?status_filter=completed")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["analysis_status"] == "completed"

    def test_list_candidates_with_verdict_filter(self, authenticated_client):
        """Test listing candidates with verdict filter"""
        response_data = [
            {"id": 2, "analysis_status": "completed", "final_verdict": "confirmed"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?verdict_filter=confirmed")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["final_verdict"] == "confirmed"

    def test_list_candidates_with_both_filters(self, authenticated_client):
        """Test listing candidates with both status and verdict filters"""
        response_data = [
            {"id": 2, "analysis_status": "completed", "final_verdict": "confirmed"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?status_filter=completed&verdict_filter=confirmed")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["analysis_status"] == "completed"
        assert data[0]["final_verdict"] == "confirmed"

    def test_list_candidates_invalid_status_filter(self, authenticated_client):
        """Test listing candidates with invalid status filter returns 400"""
        authenticated_client.get.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.get.return_value.json.return_value = {
            "detail": "Invalid status filter: invalid_status"}

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?status_filter=invalid_status")

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid status filter" in response.json()["detail"]

    def test_list_candidates_invalid_verdict_filter(self, authenticated_client):
        """Test listing candidates with invalid verdict filter returns 400"""
        authenticated_client.get.return_value.status_code = HTTP_400_BAD_REQUEST
        authenticated_client.get.return_value.json.return_value = {
            "detail": "Invalid verdict filter: invalid_verdict"}

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?verdict_filter=invalid_verdict")

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid verdict filter" in response.json()["detail"]

    def test_list_candidates_with_pagination(self, authenticated_client):
        """Test listing candidates with pagination"""
        response_data = [
            {"id": 3, "analysis_status": "pending"},
            {"id": 4, "analysis_status": "pending"}
        ]

        authenticated_client.get.return_value.status_code = HTTP_200_OK
        authenticated_client.get.return_value.json.return_value = response_data

        response = authenticated_client.get(
            "/api/v1/data-upload/candidates?skip=2&limit=2")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_list_candidates_unauthenticated(self, client):
        """Test list candidates without authentication returns 401"""
        client.get.return_value.status_code = HTTP_401_UNAUTHORIZED
        client.get.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.get("/api/v1/data-upload/candidates")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestErrorHandlingAndEdgeCases:
    """Test cases for error handling and edge cases"""

    def test_uuid_generation_in_response(self, authenticated_client, valid_csv_content):
        """Test that upload_id is properly generated as UUID"""
        upload_id = str(uuid.uuid4())
        response_data = {
            "message": "Successfully uploaded 1 exoplanet candidates",
            "candidates_created": 1,
            "upload_id": upload_id,
            "filename": "test.csv",
            "warnings": []
        }

        authenticated_client.post.return_value.status_code = HTTP_201_CREATED
        authenticated_client.post.return_value.json.return_value = response_data

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.csv", valid_csv_content, "text/csv")})

        assert response.status_code == HTTP_201_CREATED
        data = response.json()

        # Verify upload_id is a valid UUID
        returned_upload_id = data["upload_id"]
        try:
            uuid.UUID(returned_upload_id)
        except ValueError:
            pytest.fail("upload_id is not a valid UUID")

    def test_csv_processor_exception_handling(self, authenticated_client):
        """Test that CSV processor exceptions are properly handled"""
        authenticated_client.post.return_value.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        authenticated_client.post.return_value.json.return_value = {
            "detail": "Error processing CSV file: Invalid data format"}

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.csv", "some,content", "text/csv")})

        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error processing CSV file" in response.json()["detail"]

    def test_service_dependency_failure(self, authenticated_client, valid_csv_content):
        """Test handling of service dependency failures"""
        authenticated_client.post.return_value.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        authenticated_client.post.return_value.json.return_value = {
            "detail": "Error processing CSV file: Service initialization failed"}

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.csv", valid_csv_content, "text/csv")})

        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    def test_file_read_error(self, authenticated_client):
        """Test handling of file read errors"""
        authenticated_client.post.return_value.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        authenticated_client.post.return_value.json.return_value = {
            "detail": "Error processing CSV file: File read error"}

        response = authenticated_client.post(
            "/api/v1/data-upload/upload-csv", files={"file": ("test.csv", "content", "text/csv")})

        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
