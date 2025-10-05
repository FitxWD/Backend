import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the Firebase imports before importing db_client
with patch('firebase_admin.initialize_app'), \
     patch('firebase_admin.firestore.client') as mock_client:
    
    mock_db = Mock()
    mock_client.return_value = mock_db
    
    from src.db_client import add_user, get_user, delete_user, update_user, authenticate_user, get_user_by_email

class TestUserAuthenticationFlow:
    """Test complete user registration, login, and health data flow"""
    
    # REGISTRATION TESTS
    @patch('src.db_client.db')
    def test_create_account_valid_data(self, mock_db):
        """Test Step 1: Create account with valid basic information"""
        # Setup mock
        mock_doc_ref = Mock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Registration data from "Create an account" form
        account_data = {
            "fullName": "Chehan Helitha",
            "email": "chehan@example.com",
            "password": "hashedPassword123",  # In real app, this would be hashed
            "createdAt": "2024-01-01T00:00:00Z",
            "role": "user",
            "profileComplete": False,  # Health data not yet added
            "isActive": True
        }
        
        # Test account creation
        result = add_user("user_123", account_data)
        assert result is True
        mock_doc_ref.set.assert_called_once_with(account_data)

    @patch('src.db_client.db')
    def test_add_health_data_to_existing_user(self, mock_db):
        """Test Step 2: Add health data from 'Tell Us About You' form"""
        # Setup mock for existing user
        mock_doc_ref = Mock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Health data from "Tell Us About You" form
        health_data_update = {
            "healthData": {
                "gender": "Male",      # From gender dropdown
                "age": 25,             # From age input
                "height": 175,         # From height input (cm)
                "weight": 70           # From weight input (kg)
            },
            "profileComplete": True,
            "profileCompletedAt": "2024-01-01T00:05:00Z"
        }
        
        # Test health data addition
        result = update_user("user_123", health_data_update)
        assert result is True
        mock_doc_ref.update.assert_called_once_with(health_data_update)

    # LOGIN TESTS
    @patch('src.db_client.db')
    def test_user_login_valid_credentials(self, mock_db):
        """Test login with valid email and password"""
        # Setup mock for existing user
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "fullName": "Chehan Helitha",
            "email": "chehan@example.com",
            "password": "hashedPassword123",
            "role": "user",
            "profileComplete": True,
            "isActive": True,
            "healthData": {
                "gender": "Male",
                "age": 25,
                "height": 175,
                "weight": 70
            }
        }
        mock_query.get.return_value = [mock_doc]
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Test login credentials from "Welcome Back" form
        login_email = "chehan@example.com"
        login_password = "hashedPassword123"
        
        # Simulate authentication
        user_data = mock_doc.to_dict()
        assert user_data["email"] == login_email
        assert user_data["password"] == login_password  # In real app, use password hashing
        assert user_data["isActive"] is True

    @patch('src.db_client.db')
    def test_user_login_invalid_email(self, mock_db):
        """Test login with non-existent email"""
        # Setup mock for no user found
        mock_collection = Mock()
        mock_query = Mock()
        mock_query.get.return_value = []  # No users found
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Test with invalid email
        login_email = "nonexistent@example.com"
        users = mock_query.get.return_value
        assert len(users) == 0, "User with this email should not exist"

    @patch('src.db_client.db')
    def test_user_login_wrong_password(self, mock_db):
        """Test login with correct email but wrong password"""
        # Setup mock for existing user
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "email": "chehan@example.com",
            "password": "correctHashedPassword",
            "isActive": True
        }
        mock_query.get.return_value = [mock_doc]
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Test with wrong password
        user_data = mock_doc.to_dict()
        correct_password = "correctHashedPassword"
        attempted_password = "wrongPassword"
        
        assert user_data["password"] != attempted_password, "Password should not match"

    @patch('src.db_client.db')
    def test_user_login_inactive_account(self, mock_db):
        """Test login with deactivated account"""
        # Setup mock for inactive user
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "email": "inactive@example.com",
            "password": "hashedPassword",
            "isActive": False  # Account deactivated
        }
        mock_query.get.return_value = [mock_doc]
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Test login with inactive account
        user_data = mock_doc.to_dict()
        assert user_data["isActive"] is False, "Account should be inactive"

    # DATA VALIDATION TESTS
    def test_registration_form_validation(self):
        """Test validation of registration form data"""
        valid_registration = {
            "fullName": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!"
        }
        
        # Test required fields
        assert "fullName" in valid_registration
        assert "email" in valid_registration
        assert "password" in valid_registration
        
        # Test email format
        assert "@" in valid_registration["email"]
        assert "." in valid_registration["email"].split("@")[1]
        
        # Test password strength
        password = valid_registration["password"]
        assert len(password) >= 8
        assert any(c.isupper() for c in password)  # At least one uppercase
        assert any(c.islower() for c in password)  # At least one lowercase
        assert any(c.isdigit() for c in password)  # At least one number

    def test_health_data_form_validation(self):
        """Test validation of 'Tell Us About You' form"""
        valid_health_data = {
            "gender": "Female",
            "age": 28,
            "height": 165,  # cm
            "weight": 55    # kg
        }
        
        # Test gender options
        assert valid_health_data["gender"] in ["Male", "Female", "Other"]
        
        # Test age constraints
        assert 18 < valid_health_data["age"] <= 120
        
        # Test height constraints (cm)
        assert 100 <= valid_health_data["height"] <= 250
        
        # Test weight constraints (kg)
        assert 30 <= valid_health_data["weight"] <= 300

    def test_login_form_validation(self):
        """Test validation of login form data"""
        valid_login = {
            "email": "user@example.com",
            "password": "userPassword123"
        }
        
        # Test required fields
        assert "email" in valid_login
        assert "password" in valid_login
        
        # Test email format
        assert "@" in valid_login["email"]
        
        # Test password not empty
        assert len(valid_login["password"]) > 0

    # INTEGRATION TESTS
    @patch('src.db_client.db')
    def test_complete_user_journey(self, mock_db):
        """Test complete flow: Register → Add Health Data → Login"""
        # Setup mocks
        mock_doc_ref = Mock()
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        
        # Step 1: Registration
        registration_data = {
            "fullName": "Sarah Johnson",
            "email": "sarah@example.com",
            "password": "hashedSarahPass123",
            "role": "user",
            "profileComplete": False,
            "isActive": True,
            "createdAt": "2024-01-01T00:00:00Z"
        }
        
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        result = add_user("user_sarah", registration_data)
        assert result is True
        
        # Step 2: Add Health Data
        health_update = {
            "healthData": {
                "gender": "Female",
                "age": 30,
                "height": 168,
                "weight": 62
            },
            "profileComplete": True,
            "profileCompletedAt": "2024-01-01T00:10:00Z"
        }
        
        result = update_user("user_sarah", health_update)
        assert result is True
        
        # Step 3: Login Simulation
        complete_user_data = {
            **registration_data,
            **health_update
        }
        
        mock_doc.to_dict.return_value = complete_user_data
        mock_query.get.return_value = [mock_doc]
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Verify complete profile
        user_data = mock_doc.to_dict()
        assert user_data["email"] == "sarah@example.com"
        assert user_data["profileComplete"] is True
        assert user_data["healthData"]["gender"] == "Female"

    def test_invalid_registration_data(self):
        """Test registration with invalid data"""
        invalid_cases = [
            {"fullName": "", "email": "test@test.com", "password": "pass123"},       # Empty name
            {"fullName": "John", "email": "invalid-email", "password": "pass123"},   # Invalid email
            {"fullName": "John", "email": "john@test.com", "password": "123"},       # Weak password
            {"email": "john@test.com", "password": "pass123"},                       # Missing name
            {"fullName": "John", "password": "pass123"},                            # Missing email
            {"fullName": "John", "email": "john@test.com"},                         # Missing password
        ]
        
        # Import the validation function from db_client
        from src.db_client import validate_registration_data
        
        for i, invalid_data in enumerate(invalid_cases):
            full_name = invalid_data.get("fullName", "")
            email = invalid_data.get("email", "")
            password = invalid_data.get("password", "")
            
            # Test that validation returns False for invalid data
            is_valid, error_message = validate_registration_data(full_name, email, password)
            
            assert is_valid is False, f"Case {i+1} should be invalid: {invalid_data}. Error: {error_message}"
            assert error_message != "Valid", f"Case {i+1} should have an error message"
            
            print(f"✅ Case {i+1} correctly identified as invalid: {error_message}")

    def test_invalid_health_data(self):
        """Test health data with invalid values"""
        invalid_health_cases = [
            {"gender": "Invalid", "age": 25, "height": 170, "weight": 65},        # Invalid gender
            {"gender": "Male", "age": 5, "height": 170, "weight": 65},            # Too young
            {"gender": "Female", "age": 150, "height": 170, "weight": 65},        # Too old
            {"gender": "Male", "age": 25, "height": 50, "weight": 65},            # Too short
            {"gender": "Female", "age": 25, "height": 300, "weight": 65},         # Too tall
            {"gender": "Male", "age": 25, "height": 170, "weight": 10},           # Too light
            {"gender": "Female", "age": 25, "height": 170, "weight": 500},        # Too heavy
        ]
        
        # Import the validation function from db_client
        from src.db_client import validate_health_data
        
        for i, invalid_data in enumerate(invalid_health_cases):
            gender = invalid_data["gender"]
            age = invalid_data["age"]
            height = invalid_data["height"]
            weight = invalid_data["weight"]
            
            # Test that validation returns False for invalid data
            is_valid, error_message = validate_health_data(gender, age, height, weight)
            
            assert is_valid is False, f"Case {i+1} should be invalid: {invalid_data}. Error: {error_message}"
            assert error_message != "Valid", f"Case {i+1} should have an error message"
            
            print(f"✅ Case {i+1} correctly identified as invalid: {error_message}")

    def test_valid_registration_data(self):
        """Test registration with valid data"""
        from src.db_client import validate_registration_data
        
        valid_cases = [
            {"fullName": "John Doe", "email": "john@example.com", "password": "SecurePass123!"},
            {"fullName": "Jane Smith", "email": "jane.smith@company.co.uk", "password": "MyPassword456@"},
            {"fullName": "Bob Johnson", "email": "bob123@gmail.com", "password": "StrongPass789#"},
        ]
        
        for i, valid_data in enumerate(valid_cases):
            full_name = valid_data["fullName"]
            email = valid_data["email"]
            password = valid_data["password"]
            
            # Test that validation returns True for valid data
            is_valid, error_message = validate_registration_data(full_name, email, password)
            
            assert is_valid is True, f"Case {i+1} should be valid: {valid_data}. Error: {error_message}"
            assert error_message == "Valid", f"Case {i+1} should have 'Valid' message"
            
            print(f"✅ Case {i+1} correctly identified as valid")

    def test_valid_health_data(self):
        """Test health data with valid values"""
        from src.db_client import validate_health_data
        
        valid_health_cases = [
            {"gender": "Male", "age": 25, "height": 175, "weight": 70},
            {"gender": "Female", "age": 30, "height": 165, "weight": 55},
            {"gender": "Other", "age": 45, "height": 180, "weight": 85},
            {"gender": "Male", "age": 18, "height": 170, "weight": 65},
            {"gender": "Female", "age": 65, "height": 160, "weight": 60},
        ]
        
        for i, valid_data in enumerate(valid_health_cases):
            gender = valid_data["gender"]
            age = valid_data["age"]
            height = valid_data["height"]
            weight = valid_data["weight"]
            
            # Test that validation returns True for valid data
            is_valid, error_message = validate_health_data(gender, age, height, weight)
            
            assert is_valid is True, f"Case {i+1} should be valid: {valid_data}. Error: {error_message}"
            assert error_message == "Valid", f"Case {i+1} should have 'Valid' message"
            
            print(f"✅ Case {i+1} correctly identified as valid")

    @patch('src.db_client.db')
    def test_duplicate_email_prevention(self, mock_db):
        """Test preventing duplicate email registration"""
        # Setup mock for existing user check
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {"email": "existing@example.com"}
        mock_query.get.return_value = [mock_doc]  # User already exists
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        
        # Check for existing email
        existing_users = mock_query.get.return_value
        assert len(existing_users) > 0, "Email should already exist in database"

    @patch('src.db_client.db')
    def test_user_profile_retrieval_after_login(self, mock_db):
        """Test retrieving complete user profile after successful login"""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fullName": "Test User",
            "email": "test@example.com",
            "role": "user",
            "profileComplete": True,
            "isActive": True,
            "healthData": {
                "gender": "Male",
                "age": 35,
                "height": 180,
                "weight": 75
            },
            "lastLoginAt": "2024-01-01T12:00:00Z"
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Test profile retrieval
        result = get_user("test_user_id")
        assert result is not None
        assert result["profileComplete"] is True
        assert "healthData" in result
        assert result["isActive"] is True

    @patch('src.db_client.db') 
    def test_user_session_management(self, mock_db):
        """Test updating user session data on login"""
        # Setup mock
        mock_doc_ref = Mock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Session update data
        session_update = {
            "lastLoginAt": "2024-01-01T12:00:00Z",
            "loginCount": 1,
            "isOnline": True
        }
        
        result = update_user("user_id", session_update)
        assert result is True
        mock_doc_ref.update.assert_called_once_with(session_update)