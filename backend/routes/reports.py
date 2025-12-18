from flask import Blueprint, request, jsonify
from models import db, Event, Resource, EventResourceAllocation
from datetime import datetime
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/utilization', methods=['GET'])
def resource_utilization():
    """
    Generate resource utilization report for a date range.
    Query parameters:
    - start_date: Start date (YYYY-MM-DD or ISO format)
    - end_date: End date (YYYY-MM-DD or ISO format)
    - resource_type: Optional filter by resource type (room, instructor, equipment)
    
    Example: /api/reports/utilization?start_date=2025-12-01&end_date=2025-12-31
    """
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        resource_type = request.args.get('resource_type')
        
        if not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: start_date, end_date'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD or ISO format'
            }), 400
        
        # Validate date range
        if start_date >= end_date:
            return jsonify({
                'success': False,
                'error': 'start_date must be before end_date'
            }), 400
        
        # Build query for resources
        resource_query = Resource.query
        if resource_type:
            resource_query = resource_query.filter_by(resource_type=resource_type)
        
        resources = resource_query.all()
        
        utilization_data = []
        
        for resource in resources:
            # Get all events for this resource within the date range
            events = db.session.query(Event).join(
                EventResourceAllocation,
                Event.event_id == EventResourceAllocation.event_id
            ).filter(
                EventResourceAllocation.resource_id == resource.resource_id,
                Event.start_time < end_date,
                Event.end_time > start_date
            ).all()
            
            # Calculate total hours
            total_hours = 0
            upcoming_bookings = []
            past_bookings = []
            
            now = datetime.utcnow()
            
            for event in events:
                # Calculate overlap with the report date range
                event_start = max(event.start_time, start_date)
                event_end = min(event.end_time, end_date)
                
                duration = (event_end - event_start).total_seconds() / 3600  # Convert to hours
                total_hours += duration
                
                # Categorize bookings
                booking_info = {
                    'event_id': event.event_id,
                    'title': event.title,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'duration_hours': round((event.end_time - event.start_time).total_seconds() / 3600, 2)
                }
                
                if event.start_time > now:
                    upcoming_bookings.append(booking_info)
                else:
                    past_bookings.append(booking_info)
            
            utilization_data.append({
                'resource_id': resource.resource_id,
                'resource_name': resource.resource_name,
                'resource_type': resource.resource_type,
                'total_hours_utilized': round(total_hours, 2),
                'total_bookings': len(events),
                'upcoming_bookings_count': len(upcoming_bookings),
                'upcoming_bookings': upcoming_bookings,
                'past_bookings_count': len(past_bookings)
            })
        
        # Sort by total hours (most utilized first)
        utilization_data.sort(key=lambda x: x['total_hours_utilized'], reverse=True)
        
        return jsonify({
            'success': True,
            'report': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'resource_type_filter': resource_type,
                'total_resources': len(utilization_data),
                'data': utilization_data
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reports_bp.route('/conflicts', methods=['GET'])
def conflicts_report():
    """
    Generate a report of all current allocation conflicts in the system.
    This helps identify any data integrity issues.
    """
    try:
        from utils.conflict import check_resource_conflict
        
        all_allocations = EventResourceAllocation.query.all()
        conflicts = []
        
        checked_pairs = set()
        
        for allocation in all_allocations:
            event = allocation.event
            resource_id = allocation.resource_id
            
            # Skip if already checked
            pair_key = f"{event.event_id}-{resource_id}"
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            # Check for conflicts
            is_available, conflict_list = check_resource_conflict(
                resource_id=resource_id,
                start_time=event.start_time,
                end_time=event.end_time,
                exclude_event_id=event.event_id
            )
            
            if not is_available:
                conflicts.append({
                    'event_id': event.event_id,
                    'event_title': event.title,
                    'resource_id': resource_id,
                    'resource_name': allocation.resource.resource_name,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'conflicting_events': conflict_list
                })
        
        return jsonify({
            'success': True,
            'conflicts_found': len(conflicts),
            'conflicts': conflicts
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reports_bp.route('/summary', methods=['GET'])
def system_summary():
    """
    Get overall system summary statistics.
    """
    try:
        total_events = Event.query.count()
        total_resources = Resource.query.count()
        total_allocations = EventResourceAllocation.query.count()
        
        # Count by resource type
        resource_type_counts = db.session.query(
            Resource.resource_type,
            func.count(Resource.resource_id)
        ).group_by(Resource.resource_type).all()
        
        # Upcoming events
        now = datetime.utcnow()
        upcoming_events = Event.query.filter(Event.start_time > now).count()
        past_events = Event.query.filter(Event.end_time <= now).count()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'past_events': past_events,
                'total_resources': total_resources,
                'total_allocations': total_allocations,
                'resources_by_type': {
                    resource_type: count for resource_type, count in resource_type_counts
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
