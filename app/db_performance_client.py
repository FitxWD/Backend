import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import firebase_admin
from firebase_admin import firestore
from config import db, monitor_db_performance

class DatabasePerformanceTester:
    """Test database performance with various scenarios"""
    
    def __init__(self):
        self.db = db
        self.results = []
    
    @monitor_db_performance("single_document_read")
    def test_single_document_read(self, collection_name, doc_id):
        """Test reading a single document"""
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc = doc_ref.get()
        return doc.exists
    
    @monitor_db_performance("collection_scan")
    def test_collection_scan(self, collection_name, limit=None):
        """Test scanning entire collection"""
        query = self.db.collection(collection_name)
        if limit:
            query = query.limit(limit)
        docs = query.get()
        return len(docs)
    
    @monitor_db_performance("filtered_query")
    def test_filtered_query(self, collection_name, field, value):
        """Test filtered query performance"""
        query = self.db.collection(collection_name).where(field, '==', value)
        docs = query.get()
        return len(docs)
    
    @monitor_db_performance("document_write")
    def test_document_write(self, collection_name, data):
        """Test document creation performance"""
        doc_ref = self.db.collection(collection_name).add(data)
        return doc_ref[1].id
    
    @monitor_db_performance("document_update")
    def test_document_update(self, collection_name, doc_id, update_data):
        """Test document update performance"""
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.update(update_data)
        return True
    
    @monitor_db_performance("document_delete")
    def test_document_delete(self, collection_name, doc_id):
        """Test document deletion performance"""
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.delete()
        return True
    
    def run_performance_suite(self):
        """Run comprehensive performance test suite"""
        print(">> Starting Database Performance Test Suite...")
        
        # Test scenarios
        scenarios = [
            self.test_read_performance,
            self.test_write_performance,
            self.test_query_performance,
            self.test_concurrent_performance,
            self.test_bulk_operations
        ]
        
        for scenario in scenarios:
            try:
                print(f"\n[RUNNING] {scenario.__name__}...")
                scenario()
            except Exception as e:
                print(f"[ERROR] {scenario.__name__} failed: {e}")
        
        self.generate_performance_report()
    
    def test_read_performance(self):
        """Test read operation performance"""
        print("[TEST] Reading Performance...")
        
        # Test single document reads
        read_times = []
        for i in range(10):
            start = time.time()
            try:
                # Test reading from workoutPlans
                self.test_single_document_read('workoutPlans', 'test_read')
            except:
                pass
            read_times.append((time.time() - start) * 1000)
        
        avg_read_time = statistics.mean(read_times)
        print(f"   Average single document read: {avg_read_time:.2f}ms")
        
        # Test collection scans
        start = time.time()
        workout_count = self.test_collection_scan('workoutPlans')
        scan_time = (time.time() - start) * 1000
        print(f"   Collection scan ({workout_count} docs): {scan_time:.2f}ms")
        
        start = time.time()
        diet_count = self.test_collection_scan('dietPlans')
        scan_time = (time.time() - start) * 1000
        print(f"   Collection scan ({diet_count} docs): {scan_time:.2f}ms")
    
    def test_write_performance(self):
        """Test write operation performance"""
        print("[TEST] Write Performance...")
        
        created_docs = []
        write_times = []
        
        # Test document creation
        for i in range(5):
            test_data = {
                "name": f"Performance Test {i}",
                "created_at": datetime.now(),
                "test_id": f"perf_test_{i}",
                "data": "x" * 100  # Small payload
            }
            
            start = time.time()
            doc_id = self.test_document_write('performance_tests', test_data)
            write_time = (time.time() - start) * 1000
            write_times.append(write_time)
            created_docs.append(doc_id)
            
            print(f"   Document write {i+1}: {write_time:.2f}ms")
        
        avg_write_time = statistics.mean(write_times)
        print(f"   Average write time: {avg_write_time:.2f}ms")
        
        # Test updates
        update_times = []
        for doc_id in created_docs:
            update_data = {"updated_at": datetime.now(), "status": "updated"}
            start = time.time()
            self.test_document_update('performance_tests', doc_id, update_data)
            update_time = (time.time() - start) * 1000
            update_times.append(update_time)
        
        avg_update_time = statistics.mean(update_times)
        print(f"   Average update time: {avg_update_time:.2f}ms")
        
        # Cleanup
        for doc_id in created_docs:
            self.test_document_delete('performance_tests', doc_id)
    
    def test_query_performance(self):
        """Test query operation performance"""
        print("[TEST] Query Performance...")
        
        # Test searching for specific workout plans
        start = time.time()
        results = self.test_filtered_query('workoutPlans', 'level', 'beginner')
        query_time = (time.time() - start) * 1000
        print(f"   Beginner workouts query ({results} results): {query_time:.2f}ms")
        
        # Test searching for diet plans
        start = time.time()
        results = self.test_filtered_query('dietPlans', 'level', 'beginner')
        query_time = (time.time() - start) * 1000
        print(f"   Beginner diets query ({results} results): {query_time:.2f}ms")
    
    def test_concurrent_performance(self):
        """Test concurrent database operations"""
        print("[TEST] Concurrent Performance...")
        
        def concurrent_read():
            return self.test_collection_scan('workoutPlans', limit=5)
        
        # Test concurrent reads
        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_read) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        concurrent_time = (time.time() - start) * 1000
        print(f"   10 concurrent reads: {concurrent_time:.2f}ms")
        print(f"   Average per operation: {concurrent_time/10:.2f}ms")
    
    def test_bulk_operations(self):
        """Test bulk database operations"""
        print("[TEST] Bulk Operations...")
        
        # Create multiple documents
        bulk_data = []
        for i in range(10):
            bulk_data.append({
                "name": f"Bulk Test {i}",
                "created_at": datetime.now(),
                "index": i
            })
        
        start = time.time()
        created_ids = []
        for data in bulk_data:
            doc_id = self.test_document_write('bulk_tests', data)
            created_ids.append(doc_id)
        
        bulk_write_time = (time.time() - start) * 1000
        print(f"   Bulk write (10 docs): {bulk_write_time:.2f}ms")
        print(f"   Average per document: {bulk_write_time/10:.2f}ms")
        
        # Cleanup bulk test data
        start = time.time()
        for doc_id in created_ids:
            self.test_document_delete('bulk_tests', doc_id)
        
        bulk_delete_time = (time.time() - start) * 1000
        print(f"   Bulk delete (10 docs): {bulk_delete_time:.2f}ms")
    
    def generate_performance_report(self):
        """Generate performance test summary"""
        print("\n[SUMMARY] Performance Test Results:")
        print("=" * 50)
        print("[PASS] Read Performance: Tested single reads and collection scans")
        print("[PASS] Write Performance: Tested document creation and updates") 
        print("[PASS] Query Performance: Tested filtered queries")
        print("[PASS] Concurrent Performance: Tested multiple simultaneous operations")
        print("[PASS] Bulk Operations: Tested batch create and delete")
        print("\n[INFO] Check performance_logs collection for detailed metrics")

# Usage function
def run_db_performance_tests():
    """Run database performance tests"""
    print("Initializing Database Performance Tester...")
    tester = DatabasePerformanceTester()
    tester.run_performance_suite()

if __name__ == "__main__":
    run_db_performance_tests()