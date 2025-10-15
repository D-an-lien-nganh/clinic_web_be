from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.payroll import get_performance_payroll
from datetime import date

class PayrollAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("start_date")
        end   = request.query_params.get("end_date")
        user_type = request.query_params.get("type")           # 'employee' / 'collaborator'
        department_id = request.query_params.get("department") # ví dụ: id
        search = request.query_params.get("q")  

        if not start or not end:
            today = date.today()
            start = today.replace(day=1).isoformat()
            end = today.isoformat()

        data = get_performance_payroll(start, end, user_type=user_type, department_id=department_id, search=search)
        return Response(data)
