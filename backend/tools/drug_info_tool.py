"""
Drug Info Tool - Queries drug information
"""

import asyncio
from typing import Dict, Any, Optional
from .base_tool import BaseTool, ToolResult


class DrugInfoTool(BaseTool):
    """Tool for querying drug information from a mock/external API."""
    
    def __init__(self):
        super().__init__(
            name="drug_info",
            description="Retrieves information about medications including dosage, side effects, interactions, and instructions."
        )
        # Mock drug database (in production, this would query an external API)
        self.drug_database = {
            "paracetamol": {
                "name": "Paracetamol (Acetaminophen)",
                "dosage": "Adults: 500-1000mg every 4-6 hours, max 4000mg/day",
                "instructions": "Take with or without food. Do not exceed recommended dose. May take with water.",
                "side_effects": "Rare: skin rash, allergic reactions. Overdose can cause liver damage.",
                "interactions": "May interact with warfarin. Avoid alcohol.",
                "warnings": "Do not use if allergic to paracetamol. Consult doctor if symptoms persist.",
            },
            "ibuprofen": {
                "name": "Ibuprofen",
                "dosage": "Adults: 200-400mg every 4-6 hours, max 1200mg/day",
                "instructions": "Take with food or milk to reduce stomach upset. Swallow whole with water.",
                "side_effects": "Common: stomach upset, nausea. Rare: stomach bleeding, kidney problems.",
                "interactions": "May interact with aspirin, blood thinners, ACE inhibitors.",
                "warnings": "Do not use if you have stomach ulcers or kidney disease. Avoid during pregnancy.",
            },
            "aspirin": {
                "name": "Aspirin (Acetylsalicylic Acid)",
                "dosage": "Adults: 75-325mg daily for heart protection, 325-650mg for pain every 4-6 hours",
                "instructions": "Take with food or water. Do not crush enteric-coated tablets.",
                "side_effects": "Common: stomach irritation. Rare: bleeding, allergic reactions.",
                "interactions": "Interacts with many medications including warfarin, methotrexate.",
                "warnings": "Do not give to children with viral infections. Avoid if bleeding disorder.",
            },
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "Name of the drug to look up (e.g., 'paracetamol', 'ibuprofen')"
                },
                "info_type": {
                    "type": "string",
                    "enum": ["all", "dosage", "instructions", "side_effects", "interactions", "warnings"],
                    "description": "Type of information to retrieve (default: 'all')",
                    "default": "all"
                }
            },
            "required": ["drug_name"]
        }
    
    def validate_args(self, **kwargs) -> bool:
        """Validate drug_name is provided."""
        return "drug_name" in kwargs and isinstance(kwargs["drug_name"], str)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute drug info lookup."""
        drug_name = kwargs.get("drug_name", "").strip().lower()
        info_type = kwargs.get("info_type", "all").lower()
        
        if not drug_name:
            return ToolResult(
                success=False,
                output=None,
                error="Drug name is required"
            )
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Look up drug in database
        drug_info = self.drug_database.get(drug_name)
        
        if not drug_info:
            # Try partial match
            matching_drugs = [
                name for name in self.drug_database.keys()
                if drug_name in name or name in drug_name
            ]
            
            if matching_drugs:
                drug_info = self.drug_database[matching_drugs[0]]
                drug_name = matching_drugs[0]
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Drug '{drug_name}' not found in database. Available drugs: {', '.join(self.drug_database.keys())}",
                    metadata={"available_drugs": list(self.drug_database.keys())}
                )
        
        # Filter by info_type if specified
        if info_type == "all":
            output = drug_info.copy()
        else:
            output = {info_type: drug_info.get(info_type, "Information not available")}
        
        return ToolResult(
            success=True,
            output={
                "drug_name": drug_name,
                "info_type": info_type,
                "data": output
            },
            metadata={
                "tool": "drug_info",
                "drug_found": True,
                "info_type": info_type
            }
        )

