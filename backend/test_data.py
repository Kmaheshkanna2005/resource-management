from app import create_app
from models import db, Event, Resource, EventResourceAllocation
from datetime import datetime, timedelta

def clear_database():
    """Clear all existing data."""
    print("Clearing existing data...")
    EventResourceAllocation.query.delete()
    Event.query.delete()
    Resource.query.delete()
    db.session.commit()
    print("Database cleared.")

def create_sample_resources():
    """Create 3-4 sample resources."""
    print("\nCreating sample resources...")
    
    resources = [
        Resource(resource_name="Room A1", resource_type="room"),
        Resource(resource_name="Room B2", resource_type="room"),
        Resource(resource_name="Dr. Smith", resource_type="instructor"),
        Resource(resource_name="Projector #1", resource_type="equipment"),
    ]
    
    for resource in resources:
        db.session.add(resource)
    
    db.session.commit()
    print(f"Created {len(resources)} resources:")
    for r in resources:
        print(f"  - {r.resource_name} ({r.resource_type}) [ID: {r.resource_id}]")
    
    return resources

def create_sample_events():
    """Create 3-4 sample events with overlapping time windows."""
    print("\nCreating sample events...")
    
    base_date = datetime(2025, 12, 20, 10, 0, 0)  # Dec 20, 2025, 10:00 AM
    
    events = [
        Event(
            title="AI Workshop",
            start_time=base_date,
            end_time=base_date + timedelta(hours=2),
            description="Introduction to Artificial Intelligence"
        ),
        Event(
            title="Python Seminar",
            start_time=base_date + timedelta(hours=1),  # 11:00 AM (overlaps with AI Workshop)
            end_time=base_date + timedelta(hours=3),     # 1:00 PM
            description="Advanced Python Programming"
        ),
        Event(
            title="Data Science Class",
            start_time=base_date + timedelta(hours=4),  # 2:00 PM (no overlap)
            end_time=base_date + timedelta(hours=6),     # 4:00 PM
            description="Data Science Fundamentals"
        ),
        Event(
            title="Machine Learning Lab",
            start_time=base_date + timedelta(hours=5),  # 3:00 PM (overlaps with Data Science)
            end_time=base_date + timedelta(hours=7),     # 5:00 PM
            description="Hands-on ML Projects"
        ),
    ]
    
    for event in events:
        db.session.add(event)
    
    db.session.commit()
    print(f"Created {len(events)} events:")
    for e in events:
        print(f"  - {e.title} [ID: {e.event_id}]")
        print(f"    Time: {e.start_time.strftime('%Y-%m-%d %H:%M')} - {e.end_time.strftime('%H:%M')}")
    
    return events

def create_sample_allocations(events, resources):
    """Allocate resources to events (including some that will cause conflicts)."""
    print("\nCreating sample allocations...")
    
    # Successful allocations
    allocations = [
        # AI Workshop - Room A1 and Dr. Smith (10:00 - 12:00)
        EventResourceAllocation(event_id=events[0].event_id, resource_id=resources[0].resource_id),
        EventResourceAllocation(event_id=events[0].event_id, resource_id=resources[2].resource_id),
        
        # Python Seminar - Room B2 (11:00 - 1:00, no conflict)
        EventResourceAllocation(event_id=events[1].event_id, resource_id=resources[1].resource_id),
        
        # Data Science Class - Room A1 and Projector (2:00 - 4:00, no conflict with Room A1)
        EventResourceAllocation(event_id=events[2].event_id, resource_id=resources[0].resource_id),
        EventResourceAllocation(event_id=events[2].event_id, resource_id=resources[3].resource_id),
    ]
    
    for allocation in allocations:
        db.session.add(allocation)
    
    db.session.commit()
    print(f"Created {len(allocations)} allocations successfully.")
    
    # Test conflict scenarios
    print("\n" + "="*60)
    print("TESTING CONFLICT SCENARIOS:")
    print("="*60)
    
    print("\n1. Attempting to allocate Room A1 to Python Seminar (11:00-1:00)...")
    print("   This should FAIL because Room A1 is already allocated to AI Workshop (10:00-12:00)")
    print("   Overlap: 11:00-12:00")
    
    print("\n2. Attempting to allocate Dr. Smith to Machine Learning Lab (3:00-5:00)...")
    print("   This should SUCCEED because Dr. Smith is only busy during AI Workshop (10:00-12:00)")
    
    print("\n3. Attempting to allocate Projector to Machine Learning Lab (3:00-5:00)...")
    print("   This should FAIL because Projector is allocated to Data Science Class (2:00-4:00)")
    print("   Overlap: 3:00-4:00")
    
    return allocations

def display_summary():
    """Display summary of created data."""
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)
    
    print(f"\nTotal Events: {Event.query.count()}")
    print(f"Total Resources: {Resource.query.count()}")
    print(f"Total Allocations: {EventResourceAllocation.query.count()}")
    
    print("\n" + "="*60)
    print("RESOURCE ALLOCATION DETAILS")
    print("="*60)
    
    for event in Event.query.all():
        print(f"\n{event.title} (ID: {event.event_id})")
        print(f"  Time: {event.start_time.strftime('%Y-%m-%d %H:%M')} - {event.end_time.strftime('%H:%M')}")
        print(f"  Allocated Resources:")
        if event.allocations:
            for alloc in event.allocations:
                print(f"    - {alloc.resource.resource_name} ({alloc.resource.resource_type})")
        else:
            print(f"    - None")

def main():
    """Main function to populate database with test data."""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("POPULATING DATABASE WITH TEST DATA")
        print("="*60)
        
        # Clear existing data
        clear_database()
        
        # Create sample data
        resources = create_sample_resources()
        events = create_sample_events()
        allocations = create_sample_allocations(events, resources)
        
        # Display summary
        display_summary()
        
        print("\n" + "="*60)
        print("TEST DATA CREATION COMPLETE!")
        print("="*60)
        print("\nYou can now:")
        print("1. Run the Flask app: python app.py")
        print("2. Test the API endpoints with the created data")
        print("3. Try the conflict scenarios mentioned above using the API")
        print("\nAPI Base URL: http://localhost:5000")

if __name__ == '__main__':
    main()
