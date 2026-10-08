from decimal import Decimal
from fastapi.testclient import TestClient


def create_test_membership(client: TestClient, seat_id=18) -> str:
    """Helper to create a student and an active membership with final fee = 800.00."""
    # 1. Create student
    res_student = client.post("/api/v1/students", json={
        "full_name": f"Payment Test User {seat_id}",
        "mobile": f"98770000{seat_id:02d}",
        "email": f"payuser{seat_id}@example.com"
    })
    student_id = res_student.json()["id"]

    # 2. Create membership (Morning shift 1, base 800)
    res_mem = client.post("/api/v1/memberships", json={
        "student_id": student_id,
        "seat_id": seat_id,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "discount_amount": 0.00
    })
    return res_mem.json()["id"]


def test_payment_installment_and_balance_update(client: TestClient):
    """Verifies paying a partial installment updates live due balance and issues receipt."""
    mem_id = create_test_membership(client, seat_id=21)

    # 1. Record partial payment of 300.00
    pay_res = client.post("/api/v1/payments", json={
        "membership_id": mem_id,
        "amount": 300.00,
        "payment_method": "CASH",
        "notes": "Paid first installment at front desk"
    })
    assert pay_res.status_code == 201
    pay_data = pay_res.json()
    assert pay_data["amount"] == "300.00"
    assert pay_data["status"] == "COMPLETED"
    assert pay_data["receipt_number"].startswith("RCP-")

    # 2. Verify membership balances
    mem_detail = client.get(f"/api/v1/memberships/{mem_id}").json()
    assert Decimal(str(mem_detail["total_paid"])) == Decimal("300.00")
    assert Decimal(str(mem_detail["due_amount"])) == Decimal("500.00")
    assert mem_detail["payment_status"] == "PARTIAL"


def test_full_payment_clears_due_balance(client: TestClient):
    """Verifies completing all payments moves status to PAID with zero due amount."""
    mem_id = create_test_membership(client, seat_id=22)

    # Pay full fee of 800.00
    pay_res = client.post("/api/v1/payments", json={
        "membership_id": mem_id,
        "amount": 800.00,
        "payment_method": "UPI",
        "transaction_ref": "UPI-UTR-11223344"
    })
    assert pay_res.status_code == 201

    mem_detail = client.get(f"/api/v1/memberships/{mem_id}").json()
    assert Decimal(str(mem_detail["total_paid"])) == Decimal("800.00")
    assert Decimal(str(mem_detail["due_amount"])) == Decimal("0.00")
    assert mem_detail["payment_status"] == "PAID"


def test_overpayment_rejected(client: TestClient):
    """Verifies attempting to pay more than outstanding dues is rejected with 400."""
    mem_id = create_test_membership(client, seat_id=23)

    # Attempt to pay 900.00 on 800.00 due
    res = client.post("/api/v1/payments", json={
        "membership_id": mem_id,
        "amount": 900.00,
        "payment_method": "CASH"
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "PAYMENT_EXCEEDS_DUE"


def test_void_payment_workflow(client: TestClient):
    """Verifies voiding a payment restores due balance on the ledger without deleting row."""
    mem_id = create_test_membership(client, seat_id=24)

    # 1. Pay 400.00
    pay_res = client.post("/api/v1/payments", json={
        "membership_id": mem_id,
        "amount": 400.00,
        "payment_method": "UPI",
        "transaction_ref": "UPI-9900"
    })
    assert pay_res.status_code == 201
    pay_id = pay_res.json()["id"]

    # Status before void: total_paid=400, due=400
    before = client.get(f"/api/v1/memberships/{mem_id}").json()
    assert Decimal(str(before["total_paid"])) == Decimal("400.00")

    # 2. Void the payment
    void_res = client.post(f"/api/v1/payments/{pay_id}/void", json={
        "void_reason": "Clerical entry error; student paid cash instead"
    })
    assert void_res.status_code == 200
    voided_data = void_res.json()
    assert voided_data["status"] == "VOIDED"
    assert voided_data["void_reason"] == "Clerical entry error; student paid cash instead"

    # 3. Status after void: total_paid=0, due=800
    after = client.get(f"/api/v1/memberships/{mem_id}").json()
    assert Decimal(str(after["total_paid"])) == Decimal("0.00")
    assert Decimal(str(after["due_amount"])) == Decimal("800.00")
    assert after["payment_status"] == "PENDING"


def test_double_void_rejected(client: TestClient):
    """Verifies that an already-voided payment cannot be voided again."""
    mem_id = create_test_membership(client, seat_id=27)

    pay_id = client.post("/api/v1/payments", json={
        "membership_id": mem_id,
        "amount": 200.00,
        "payment_method": "CASH"
    }).json()["id"]

    # Void first time -> Success
    client.post(f"/api/v1/payments/{pay_id}/void", json={"void_reason": "First valid void reason"})

    # Void second time -> 400 ALREADY_VOIDED
    res_second = client.post(f"/api/v1/payments/{pay_id}/void", json={"void_reason": "Second void attempt"})
    assert res_second.status_code == 400
    assert res_second.json()["error"]["code"] == "ALREADY_VOIDED"


def test_list_membership_payments(client: TestClient):
    """Verifies retrieving historical payments for a membership."""
    mem_id = create_test_membership(client, seat_id=28)

    # Make 2 installment payments
    client.post("/api/v1/payments", json={"membership_id": mem_id, "amount": 200.00, "payment_method": "CASH"})
    client.post("/api/v1/payments", json={"membership_id": mem_id, "amount": 300.00, "payment_method": "UPI"})

    res = client.get(f"/api/v1/memberships/{mem_id}/payments")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2
    assert Decimal(str(history[0]["amount"])) == Decimal("200.00")
    assert Decimal(str(history[1]["amount"])) == Decimal("300.00")
