"""
Production Posting Service - Handles consumption/output/capacity postings with idempotency
"""
from datetime import datetime
from typing import Dict, Any, List
from config.db import db
from models.item_ledger_entry import ItemLedgerEntry
from models.capacity_ledger_entry import CapacityLedgerEntry
from models.production_journal import ProductionJournal
from models.production_order import ProductionOrder
from models.work_center import WorkCenter
from models.service import Service  # Items are in Service model
from sqlalchemy.exc import IntegrityError

class PostingService:
    """Service for posting production journals with idempotency"""
    
    @staticmethod
    def validate_consumption(tenant_id: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate consumption posting
        Returns: (is_valid, error_message)
        """
        # Check required fields
        if not data.get('posting_id'):
            return False, "posting_id is required"
        if not data.get('production_order_no'):
            return False, "production_order_no is required"
        if not data.get('items') or len(data['items']) == 0:
            return False, "At least one item is required"
        
        # Check production order exists
        order = ProductionOrder.query.filter_by(
            tenant_id=tenant_id,
            order_no=data['production_order_no']
        ).first()
        if not order:
            return False, f"Production order {data['production_order_no']} not found"
        
        # Validate each item
        for item in data['items']:
            if not item.get('item_no'):
                return False, "item_no is required for each item"
            if not item.get('quantity') or item['quantity'] <= 0:
                return False, "quantity must be > 0 for each item"
            
            # Check item exists
            item_obj = Service.query.filter_by(
                tenant_id=tenant_id,
                item_no=item['item_no']
            ).first()
            if not item_obj:
                return False, f"Item {item['item_no']} not found"
        
        return True, ""
    
    @staticmethod
    def post_consumption(tenant_id: str, data: Dict[str, Any], posted_by: str) -> Dict[str, Any]:
        """
        Post material consumption
        Returns: {'success': bool, 'posting_id': str, 'entries_created': int, 'message': str}
        """
        # Check idempotency - if posting_id already exists, return success
        existing_journal = ProductionJournal.query.filter_by(
            tenant_id=tenant_id,
            posting_id=data['posting_id']
        ).first()
        
        if existing_journal:
            # Already posted, return success with existing data
            entries_count = ItemLedgerEntry.query.filter_by(
                tenant_id=tenant_id,
                posting_id=data['posting_id']
            ).count()
            return {
                'success': True,
                'posting_id': str(existing_journal.posting_id),
                'entries_created': entries_count,
                'message': 'Posting already exists (idempotent)',
                'already_posted': True
            }
        
        # Validate before posting
        is_valid, error_msg = PostingService.validate_consumption(tenant_id, data)
        if not is_valid:
            return {'success': False, 'message': error_msg}
        
        try:
            # Create journal header
            journal = ProductionJournal(
                posting_id=data['posting_id'],
                tenant_id=tenant_id,
                journal_type='Consumption',
                production_order_no=data['production_order_no'],
                posting_date=datetime.utcnow(),
                posted_by=posted_by,
                notes=data.get('notes'),
                created_by=posted_by
            )
            db.session.add(journal)
            
            # Create item ledger entries
            entries_created = 0
            for item in data['items']:
                entry = ItemLedgerEntry(
                    posting_id=data['posting_id'],
                    tenant_id=tenant_id,
                    item_no=item['item_no'],
                    description=item.get('description'),
                    quantity=-abs(item['quantity']),  # Negative for consumption
                    uom_code=item.get('uom_code', 'UN'),
                    entry_type='Consumption',
                    source_type='ProductionOrder',
                    production_order_no=data['production_order_no'],
                    work_center_code=data.get('work_center_code'),
                    operation_no=data.get('operation_no'),
                    posting_date=datetime.utcnow(),
                    posted_by=posted_by,
                    created_by=posted_by
                )
                db.session.add(entry)
                entries_created += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'posting_id': str(journal.posting_id),
                'entries_created': entries_created,
                'message': 'Consumption posted successfully',
                'already_posted': False
            }
            
        except IntegrityError as e:
            db.session.rollback()
            # Race condition - another process posted with same posting_id
            return {
                'success': True,
                'posting_id': str(data['posting_id']),
                'message': 'Posting already exists (race condition handled)',
                'already_posted': True
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error posting consumption: {str(e)}'}
    
    @staticmethod
    def validate_output(tenant_id: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate output posting
        Returns: (is_valid, error_message)
        """
        # Check required fields
        if not data.get('posting_id'):
            return False, "posting_id is required"
        if not data.get('production_order_no'):
            return False, "production_order_no is required"
        if not data.get('item_no'):
            return False, "item_no is required"
        if not data.get('quantity') or data['quantity'] <= 0:
            return False, "quantity must be > 0"
        
        # Check production order exists
        order = ProductionOrder.query.filter_by(
            tenant_id=tenant_id,
            order_no=data['production_order_no']
        ).first()
        if not order:
            return False, f"Production order {data['production_order_no']} not found"
        
        # Check item exists and is manufactured
        item = Service.query.filter_by(
            tenant_id=tenant_id,
            item_no=data['item_no']
        ).first()
        if not item:
            return False, f"Item {data['item_no']} not found"
        
        return True, ""
    
    @staticmethod
    def post_output(tenant_id: str, data: Dict[str, Any], posted_by: str) -> Dict[str, Any]:
        """
        Post finished goods output
        Returns: {'success': bool, 'posting_id': str, 'message': str}
        """
        # Check idempotency
        existing_journal = ProductionJournal.query.filter_by(
            tenant_id=tenant_id,
            posting_id=data['posting_id']
        ).first()
        
        if existing_journal:
            return {
                'success': True,
                'posting_id': str(existing_journal.posting_id),
                'message': 'Posting already exists (idempotent)',
                'already_posted': True
            }
        
        # Validate
        is_valid, error_msg = PostingService.validate_output(tenant_id, data)
        if not is_valid:
            return {'success': False, 'message': error_msg}
        
        try:
            # Create journal header
            journal = ProductionJournal(
                posting_id=data['posting_id'],
                tenant_id=tenant_id,
                journal_type='Output',
                production_order_no=data['production_order_no'],
                posting_date=datetime.utcnow(),
                posted_by=posted_by,
                notes=data.get('notes'),
                created_by=posted_by
            )
            db.session.add(journal)
            
            # Create item ledger entry
            entry = ItemLedgerEntry(
                posting_id=data['posting_id'],
                tenant_id=tenant_id,
                item_no=data['item_no'],
                description=data.get('description'),
                quantity=abs(data['quantity']),  # Positive for output
                uom_code=data.get('uom_code', 'UN'),
                entry_type='Output',
                source_type='ProductionOrder',
                production_order_no=data['production_order_no'],
                work_center_code=data.get('work_center_code'),
                operation_no=data.get('operation_no'),
                posting_date=datetime.utcnow(),
                posted_by=posted_by,
                created_by=posted_by
            )
            db.session.add(entry)
            
            db.session.commit()
            
            return {
                'success': True,
                'posting_id': str(journal.posting_id),
                'message': 'Output posted successfully',
                'already_posted': False
            }
            
        except IntegrityError:
            db.session.rollback()
            return {
                'success': True,
                'posting_id': str(data['posting_id']),
                'message': 'Posting already exists (race condition handled)',
                'already_posted': True
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error posting output: {str(e)}'}
    
    @staticmethod
    def validate_capacity(tenant_id: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate capacity posting
        Returns: (is_valid, error_message)
        """
        # Check required fields
        if not data.get('posting_id'):
            return False, "posting_id is required"
        if not data.get('production_order_no'):
            return False, "production_order_no is required"
        if not data.get('operation_no'):
            return False, "operation_no is required"
        if not data.get('work_center_code'):
            return False, "work_center_code is required"
        
        # Check times are valid
        setup_time = data.get('setup_time', 0)
        run_time = data.get('run_time', 0)
        if setup_time < 0 or run_time < 0:
            return False, "Times must be >= 0"
        if setup_time == 0 and run_time == 0:
            return False, "At least one time value must be > 0"
        
        # Check work center exists
        wc = WorkCenter.query.filter_by(
            tenant_id=tenant_id,
            code=data['work_center_code']
        ).first()
        if not wc:
            return False, f"Work center {data['work_center_code']} not found"
        
        return True, ""
    
    @staticmethod
    def post_capacity(tenant_id: str, data: Dict[str, Any], posted_by: str) -> Dict[str, Any]:
        """
        Post capacity usage
        Returns: {'success': bool, 'posting_id': str, 'message': str}
        """
        # Check idempotency
        existing_journal = ProductionJournal.query.filter_by(
            tenant_id=tenant_id,
            posting_id=data['posting_id']
        ).first()
        
        if existing_journal:
            return {
                'success': True,
                'posting_id': str(existing_journal.posting_id),
                'message': 'Posting already exists (idempotent)',
                'already_posted': True
            }
        
        # Validate
        is_valid, error_msg = PostingService.validate_capacity(tenant_id, data)
        if not is_valid:
            return {'success': False, 'message': error_msg}
        
        try:
            # Create journal header
            journal = ProductionJournal(
                posting_id=data['posting_id'],
                tenant_id=tenant_id,
                journal_type='Capacity',
                production_order_no=data['production_order_no'],
                posting_date=datetime.utcnow(),
                posted_by=posted_by,
                notes=data.get('notes'),
                created_by=posted_by
            )
            db.session.add(journal)
            
            # Create capacity ledger entry
            entry = CapacityLedgerEntry(
                posting_id=data['posting_id'],
                tenant_id=tenant_id,
                work_center_code=data['work_center_code'],
                machine_center_code=data.get('machine_center_code'),
                operation_no=data['operation_no'],
                production_order_no=data['production_order_no'],
                item_no=data.get('item_no'),
                setup_time=data.get('setup_time', 0),
                run_time=data.get('run_time', 0),
                stop_time=data.get('stop_time', 0),
                scrap_time=data.get('scrap_time', 0),
                quantity=data.get('quantity', 0),
                scrap_quantity=data.get('scrap_quantity', 0),
                operator_id=data.get('operator_id'),
                operator_name=data.get('operator_name'),
                posting_date=datetime.utcnow(),
                posted_by=posted_by,
                created_by=posted_by
            )
            db.session.add(entry)
            
            db.session.commit()
            
            return {
                'success': True,
                'posting_id': str(journal.posting_id),
                'message': 'Capacity posted successfully',
                'already_posted': False
            }
            
        except IntegrityError:
            db.session.rollback()
            return {
                'success': True,
                'posting_id': str(data['posting_id']),
                'message': 'Posting already exists (race condition handled)',
                'already_posted': True
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error posting capacity: {str(e)}'}
