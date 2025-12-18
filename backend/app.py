from flask import Flask
from flask_cors import CORS
from config import Config
from models import db

def create_app(config_class=Config):
    """
    Application factory pattern for Flask app creation.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for React frontend
    
    # Register blueprints (we'll create these next)
    from routes.events import events_bp
    from routes.resources import resources_bp
    from routes.allocations import allocations_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')
    app.register_blueprint(allocations_bp, url_prefix='/api/allocations')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    # Root route
    @app.route('/')
    def home():
        return {
            'message': 'Event Scheduling & Resource Allocation API',
            'version': '1.0',
            'endpoints': {
                'events': '/api/events',
                'resources': '/api/resources',
                'allocations': '/api/allocations',
                'reports': '/api/reports'
            }
        }
    
    # Health check route
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
