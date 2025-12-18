from flask import Blueprint, request, jsonify
from models import db, Resource

resources_bp = Blueprint('resources', __name__)


@resources_bp.route('', methods=['GET'])
def get_resources():
    """
    Get all resources.
    Optional query parameter: ?type=room (filter by resource_type)
    """
    try:
        resource_type = request.args.get('type')
        
        if resource_type:
            resources = Resource.query.filter_by(resource_type=resource_type).all()
        else:
            resources = Resource.query.all()
        
        return jsonify({
            'success': True,
            'resources': [resource.to_dict() for resource in resources],
            'count': len(resources)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resources_bp.route('/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """
    Get a single resource by ID.
    """
    try:
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        
        return jsonify({
            'success': True,
            'resource': resource.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resources_bp.route('', methods=['POST'])
def create_resource():
    """
    Create a new resource.
    Expected JSON body:
    {
        "resource_name": "Room A1",
        "resource_type": "room"
    }
    Valid resource_types: room, instructor, equipment
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('resource_name') or not data.get('resource_type'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: resource_name, resource_type'
            }), 400
        
        # Validate resource_type
        valid_types = ['room', 'instructor', 'equipment']
        if data['resource_type'].lower() not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid resource_type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Check for duplicate resource name
        existing_resource = Resource.query.filter_by(
            resource_name=data['resource_name']
        ).first()
        
        if existing_resource:
            return jsonify({
                'success': False,
                'error': 'Resource with this name already exists'
            }), 409
        
        # Create new resource
        new_resource = Resource(
            resource_name=data['resource_name'],
            resource_type=data['resource_type'].lower()
        )
        
        db.session.add(new_resource)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resource created successfully',
            'resource': new_resource.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resources_bp.route('/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    """
    Update an existing resource.
    """
    try:
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        
        data = request.get_json()
        
        # Update resource_name if provided
        if 'resource_name' in data:
            # Check for duplicate name
            existing = Resource.query.filter(
                Resource.resource_name == data['resource_name'],
                Resource.resource_id != resource_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Another resource with this name already exists'
                }), 409
            
            resource.resource_name = data['resource_name']
        
        # Update resource_type if provided
        if 'resource_type' in data:
            valid_types = ['room', 'instructor', 'equipment']
            if data['resource_type'].lower() not in valid_types:
                return jsonify({
                    'success': False,
                    'error': f'Invalid resource_type. Must be one of: {", ".join(valid_types)}'
                }), 400
            
            resource.resource_type = data['resource_type'].lower()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resource updated successfully',
            'resource': resource.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resources_bp.route('/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """
    Delete a resource.
    Note: This will fail if resource has active allocations (due to foreign key constraint).
    """
    try:
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        
        # Check if resource has any allocations
        if resource.allocations:
            return jsonify({
                'success': False,
                'error': f'Cannot delete resource. It has {len(resource.allocations)} active allocation(s). Remove allocations first.'
            }), 400
        
        db.session.delete(resource)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resource deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resources_bp.route('/types', methods=['GET'])
def get_resource_types():
    """
    Get available resource types.
    """
    return jsonify({
        'success': True,
        'resource_types': ['room', 'instructor', 'equipment']
    }), 200
