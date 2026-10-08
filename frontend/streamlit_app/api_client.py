import os
from typing import Optional, Dict, Any, List
import httpx

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")


class APIClient:
    """
    Robust HTTP REST API client connecting the Streamlit front-desk interface
    to the FastAPI application backend.
    """
    def __init__(self, base_url: str = BACKEND_API_URL, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text}

        if response.is_success:
            return data
        
        # Format informative error message
        error_msg = f"HTTP {response.status_code}"
        if isinstance(data, dict):
            if "message" in data:
                error_msg = f"{data.get('error_code', 'ERROR')}: {data['message']}"
            elif "detail" in data:
                error_msg = str(data["detail"])
            else:
                error_msg = str(data)
        raise RuntimeError(error_msg)

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------
    def login(self, username: str, password: str) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            data = self._handle_response(resp)
            if "access_token" in data:
                self.token = data["access_token"]
            return data

    def get_me(self) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/auth/me", headers=self._headers())
            return self._handle_response(resp)

    # -------------------------------------------------------------------------
    # Seats & Inventory
    # -------------------------------------------------------------------------
    def get_seats(self) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/seats", headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    def get_seat_availability(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if target_date:
            params["target_date"] = target_date
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/seats/availability", params=params, headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            if isinstance(data, dict) and "seats" in data:
                return data["seats"]
            return data if isinstance(data, list) else []

    def toggle_seat_maintenance(self, seat_id: int) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.put(f"{self.base_url}/seats/{seat_id}/toggle-maintenance", headers=self._headers())
            return self._handle_response(resp)

    # -------------------------------------------------------------------------
    # Shifts
    # -------------------------------------------------------------------------
    def get_shifts(self) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/shifts", headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    # -------------------------------------------------------------------------
    # Students
    # -------------------------------------------------------------------------
    def get_students(self, search: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/students", params=params, headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    def get_student(self, student_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/students/{student_id}", headers=self._headers())
            return self._handle_response(resp)

    def create_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/students", json=data, headers=self._headers())
            return self._handle_response(resp)

    def update_student(self, student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.put(f"{self.base_url}/students/{student_id}", json=data, headers=self._headers())
            return self._handle_response(resp)

    # -------------------------------------------------------------------------
    # Memberships
    # -------------------------------------------------------------------------
    def get_memberships(
        self,
        status: Optional[str] = None,
        student_id: Optional[str] = None,
        seat_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if student_id:
            params["student_id"] = student_id
        if seat_id:
            params["seat_id"] = seat_id
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/memberships", params=params, headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    def get_membership(self, membership_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/memberships/{membership_id}", headers=self._headers())
            return self._handle_response(resp)

    def create_membership(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/memberships", json=data, headers=self._headers())
            return self._handle_response(resp)

    def renew_membership(self, membership_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/memberships/{membership_id}/renew", json=data, headers=self._headers())
            return self._handle_response(resp)

    def cancel_membership(self, membership_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/memberships/{membership_id}/cancel", json=data, headers=self._headers())
            return self._handle_response(resp)

    # -------------------------------------------------------------------------
    # Payments
    # -------------------------------------------------------------------------
    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/payments", json=data, headers=self._headers())
            return self._handle_response(resp)

    def void_payment(self, payment_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/payments/{payment_id}/void", json=data, headers=self._headers())
            return self._handle_response(resp)

    def get_membership_payments(self, membership_id: str) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/memberships/{membership_id}/payments", headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    # -------------------------------------------------------------------------
    # Attendance
    # -------------------------------------------------------------------------
    def check_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/attendance/check-in", json=data, headers=self._headers())
            return self._handle_response(resp)

    def check_out(self, attendance_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{self.base_url}/attendance/{attendance_id}/check-out", headers=self._headers())
            return self._handle_response(resp)

    def get_daily_attendance(self, attendance_date: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if attendance_date:
            params["attendance_date"] = attendance_date
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/attendance/daily", params=params, headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    # -------------------------------------------------------------------------
    # Dashboard & Analytics
    # -------------------------------------------------------------------------
    def get_dashboard_summary(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if target_date:
            params["target_date"] = target_date
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/dashboard/summary", params=params, headers=self._headers())
            return self._handle_response(resp)

    def get_expiring_memberships(self, threshold_days: int = 3) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/reports/expiring", params={"days_threshold": threshold_days}, headers=self._headers())
            data = self._handle_response(resp)
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []

    def get_revenue_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/reports/revenue", params=params, headers=self._headers())
            return self._handle_response(resp)
