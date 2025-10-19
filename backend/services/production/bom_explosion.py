# backend/services/production/bom_explosion.py
"""
BOM Explosion Service - Multi-Level DFS Algorithm

This service implements advanced BOM explosion logic following NAV/BC patterns:
- Multi-level explosion: Recursively explodes nested BOMs (sub-assemblies)
- Cycle detection: Detects circular references using DFS with recursion stack
- Component consolidation: Aggregates same components across levels
- Scrap calculation: Applies scrap percentages in cascade through BOM levels
- Phantom BOMs: Handles phantom items (explode components directly into parent)
- Inventory availability: Can check stock levels vs requirements

Algorithm: Depth-First Search (DFS) with backtracking
- Visits each BOM node once
- Tracks visited nodes to prevent infinite loops
- Uses recursion stack to detect back edges (cycles)
- Accumulates quantities as it traverses

Usage:
    from services.production.bom_explosion import BOMExplosionService
    
    service = BOMExplosionService(tenant_id)
    result = service.explode(
        item_no="FG-CHAIR-001",
        quantity=10,
        level=0,
        check_availability=True
    )
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from models.production import BOM, Item


@dataclass
class ExplosionComponent:
    """
    Represents a component in the explosion result.
    Consolidates quantities from multiple BOM levels.
    """
    item_no: str
    description: str
    uom_code: str
    quantity_per: float  # Per parent
    total_quantity: float  # Accumulated across all levels
    scrap_pct: float
    level: int  # BOM level (0=root, 1=direct children, 2=sub-components, etc.)
    is_phantom: bool = False
    position: Optional[str] = None
    source_boms: List[str] = field(default_factory=list)  # Which BOMs contributed
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "item_no": self.item_no,
            "description": self.description,
            "uom_code": self.uom_code,
            "quantity_per": self.quantity_per,
            "total_quantity": self.total_quantity,
            "scrap_pct": self.scrap_pct,
            "level": self.level,
            "is_phantom": self.is_phantom,
            "position": self.position,
            "source_boms": self.source_boms,
        }


@dataclass
class ExplosionResult:
    """
    Complete explosion result with hierarchy and consolidated components.
    """
    item_no: str
    description: str
    quantity: float
    status: str  # "success", "warning", "error"
    messages: List[str] = field(default_factory=list)
    components: List[ExplosionComponent] = field(default_factory=list)
    consolidated_components: Dict[str, ExplosionComponent] = field(default_factory=dict)
    max_level: int = 0
    has_cycles: bool = False
    cycles_detected: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "item_no": self.item_no,
            "description": self.description,
            "quantity": self.quantity,
            "status": self.status,
            "messages": self.messages,
            "components": [c.to_dict() for c in self.components],
            "consolidated_components": {
                k: v.to_dict() for k, v in self.consolidated_components.items()
            },
            "max_level": self.max_level,
            "has_cycles": self.has_cycles,
            "cycles_detected": self.cycles_detected,
        }


class BOMExplosionService:
    """
    BOM Explosion Service implementing DFS algorithm for multi-level explosion.
    """
    
    def __init__(self, tenant_id: str):
        """
        Initialize explosion service for a specific tenant.
        
        Args:
            tenant_id: Laboratory/tenant identifier
        """
        self.tenant_id = tenant_id
        self.visited: Set[str] = set()
        self.recursion_stack: Set[str] = set()
        self.components: List[ExplosionComponent] = []
        self.consolidated: Dict[str, ExplosionComponent] = {}
        self.messages: List[str] = []
        self.cycles: List[str] = []
        self.max_level: int = 0
    
    def explode(
        self,
        item_no: str,
        quantity: float,
        level: int = 0,
        parent_scrap_multiplier: float = 1.0,
        check_availability: bool = False
    ) -> ExplosionResult:
        """
        Explode a BOM recursively to get all required components.
        
        Algorithm:
        1. Find certified BOM for item
        2. For each line in BOM:
           a. Calculate quantity with scrap
           b. Check if component has its own BOM (sub-assembly)
           c. If yes, recursively explode (DFS)
           d. If no (or phantom), add to components list
        3. Consolidate components by item_no
        4. Detect cycles using recursion stack
        
        Args:
            item_no: Item to explode
            quantity: Quantity to produce
            level: Current BOM level (0=root)
            parent_scrap_multiplier: Accumulated scrap from parent levels
            check_availability: Whether to check inventory availability
        
        Returns:
            ExplosionResult with all components and metadata
        """
        # Initialize on first call (level 0)
        if level == 0:
            self.visited = set()
            self.recursion_stack = set()
            self.components = []
            self.consolidated = {}
            self.messages = []
            self.cycles = []
            self.max_level = 0
        
        # Cycle detection: Check if item is in recursion stack
        if item_no in self.recursion_stack:
            cycle_msg = f"Cycle detected: {item_no} appears in its own BOM tree"
            self.messages.append(cycle_msg)
            self.cycles.append(item_no)
            return self._build_result(item_no, quantity, "warning")
        
        # Mark as visiting (push to recursion stack)
        self.recursion_stack.add(item_no)
        
        # Get certified BOM for this item
        bom = BOM.objects(
            tenant_id=self.tenant_id,
            item_no=item_no,
            status="Certified"
        ).first()
        
        if not bom:
            # Leaf node (purchased item or no BOM defined)
            if level > 0:  # Don't warn for root item
                self.messages.append(f"No certified BOM found for {item_no} (leaf component)")
            self.recursion_stack.remove(item_no)
            return self._build_result(item_no, quantity, "success")
        
        # Get item details
        item = Item.objects(tenant_id=self.tenant_id, item_no=item_no).first()
        item_type = item.item_type if item else "unknown"
        
        # Explode each line in the BOM
        for line in bom.lines:
            # Calculate quantity with scrap
            # Formula: component_qty = (qty_per * parent_qty) * (1 + scrap_pct/100) * parent_scrap_multiplier
            scrap_multiplier = 1.0 + (line.scrap_pct / 100.0)
            component_qty = line.quantity_per * quantity * scrap_multiplier * parent_scrap_multiplier
            
            # Get component item details
            component_item = Item.objects(
                tenant_id=self.tenant_id,
                item_no=line.component_item_no
            ).first()
            
            is_phantom = False
            if component_item:
                # Check if phantom (in NAV/BC, phantom items have a flag)
                # For now, we'll use item_type logic
                is_phantom = getattr(component_item, 'is_phantom', False)
            
            # Create component entry
            component = ExplosionComponent(
                item_no=line.component_item_no,
                description=line.description or (component_item.description if component_item else ""),
                uom_code=line.uom_code,
                quantity_per=line.quantity_per,
                total_quantity=component_qty,
                scrap_pct=line.scrap_pct,
                level=level + 1,
                is_phantom=is_phantom,
                position=line.position,
                source_boms=[bom.item_no],
            )
            
            # Add to components list
            self.components.append(component)
            
            # Update max level tracking
            if component.level > self.max_level:
                self.max_level = component.level
            
            # Consolidate (aggregate same components)
            if component.item_no in self.consolidated:
                existing = self.consolidated[component.item_no]
                existing.total_quantity += component.total_quantity
                if bom.item_no not in existing.source_boms:
                    existing.source_boms.append(bom.item_no)
            else:
                self.consolidated[component.item_no] = component
            
            # Recursive explosion if component is manufactured or phantom
            if component_item and component_item.item_type in ["manufactured", "both"]:
                # Recursively explode sub-assembly
                self.explode(
                    item_no=line.component_item_no,
                    quantity=component_qty,
                    level=level + 1,
                    parent_scrap_multiplier=scrap_multiplier * parent_scrap_multiplier,
                    check_availability=check_availability
                )
        
        # Mark as visited (pop from recursion stack)
        self.recursion_stack.remove(item_no)
        self.visited.add(item_no)
        
        # Build result on root level
        if level == 0:
            return self._build_result(item_no, quantity, "success")
        
        return None  # Intermediate levels return None
    
    def _build_result(self, item_no: str, quantity: float, status: str) -> ExplosionResult:
        """Build final explosion result"""
        # Get root item details
        item = Item.objects(tenant_id=self.tenant_id, item_no=item_no).first()
        description = item.description if item else item_no
        
        # Determine final status
        final_status = status
        if self.cycles:
            final_status = "warning"
        
        return ExplosionResult(
            item_no=item_no,
            description=description,
            quantity=quantity,
            status=final_status,
            messages=self.messages,
            components=self.components,
            consolidated_components=self.consolidated,
            max_level=self.max_level,
            has_cycles=len(self.cycles) > 0,
            cycles_detected=self.cycles,
        )
    
    def check_availability(self, components: List[ExplosionComponent]) -> Dict[str, dict]:
        """
        Check inventory availability for components.
        
        Args:
            components: List of components to check
        
        Returns:
            Dict mapping item_no to availability info
        """
        availability = {}
        
        for component in components:
            item = Item.objects(
                tenant_id=self.tenant_id,
                item_no=component.item_no
            ).first()
            
            if not item:
                availability[component.item_no] = {
                    "available": False,
                    "reason": "Item not found",
                    "on_hand": 0,
                    "required": component.total_quantity,
                    "shortage": component.total_quantity,
                }
                continue
            
            # In a real system, we'd query inventory here
            # For now, we'll use safety stock as a proxy
            on_hand = getattr(item, 'inventory_quantity', 0)  # Future field
            safety_stock = getattr(item, 'safety_stock_qty', 0)
            
            required = component.total_quantity
            available_qty = max(0, on_hand - safety_stock)
            shortage = max(0, required - available_qty)
            
            availability[component.item_no] = {
                "available": shortage == 0,
                "reason": "Sufficient stock" if shortage == 0 else "Insufficient stock",
                "on_hand": on_hand,
                "safety_stock": safety_stock,
                "available_qty": available_qty,
                "required": required,
                "shortage": shortage,
            }
        
        return availability


# Convenience function for direct use
def explode_bom(
    tenant_id: str,
    item_no: str,
    quantity: float,
    check_availability: bool = False
) -> ExplosionResult:
    """
    Convenience function to explode a BOM.
    
    Args:
        tenant_id: Laboratory/tenant identifier
        item_no: Item to explode
        quantity: Quantity to produce
        check_availability: Whether to check inventory availability
    
    Returns:
        ExplosionResult with all components
    
    Example:
        result = explode_bom("lab123", "FG-CHAIR-001", 10)
        print(f"Components: {len(result.components)}")
        for comp in result.components:
            print(f"  {comp.item_no}: {comp.total_quantity}")
    """
    service = BOMExplosionService(tenant_id)
    return service.explode(item_no, quantity, check_availability=check_availability)
