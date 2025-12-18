from flask import Blueprint, request, jsonify
from models import db, Event, EventResourceAllocation
from datetime import datetime
from utils.conflict import validate_event_time

events_bp = Blueprint('events', __name__)


@events_bp.route('', methods=['GET'])
def get_events():
    """
    Get all events with their allocated resources.
    """
    try:
        events = Event.query.all()
        return jsonify({
            'success': True,
            'events': [event.to_dict() for event in events],
            'count': len(events)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """
    Get a single event by ID.
    """
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        return jsonify({
            'success': True,
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@events_bp.route('', methods=['POST'])
def create_event():
    """
    Create a new event.
    Expected JSON body:
    {
        "title": "Workshop on AI",
        "start_time": "2025-12-20T10:00:00",
        "end_time": "2025-12-20T12:00:00",
        "description": "Introduction to AI"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: title, start_time, end_time'
            }), 400
        
        # Parse datetime strings
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS'
            }), 400
        
        # Validate event times
        is_valid, error_msg = validate_event_time(start_time, end_time)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Create new event
        new_event = Event(
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            description=data.get('description', '')
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event': new_event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """
    Update an existing event.
    """
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            event.title = data['title']
        
        if 'description' in data:
            event.description = data['description']
        
        # Handle time updates
        if 'start_time' in data or 'end_time' in data:
            try:
                start_time = datetime.fromisoformat(data.get('start_time', event.start_time.isoformat()).replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(data.get('end_time', event.end_time.isoformat()).replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid datetime format'
                }), 400
            
            # Validate new times
            is_valid, error_msg = validate_event_time(start_time, end_time)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            event.start_time = start_time
            event.end_time = end_time
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """
    Delete an event (cascades to allocations).
    """
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
