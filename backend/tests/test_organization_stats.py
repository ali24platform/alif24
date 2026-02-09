import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.core.database import get_db
from app.middleware.deps import only_organization
from app.models import User, OrganizationProfile, StudentProfile, TeacherProfile
from app.crm.models import Lead, Activity, LeadStatus, ActivityType

from app.models.rbac_models import UserRole

class TestOrganizationStats(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.client = TestClient(app)
        
        # Override get_db
        def override_get_db():
            yield self.mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Override only_organization
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 1
        self.mock_user.email = "test@org.com"
        self.mock_user.role = UserRole.organization
        self.mock_user.organization_profile = MagicMock(spec=OrganizationProfile)
        self.mock_user.organization_profile.id = 999
        
        def override_only_organization():
            return self.mock_user
            
        app.dependency_overrides[only_organization] = override_only_organization
        
        # Also override underlying dependencies just in case
        from app.middleware.auth import get_current_user
        from app.middleware.deps import get_current_active_user
        
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_current_active_user] = lambda: self.mock_user


    def tearDown(self):
        app.dependency_overrides = {}

    def test_get_dashboard_stats_success(self):
        """Test getting organization dashboard stats successfully"""
        # Configure the mock query chain
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        # Make chainable methods return the mock_query itself
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # 1. Total Students -> scalar()
        # 2. Total Leads -> scalar()
        # 3. Leads by Status -> all()
        # 4. Recent Activities -> all()
        # 5. Total Teachers -> scalar()
        
        # Set return values for scalar()
        # Order: Students (150), Leads (50), Teachers (10)
        mock_query.scalar.side_effect = [150, 50, 10]
        
        # Set return values for all()
        # Order: Leads by Status, Recent Activities
        
        # Status Data
        mock_status_1 = MagicMock()
        mock_status_1.status = LeadStatus.NEW
        mock_status_1.value = 'new' # Mocking the Enum value access if needed, or just tuple unpacking
        # The query returns list of tuples: (LeadStatus enum, count)
        # But wait, in the router: `for status, count in leads_by_status_result`
        # So we should return a list of tuples.
        # But LeadStatus is an Enum. The router does `status.value`.
        # So the first element of tuple must be an Enum object or mock with .value
        
        status_new = MagicMock()
        status_new.value = 'new'
        status_won = MagicMock()
        status_won.value = 'won'
        
        leads_by_status_data = [
            (status_new, 30),
            (status_won, 20)
        ]
        
        # Activities Data
        activity_1 = MagicMock(spec=Activity)
        activity_1.id = 1
        activity_1.type = ActivityType.CALL
        activity_1.summary = "Called lead"
        activity_1.created_at = datetime(2023, 1, 1, 12, 0, 0)
        activity_1.lead = MagicMock(spec=Lead)
        activity_1.lead.first_name = "John"
        activity_1.lead.last_name = "Doe"
        
        recent_activities_data = [activity_1]
        
        mock_query.all.side_effect = [leads_by_status_data, recent_activities_data]
        
        # Make the request
        response = self.client.get("/api/v1/org-dashboard/stats")
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['total_students'], 150)
        self.assertEqual(data['total_leads'], 50)
        self.assertEqual(data['total_teachers'], 10)
        
        # Check leads by status
        self.assertEqual(len(data['leads_by_status']), 2)
        self.assertEqual(data['leads_by_status'][0]['name'], 'new')
        self.assertEqual(data['leads_by_status'][0]['value'], 30)
        
        # Check activities
        self.assertEqual(len(data['recent_activities']), 1)
        self.assertEqual(data['recent_activities'][0]['summary'], "Called lead")
        self.assertEqual(data['recent_activities'][0]['lead_name'], "John Doe")
        self.assertEqual(data['recent_activities'][0]['type'], "call")

    def test_get_dashboard_stats_error(self):
        """Test error handling in stats endpoint"""
        # Mock database raising exception
        self.mock_db.query.side_effect = Exception("DB Connection Failed")
        
        response = self.client.get("/api/v1/org-dashboard/stats")
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], "Statistikani yuklashda xatolik yuz berdi")

if __name__ == '__main__':
    unittest.main()
