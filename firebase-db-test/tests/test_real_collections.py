import pytest
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestRealFirebaseCollections:
    """Test actual Firebase collections - fetch specific plans"""
    
    @classmethod
    def setup_class(cls):
        """Initialize Firebase connection once for all tests"""
        if not firebase_admin._apps:
            try:
                # Path to service account key
                service_account_path = os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json')
                
                if os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                    print("✅ Connected using service account key")
                else:
                    print(f"❌ Service account key not found at: {service_account_path}")
                    raise FileNotFoundError("Service account key not found")
                    
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                raise
        
        cls.db = firestore.client()
        print("🔥 Firebase client initialized")

    def test_collection_overview(self):
        """Get an overview of all collections and their documents"""
        try:
            print("\n📊 Database Collections Overview:")
            
            # List all collections
            collections = self.db.collections()
            for collection in collections:
                collection_name = collection.id
                
                # Count documents in collection
                docs = collection.get()
                doc_count = len(docs)
                
                print(f"\n📁 Collection: {collection_name} ({doc_count} documents)")
                
                # Show first few document IDs and sample structure
                for i, doc in enumerate(docs[:3]):  # Show first 3 documents
                    doc_data = doc.to_dict()
                    print(f"   📄 Document {i+1}: {doc.id}")
                    
                    # Show structure of first document in each collection
                    if i == 0:
                        print(f"      Sample fields: {list(doc_data.keys())}")
                        
                        # Look for name-like fields
                        name_fields = ['name', 'title', 'planName', 'dietName', 'workoutName']
                        found_name = None
                        for name_field in name_fields:
                            if name_field in doc_data:
                                found_name = doc_data[name_field]
                                print(f"      {name_field}: {found_name}")
                                break
                
                if doc_count > 3:
                    print(f"   ... and {doc_count - 3} more documents")
                    
        except Exception as e:
            print(f"❌ Error getting collection overview: {e}")
            raise

    def test_fetch_gentle_start_workout(self):
        """Test fetching 'Gentle Start' workout plan"""
        try:
            print("\n🎯 Searching for 'Gentle Start' workout plan...")
            
            # Search for workout plan with name "Gentle Start"
            workout_plans_ref = self.db.collection('workoutPlans')
            
            # Try different possible field names for the plan name
            possible_name_fields = ['name', 'title', 'planName', 'workoutName']
            gentle_start_plan = None
            
            for name_field in possible_name_fields:
                try:
                    query = workout_plans_ref.where(name_field, '==', 'Gentle Start')
                    results = query.get()
                    
                    if len(results) > 0:
                        gentle_start_plan = results[0]
                        print(f"✅ Found 'Gentle Start' using field: {name_field}")
                        break
                        
                except Exception as field_error:
                    # Field might not exist, continue to next
                    continue
            
            # If not found by exact match, search all documents
            if gentle_start_plan is None:
                print("🔍 Exact match not found, searching all workout plans...")
                all_workouts = workout_plans_ref.get()
                
                for doc in all_workouts:
                    doc_data = doc.to_dict()
                    # Check all string fields for "Gentle Start"
                    for key, value in doc_data.items():
                        if isinstance(value, str) and 'Gentle Start' in value:
                            gentle_start_plan = doc
                            print(f"✅ Found 'Gentle Start' in field: {key}")
                            break
                    if gentle_start_plan:
                        break
            
            # If still not found, show available workout plans
            if gentle_start_plan is None:
                print("❌ 'Gentle Start' not found. Available workout plans:")
                all_workouts = workout_plans_ref.get()
                for i, doc in enumerate(all_workouts):
                    doc_data = doc.to_dict()
                    # Try to find a name-like field
                    possible_name = None
                    for field in ['name', 'title', 'planName', 'workoutName']:
                        if field in doc_data:
                            possible_name = doc_data[field]
                            break
                    
                    if possible_name is None:
                        # If no obvious name field, show document ID
                        possible_name = f"Document ID: {doc.id}"
                    
                    print(f"   {i+1}. {possible_name}")
                
                pytest.fail("Could not find 'Gentle Start' workout plan")
            
            # Display the found plan
            plan_data = gentle_start_plan.to_dict()
            plan_id = gentle_start_plan.id
            
            print(f"\n💪 'Gentle Start' Workout Plan Found!")
            print(f"📄 Document ID: {plan_id}")
            print(f"🔍 Plan Structure:")
            
            # Display full structure without assumptions
            for key, value in plan_data.items():
                value_type = type(value).__name__
                
                if isinstance(value, dict):
                    print(f"   {key}: {value_type} (keys: {list(value.keys())})")
                elif isinstance(value, list):
                    print(f"   {key}: {value_type} (length: {len(value)})")
                    if len(value) > 0:
                        print(f"      First item: {type(value[0]).__name__}")
                elif isinstance(value, str):
                    if len(value) > 100:
                        print(f"   {key}: {value_type} = '{value[:100]}...'")
                    else:
                        print(f"   {key}: {value_type} = '{value}'")
                else:
                    print(f"   {key}: {value_type} = {value}")
            
            return plan_data
            
        except Exception as e:
            print(f"❌ Error fetching 'Gentle Start' workout: {e}")
            raise

    def test_fetch_balanced_2100_diet(self):
        """Test fetching 'Balanced_2100' diet plan"""
        try:
            print("\n🎯 Searching for 'Balanced_2100' diet plan...")
            
            # Search for diet plan with name "Balanced_2100"
            diet_plans_ref = self.db.collection('dietPlans')
            
            # Try different possible field names and variations
            possible_name_fields = ['name', 'title', 'planName', 'dietName']
            possible_names = ['Balanced_2100', 'Balanced 2100', 'balanced_2100', 'BALANCED_2100']
            
            balanced_2100_plan = None
            
            for name_field in possible_name_fields:
                for name_variant in possible_names:
                    try:
                        query = diet_plans_ref.where(name_field, '==', name_variant)
                        results = query.get()
                        
                        if len(results) > 0:
                            balanced_2100_plan = results[0]
                            print(f"✅ Found 'Balanced_2100' using field: {name_field}, value: {name_variant}")
                            break
                    except Exception as field_error:
                        # Field might not exist, continue to next
                        continue
                if balanced_2100_plan:
                    break
            
            # If not found by exact match, search all documents
            if balanced_2100_plan is None:
                print("🔍 Exact match not found, searching all diet plans...")
                all_diets = diet_plans_ref.get()
                
                for doc in all_diets:
                    doc_data = doc.to_dict()
                    # Check all string fields for variations of "Balanced_2100"
                    for key, value in doc_data.items():
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if any(variant.lower() in value_lower for variant in possible_names):
                                balanced_2100_plan = doc
                                print(f"✅ Found 'Balanced_2100' variant in field: {key} = '{value}'")
                                break
                    if balanced_2100_plan:
                        break
            
            # If still not found, show available diet plans
            if balanced_2100_plan is None:
                print("❌ 'Balanced_2100' not found. Available diet plans:")
                all_diets = diet_plans_ref.get()
                for i, doc in enumerate(all_diets):
                    doc_data = doc.to_dict()
                    # Try to find a name-like field
                    possible_name = None
                    for field in ['name', 'title', 'planName', 'dietName']:
                        if field in doc_data:
                            possible_name = doc_data[field]
                            break
                    
                    if possible_name is None:
                        # If no obvious name field, show document ID
                        possible_name = f"Document ID: {doc.id}"
                    
                    print(f"   {i+1}. {possible_name}")
                
                pytest.fail("Could not find 'Balanced_2100' diet plan")
            
            # Display the found plan
            plan_data = balanced_2100_plan.to_dict()
            plan_id = balanced_2100_plan.id
            
            print(f"\n🥗 'Balanced_2100' Diet Plan Found!")
            print(f"📄 Document ID: {plan_id}")
            print(f"🔍 Plan Structure:")
            
            # Display full structure without assumptions
            for key, value in plan_data.items():
                value_type = type(value).__name__
                
                if isinstance(value, dict):
                    print(f"   {key}: {value_type} (keys: {list(value.keys())})")
                    # Show first level of nested structure
                    for nested_key, nested_value in value.items():
                        nested_type = type(nested_value).__name__
                        if isinstance(nested_value, (dict, list)):
                            print(f"      {nested_key}: {nested_type}")
                        elif isinstance(nested_value, str) and len(nested_value) > 50:
                            print(f"      {nested_key}: {nested_type} = '{nested_value[:50]}...'")
                        else:
                            print(f"      {nested_key}: {nested_type} = {nested_value}")
                            
                elif isinstance(value, list):
                    print(f"   {key}: {value_type} (length: {len(value)})")
                    if len(value) > 0:
                        first_item = value[0]
                        print(f"      First item: {type(first_item).__name__}")
                        if isinstance(first_item, dict):
                            print(f"      First item keys: {list(first_item.keys())}")
                            
                elif isinstance(value, str):
                    if len(value) > 100:
                        print(f"   {key}: {value_type} = '{value[:100]}...'")
                    else:
                        print(f"   {key}: {value_type} = '{value}'")
                else:
                    print(f"   {key}: {value_type} = {value}")
            
            return plan_data
            
        except Exception as e:
            print(f"❌ Error fetching 'Balanced_2100' diet: {e}")
            raise

    def test_add_and_delete_workout_plan(self):
        """Test adding a new workout plan and then deleting it"""
        try:
            print("\n➕ Testing Add and Delete Workout Plan...")
            
            # Create a new workout plan with the discovered structure
            new_workout_plan = {
                "name": "Test Workout Plan",
                "description": "A test workout plan for CRUD testing. This plan includes basic exercises for strength and flexibility training.",
                "durationMinutes": 30,
                "level": "beginner",
                "goals": [
                    "Build basic strength",
                    "Improve flexibility", 
                    "Increase endurance",
                    "Learn proper form",
                    "Establish routine"
                ],
                "personalization_rules": [
                    "Adjust weight based on fitness level",
                    "Modify reps for beginners",
                    "Include rest days for recovery"
                ],
                "micro_workouts": [
                    {
                        "name": "Warm Up",
                        "duration": 5,
                        "exercises": ["Light stretching", "Joint mobility"]
                    },
                    {
                        "name": "Strength Circuit",
                        "duration": 15,
                        "exercises": ["Push-ups", "Squats", "Planks"]
                    },
                    {
                        "name": "Cardio Burst", 
                        "duration": 5,
                        "exercises": ["Jumping jacks", "High knees"]
                    },
                    {
                        "name": "Cool Down",
                        "duration": 5,
                        "exercises": ["Deep stretching", "Breathing exercises"]
                    },
                    {
                        "name": "Core Focus",
                        "duration": 10,
                        "exercises": ["Crunches", "Leg raises", "Russian twists"]
                    },
                    {
                        "name": "Balance Training",
                        "duration": 5,
                        "exercises": ["Single leg stands", "Balance poses"]
                    }
                ],
                "progression_4_weeks": [
                    "Week 1: Focus on form and basic movements",
                    "Week 2: Increase repetitions by 25%", 
                    "Week 3: Add light weights and resistance",
                    "Week 4: Combine movements for complex exercises"
                ],
                "weekly_template": [
                    {
                        "day": "Monday",
                        "workout_type": "Full Body",
                        "duration": 30,
                        "focus": "Strength and mobility"
                    },
                    {
                        "day": "Tuesday", 
                        "workout_type": "Active Recovery",
                        "duration": 15,
                        "focus": "Light stretching and walking"
                    },
                    {
                        "day": "Wednesday",
                        "workout_type": "Core and Cardio",
                        "duration": 25,
                        "focus": "Core strength and cardiovascular fitness"
                    },
                    {
                        "day": "Thursday",
                        "workout_type": "Rest Day",
                        "duration": 0,
                        "focus": "Complete rest and recovery"
                    },
                    {
                        "day": "Friday",
                        "workout_type": "Strength Training",
                        "duration": 35,
                        "focus": "Progressive overload and muscle building"
                    },
                    {
                        "day": "Saturday",
                        "workout_type": "Flexibility",
                        "duration": 20,
                        "focus": "Deep stretching and mobility work"
                    },
                    {
                        "day": "Sunday",
                        "workout_type": "Optional Light Activity",
                        "duration": 15,
                        "focus": "Gentle movement or recreational activity"
                    }
                ]
            }
            
            # Step 1: Add the workout plan
            print("📝 Adding new workout plan...")
            workout_plans_ref = self.db.collection('workoutPlans')
            
            # Add the document and get the reference
            new_doc_ref = workout_plans_ref.add(new_workout_plan)
            new_doc_id = new_doc_ref[1].id  # The document reference is the second element
            
            print(f"✅ Successfully added workout plan with ID: {new_doc_id}")
            
            # Step 2: Verify the plan was added by reading it back
            print("🔍 Verifying the added plan...")
            added_doc = workout_plans_ref.document(new_doc_id).get()
            
            assert added_doc.exists, "The added workout plan should exist"
            
            added_data = added_doc.to_dict()
            assert added_data["name"] == "Test Workout Plan", "Plan name should match"
            assert added_data["durationMinutes"] == 30, "Duration should match"
            assert added_data["level"] == "beginner", "Level should match"
            assert len(added_data["goals"]) == 5, "Should have 5 goals"
            assert len(added_data["micro_workouts"]) == 6, "Should have 6 micro workouts"
            assert len(added_data["weekly_template"]) == 7, "Should have 7 day template"
            
            print("✅ Plan verification successful!")
            print(f"   Name: {added_data['name']}")
            print(f"   Duration: {added_data['durationMinutes']} minutes")
            print(f"   Level: {added_data['level']}")
            print(f"   Goals count: {len(added_data['goals'])}")
            print(f"   Micro workouts count: {len(added_data['micro_workouts'])}")
            
            # Step 3: Update the plan (optional - test update operation)
            print("✏️ Testing plan update...")
            update_data = {
                "description": "Updated test workout plan - now includes advanced modifications.",
                "durationMinutes": 35,
                "goals": added_data["goals"] + ["Build confidence in fitness"]
            }
            
            workout_plans_ref.document(new_doc_id).update(update_data)
            
            # Verify update
            updated_doc = workout_plans_ref.document(new_doc_id).get()
            updated_data = updated_doc.to_dict()
            
            assert updated_data["durationMinutes"] == 35, "Duration should be updated"
            assert len(updated_data["goals"]) == 6, "Should now have 6 goals"
            
            print("✅ Plan update successful!")
            print(f"   Updated duration: {updated_data['durationMinutes']} minutes")
            print(f"   Updated goals count: {len(updated_data['goals'])}")
            
            # Step 4: Check collection count before deletion
            all_workouts_before = workout_plans_ref.get()
            count_before = len(all_workouts_before)
            print(f"📊 Workout plans count before deletion: {count_before}")
            
            # Step 5: Delete the plan
            print("🗑️ Deleting the test workout plan...")
            workout_plans_ref.document(new_doc_id).delete()
            
            print(f"✅ Successfully deleted workout plan: {new_doc_id}")
            
            # Step 6: Verify the plan was deleted
            print("🔍 Verifying deletion...")
            deleted_doc = workout_plans_ref.document(new_doc_id).get()
            
            assert not deleted_doc.exists, "The deleted workout plan should not exist"
            
            # Check collection count after deletion
            all_workouts_after = workout_plans_ref.get()
            count_after = len(all_workouts_after)
            print(f"📊 Workout plans count after deletion: {count_after}")
            
            assert count_after == count_before - 1, "Collection should have one less document"
            
            print("✅ Deletion verification successful!")
            print(f"   Document {new_doc_id} no longer exists")
            print(f"   Collection count reduced by 1: {count_before} → {count_after}")
            
            # Step 7: Try to search for the deleted plan (should not be found)
            print("🔍 Confirming plan is not searchable...")
            search_query = workout_plans_ref.where("name", "==", "Test Workout Plan")
            search_results = search_query.get()
            
            assert len(search_results) == 0, "Deleted plan should not be found in search"
            print("✅ Deleted plan is not found in search results")
            
            print("\n✅ CRUD Test Complete!")
            print("   CREATE: Successfully added workout plan")
            print("   READ: Successfully retrieved and verified plan")
            print("   UPDATE: Successfully modified plan data")
            print("   DELETE: Successfully removed plan from database")
            
            return {
                "operation": "CRUD_TEST_SUCCESS",
                "created_id": new_doc_id,
                "initial_count": count_before,
                "final_count": count_after
            }
            
        except Exception as e:
            print(f"❌ Error in CRUD test: {e}")
            # If we created a document but failed later, try to clean up
            try:
                if 'new_doc_id' in locals():
                    self.db.collection('workoutPlans').document(new_doc_id).delete()
                    print(f"🧹 Cleaned up test document: {new_doc_id}")
            except:
                pass
            raise

