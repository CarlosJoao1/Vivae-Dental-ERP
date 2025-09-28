import os
from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine

def create_app():
    app = Flask(__name__)
    
    # Configurações via variáveis de ambiente
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-temporaria')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sua-jwt-chave-temporaria')
    app.config['MONGODB_SETTINGS'] = {
        'host': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/vivae-dental-erp')
    }
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', '*').split(',')

    # Inicializa extensões
    CORS(app, origins=app.config['CORS_ORIGINS'])
    db = MongoEngine(app)

    # Blueprint de health check
    from flask import Blueprint
    health = Blueprint('health', __name__)
    
    @health.route('/api/health')
    def health_check():
        return {'status': 'healthy'}, 200

    # Registrar blueprints
    app.register_blueprint(health)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run() 
