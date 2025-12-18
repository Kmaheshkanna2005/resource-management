from flask import Blueprint, request, jsonify
from models import db, Event, Resource, EventResourceAllocation
from utils.conflict import check_resource_conflict, check_multiple_resources_conflict

allocations_bp = Blueprint('allocations', __name__)


@allocations_bp.route('', methods=['GET'])
def get_allocations():
    """
    Get all allocations.
    Optional query parameters:
    - ?event_id=1 (filter by event)
    - ?resource_id=2 (filter by resource)
    """
    try:
        event_id = request.args.get('event_id', type=int)
        resource_id = request.args.get('resource_id', type=int)
        
        query = EventResourceAllocation.query
        
        if event_id:
            query = query.filter_by(event_id=event_id)
        if resource_id:
            query = query.filter_by(resource_id=resource_id)
        
        allocations = query.all()
        
        # Include event and resource details
        result = []
        for alloc in allocations:
            alloc_dict = alloc.to_dict()
            alloc_dict['event'] = alloc.event.to_dict() if alloc.event else None
            alloc_dict['resource'] = alloc.resource.to_dict() if alloc.resource else None
            result.append(alloc_dict)
        
        return jsonify({
            'success': True,
            'allocations': result,
            'count': len(result)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@allocations_bp.route('', methods=['POST'])
def create_allocation():
    """
    Allocate a resource to an event with conflict detection.
    Expected JSON body:
    {
        "event_id": 1,
        "resource_id": 2
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('event_id') or not data.get('resource_id'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: event_id, resource_id'
            }), 400
        
        event_id = data['event_id']
        resource_id = data['resource_id']
        
        # Check if event exists
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': f'Event with ID {event_id} not found'
            }), 404
        
        # Check if resource exists
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({
                'success': False,
                'error': f'Resource with ID {resource_id} not found'
            }), 404
        
        # Check if allocation already exists
        existing_allocation = EventResourceAllocation.query.filter_by(
            event_id=event_id,
            resource_id=resource_id
        ).first()
        
        if existing_allocation:
            return jsonify({
                'success': False,
                'error': 'This resource is already allocated to this event'
            }), 409
        
        # **CONFLICT DETECTION** - This is the key logic!
        is_available, conflicts = check_resource_conflict(
            resource_id=resource_id,
            start_time=event.start_time,
            end_time=event.end_time,
            exclude_event_id=None
        )
        
        if not is_available:
            return jsonify({
                'success': False,
                'error': 'Resource conflict detected',
                'conflicts': conflicts
            }), 409
        
        # Create allocation
        new_allocation = EventResourceAllocation(
            event_id=event_id,
            resource_id=resource_id
        )
        
        db.session.add(new_allocation)
        db.session.commit()
        
        # Return allocation with event and resource details
        result = new_allocation.to_dict()
        result['event'] = event.to_dict()
        result['resource'] = resource.to_dict()
        
        return jsonify({
            'success': True,
            'message': 'Resource allocated successfully',
            'allocation': result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@allocations_bp.route('/batch', methods=['POST'])
def create_batch_allocations():
    """
    Allocate multiple resources to an event at once.
    Expected JSON body:
    {
        "event_id": 1,
        "resource_ids": [1, 2, 3]
    }
    """
    try:
        data = request.get_json()
        
        if not data.get('event_id') or not data.get('resource_ids'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: event_id, resource_ids'
            }), 400
        
        event_id = data['event_id']
        resource_ids = data['resource_ids']
        
        # Check if event exists
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': f'Event with ID {event_id} not found'
            }), 404
        
        # Check conflicts for all resources
        conflict_results = check_multiple_resources_conflict(
            resource_ids=resource_ids,
            start_time=event.start_time,
            end_time=event.end_time,
            exclude_event_id=None
        )
        
        # Check if any resource has conflicts
        conflicts_found = {}
        for res_id, result in conflict_results.items():
            if not result['is_available']:
                conflicts_found[res_id] = result['conflicts']
        
        if conflicts_found:
            return jsonify({
                'success': False,
                'error': 'One or more resources have conflicts',
                'conflicts': conflicts_found
            }), 409
        
        # Allocate all resources
        allocated = []
        for resource_id in resource_ids:
            # Check if already allocated
            existing = EventResourceAllocation.query.filter_by(
                event_id=event_id,
                resource_id=resource_id
            ).first()
            
            if not existing:
                allocation = EventResourceAllocation(
                    event_id=event_id,
                    resource_id=resource_id
                )
                db.session.add(allocation)
                allocated.append(resource_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully allocated {len(allocated)} resource(s)',
            'allocated_resource_ids': allocated
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@allocations_bp.route('/<int:allocation_id>', methods=['DELETE'])
def delete_allocation(allocation_id):
    """
    Remove a resource allocation.
    """
    try:
        allocation = EventResourceAllocation.query.get(allocation_id)
        if not allocation:
            return jsonify({
                'success': False,
                'error': 'Allocation not found'
            }), 404
        
        db.session.delete(allocation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Allocation removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@allocations_bp.route('/conflicts', methods=['POST'])
def check_conflicts():
    """
    Check for conflicts without creating allocation (preview/validation endpoint).
    Expected JSON body:
    {
        "resource_id": 1,
        "start_time": "2025-12-20T10:00:00",
        "end_time": "2025-12-20T12:00:00",
        "exclude_event_id": 5  (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['resource_id', 'start_time', 'end_time']):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: resource_id, start_time, end_time'
            }), 400
        
        from datetime import datetime
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        is_available, conflicts = check_resource_conflict(
            resource_id=data['resource_id'],
            start_time=start_time,
            end_time=end_time,
            exclude_event_id=data.get('exclude_event_id')
        )
        
        return jsonify({
            'success': True,
            'is_available': is_available,
            'conflicts': conflicts
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
