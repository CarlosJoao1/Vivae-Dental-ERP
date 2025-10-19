"""
Production Journals API Routes - Consumption/Output/Capacity posting
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
from config.db import db
from config.auth import token_required, get_tenant_from_token
from models.production_journal import ProductionJournal
from models.item_ledger_entry import ItemLedgerEntry
from models.capacity_ledger_entry import CapacityLedgerEntry
from services.posting_service import PostingService

journals_bp = Blueprint('journals', __name__)

@journals_bp.route('/consumption', methods=['POST'])
@token_required
def post_consumption():
    """
    Post material consumption
    
    Body:
    {
        "posting_id": "uuid",
        "production_order_no": "PO-2025-001",
        "work_center_code": "MACHINING",
        "operation_no": 10,
        "items": [
            {"item_no": "RM-001", "quantity": 5.0, "uom_code": "KG", "description": "Steel plate"},
            {"item_no": "RM-002", "quantity": 2.0, "uom_code": "L", "description": "Cutting fluid"}
        ],
        "notes": "Material consumption for Op 10"
    }
    """
    try:
        tenant_id = get_tenant_from_token()
        data = request.json
        
        # Get user from token (future: extract from JWT)
        posted_by = "system"  # TODO: Extract from JWT
        
        # Post consumption
        result = PostingService.post_consumption(tenant_id, data, posted_by)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journals_bp.route('/output', methods=['POST'])
@token_required
def post_output():
    """
    Post finished goods output
    
    Body:
    {
        "posting_id": "uuid",
        "production_order_no": "PO-2025-001",
        "item_no": "FG-CHAIR-001",
        "quantity": 10.0,
        "uom_code": "UN",
        "work_center_code": "ASSEMBLY",
        "operation_no": 20,
        "notes": "Finished 10 chairs"
    }
    """
    try:
        tenant_id = get_tenant_from_token()
        data = request.json
        
        posted_by = "system"  # TODO: Extract from JWT
        
        # Post output
        result = PostingService.post_output(tenant_id, data, posted_by)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journals_bp.route('/capacity', methods=['POST'])
@token_required
def post_capacity():
    """
    Post capacity usage
    
    Body:
    {
        "posting_id": "uuid",
        "production_order_no": "PO-2025-001",
        "operation_no": 10,
        "work_center_code": "MACHINING",
        "machine_center_code": "CNC-001",
        "item_no": "FG-CHAIR-001",
        "setup_time": 30.0,
        "run_time": 80.0,
        "stop_time": 0.0,
        "scrap_time": 0.0,
        "quantity": 10.0,
        "scrap_quantity": 0.0,
        "operator_id": "OPER-001",
        "operator_name": "João Silva",
        "notes": "Operation 10 completed"
    }
    """
    try:
        tenant_id = get_tenant_from_token()
        data = request.json
        
        posted_by = "system"  # TODO: Extract from JWT
        
        # Post capacity
        result = PostingService.post_capacity(tenant_id, data, posted_by)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journals_bp.route('/', methods=['GET'])
@token_required
def list_journals():
    """
    List all production journals
    
    Query params:
    - journal_type: Filter by type (Consumption/Output/Capacity)
    - production_order_no: Filter by order
    - from_date, to_date: Date range
    - limit: Max results (default 100)
    - offset: Pagination offset (default 0)
    """
    try:
        tenant_id = get_tenant_from_token()
        
        # Build query
        query = ProductionJournal.query.filter_by(tenant_id=tenant_id)
        
        # Apply filters
        journal_type = request.args.get('journal_type')
        if journal_type:
            query = query.filter_by(journal_type=journal_type)
        
        order_no = request.args.get('production_order_no')
        if order_no:
            query = query.filter_by(production_order_no=order_no)
        
        from_date = request.args.get('from_date')
        if from_date:
            query = query.filter(ProductionJournal.posting_date >= datetime.fromisoformat(from_date))
        
        to_date = request.args.get('to_date')
        if to_date:
            query = query.filter(ProductionJournal.posting_date <= datetime.fromisoformat(to_date))
        
        # Pagination
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Execute
        journals = query.order_by(ProductionJournal.posting_date.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'journals': [j.to_dict() for j in journals],
            'count': len(journals),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journals_bp.route('/ledger/items', methods=['GET'])
@token_required
def query_item_ledger():
    """
    Query Item Ledger Entries
    
    Query params:
    - item_no: Filter by item
    - entry_type: Filter by type (Consumption/Output)
    - production_order_no: Filter by order
    - from_date, to_date: Date range
    - limit, offset: Pagination
    """
    try:
        tenant_id = get_tenant_from_token()
        
        # Build query
        query = ItemLedgerEntry.query.filter_by(tenant_id=tenant_id)
        
        # Apply filters
        item_no = request.args.get('item_no')
        if item_no:
            query = query.filter_by(item_no=item_no)
        
        entry_type = request.args.get('entry_type')
        if entry_type:
            query = query.filter_by(entry_type=entry_type)
        
        order_no = request.args.get('production_order_no')
        if order_no:
            query = query.filter_by(production_order_no=order_no)
        
        from_date = request.args.get('from_date')
        if from_date:
            query = query.filter(ItemLedgerEntry.posting_date >= datetime.fromisoformat(from_date))
        
        to_date = request.args.get('to_date')
        if to_date:
            query = query.filter(ItemLedgerEntry.posting_date <= datetime.fromisoformat(to_date))
        
        # Pagination
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Execute
        entries = query.order_by(ItemLedgerEntry.posting_date.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'entries': [e.to_dict() for e in entries],
            'count': len(entries),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journals_bp.route('/ledger/capacity', methods=['GET'])
@token_required
def query_capacity_ledger():
    """
    Query Capacity Ledger Entries
    
    Query params:
    - work_center_code: Filter by work center
    - machine_center_code: Filter by machine
    - production_order_no: Filter by order
    - operator_id: Filter by operator
    - from_date, to_date: Date range
    - limit, offset: Pagination
    """
    try:
        tenant_id = get_tenant_from_token()
        
        # Build query
        query = CapacityLedgerEntry.query.filter_by(tenant_id=tenant_id)
        
        # Apply filters
        wc_code = request.args.get('work_center_code')
        if wc_code:
            query = query.filter_by(work_center_code=wc_code)
        
        mc_code = request.args.get('machine_center_code')
        if mc_code:
            query = query.filter_by(machine_center_code=mc_code)
        
        order_no = request.args.get('production_order_no')
        if order_no:
            query = query.filter_by(production_order_no=order_no)
        
        operator_id = request.args.get('operator_id')
        if operator_id:
            query = query.filter_by(operator_id=operator_id)
        
        from_date = request.args.get('from_date')
        if from_date:
            query = query.filter(CapacityLedgerEntry.posting_date >= datetime.fromisoformat(from_date))
        
        to_date = request.args.get('to_date')
        if to_date:
            query = query.filter(CapacityLedgerEntry.posting_date <= datetime.fromisoformat(to_date))
        
        # Pagination
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Execute
        entries = query.order_by(CapacityLedgerEntry.posting_date.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'entries': [e.to_dict() for e in entries],
            'count': len(entries),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
