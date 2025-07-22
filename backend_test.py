#!/usr/bin/env python3
"""
Backend API Testing for Face Recognition Attendance System
Tests Person Management API, Attendance Management API, and Database Integration
"""

import requests
import json
import base64
from datetime import datetime
import uuid

# Backend URL from frontend/.env
BASE_URL = "https://e51fd1de-ee8f-44e7-9eb8-8a926f208438.preview.emergentagent.com/api"

# Test data - realistic face recognition attendance system data
TEST_PERSONS = [
    {
        "name": "John Smith",
        "employee_id": "EMP001",
        "face_descriptor": base64.b64encode(b"mock_face_descriptor_john_smith_128_features").decode(),
        "photo": base64.b64encode(b"mock_photo_data_john_smith_jpeg").decode(),
        "role": "employee"
    },
    {
        "name": "Sarah Johnson",
        "employee_id": "STU001", 
        "face_descriptor": base64.b64encode(b"mock_face_descriptor_sarah_johnson_128_features").decode(),
        "photo": base64.b64encode(b"mock_photo_data_sarah_johnson_jpeg").decode(),
        "role": "student"
    },
    {
        "name": "Michael Brown",
        "employee_id": "EMP002",
        "face_descriptor": base64.b64encode(b"mock_face_descriptor_michael_brown_128_features").decode(),
        "photo": base64.b64encode(b"mock_photo_data_michael_brown_jpeg").decode(),
        "role": "employee"
    }
]

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.created_persons = []
        self.test_results = {
            "person_management": {"passed": 0, "failed": 0, "details": []},
            "attendance_management": {"passed": 0, "failed": 0, "details": []},
            "database_integration": {"passed": 0, "failed": 0, "details": []}
        }
    
    def log_result(self, category, test_name, passed, details=""):
        """Log test result"""
        if passed:
            self.test_results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results[category]["failed"] += 1
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results[category]["details"].append(result)
        print(result)
    
    def test_health_check(self):
        """Test API health check"""
        print("\n=== Testing API Health Check ===")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Health Check: {data.get('message', 'OK')}")
                return True
            else:
                print(f"❌ API Health Check Failed: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health Check Failed: {str(e)}")
            return False
    
    def test_person_management(self):
        """Test Person Management API"""
        print("\n=== Testing Person Management API ===")
        
        # Test 1: Create new person
        print("\n1. Testing person creation...")
        person_data = TEST_PERSONS[0]
        try:
            response = self.session.post(f"{BASE_URL}/persons", json=person_data)
            if response.status_code == 200:
                created_person = response.json()
                self.created_persons.append(created_person)
                self.log_result("person_management", "Create Person", True, 
                              f"Created person {created_person['name']} with ID {created_person['id']}")
            else:
                self.log_result("person_management", "Create Person", False, 
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("person_management", "Create Person", False, str(e))
        
        # Test 2: Try to create duplicate employee_id (should fail)
        print("\n2. Testing duplicate employee_id prevention...")
        try:
            response = self.session.post(f"{BASE_URL}/persons", json=person_data)
            if response.status_code == 400:
                self.log_result("person_management", "Duplicate Employee ID Prevention", True,
                              "Correctly rejected duplicate employee_id")
            else:
                self.log_result("person_management", "Duplicate Employee ID Prevention", False,
                              f"Should have failed with 400, got {response.status_code}")
        except Exception as e:
            self.log_result("person_management", "Duplicate Employee ID Prevention", False, str(e))
        
        # Test 3: Create second person
        print("\n3. Creating second person...")
        person_data_2 = TEST_PERSONS[1]
        try:
            response = self.session.post(f"{BASE_URL}/persons", json=person_data_2)
            if response.status_code == 200:
                created_person = response.json()
                self.created_persons.append(created_person)
                self.log_result("person_management", "Create Second Person", True,
                              f"Created person {created_person['name']}")
            else:
                self.log_result("person_management", "Create Second Person", False,
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("person_management", "Create Second Person", False, str(e))
        
        # Test 4: Get all persons
        print("\n4. Testing get all persons...")
        try:
            response = self.session.get(f"{BASE_URL}/persons")
            if response.status_code == 200:
                persons = response.json()
                if len(persons) >= 2:
                    self.log_result("person_management", "Get All Persons", True,
                                  f"Retrieved {len(persons)} persons")
                else:
                    self.log_result("person_management", "Get All Persons", False,
                                  f"Expected at least 2 persons, got {len(persons)}")
            else:
                self.log_result("person_management", "Get All Persons", False,
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("person_management", "Get All Persons", False, str(e))
        
        # Test 5: Get specific person
        if self.created_persons:
            print("\n5. Testing get specific person...")
            person_id = self.created_persons[0]['id']
            try:
                response = self.session.get(f"{BASE_URL}/persons/{person_id}")
                if response.status_code == 200:
                    person = response.json()
                    self.log_result("person_management", "Get Specific Person", True,
                                  f"Retrieved person {person['name']}")
                else:
                    self.log_result("person_management", "Get Specific Person", False,
                                  f"Status {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("person_management", "Get Specific Person", False, str(e))
        
        # Test 6: Get non-existent person (should fail)
        print("\n6. Testing get non-existent person...")
        fake_id = str(uuid.uuid4())
        try:
            response = self.session.get(f"{BASE_URL}/persons/{fake_id}")
            if response.status_code == 404:
                self.log_result("person_management", "Get Non-existent Person", True,
                              "Correctly returned 404 for non-existent person")
            else:
                self.log_result("person_management", "Get Non-existent Person", False,
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("person_management", "Get Non-existent Person", False, str(e))
    
    def test_attendance_management(self):
        """Test Attendance Management API"""
        print("\n=== Testing Attendance Management API ===")
        
        if not self.created_persons:
            print("❌ No persons created, skipping attendance tests")
            return
        
        # Test 1: Mark attendance for first person
        print("\n1. Testing mark attendance...")
        person = self.created_persons[0]
        attendance_data = {
            "person_id": person['id'],
            "person_name": person['name'],
            "employee_id": person['employee_id'],
            "confidence": 0.95,
            "photo": base64.b64encode(b"mock_attendance_photo_data").decode()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/attendance", json=attendance_data)
            if response.status_code == 200:
                attendance_record = response.json()
                self.log_result("attendance_management", "Mark Attendance", True,
                              f"Marked attendance for {attendance_record['person_name']}")
            else:
                self.log_result("attendance_management", "Mark Attendance", False,
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("attendance_management", "Mark Attendance", False, str(e))
        
        # Test 2: Try to mark attendance again for same person (should fail)
        print("\n2. Testing duplicate attendance prevention...")
        try:
            response = self.session.post(f"{BASE_URL}/attendance", json=attendance_data)
            if response.status_code == 400:
                self.log_result("attendance_management", "Duplicate Attendance Prevention", True,
                              "Correctly rejected duplicate attendance for same day")
            else:
                self.log_result("attendance_management", "Duplicate Attendance Prevention", False,
                              f"Should have failed with 400, got {response.status_code}")
        except Exception as e:
            self.log_result("attendance_management", "Duplicate Attendance Prevention", False, str(e))
        
        # Test 3: Mark attendance for second person
        if len(self.created_persons) > 1:
            print("\n3. Testing mark attendance for second person...")
            person2 = self.created_persons[1]
            attendance_data_2 = {
                "person_id": person2['id'],
                "person_name": person2['name'],
                "employee_id": person2['employee_id'],
                "confidence": 0.92
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/attendance", json=attendance_data_2)
                if response.status_code == 200:
                    self.log_result("attendance_management", "Mark Attendance Second Person", True,
                                  f"Marked attendance for {person2['name']}")
                else:
                    self.log_result("attendance_management", "Mark Attendance Second Person", False,
                                  f"Status {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("attendance_management", "Mark Attendance Second Person", False, str(e))
        
        # Test 4: Get today's attendance
        print("\n4. Testing get today's attendance...")
        try:
            response = self.session.get(f"{BASE_URL}/attendance/today")
            if response.status_code == 200:
                today_attendance = response.json()
                expected_count = min(2, len(self.created_persons))
                if len(today_attendance) >= 1:
                    self.log_result("attendance_management", "Get Today's Attendance", True,
                                  f"Retrieved {len(today_attendance)} attendance records")
                else:
                    self.log_result("attendance_management", "Get Today's Attendance", False,
                                  f"Expected at least 1 record, got {len(today_attendance)}")
            else:
                self.log_result("attendance_management", "Get Today's Attendance", False,
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("attendance_management", "Get Today's Attendance", False, str(e))
        
        # Test 5: Get attendance stats
        print("\n5. Testing get attendance stats...")
        try:
            response = self.session.get(f"{BASE_URL}/attendance/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ['total_registered', 'present_today', 'absent_today', 'attendance_rate']
                if all(field in stats for field in required_fields):
                    self.log_result("attendance_management", "Get Attendance Stats", True,
                                  f"Stats: {stats['present_today']}/{stats['total_registered']} present ({stats['attendance_rate']}%)")
                else:
                    self.log_result("attendance_management", "Get Attendance Stats", False,
                                  f"Missing required fields in stats response")
            else:
                self.log_result("attendance_management", "Get Attendance Stats", False,
                              f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("attendance_management", "Get Attendance Stats", False, str(e))
        
        # Test 6: Mark attendance for non-existent person (should fail)
        print("\n6. Testing mark attendance for non-existent person...")
        fake_attendance = {
            "person_id": str(uuid.uuid4()),
            "person_name": "Fake Person",
            "employee_id": "FAKE001",
            "confidence": 0.90
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/attendance", json=fake_attendance)
            if response.status_code == 404:
                self.log_result("attendance_management", "Mark Attendance Non-existent Person", True,
                              "Correctly rejected attendance for non-existent person")
            else:
                self.log_result("attendance_management", "Mark Attendance Non-existent Person", False,
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("attendance_management", "Mark Attendance Non-existent Person", False, str(e))
    
    def test_database_integration(self):
        """Test Database Integration"""
        print("\n=== Testing Database Integration ===")
        
        # Test 1: Data persistence - verify created persons still exist
        print("\n1. Testing data persistence...")
        try:
            response = self.session.get(f"{BASE_URL}/persons")
            if response.status_code == 200:
                persons = response.json()
                if len(persons) >= len(self.created_persons):
                    self.log_result("database_integration", "Data Persistence", True,
                                  f"All {len(self.created_persons)} created persons persist in database")
                else:
                    self.log_result("database_integration", "Data Persistence", False,
                                  f"Expected {len(self.created_persons)} persons, found {len(persons)}")
            else:
                self.log_result("database_integration", "Data Persistence", False,
                              f"Failed to retrieve persons: {response.status_code}")
        except Exception as e:
            self.log_result("database_integration", "Data Persistence", False, str(e))
        
        # Test 2: UUID consistency
        print("\n2. Testing UUID consistency...")
        if self.created_persons:
            person_id = self.created_persons[0]['id']
            try:
                # Verify UUID format
                uuid.UUID(person_id)
                self.log_result("database_integration", "UUID Format", True,
                              f"Person ID {person_id} is valid UUID")
            except ValueError:
                self.log_result("database_integration", "UUID Format", False,
                              f"Person ID {person_id} is not valid UUID")
        
        # Test 3: Delete person and verify cascade
        if self.created_persons:
            print("\n3. Testing person deletion and cascade...")
            person_to_delete = self.created_persons[0]
            person_id = person_to_delete['id']
            
            try:
                response = self.session.delete(f"{BASE_URL}/persons/{person_id}")
                if response.status_code == 200:
                    self.log_result("database_integration", "Delete Person", True,
                                  f"Successfully deleted person {person_to_delete['name']}")
                    
                    # Verify person is deleted
                    response = self.session.get(f"{BASE_URL}/persons/{person_id}")
                    if response.status_code == 404:
                        self.log_result("database_integration", "Verify Person Deleted", True,
                                      "Person correctly removed from database")
                    else:
                        self.log_result("database_integration", "Verify Person Deleted", False,
                                      f"Person still exists after deletion")
                else:
                    self.log_result("database_integration", "Delete Person", False,
                                  f"Status {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("database_integration", "Delete Person", False, str(e))
        
        # Test 4: Delete non-existent person (should fail gracefully)
        print("\n4. Testing delete non-existent person...")
        fake_id = str(uuid.uuid4())
        try:
            response = self.session.delete(f"{BASE_URL}/persons/{fake_id}")
            if response.status_code == 404:
                self.log_result("database_integration", "Delete Non-existent Person", True,
                              "Correctly returned 404 for non-existent person")
            else:
                self.log_result("database_integration", "Delete Non-existent Person", False,
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("database_integration", "Delete Non-existent Person", False, str(e))
    
    def cleanup(self):
        """Clean up test data"""
        print("\n=== Cleaning up test data ===")
        for person in self.created_persons[1:]:  # Skip first one as it was deleted in tests
            try:
                response = self.session.delete(f"{BASE_URL}/persons/{person['id']}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up person {person['name']}")
                else:
                    print(f"⚠️ Failed to cleanup person {person['name']}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error cleaning up person {person['name']}: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("BACKEND API TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            print(f"\n{category.replace('_', ' ').title()}:")
            print(f"  ✅ Passed: {passed}")
            print(f"  ❌ Failed: {failed}")
            
            for detail in results["details"]:
                print(f"    {detail}")
        
        print(f"\nOVERALL RESULTS:")
        print(f"✅ Total Passed: {total_passed}")
        print(f"❌ Total Failed: {total_failed}")
        print(f"📊 Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%" if (total_passed+total_failed) > 0 else "N/A")
        
        return total_failed == 0

def main():
    """Main test execution"""
    print("Starting Backend API Tests for Face Recognition Attendance System")
    print(f"Testing against: {BASE_URL}")
    
    tester = BackendTester()
    
    # Run health check first
    if not tester.test_health_check():
        print("❌ API is not accessible. Aborting tests.")
        return False
    
    try:
        # Run all tests
        tester.test_person_management()
        tester.test_attendance_management()
        tester.test_database_integration()
        
        # Print summary
        success = tester.print_summary()
        
        return success
        
    finally:
        # Always cleanup
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)