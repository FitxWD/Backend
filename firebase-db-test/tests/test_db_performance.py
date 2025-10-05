import time
import statistics
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    firebase_admin.initialize_app(cred)

db = firestore.client()

class SimplePerformanceTester:
    """Simple database performance tester without decorators"""
    
    def __init__(self):
        self.db = db
    
    def test_collection_scan(self, collection_name, limit=None):
        """Test scanning collection"""
        query = self.db.collection(collection_name)
        if limit:
            query = query.limit(limit)
        docs = query.get()
        return len(docs)
    
    def test_document_write(self, collection_name, data):
        """Test document creation"""
        doc_ref = self.db.collection(collection_name).add(data)
        return doc_ref[1].id
    
    def test_document_update(self, collection_name, doc_id, update_data):
        """Test document update"""
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.update(update_data)
        return True
    
    def test_document_delete(self, collection_name, doc_id):
        """Test document deletion"""
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.delete()
        return True
    
    def test_filtered_query(self, collection_name, field, value):
        """Test filtered query"""
        query = self.db.collection(collection_name).where(field, '==', value)
        docs = query.get()
        return len(docs)
    
    def run_read_performance_test(self):
        """Test read operations"""
        print("[TEST] Read Performance...")
        
        # Test collection scans
        start = time.time()
        workout_count = self.test_collection_scan('workoutPlans')
        scan_time = (time.time() - start) * 1000
        print(f"   Workout collection scan ({workout_count} docs): {scan_time:.2f}ms")
        
        start = time.time()
        diet_count = self.test_collection_scan('dietPlans')
        scan_time = (time.time() - start) * 1000
        print(f"   Diet collection scan ({diet_count} docs): {scan_time:.2f}ms")
        
        return True
    
    def run_write_performance_test(self):
        """Test write operations"""
        print("[TEST] Write Performance...")
        
        created_docs = []
        write_times = []
        
        # Test document creation
        for i in range(3):
            test_data = {
                "name": f"Performance Test {i}",
                "created_at": datetime.now().isoformat(),
                "test_id": f"perf_test_{i}",
                "data": "x" * 50
            }
            
            start = time.time()
            doc_id = self.test_document_write('performance_tests', test_data)
            write_time = (time.time() - start) * 1000
            write_times.append(write_time)
            created_docs.append(doc_id)
            
            print(f"   Document write {i+1}: {write_time:.2f}ms")
        
        if write_times:
            avg_write_time = statistics.mean(write_times)
            print(f"   Average write time: {avg_write_time:.2f}ms")
        
        # Test updates
        update_times = []
        for doc_id in created_docs:
            update_data = {"updated_at": datetime.now().isoformat(), "status": "updated"}
            start = time.time()
            self.test_document_update('performance_tests', doc_id, update_data)
            update_time = (time.time() - start) * 1000
            update_times.append(update_time)
        
        if update_times:
            avg_update_time = statistics.mean(update_times)
            print(f"   Average update time: {avg_update_time:.2f}ms")
        
        # Cleanup
        for doc_id in created_docs:
            self.test_document_delete('performance_tests', doc_id)
        
        print(f"   Cleaned up {len(created_docs)} test documents")
        return True
    
    def run_query_performance_test(self):
        """Test query operations"""
        print("[TEST] Query Performance...")
        
        try:
            # Test searching for workout plans
            start = time.time()
            results = self.test_filtered_query('workoutPlans', 'level', 'beginner')
            query_time = (time.time() - start) * 1000
            print(f"   Beginner workouts query ({results} results): {query_time:.2f}ms")
        except Exception as e:
            print(f"   Workout query failed: {e}")
        
        try:
            # Test searching for diet plans
            start = time.time()
            results = self.test_filtered_query('dietPlans', 'level', 'beginner')
            query_time = (time.time() - start) * 1000
            print(f"   Beginner diets query ({results} results): {query_time:.2f}ms")
        except Exception as e:
            print(f"   Diet query failed: {e}")
        
        return True
    
    def run_bulk_operations_test(self):
        """Test bulk operations"""
        print("[TEST] Bulk Operations...")
        
        # Create multiple documents
        bulk_data = []
        for i in range(5):
            bulk_data.append({
                "name": f"Bulk Test {i}",
                "created_at": datetime.now().isoformat(),
                "index": i
            })
        
        start = time.time()
        created_ids = []
        for data in bulk_data:
            doc_id = self.test_document_write('bulk_tests', data)
            created_ids.append(doc_id)
        
        bulk_write_time = (time.time() - start) * 1000
        print(f"   Bulk write (5 docs): {bulk_write_time:.2f}ms")
        print(f"   Average per document: {bulk_write_time/5:.2f}ms")
        
        # Cleanup bulk test data
        start = time.time()
        for doc_id in created_ids:
            self.test_document_delete('bulk_tests', doc_id)
        
        bulk_delete_time = (time.time() - start) * 1000
        print(f"   Bulk delete (5 docs): {bulk_delete_time:.2f}ms")
        
        return True
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("Starting Simple Database Performance Tests...")
        print("=" * 50)
        
        tests = [
            ("Read Performance", self.run_read_performance_test),
            ("Write Performance", self.run_write_performance_test),
            ("Query Performance", self.run_query_performance_test),
            ("Bulk Operations", self.run_bulk_operations_test)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                print(f"\n[RUNNING] {test_name}...")
                result = test_func()
                if result:
                    print(f"[PASS] {test_name}")
                    passed += 1
                else:
                    print(f"[FAIL] {test_name}")
            except Exception as e:
                print(f"[ERROR] {test_name} failed: {e}")
        
        print(f"\n[SUMMARY] Performance Tests Complete")
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 50)

def main():
    """Main function to run performance tests"""
    tester = SimplePerformanceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()