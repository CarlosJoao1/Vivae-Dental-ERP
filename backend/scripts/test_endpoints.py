# backend/scripts/test_endpoints.py
"""
Quick endpoint tester for Production Module NAV++
Tests that seed data is accessible via API
"""
import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:5000"
USERNAME = "admin"
PASSWORD = "admin123"

# ANSI colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class EndpointTester:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.tests_passed = 0
        self.tests_failed = 0

    def login(self) -> bool:
        """Authenticate and get access token"""
        print(f"\n{BLUE}🔐 Logging in as {self.username}...{RESET}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                
                # Get user info to extract tenant
                me_response = requests.get(
                    f"{self.base_url}/api/auth/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=5
                )
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    self.tenant_id = user_data.get("tenant_id")
                    print(f"{GREEN}✅ Login successful! Tenant: {self.tenant_id}{RESET}")
                    return True
            
            print(f"{RED}❌ Login failed: {response.status_code}{RESET}")
            return False
            
        except Exception as e:
            print(f"{RED}❌ Login error: {e}{RESET}")
            return False

    def get(self, endpoint: str, description: str, expected_count: Optional[int] = None):
        """Test GET endpoint"""
        print(f"\n{YELLOW}📍 Testing: {description}{RESET}")
        print(f"   GET {endpoint}")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            if self.tenant_id:
                headers["X-Tenant-Id"] = self.tenant_id
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    if "items" in data:
                        count = len(data["items"])
                    elif "data" in data:
                        count = len(data["data"]) if isinstance(data["data"], list) else 1
                    else:
                        count = 1
                else:
                    count = len(data) if isinstance(data, list) else 1
                
                print(f"{GREEN}✅ Success! Returned {count} item(s){RESET}")
                
                if expected_count is not None:
                    if count == expected_count:
                        print(f"{GREEN}   ✓ Expected count matches: {count}{RESET}")
                    else:
                        print(f"{YELLOW}   ⚠ Expected {expected_count}, got {count}{RESET}")
                
                # Show sample data (first item only, truncated)
                if isinstance(data, dict) and "items" in data and data["items"]:
                    item = data["items"][0]
                    print(f"{BLUE}   Sample: {json.dumps(item, indent=2)[:200]}...{RESET}")
                elif isinstance(data, list) and data:
                    item = data[0]
                    print(f"{BLUE}   Sample: {json.dumps(item, indent=2)[:200]}...{RESET}")
                
                self.tests_passed += 1
                return True
            else:
                print(f"{RED}❌ Failed: {response.status_code} - {response.text[:200]}{RESET}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
            self.tests_failed += 1
            return False

    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"\n{'='*60}")
        print(f"{BLUE}🧪 PRODUCTION MODULE NAV++ - ENDPOINT TESTS{RESET}")
        print(f"{'='*60}")
        
        # Login first
        if not self.login():
            print(f"\n{RED}❌ Cannot proceed without authentication{RESET}")
            return
        
        # Test Master Data
        print(f"\n{BLUE}📦 MASTER DATA TESTS{RESET}")
        self.get("/api/production/masterdata/items", "List all Items", expected_count=3)
        self.get("/api/production/masterdata/uom", "List all UOMs", expected_count=5)
        self.get("/api/production/masterdata/locations", "List all Locations", expected_count=1)
        self.get("/api/production/masterdata/suppliers", "List all Suppliers", expected_count=1)
        
        # Test Work Centers
        print(f"\n{BLUE}🏭 WORK/MACHINE CENTERS TESTS{RESET}")
        self.get("/api/production/work-centers", "List all Work Centers", expected_count=3)
        self.get("/api/production/machine-centers", "List all Machine Centers", expected_count=2)
        self.get("/api/production/work-centers/by-code/ASSEMBLY", "Get Work Center by code")
        
        # Test BOMs
        print(f"\n{BLUE}📋 BOM TESTS{RESET}")
        self.get("/api/production/boms", "List all BOMs", expected_count=1)
        self.get("/api/production/boms/certified/FG-CHAIR-001", "Get Certified BOM for FG-CHAIR-001")
        self.get("/api/production/boms/by-item/FG-CHAIR-001", "Get all BOMs for FG-CHAIR-001")
        
        # Test Routings
        print(f"\n{BLUE}🛣️ ROUTING TESTS{RESET}")
        self.get("/api/production/routings", "List all Routings", expected_count=1)
        self.get("/api/production/routings/certified/FG-CHAIR-001", "Get Certified Routing for FG-CHAIR-001")
        self.get("/api/production/routings/by-item/FG-CHAIR-001", "Get all Routings for FG-CHAIR-001")
        
        # Test Production Orders
        print(f"\n{BLUE}📦 PRODUCTION ORDERS TESTS{RESET}")
        self.get("/api/production/production-orders", "List all Production Orders", expected_count=2)
        self.get("/api/production/production-orders/by-status/Planned", "Get Planned orders", expected_count=1)
        self.get("/api/production/production-orders/by-status/Released", "Get Released orders", expected_count=1)
        self.get("/api/production/production-orders/by-item/FG-CHAIR-001", "Get orders by item")
        
        # Test Dependency Check
        print(f"\n{BLUE}🔍 DEPENDENCY CHECK TEST{RESET}")
        self.get("/api/production/masterdata/dependency-check", "Check production dependencies")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"{BLUE}📊 TEST SUMMARY{RESET}")
        print(f"{'='*60}")
        total = self.tests_passed + self.tests_failed
        print(f"   Total Tests: {total}")
        print(f"   {GREEN}Passed: {self.tests_passed}{RESET}")
        print(f"   {RED}Failed: {self.tests_failed}{RESET}")
        
        if self.tests_failed == 0:
            print(f"\n{GREEN}🎉 ALL TESTS PASSED! 🎉{RESET}")
        else:
            print(f"\n{YELLOW}⚠️  Some tests failed. Check endpoints above.{RESET}")
        
        print()


def main():
    tester = EndpointTester(BASE_URL, USERNAME, PASSWORD)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
