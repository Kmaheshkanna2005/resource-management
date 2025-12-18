from models import Event, EventResourceAllocation, db
from datetime import datetime

def check_resource_conflict(resource_id, start_time, end_time, exclude_event_id=None):
    """
    Check if a resource is available during the given time period.
    
    Handles all edge cases:
    - Exact overlaps
    - Partial overlaps
    - Nested intervals (new event completely inside existing)
    - Containing intervals (new event completely contains existing)
    - Adjacent events (start = end) are allowed
    
    Args:
        resource_id: ID of the resource to check
        start_time: Start datetime of the event
        end_time: End datetime of the event
        exclude_event_id: Event ID to exclude from conflict check (for updates)
    
    Returns:
        tuple: (is_available: bool, conflicting_events: list)
    """
    
    # Validation: start_time must be before end_time
    if start_time >= end_time:
        return False, [{"error": "Start time must be before end time"}]
    
    # Query for overlapping events
    # Two intervals [A_start, A_end] and [B_start, B_end] overlap if:
    # A_start < B_end AND A_end > B_start
    query = db.session.query(Event, EventResourceAllocation).join(
        EventResourceAllocation, Event.event_id == EventResourceAllocation.event_id
    ).filter(
        EventResourceAllocation.resource_id == resource_id,
        Event.start_time < end_time,      # Existing event starts before our end
        Event.end_time > start_time        # Existing event ends after our start
    )
    
    # Exclude the current event if we're updating
    if exclude_event_id:
        query = query.filter(Event.event_id != exclude_event_id)
    
    conflicts = query.all()
    
    if len(conflicts) == 0:
        return True, []
    
    # Format conflict details
    conflict_details = [
        {
            'event_id': event.event_id,
            'title': event.title,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
            'resource_id': resource_id
        }
        for event, allocation in conflicts
    ]
    
    return False, conflict_details


def check_multiple_resources_conflict(resource_ids, start_time, end_time, exclude_event_id=None):
    """
    Check conflicts for multiple resources at once.
    Useful when allocating multiple resources to a single event.
    
    Args:
        resource_ids: List of resource IDs to check
        start_time: Start datetime of the event
        end_time: End datetime of the event
        exclude_event_id: Event ID to exclude from conflict check
    
    Returns:
        dict: {resource_id: (is_available, conflicts)}
    """
    results = {}
    
    for resource_id in resource_ids:
        is_available, conflicts = check_resource_conflict(
            resource_id, start_time, end_time, exclude_event_id
        )
        results[resource_id] = {
            'is_available': is_available,
            'conflicts': conflicts
        }
    
    return results


def validate_event_time(start_time, end_time):
    """
    Validate event time constraints.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    # Check if start is before end
    if start_time >= end_time:
        return False, "Start time must be before end time"
    
    # Check if times are in the past (optional - uncomment if needed)
    # now = datetime.utcnow()
    # if start_time < now:
    #     return False, "Cannot schedule events in the past"
    
    # Check reasonable duration (optional - e.g., max 12 hours)
    duration = (end_time - start_time).total_seconds() / 3600  # hours
    if duration > 24:
        return False, "Event duration cannot exceed 24 hours"
    
    return True, None
